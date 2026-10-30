"""
Camada de Serviços (Service Layer) para Alunos.

Centraliza toda a lógica de negócio cadastral de alunos:
1. Validação de regras de negócio (duplicidade de matrícula, pertencimento da turma à escola).
2. Orquestração de persistência transacional atômica (@transaction.atomic).
3. Enfileiramento do processamento facial inteligente em segundo plano.
"""

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Value
from django.db.models.functions import Replace, Trim

from apps.academico.models import Turma
from apps.comunidade.models import Aluno, Matricula
from apps.processamento.async_worker import enfileirar_processamento_aluno


class AlunoService:
    """
    Serviço que encapsula regras de negócio do aluno.
    Isola os Models e Views do acoplamento direto com validações complexas.
    """

    @staticmethod
    def normalizar_matricula(matricula):
        """Remove pontos e hífens usados apenas para formatar a matrícula."""
        if matricula is None:
            return None
        return re.sub(r"[.-]", "", str(matricula)).strip()

    @classmethod
    def validar_matricula(cls, matricula, aluno_id=None):
        """
        Garante que o código de matrícula seja único na base de dados.
        Se aluno_id for fornecido (edição), ignora o próprio registro.
        """
        if not matricula:
            return
        matricula_normalizada = cls.normalizar_matricula(matricula)
        query = Aluno.objects.exclude(matricula__isnull=True).exclude(matricula="")
        if aluno_id:
            query = query.exclude(id=aluno_id)
        matricula_sem_formatacao = Replace(
            Replace(F("matricula"), Value("."), Value("")),
            Value("-"),
            Value(""),
        )
        if query.annotate(
            matricula_normalizada=Trim(matricula_sem_formatacao)
        ).filter(matricula_normalizada=matricula_normalizada).exists():
            raise ValidationError({"matricula": "Já existe um aluno cadastrado com este número de matrícula."})

    @classmethod
    def validar_turma(cls, turma, escola=None):
        """
        Valida a consistência da turma selecionada:
        - Deve existir e estar ativa, assim como seu ano letivo.
        - Se a escola do gestor for fornecida, garante que a turma pertence a ela.
        """
        if not turma:
            raise ValidationError({"turma": "É necessário informar uma turma."})

        if isinstance(turma, int):
            try:
                turma = Turma.objects.select_related("ano_letivo__escola").get(id=turma)
            except Turma.DoesNotExist:
                raise ValidationError({"turma": "Turma informada não foi encontrada."})

        if not turma.ativo or not turma.ano_letivo.ativo:
            raise ValidationError({"turma": "A turma informada ou seu ano letivo estão inativos."})

        if escola and turma.ano_letivo.escola_id != escola.id:
            raise ValidationError({"turma": "A turma informada não pertence à sua escola."})

        return turma

    @classmethod
    @transaction.atomic
    def criar_aluno(cls, dados, turma, escola=None):
        """
        Fluxo completo de criação do Aluno em transação atômica:
        1. Valida a turma e a matrícula.
        2. Instancia e salva o Aluno com a foto original enviada pelo usuário.
        3. Cria o vínculo de Matrícula ativa com a Turma.
        4. Enfileira o processamento pesado de corte e detecção facial (OpenCV)
           em background worker, respondendo imediatamente a requisição HTTP.
        """
        turma_obj = cls.validar_turma(turma, escola=escola)
        matricula_val = cls.normalizar_matricula(dados.get("matricula") or "")
        if not matricula_val:
            raise ValidationError({"matricula": "A matrícula do aluno é obrigatória."})
        cls.validar_matricula(matricula_val)

        foto = dados.get("foto")
        aluno = Aluno(
            nome_completo=dados.get("nome_completo"),
            nome_social=dados.get("nome_social") or "",
            data_nascimento=dados.get("data_nascimento"),
            matricula=matricula_val,
            foto=foto,
            ativo=dados.get("ativo", True),
        )
        # Evita enfileiramento duplicado no model.save() já que chamaremos o worker explicitamente
        if foto:
            from apps.processamento.services.imagem_service import ImagemService
            aluno.foto_base64 = ImagemService.arquivo_para_data_uri(foto)
        aluno._skip_async = True
        aluno.save()

        # Vincula o aluno à turma com matrícula ativa
        Matricula.objects.create(
            aluno=aluno,
            turma=turma_obj,
            status=Matricula.Status.ATIVA,
        )

        # Enfileira o processamento de imagem em background
        if aluno.foto:
            enfileirar_processamento_aluno(aluno.id)
            # Em modo síncrono (ex: suíte de testes), recarrega a instância com a foto processada
            if not getattr(settings, "CAROMETRO_ASYNC_IMAGE_PROCESSING", True):
                aluno.refresh_from_db()

        return aluno


def criar_aluno(dados, turma, escola=None):
    """Atalho funcional para AlunoService.criar_aluno."""
    return AlunoService.criar_aluno(dados, turma=turma, escola=escola)
