"""
Mapeamento de Rotas da API Acadêmica.
"""

from django.urls import path

from .views import EscolaView, TurmaListView

urlpatterns = [
    # Consulta os dados da escola do usuário logado
    path("escola/", EscolaView.as_view(), name="escola_atual"),

    # Listagem de turmas disponíveis para o usuário (escola ou professor)
    path("turmas/", TurmaListView.as_view(), name="turmas"),
]
