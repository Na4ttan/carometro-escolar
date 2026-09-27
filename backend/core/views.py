from django.contrib.auth import authenticate, get_user_model
from rest_framework import exceptions, generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Aluno, Professor, Turma
from .permissions import PertenceAEscola, PodeVisualizarOuEscolaCria
from .serializers import (
    AlunoSerializer,
    EscolaSerializer,
    ProfessorSerializer,
    TurmaSerializer,
)


class CustomLoginView(APIView):
    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", ""))

        if not username or not password:
            return Response(
                {"detail": "Informe o usuário/e-mail e a senha."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Verifica se é um professor com este e-mail
        professor = Professor.objects.filter(email__iexact=username, ativo=True).first()
        if professor and professor.check_password(password):
            user_model = get_user_model()
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

            token, _ = Token.objects.get_or_create(user=professor.usuario)
            return Response({
                "token": token.key,
                "tipo": "professor",
                "nome": professor.nome_completo,
            })

        # 2. Autentica usuário padrão (escola ou professor vinculado)
        user = authenticate(username=username, password=password)
        if user and user.is_active:
            if hasattr(user, "escola") and user.escola.ativo:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    "token": token.key,
                    "tipo": "escola",
                    "nome": user.escola.nome,
                })
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

        return Response(
            {"detail": "Usuário ou senha inválidos."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PerfilView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        if hasattr(user, "escola") and user.escola.ativo:
            return Response({
                "tipo": "escola",
                "id": user.escola.id,
                "nome": user.escola.nome,
            })
        elif hasattr(user, "professor") and user.professor.ativo:
            professor = user.professor
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
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if hasattr(request.user, "auth_token"):
            request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EscolaView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PertenceAEscola)

    def get(self, request):
        return Response(EscolaSerializer(request.user.escola).data)


class TurmaListView(generics.ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = TurmaSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "escola") and user.escola.ativo:
            return Turma.objects.filter(
                ano_letivo__escola=user.escola,
                ano_letivo__ativo=True,
                ativo=True,
            ).select_related("ano_letivo")
        elif hasattr(user, "professor") and user.professor.ativo:
            return user.professor.turmas.filter(
                ano_letivo__ativo=True,
                ativo=True,
            ).select_related("ano_letivo")
        return Turma.objects.none()


class AlunoListCreateView(generics.ListCreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PodeVisualizarOuEscolaCria)
    serializer_class = AlunoSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "escola") and user.escola.ativo:
            return Aluno.objects.filter(
                matriculas__turma__ano_letivo__escola=user.escola,
                matriculas__status="ativa",
                ativo=True,
            ).distinct()
        elif hasattr(user, "professor") and user.professor.ativo:
            return Aluno.objects.filter(
                matriculas__turma__in=user.professor.turmas.all(),
                matriculas__status="ativa",
                ativo=True,
            ).distinct()
        return Aluno.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not (hasattr(user, "escola") and user.escola.ativo):
            raise exceptions.PermissionDenied(
                "Apenas a administração da escola pode cadastrar alunos."
            )
        serializer.save()


class ProfessorListCreateView(generics.ListCreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, PertenceAEscola)
    serializer_class = ProfessorSerializer

    def get_queryset(self):
        return Professor.objects.filter(
            turmas__ano_letivo__escola=self.request.user.escola
        ).distinct()


class TesteApiView(APIView):
    def get(self, request):
        return Response({
            "mensagem": "API do Carômetro funcionando!",
            "status": "ok",
        })
