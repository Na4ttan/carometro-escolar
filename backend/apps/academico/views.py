"""
Controladores REST para o Domínio Acadêmico.

Disponibiliza os dados de:
1. EscolaView: Informações da instituição do usuário logado.
2. TurmaListView: Lista de turmas ativas visíveis para o usuário (escola ou professor logado).
"""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.autenticacao.permissions import PertenceAEscola, PodeVisualizarOuEscolaCria
from .models import AnoLetivo, Escola, Turma
from .serializers import AnoLetivoSerializer, EscolaSerializer, TurmaSerializer


class EscolaView(APIView):
    """
    Endpoint: GET /api/escola/
    Retorna os detalhes da escola à qual o administrador autenticado está vinculado.
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PertenceAEscola)

    def get(self, request):
        return Response(EscolaSerializer(request.user.escola).data)


class AnoLetivoListCreateView(generics.ListCreateAPIView):
    """Lista anos visíveis ao perfil e permite à escola criar novos períodos."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PodeVisualizarOuEscolaCria)
    serializer_class = AnoLetivoSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "escola") and user.escola.ativo:
            return AnoLetivo.objects.filter(escola=user.escola).order_by("-ano")
        if hasattr(user, "professor") and user.professor.ativo:
            return AnoLetivo.objects.filter(
                turmas__professores=user.professor,
                turmas__ativo=True,
            ).distinct().order_by("-ano")
        return AnoLetivo.objects.none()

    def perform_create(self, serializer):
        with transaction.atomic():
            if serializer.validated_data.get("ativo", True):
                AnoLetivo.objects.filter(
                    escola=self.request.user.escola, ativo=True
                ).update(ativo=False)
            serializer.save(escola=self.request.user.escola)


class AnoLetivoAtivarView(APIView):
    """Ativa um ano letivo da escola e desativa os demais sem removê-los."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PertenceAEscola)

    @transaction.atomic
    def post(self, request, pk):
        # Serializa ativações concorrentes da mesma escola.
        Escola.objects.select_for_update().get(pk=request.user.escola.pk)
        ano = get_object_or_404(
            AnoLetivo.objects.select_for_update(),
            pk=pk,
            escola=request.user.escola,
        )
        AnoLetivo.objects.filter(escola=request.user.escola).exclude(pk=ano.pk).update(ativo=False)
        if not ano.ativo:
            ano.ativo = True
            ano.save(update_fields=["ativo"])
        return Response(AnoLetivoSerializer(ano).data)


class TurmaListCreateView(generics.ListCreateAPIView):
    """Lista turmas para consulta e permite que a escola cadastre novas turmas."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PodeVisualizarOuEscolaCria)
    serializer_class = TurmaSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("nome",)
    ordering_fields = ("serie", "nome")
    ordering = ("serie", "nome")

    def get_queryset(self):
        user = self.request.user
        ano_letivo_id = self.request.query_params.get("ano_letivo")
        if hasattr(user, "escola") and user.escola.ativo:
            incluir_arquivadas = self.request.query_params.get("incluir_arquivadas") == "true"
            qs = Turma.objects.filter(ano_letivo__escola=user.escola)
            if not incluir_arquivadas:
                qs = qs.filter(ativo=True)
            if ano_letivo_id:
                qs = qs.filter(ano_letivo_id=ano_letivo_id)
            else:
                qs = qs.filter(ano_letivo__ativo=True)
            return qs.select_related("ano_letivo")
        if hasattr(user, "professor") and user.professor.ativo:
            qs = user.professor.turmas.filter(ativo=True)
            if ano_letivo_id:
                qs = qs.filter(ano_letivo_id=ano_letivo_id)
            else:
                qs = qs.filter(ano_letivo__ativo=True)
            return qs.select_related("ano_letivo")
        return Turma.objects.none()


class TurmaDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PertenceAEscola)
    serializer_class = TurmaSerializer

    def get_queryset(self):
        return Turma.objects.filter(ano_letivo__escola=self.request.user.escola)


class TurmaArquivarView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PertenceAEscola)

    def post(self, request, pk, acao):
        if acao not in ("arquivar", "restaurar"):
            return Response({"detail": "Ação inválida."}, status=400)
        turma = get_object_or_404(
            Turma.objects.filter(ano_letivo__escola=request.user.escola), pk=pk
        )
        turma.ativo = acao == "restaurar"
        turma.save(update_fields=["ativo"])
        return Response(TurmaSerializer(turma, context={"request": request}).data)
