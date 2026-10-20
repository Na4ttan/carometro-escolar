"""
Mapeamento de Rotas da API de Autenticação e Perfis.
"""

from django.urls import path

from .views import CustomLoginView, LogoutView, PerfilView, TesteApiView

urlpatterns = [
    # Verificação de status da API
    path("teste/", TesteApiView.as_view(), name="teste_api"),

    # Autenticação, encerramento de sessão e consulta de perfil ativo
    path("auth/login/", CustomLoginView.as_view(), name="api_login"),
    path("auth/logout/", LogoutView.as_view(), name="api_logout"),
    path("auth/perfil/", PerfilView.as_view(), name="api_perfil"),
]
