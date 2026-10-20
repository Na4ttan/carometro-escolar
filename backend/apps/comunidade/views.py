"""
Controladores REST para o Domínio de Comunidade Escolar (Alunos e Professores).

Responsabilidades:
1. AlunoListCreateView: Listagem paginada, busca textual, filtro de turma e cadastro de alunos.
2. ProfessorListCreateView: Gestão de docentes vinculados às turmas da escola.
3. Otimização de Performance: Aplicação de Prefetch com to_attr para eliminar consultas N+1.
"""

from django.db.models import Prefetch
from rest_framework import exceptions, filters, generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from apps.academico.models import Turma
from apps.autenticacao.permissions import PertenceAEscola, PodeVisualizarOuEscolaCria
from .models import Aluno, Matricula, Professor
from .pagination import CarometroPagination
from .serializers import AlunoSerializer, ProfessorSerializer


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
        turma_filtro = self.request.query_params.get("turma") or self.request.query_params.get("turma_id")

        # Escopo do Administrador da Escola
        if hasattr(user, "escola") and user.escola.ativo:
            prefetch_matricula = Prefetch(
                "matriculas",
                queryset=Matricula.objects.filter(
                    status=Matricula.Status.ATIVA,
                    turma__ano_letivo__escola=user.escola,
                ).select_related("turma__ano_letivo"),
                to_attr="matriculas_ativas",
            )
            qs = Aluno.objects.filter(
                matriculas__turma__ano_letivo__escola=user.escola,
                matriculas__status=Matricula.Status.ATIVA,
                ativo=True,
            )

        # Escopo do Professor (somente turmas atribuídas)
        elif hasattr(user, "professor") and user.professor.ativo:
            prefetch_matricula = Prefetch(
                "matriculas",
                queryset=Matricula.objects.filter(
                    status=Matricula.Status.ATIVA,
                    turma__in=user.professor.turmas.all(),
                ).select_related("turma__ano_letivo"),
                to_attr="matriculas_ativas",
            )
            qs = Aluno.objects.filter(
                matriculas__turma__in=user.professor.turmas.all(),
                matriculas__status=Matricula.Status.ATIVA,
                ativo=True,
            )
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
        turma_filtro = self.request.query_params.get("turma") or self.request.query_params.get("turma_id")

        # Pré-carrega turmas da escola de forma ordenada para leitura imediata no serializer
        prefetch_turmas = Prefetch(
            "turmas",
            queryset=Turma.objects.filter(
                ano_letivo__escola=user.escola
            ).select_related("ano_letivo").order_by("serie", "nome"),
            to_attr="turmas_da_escola",
        )

        qs = Professor.objects.filter(
            turmas__ano_letivo__escola=user.escola
        )

        # Filtro de turma fornecido na query string
        if turma_filtro:
            qs = qs.filter(turmas__id=turma_filtro)

        return qs.prefetch_related(prefetch_turmas).distinct()
