from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import AnoLetivo, Escola, Turma


class AcademicoApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.escola_user = user_model.objects.create_user(
            username="escola-acad",
            password="senha-segura",
        )
        self.escola = Escola.objects.create(
            nome="Escola Academica",
            usuario=self.escola_user,
        )
        self.ano = AnoLetivo.objects.create(escola=self.escola, ano=2026)
        self.turma = Turma.objects.create(
            ano_letivo=self.ano,
            nome="6º A",
            serie="6º ano",
            turno=Turma.Turno.MANHA,
        )
        self.client.force_authenticate(user=self.escola_user)

    def test_consulta_dados_da_escola(self):
        response = self.client.get(reverse("escola_atual"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["nome"], "Escola Academica")

    def test_consulta_turmas_da_escola(self):
        response = self.client.get(reverse("turmas"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["nome"], "6º A")
