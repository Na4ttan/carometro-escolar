"""
Módulo de Processamento Assíncrono de Imagens (Worker em Background).

Responsabilidades:
1. Desacoplamento da requisição HTTP: Libera a resposta para o navegador em < 100ms.
2. Gerenciamento de pool de threads nativo via concurrent.futures.ThreadPoolExecutor.
3. Prevenção de condições de corrida (Race Conditions): Assegura execução após o commit do banco com transaction.on_commit.
4. Suporte a execução síncrona controlada para automação de testes e comandos de terminal.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.db import connection, transaction

logger = logging.getLogger(__name__)

# Pool de threads dedicado para processamento gráfico em segundo plano (2 workers simultâneos)
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="carometro_img_worker")
_FUTURES = []


def _processar_foto_aluno(aluno_id):
    """
    Função executada na thread de segundo plano para processar a foto do aluno:
    - Recupera a instância do Aluno no banco.
    - Executa o enquadramento facial inteligente via ImagemService.
    - Atualiza os campos 'foto' e 'atualizado_em' sem re-disparar o worker.
    """
    from apps.comunidade.models import Aluno
    from apps.processamento.services.imagem_service import ImagemService

    try:
        aluno = Aluno.objects.filter(id=aluno_id).first()
        if not aluno or not aluno.foto:
            return False

        sucesso = ImagemService.processar_foto(aluno.foto, force=True)
        if sucesso:
            # Sinaliza _skip_async para evitar que o model.save() enfileire outra tarefa recursivamente
            aluno._skip_async = True
            aluno.save(update_fields=["foto", "atualizado_em"])
            logger.info(f"[Async] Foto do aluno '{aluno.nome_completo}' processada com sucesso.")
            return True
    except Exception as exc:
        logger.error(f"[Async] Falha no processamento da foto do aluno {aluno_id}: {exc}")
    return False


def _processar_foto_professor(professor_id):
    """
    Função executada na thread de segundo plano para processar a foto do professor:
    - Recupera a instância do Professor no banco.
    - Executa o enquadramento facial inteligente via ImagemService.
    - Atualiza os campos 'foto' e 'atualizado_em' sem re-disparar o worker.
    """
    from apps.comunidade.models import Professor
    from apps.processamento.services.imagem_service import ImagemService

    try:
        prof = Professor.objects.filter(id=professor_id).first()
        if not prof or not prof.foto:
            return False

        sucesso = ImagemService.processar_foto(prof.foto, force=True)
        if sucesso:
            # Evita recursão infinita no save
            prof._skip_async = True
            prof.save(update_fields=["foto", "atualizado_em"])
            logger.info(f"[Async] Foto do professor '{prof.nome_completo}' processada com sucesso.")
            return True
    except Exception as exc:
        logger.error(f"[Async] Falha no processamento da foto do professor {professor_id}: {exc}")
    return False


def enfileirar_processamento_aluno(aluno_id, sync=False):
    """
    Enfileira o processamento pesado de OpenCV da foto do aluno.

    Mecanismo de segurança transacional:
    - Se houver uma transação de banco aberta (ex: dentro de @transaction.atomic),
      utiliza transaction.on_commit para agendar o envio à thread SOMENTE DEPOIS
      que os dados estiverem fisicamente comitados no banco de dados. Isso impede que
      a thread tente buscar um registro ainda invisível.
    - Se sync=True ou se CAROMETRO_ASYNC_IMAGE_PROCESSING=False nas configurações,
      executa imediatamente na mesma thread (modo síncrono).
    """
    is_async = getattr(settings, "CAROMETRO_ASYNC_IMAGE_PROCESSING", True) and not sync

    if is_async:
        def agendar():
            future = _EXECUTOR.submit(_processar_foto_aluno, aluno_id)
            _FUTURES.append(future)

        if connection.in_atomic_block:
            transaction.on_commit(agendar)
        else:
            agendar()
    else:
        _processar_foto_aluno(aluno_id)


def enfileirar_processamento_professor(professor_id, sync=False):
    """
    Enfileira o processamento pesado de OpenCV da foto do professor.
    Segue a mesma garantia transacional do enfileirar_processamento_aluno.
    """
    is_async = getattr(settings, "CAROMETRO_ASYNC_IMAGE_PROCESSING", True) and not sync

    if is_async:
        def agendar():
            future = _EXECUTOR.submit(_processar_foto_professor, professor_id)
            _FUTURES.append(future)

        if connection.in_atomic_block:
            transaction.on_commit(agendar)
        else:
            agendar()
    else:
        _processar_foto_professor(professor_id)


def aguardar_conclusao_tarefas(timeout=10):
    """
    Bloqueia temporariamente até que todas as tarefas da fila sejam concluídas.
    Utilizado principalmente em testes de integração e encerramento de processos.
    """
    global _FUTURES
    for future in list(_FUTURES):
        try:
            future.result(timeout=timeout)
        except Exception:
            pass
    _FUTURES.clear()
