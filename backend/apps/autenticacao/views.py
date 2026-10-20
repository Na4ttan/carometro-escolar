"""
Controladores de Autenticação e Gestão de Sessões da API.

Gerencia o ciclo de vida de acesso ao Carômetro:
1. CustomLoginView: Login unificado para Administradores da Escola e Professores.
2. PerfilView: Retorna as informações do usuário autenticado (nome, tipo, escola associada).
3. LogoutView: Invalidação de tokens de sessão.
4. TesteApiView: Healthcheck simples de disponibilidade da API.
"""

from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comunidade.models import Professor


class CustomLoginView(APIView):
    """
    Endpoint de login unificado: POST /api/login/
    Aceita tanto o login da Escola (username do Django) quanto o login do Professor (e-mail cadastrado).
    Gera e devolve um Token DRF para autenticação subsequente nas requisições.
    """

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", ""))

        # Validação básica de entrada
        if not username or not password:
            return Response(
                {"detail": "Informe o usuário/e-mail e a senha."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------------------
        # 1. Fluxo de Autenticação do Professor (por e-mail)
        # ---------------------------------------------------------------------
        professor = Professor.objects.filter(email__iexact=username, ativo=True).first()
        if professor and professor.check_password(password):
            user_model = get_user_model()

            # Garante que o professor possua um User do Django associado para gerar o Token DRF
            if not professor.usuario:
                user, _ = user_model.objects.get_or_create(
                    username=professor.email,
                    defaults={"email": professor.email},
                )
                user.set_password(password)
                user.save()
                professor.usuario = user
                professor.save(update_fields=["usuario"])
            elif not professor.usuario.check_password(password):
                professor.usuario.set_password(password)
                professor.usuario.save()

            # Emite ou obtém o token de autenticação
            token, _ = Token.objects.get_or_create(user=professor.usuario)
            return Response({
                "token": token.key,
                "tipo": "professor",
                "nome": professor.nome_completo,
            })

        # ---------------------------------------------------------------------
        # 2. Fluxo Padrão do Django (Escola ou Usuário de Sistema)
        # ---------------------------------------------------------------------
        user = authenticate(username=username, password=password)
        if user and user.is_active:
            # Perfil Escola
            if hasattr(user, "escola") and user.escola.ativo:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    "token": token.key,
                    "tipo": "escola",
                    "nome": user.escola.nome,
                })
            # Perfil Professor via login Django
            elif hasattr(user, "professor") and user.professor.ativo:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    "token": token.key,
                    "tipo": "professor",
                    "nome": user.professor.nome_completo,
                })
            else:
                return Response(
                    {"detail": "Esta conta não tem acesso ativo ao sistema."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Credenciais incorretas
        return Response(
            {"detail": "Usuário ou senha inválidos."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PerfilView(APIView):
    """
    Endpoint de dados do usuário autenticado: GET /api/perfil/
    Permite ao frontend saber se a interface deve exibir menus administrativos (Escola)
    ou apenas a visualização de carômetro (Professor).
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user

        # Identifica se é Escola
        if hasattr(user, "escola") and user.escola.ativo:
            return Response({
                "tipo": "escola",
                "id": user.escola.id,
                "nome": user.escola.nome,
            })

        # Identifica se é Professor
        elif hasattr(user, "professor") and user.professor.ativo:
            professor = user.professor
            # Obtém o nome da escola através das turmas em que o professor atua
            turma_escola = (
                professor.turmas.filter(ano_letivo__escola__ativo=True)
                .select_related("ano_letivo__escola")
                .first()
            )
            nome_escola = (
                turma_escola.ano_letivo.escola.nome if turma_escola else "Escola"
            )
            return Response({
                "tipo": "professor",
                "id": professor.id,
                "nome": professor.nome_completo,
                "email": professor.email,
                "escola_nome": nome_escola,
            })

        return Response(
            {"detail": "Esta conta não possui perfil ativo vinculado."},
            status=status.HTTP_403_FORBIDDEN,
        )


class LogoutView(APIView):
    """
    Endpoint de logout: POST /api/logout/
    Remove o token de sessão do banco de dados, invalidando o acesso imediato.
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if hasattr(request.user, "auth_token"):
            request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TesteApiView(APIView):
    """Endpoint utilitário (healthcheck): GET /api/teste/"""

    def get(self, request):
        return Response({
            "mensagem": "API do Carômetro funcionando!",
            "status": "ok",
        })
