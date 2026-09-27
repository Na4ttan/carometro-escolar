from django.urls import path

from .views import (
    AlunoListCreateView,
    CustomLoginView,
    EscolaView,
    LogoutView,
    PerfilView,
    ProfessorListCreateView,
    TesteApiView,
    TurmaListView,
)

urlpatterns = [
    path("teste/", TesteApiView.as_view(), name="teste_api"),
    path("auth/login/", CustomLoginView.as_view(), name="api_login"),
    path("auth/logout/", LogoutView.as_view(), name="api_logout"),
    path("auth/perfil/", PerfilView.as_view(), name="api_perfil"),
    path("escola/", EscolaView.as_view(), name="escola_atual"),
    path("turmas/", TurmaListView.as_view(), name="turmas"),
    path("alunos/", AlunoListCreateView.as_view(), name="alunos"),
    path("professores/", ProfessorListCreateView.as_view(), name="professores"),
]
