"""
Camada de Serviços (Service Layer) para Professores.

Centraliza toda a lógica de negócio cadastral de professores:
1. Validação de regras de negócio (e-mail único, pertencimento das turmas à escola).
2. Validação e encriptação de senhas (mínimo 6 caracteres, checagem de confirmação).
3. Criação ou sincronização de contas de usuário Django (User) com hash seguro.
4. Associação M2M com turmas escolares.
5. Enfileiramento do processamento facial inteligente em segundo plano.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.academico.models import Turma
from apps.comunidade.models import Professor
from apps.processamento.async_worker import enfileirar_processamento_professor


class ProfessorService:
    """
    Serviço que encapsula regras de negócio do professor.
    Garante consistência entre a tabela de Professores e a tabela de Usuários do Django.
    """

    @classmethod
    def validar_email(cls, email, professor_id=None):
        """Valida formato básico e unicidade do e-mail do professor."""
        if not email:
            raise ValidationError({"email": "O e-mail é obrigatório."})
        email_clean = email.strip().lower()
        query = Professor.objects.filter(email__iexact=email_clean)
        if professor_id:
            query = query.exclude(id=professor_id)
        if query.exists():
            raise ValidationError({"email": "Já existe um professor cadastrado com este e-mail."})
        return email_clean

    @classmethod
    def validar_turmas(cls, turmas, escola=None):
        """
        Valida a lista de turmas atribuídas ao professor:
        - Deve conter ao menos uma turma.
        - Todas as turmas e anos letivos devem estar ativos.
        - Devem pertencer à escola do administrador que está realizando o cadastro.
        """
        if not turmas:
            raise ValidationError({"turmas": "Associe o professor a pelo menos uma turma."})

        turmas_resolvidas = []
        for t in turmas:
            if isinstance(t, int):
                try:
                    t_obj = Turma.objects.select_related("ano_letivo__escola").get(id=t)
                except Turma.DoesNotExist:
                    raise ValidationError({"turmas": f"Turma com id {t} não encontrada."})
            else:
                t_obj = t

            if not t_obj.ativo or not t_obj.ano_letivo.ativo:
                raise ValidationError({"turmas": f"A turma {t_obj} ou seu ano letivo estão inativos."})

            if escola and t_obj.ano_letivo.escola_id != escola.id:
                raise ValidationError({"turmas": f"A turma {t_obj} não pertence à sua escola."})

            turmas_resolvidas.append(t_obj)

        return turmas_resolvidas

    @classmethod
    def validar_senha(cls, senha, confirmacao_senha=None):
        """Valida tamanho mínimo e correspondência da confirmação de senha."""
        if not senha or len(senha) < 6:
            raise ValidationError({"senha": "A senha deve ter no mínimo 6 caracteres."})
        if confirmacao_senha is not None and senha != confirmacao_senha:
            raise ValidationError({"confirmacao_senha": "A senha e a confirmação de senha não coincidem."})

    @classmethod
    @transaction.atomic
    def criar_professor(cls, dados, turmas, escola=None):
        """
        Fluxo completo de criação do Professor em transação atômica:
        1. Validação de e-mail, senha e turmas.
        2. Instancia o Professor e calcula o hash seguro da senha.
        3. Cria ou localiza a conta User do Django com a mesma senha (para compatibilidade com DRF Token).
        4. Salva o registro e vincula as turmas (ManyToMany).
        5. Enfileira o processamento facial inteligente em segundo plano.
        """
        email_clean = cls.validar_email(dados.get("email"))
        senha = dados.get("senha")
        confirmacao = dados.get("confirmacao_senha")
        cls.validar_senha(senha, confirmacao)

        turmas_objs = cls.validar_turmas(turmas, escola=escola)

        foto = dados.get("foto")
        professor = Professor(
            nome_completo=dados.get("nome_completo"),
            email=email_clean,
            matricula_funcional=dados.get("matricula_funcional") or None,
            foto=foto,
            ativo=dados.get("ativo", True),
        )
        professor.set_password(senha)

        # 1. Cria ou atualiza usuário padrão de autenticação do Django
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username=email_clean,
            defaults={"email": email_clean},
        )
        user.set_password(senha)
        user.save()
        professor.usuario = user
        professor._skip_async = True
        professor.save()

        # 2. Associa turmas
        professor.turmas.set(turmas_objs)

        # 3. Enfileira o processamento de imagem em background
        if professor.foto:
            enfileirar_processamento_professor(professor.id)
            if not getattr(settings, "CAROMETRO_ASYNC_IMAGE_PROCESSING", True):
                professor.refresh_from_db()

        return professor

    @classmethod
    def redefinir_senha(cls, professor, nova_senha):
        """
        Redefine a senha do professor com segurança:
        - Valida a nova senha (mínimo 6 caracteres).
        - Atualiza o hash no model Professor.
        - Sincroniza a senha na conta de usuário do Django vinculada.
        """
        cls.validar_senha(nova_senha)
        professor.set_password(nova_senha)

        User = get_user_model()
        if not professor.usuario:
            user, _ = User.objects.get_or_create(
                username=professor.email,
                defaults={"email": professor.email},
            )
            professor.usuario = user

        professor.usuario.set_password(nova_senha)
        professor.usuario.save()
        professor.save(update_fields=["senha", "usuario"])
        return professor


def criar_professor(dados, turmas, escola=None):
    """Atalho funcional para ProfessorService.criar_professor."""
    return ProfessorService.criar_professor(dados, turmas=turmas, escola=escola)
