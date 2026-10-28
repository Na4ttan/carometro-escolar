"""
Controladores REST para o Domínio de Comunidade Escolar (Alunos e Professores).

Responsabilidades:
1. AlunoListCreateView: Listagem paginada, busca textual, filtro de turma e cadastro de alunos.
2. ProfessorListCreateView: Gestão de docentes vinculados às turmas da escola.
3. Otimização de Performance: Aplicação de Prefetch com to_attr para eliminar consultas N+1.
"""

from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import exceptions, filters, generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.academico.models import Turma
from apps.autenticacao.permissions import (
    PodeEditarAluno,
    PertenceAEscola,
    PodeVisualizarOuEscolaCria,
)
from .models import Aluno, Matricula, Professor
from .pagination import CarometroPagination
from .serializers import AlunoSerializer, ProfessorSerializer
from .services.importacao_alunos import importar_alunos_csv


class AlunoListCreateView(generics.ListCreateAPIView):
    """
    Endpoint: GET e POST /api/alunos/

    Comportamento no GET (Consulta / Carômetro):
    - Escola: visualiza todos os alunos ativos da sua instituição.
    - Professor: visualiza somente os alunos matriculados nas suas turmas atribuídas.
    - Suporta busca via ?search= (nome_completo, nome_social, matricula).
    - Suporta filtro direto no banco de dados via ?turma= ou ?turma_id=.
    - Suporta paginação via ?page= e ?page_size= (ou ?sem_paginacao=true).
    - Pré-carrega matrículas ativas em memória com Prefetch(..., to_attr="matriculas_ativas")
      para eliminar consultas adicionais no serializer.

    Comportamento no POST (Cadastro):
    - Restrito a administradores da Escola.
    - Cria o aluno, matricula na turma e enfileira o processamento facial inteligente.
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PodeVisualizarOuEscolaCria)
    serializer_class = AlunoSerializer
    pagination_class = CarometroPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("nome_completo", "nome_social", "matricula")
    ordering_fields = ("nome_completo", "matricula", "criado_em")
    ordering = ("nome_completo",)

    def get_queryset(self):
        user = self.request.user
        incluir_arquivados = self.request.query_params.get("incluir_arquivados") == "true"
        turma_filtro = self.request.query_params.get("turma") or self.request.query_params.get("turma_id")
        ano_letivo_filtro = self.request.query_params.get("ano_letivo")
        try:
            ano_letivo_filtro = int(ano_letivo_filtro) if ano_letivo_filtro else None
        except (TypeError, ValueError):
            ano_letivo_filtro = -1

        # Escopo do Administrador da Escola
        if hasattr(user, "escola") and user.escola.ativo:
            matriculas_escola = Matricula.objects.filter(
                status=Matricula.Status.ATIVA,
                turma__ano_letivo__escola=user.escola,
            )
            if not incluir_arquivados:
                matriculas_escola = matriculas_escola.filter(turma__ativo=True)
            if ano_letivo_filtro is not None:
                matriculas_escola = matriculas_escola.filter(turma__ano_letivo_id=ano_letivo_filtro)
            prefetch_matricula = Prefetch(
                "matriculas",
                queryset=matriculas_escola.select_related("turma__ano_letivo"),
                to_attr="matriculas_ativas",
            )
            qs = Aluno.objects.filter(matriculas__turma__ano_letivo__escola=user.escola)
            if not incluir_arquivados:
                qs = qs.filter(matriculas__status=Matricula.Status.ATIVA, matriculas__turma__ativo=True, ativo=True)
            if ano_letivo_filtro is not None:
                qs = qs.filter(matriculas__turma__ano_letivo_id=ano_letivo_filtro)

        # Escopo do Professor (somente turmas atribuídas)
        elif hasattr(user, "professor") and user.professor.ativo:
            turmas_professor = user.professor.turmas.all()
            matriculas_professor = Matricula.objects.filter(
                status=Matricula.Status.ATIVA,
                turma__in=turmas_professor,
            )
            if ano_letivo_filtro is not None:
                matriculas_professor = matriculas_professor.filter(turma__ano_letivo_id=ano_letivo_filtro)
            prefetch_matricula = Prefetch(
                "matriculas",
                queryset=matriculas_professor.select_related("turma__ano_letivo"),
                to_attr="matriculas_ativas",
            )
            qs = Aluno.objects.filter(
                matriculas__turma__in=user.professor.turmas.filter(ativo=True),
                matriculas__status=Matricula.Status.ATIVA,
            )
            if not incluir_arquivados:
                qs = qs.filter(ativo=True)
            if ano_letivo_filtro is not None:
                qs = qs.filter(matriculas__turma__ano_letivo_id=ano_letivo_filtro)
        else:
            return Aluno.objects.none()

        # Filtro de turma fornecido na query string (?turma=ID)
        if turma_filtro:
            qs = qs.filter(matriculas__turma_id=turma_filtro, matriculas__status=Matricula.Status.ATIVA)

        return qs.prefetch_related(prefetch_matricula).distinct()

    def perform_create(self, serializer):
        """Garante permissão exclusiva da escola no momento da criação."""
        user = self.request.user
        if not (hasattr(user, "escola") and user.escola.ativo):
            raise exceptions.PermissionDenied(
                "Apenas a administração da escola pode cadastrar alunos."
            )
        serializer.save()


class AlunoImportarCsvView(APIView):
    """Importa alunos de um CSV para as turmas já existentes da escola."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PertenceAEscola)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        arquivo = request.FILES.get("arquivo")
        if not arquivo:
            return Response({"detail": "Anexe um arquivo CSV."}, status=status.HTTP_400_BAD_REQUEST)
        if not arquivo.name.lower().endswith(".csv"):
            return Response({"detail": "O arquivo precisa ter extensão .csv."}, status=status.HTTP_400_BAD_REQUEST)
        nivel_ensino = request.data.get("nivel_ensino")
        if nivel_ensino not in (Turma.NivelEnsino.FUNDAMENTAL, Turma.NivelEnsino.MEDIO):
            return Response(
                {"detail": "Selecione ensino fundamental ou ensino médio."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            resultado = importar_alunos_csv(arquivo, request.user.escola, nivel_ensino)
        except (ValueError, UnicodeError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(resultado, status=status.HTTP_200_OK)


class ProfessorListCreateView(generics.ListCreateAPIView):
    """
    Endpoint: GET e POST /api/professores/

    Comportamento no GET:
    - Retorna a lista de professores vinculados às turmas da escola do usuário logado.
    - Suporta busca via ?search= (nome, email, matricula funcional).
    - Suporta filtro por turma via ?turma=.
    - Pré-carrega as turmas associadas via Prefetch(..., to_attr="turmas_da_escola").

    Comportamento no POST:
    - Restrito a administradores da Escola.
    - Cria o registro do professor, gera o usuário Django com hash de senha e vincula às turmas.
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PertenceAEscola)
    serializer_class = ProfessorSerializer
    pagination_class = CarometroPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("nome_completo", "email", "matricula_funcional")
    ordering_fields = ("nome_completo", "email", "criado_em")
    ordering = ("nome_completo",)

    def get_queryset(self):
        user = self.request.user
        incluir_arquivados = self.request.query_params.get("incluir_arquivados") == "true"
        turma_filtro = self.request.query_params.get("turma") or self.request.query_params.get("turma_id")
        ano_letivo_filtro = self.request.query_params.get("ano_letivo")
        try:
            ano_letivo_filtro = int(ano_letivo_filtro) if ano_letivo_filtro else None
        except (TypeError, ValueError):
            ano_letivo_filtro = -1

        turmas_da_escola = Turma.objects.filter(ano_letivo__escola=user.escola)
        qs = Professor.objects.filter(turmas__ano_letivo__escola=user.escola)
        if not incluir_arquivados:
            turmas_da_escola = turmas_da_escola.filter(ativo=True)
            qs = qs.filter(ativo=True, turmas__ativo=True)
        if ano_letivo_filtro is not None:
            turmas_da_escola = turmas_da_escola.filter(ano_letivo_id=ano_letivo_filtro)
            qs = qs.filter(turmas__ano_letivo_id=ano_letivo_filtro)

        # Pré-carrega turmas da escola de forma ordenada para leitura imediata no serializer
        prefetch_turmas = Prefetch(
            "turmas",
            queryset=turmas_da_escola.select_related("ano_letivo").order_by("serie", "nome"),
            to_attr="turmas_da_escola",
        )

        # Filtro de turma fornecido na query string
        if turma_filtro:
            qs = qs.filter(turmas__id=turma_filtro)

        return qs.prefetch_related(prefetch_turmas).distinct()


class AlunoDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PodeEditarAluno)
    serializer_class = AlunoSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "escola") and user.escola.ativo:
            return Aluno.objects.filter(
                matriculas__turma__ano_letivo__escola=user.escola
            ).distinct()
        if hasattr(user, "professor") and user.professor.ativo:
            return Aluno.objects.filter(
                matriculas__turma__in=user.professor.turmas.filter(ativo=True),
                matriculas__status=Matricula.Status.ATIVA,
            ).distinct()
        return Aluno.objects.none()

    def perform_destroy(self, instance):
        foto = instance.foto
        instance.delete()
        if foto:
            transaction.on_commit(lambda: foto.storage.delete(foto.name))


class ProfessorDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PertenceAEscola)
    serializer_class = ProfessorSerializer

    def get_queryset(self):
        return Professor.objects.filter(turmas__ano_letivo__escola=self.request.user.escola).distinct()

    def perform_destroy(self, instance):
        usuario = instance.usuario
        foto = instance.foto
        instance.delete()
        if foto:
            transaction.on_commit(lambda: foto.storage.delete(foto.name))
        if usuario:
            usuario.delete()


class AlunoArquivarView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PodeEditarAluno)

    def post(self, request, pk, acao):
        if acao not in ("arquivar", "restaurar"):
            return Response({"detail": "Ação inválida."}, status=400)
        user = request.user
        if hasattr(user, "escola") and user.escola.ativo:
            alunos = Aluno.objects.filter(matriculas__turma__ano_letivo__escola=user.escola)
        else:
            alunos = Aluno.objects.filter(
                matriculas__turma__in=user.professor.turmas.filter(ativo=True),
                matriculas__status=Matricula.Status.ATIVA,
            )
        aluno = get_object_or_404(alunos.distinct(), pk=pk)
        aluno.ativo = acao == "restaurar"
        aluno.save(update_fields=["ativo", "atualizado_em"])
        return Response(AlunoSerializer(aluno, context={"request": request}).data)


class ProfessorArquivarView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PertenceAEscola)

    def post(self, request, pk, acao):
        if acao not in ("arquivar", "restaurar"):
            return Response({"detail": "Ação inválida."}, status=400)
        professor = get_object_or_404(
            Professor.objects.filter(turmas__ano_letivo__escola=request.user.escola).distinct(),
            pk=pk,
        )
        professor.ativo = acao == "restaurar"
        professor.save(update_fields=["ativo", "atualizado_em"])
        return Response(ProfessorSerializer(professor, context={"request": request}).data)
