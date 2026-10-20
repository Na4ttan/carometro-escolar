"""
Mapeamento de Rotas da API de Comunidade Escolar (Alunos e Professores).
"""

from django.urls import path

from .views import AlunoListCreateView, ProfessorListCreateView

urlpatterns = [
    # Listagem paginada e cadastro de alunos
    path("alunos/", AlunoListCreateView.as_view(), name="alunos"),

    # Listagem paginada e cadastro de professores
    path("professores/", ProfessorListCreateView.as_view(), name="professores"),
]
