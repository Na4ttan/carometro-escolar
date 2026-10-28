"""Importa listas CSV de alunos para as turmas já cadastradas da escola."""

import csv
import io
import re
import unicodedata

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from apps.academico.models import AnoLetivo, Turma
from apps.comunidade.models import Aluno, Matricula


SINONIMOS_COLUNAS = {
    "serie": {"serie", "ano", "ano escolar", "serie ano", "ano serie", "serie escolar", "turma", "classe"},
    "nome": {"nome", "nome completo", "aluno", "estudante", "nome do aluno", "nome do estudante", "nome completo do aluno", "nome completo do estudante"},
    "matricula": {"matricula", "matricula escolar", "n matricula", "numero matricula", "numero de matricula", "ra escolar", "codigo do aluno", "registro do aluno", "rm"},
}


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()


def _ler_csv(arquivo):
    bruto = arquivo.read()
    texto = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            texto = bruto.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if texto is None:
        raise ValueError("Não foi possível decodificar o arquivo CSV.")
    amostra = texto[:8192]
    try:
        dialeto = csv.Sniffer().sniff(amostra, delimiters=";,\t|")
        linhas = csv.DictReader(io.StringIO(texto), dialect=dialeto)
    except csv.Error:
        delimiter = ";" if amostra.count(";") > amostra.count(",") else ","
        linhas = csv.DictReader(io.StringIO(texto), delimiter=delimiter)
    if not linhas.fieldnames:
        raise ValueError("O CSV precisa ter uma linha de cabeçalho.")

    colunas = {}
    for campo in linhas.fieldnames:
        chave = _normalizar(campo)
        for destino, sinonimos in SINONIMOS_COLUNAS.items():
            if chave in sinonimos or any(chave.startswith(s + " ") for s in sinonimos):
                colunas[destino] = campo
                break
    faltantes = [campo for campo in ("serie", "nome", "matricula") if campo not in colunas]
    if faltantes:
        nomes = {"serie": "série", "nome": "nome completo", "matricula": "matrícula"}
        raise ValueError("Não encontrei as colunas obrigatórias: " + ", ".join(nomes[c] for c in faltantes) + ".")
    return [
        {destino: (linha.get(coluna) or "").strip() for destino, coluna in colunas.items()}
        for linha in linhas
    ]


def _extrair_turma(valor):
    normalizado = _normalizar(valor)
    # O ordinal "8º" vira "8o" ao remover o acento/normalizar o CSV.
    match = re.search(r"\b(\d{1,2})[oa]?\b", normalizado)
    if not match:
        return None, None
    serie = int(match.group(1))
    termos_ensino = {"ano", "serie", "ensino", "fundamental", "medio", "em", "ef", "do", "da"}
    secao = next(
        (parte for parte in normalizado[match.end():].split() if parte not in termos_ensino),
        None,
    )
    return serie, secao.upper() if secao else None


def _matricula_normalizada(valor):
    return re.sub(r"\s+", "", valor).replace(".", "").replace("-", "")


def _encontrar_ou_criar_turma(escola, serie, secao, nivel_ensino):
    if not secao:
        return None, "não foi possível identificar a seção da turma na coluna de série"

    ano_letivo = AnoLetivo.objects.filter(escola=escola, ativo=True).order_by("-ano").first()
    if not ano_letivo:
        return None, "a escola não possui ano letivo ativo para cadastrar a turma"

    turma = Turma.objects.filter(
        ano_letivo=ano_letivo,
        nivel_ensino=nivel_ensino,
        serie=serie,
        nome__iexact=secao,
    ).first()
    if turma:
        if not turma.ativo:
            turma.ativo = True
            turma.save(update_fields=["ativo"])
        return turma, None

    turno = _turno_mais_comum(
        Turma.objects.filter(ano_letivo=ano_letivo, nivel_ensino=nivel_ensino, serie=serie)
    )
    if not turno:
        turno = _turno_mais_comum(
            Turma.objects.filter(ano_letivo=ano_letivo, nivel_ensino=nivel_ensino)
        )
    if not turno:
        turno = Turma.Turno.MANHA

    turma = Turma.objects.create(
        ano_letivo=ano_letivo,
        nivel_ensino=nivel_ensino,
        serie=serie,
        nome=secao,
        turno=turno,
    )
    return turma, None


