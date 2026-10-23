"""
Mapeamento de Rotas da API Acadêmica.
"""

from django.urls import path

from .views import (
    AnoLetivoAtivarView,
    AnoLetivoListCreateView,
    EscolaView,
    TurmaArquivarView,
    TurmaDetailView,
    TurmaListCreateView,
)

urlpatterns = [
    # Consulta os dados da escola do usuário logado
    path("escola/", EscolaView.as_view(), name="escola_atual"),
    path("anos-letivos/", AnoLetivoListCreateView.as_view(), name="anos_letivos"),
    path("anos-letivos/<int:pk>/ativar/", AnoLetivoAtivarView.as_view(), name="ativar_ano_letivo"),

    # Listagem de turmas disponíveis para o usuário (escola ou professor)
    path("turmas/", TurmaListCreateView.as_view(), name="turmas"),
    path("turmas/<int:pk>/", TurmaDetailView.as_view(), name="turma_detalhe"),
    path("turmas/<int:pk>/<str:acao>/", TurmaArquivarView.as_view(), name="turma_arquivar"),
]
