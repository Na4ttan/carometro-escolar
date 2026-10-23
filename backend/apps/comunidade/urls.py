"""
Mapeamento de Rotas da API de Comunidade Escolar (Alunos e Professores).
"""

from django.urls import path

from .views import (
    AlunoArquivarView,
    AlunoDetailView,
    AlunoListCreateView,
    ProfessorArquivarView,
    ProfessorDetailView,
    ProfessorListCreateView,
)

urlpatterns = [
    # Listagem paginada e cadastro de alunos
    path("alunos/", AlunoListCreateView.as_view(), name="alunos"),
    path("alunos/<int:pk>/", AlunoDetailView.as_view(), name="aluno_detalhe"),
    path("alunos/<int:pk>/<str:acao>/", AlunoArquivarView.as_view(), name="aluno_arquivar"),

    # Listagem paginada e cadastro de professores
    path("professores/", ProfessorListCreateView.as_view(), name="professores"),
    path("professores/<int:pk>/", ProfessorDetailView.as_view(), name="professor_detalhe"),
    path("professores/<int:pk>/<str:acao>/", ProfessorArquivarView.as_view(), name="professor_arquivar"),
]
