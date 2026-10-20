"""
Controladores REST para o Domínio Acadêmico.

Disponibiliza os dados de:
1. EscolaView: Informações da instituição do usuário logado.
2. TurmaListView: Lista de turmas ativas visíveis para o usuário (escola ou professor logado).
"""

from rest_framework import filters, generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.autenticacao.permissions import PertenceAEscola
from .models import Turma
from .serializers import EscolaSerializer, TurmaSerializer


class EscolaView(APIView):
    """
    Endpoint: GET /api/escola/
    Retorna os detalhes da escola à qual o administrador autenticado está vinculado.
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PertenceAEscola)

    def get(self, request):
        return Response(EscolaSerializer(request.user.escola).data)


class TurmaListView(generics.ListAPIView):
    """
    Endpoint: GET /api/turmas/
    Lista as turmas ativas de acordo com o contexto do usuário:
    - Se for Escola: exibe todas as turmas ativas do ano letivo vigente da escola.
    - Se for Professor: exibe somente as turmas ativas que foram atribuídas a este professor.

    Recursos:
    - Otimização de SQL com select_related("ano_letivo") para evitar consultas redundantes.
    - Busca via ?search= pelo nome ou série da turma.
    - Ordenação padrão por série e nome.
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = TurmaSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("nome", "serie")
    ordering_fields = ("serie", "nome")
    ordering = ("serie", "nome")

    def get_queryset(self):
        user = self.request.user

        # Gestor da escola: vê todas as turmas ativas da instituição
        if hasattr(user, "escola") and user.escola.ativo:
            return Turma.objects.filter(
                ano_letivo__escola=user.escola,
                ano_letivo__ativo=True,
                ativo=True,
            ).select_related("ano_letivo")

        # Professor: vê apenas as turmas a ele atribuídas
        elif hasattr(user, "professor") and user.professor.ativo:
            return user.professor.turmas.filter(
                ano_letivo__ativo=True,
                ativo=True,
            ).select_related("ano_letivo")

        # Sem perfil reconhecido: lista vazia
        return Turma.objects.none()
