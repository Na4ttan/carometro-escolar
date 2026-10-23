from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.academico.models import AnoLetivo, Escola, Turma
from apps.comunidade.models import Professor


class AutenticacaoApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.escola_user = user_model.objects.create_user(
            username="escola-login",
            password="senha-segura-123",
        )
        self.escola = Escola.objects.create(
            nome="Escola Login",
            usuario=self.escola_user,
        )
        self.ano = AnoLetivo.objects.create(escola=self.escola, ano=2026)
        self.turma = Turma.objects.create(
            ano_letivo=self.ano,
            nome="A",
            nivel_ensino=Turma.NivelEnsino.FUNDAMENTAL,
            serie=1,
            turno=Turma.Turno.MANHA,
        )

    def test_login_escola_emite_token_e_tipo(self):
        response = self.client.post(
            reverse("api_login"),
            {"username": "escola-login", "password": "senha-segura-123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["tipo"], "escola")
        self.assertEqual(response.data["nome"], "Escola Login")

    def test_login_professor_com_email_e_senha(self):
        professor = Professor(
            nome_completo="Professor Teste Login",
            email="prof_login@escola.com",
        )
        professor.set_password("senha-prof-123")
        professor.save()
        professor.turmas.add(self.turma)

        response = self.client.post(
            reverse("api_login"),
            {"username": "prof_login@escola.com", "password": "senha-prof-123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["tipo"], "professor")
        self.assertEqual(response.data["nome"], "Professor Teste Login")

    def test_perfil_escola_e_logout(self):
        self.client.force_authenticate(user=self.escola_user)
        response = self.client.get(reverse("api_perfil"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tipo"], "escola")
        self.assertEqual(response.data["nome"], "Escola Login")

        logout_response = self.client.post(reverse("api_logout"))
        self.assertEqual(logout_response.status_code, 204)