def _turno_mais_comum(turmas):
    return (
        turmas.values("turno")
        .annotate(total=Count("id"))
        .order_by("-total", "turno")
        .values_list("turno", flat=True)
        .first()
    )


def _salvar_aluno(linha, escola, turma):
    nome = linha["nome"].strip()
    matricula = _matricula_normalizada(linha["matricula"])
    if not nome:
        raise ValueError("nome completo vazio")
    if not matricula:
        raise ValueError("matrícula vazia")

    with transaction.atomic():
        alunos_escola = Aluno.objects.filter(matriculas__turma__ano_letivo__escola=escola).distinct()
        existente = next(
            (aluno for aluno in alunos_escola if _matricula_normalizada(aluno.matricula or "") == matricula),
            None,
        )
        primeiro_nome = nome.split()[0]
        if existente:
            existente.nome_completo = nome
            existente.nome_social = primeiro_nome
            existente.matricula = matricula
            existente.save(update_fields=["nome_completo", "nome_social", "matricula", "atualizado_em"])
            matricula_atual = existente.matriculas.filter(
                status=Matricula.Status.ATIVA,
                turma__ano_letivo__escola=escola,
            ).select_related("turma").first()
            if matricula_atual and matricula_atual.turma_id == turma.id:
                return "atualizado"
            if matricula_atual:
                matricula_atual.status = Matricula.Status.TRANSFERIDA
                matricula_atual.data_saida = timezone.localdate()
                matricula_atual.save(update_fields=["status", "data_saida"])
            destino = existente.matriculas.filter(turma=turma).first()
            if destino:
                destino.status = Matricula.Status.ATIVA
                destino.data_saida = None
                destino.save(update_fields=["status", "data_saida"])
            else:
                Matricula.objects.create(aluno=existente, turma=turma)
            return "atualizado"

        aluno_com_matricula = next(
            (aluno for aluno in Aluno.objects.exclude(matricula__isnull=True).exclude(matricula="")
             if _matricula_normalizada(aluno.matricula) == matricula),
            None,
        )
        if aluno_com_matricula:
            raise ValueError("matrícula já pertence a aluno de outra escola")
        aluno = Aluno.objects.create(
            nome_completo=nome,
            nome_social=primeiro_nome,
            matricula=matricula,
        )
        Matricula.objects.create(aluno=aluno, turma=turma)
        return "criado"


def importar_alunos_csv(arquivo, escola, nivel_ensino):
    if nivel_ensino not in (Turma.NivelEnsino.FUNDAMENTAL, Turma.NivelEnsino.MEDIO):
        raise ValueError("Selecione ensino fundamental ou ensino médio.")
    linhas = _ler_csv(arquivo)
    resultado = {"criados": 0, "atualizados": 0, "erros": []}
    for numero, linha in enumerate(linhas, start=2):
        serie, secao = _extrair_turma(linha["serie"])
        if serie is None:
            resultado["erros"].append({"linha": numero, "mensagem": "série inválida"})
            continue
        turma, erro_turma = _encontrar_ou_criar_turma(escola, serie, secao, nivel_ensino)
        if not turma:
            resultado["erros"].append({
                "linha": numero,
                "mensagem": erro_turma,
            })
            continue
        try:
            status = _salvar_aluno(linha, escola, turma)
            resultado["criados" if status == "criado" else "atualizados"] += 1
        except ValueError as exc:
            resultado["erros"].append({"linha": numero, "mensagem": str(exc)})
    resultado["processados"] = resultado["criados"] + resultado["atualizados"]
    return resultado
