from io import BytesIO
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from .models import Aluno, AnoLetivo, Escola, Matricula, Professor, Turma


class CadastroEscolarApiTests(APITestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        user_model = get_user_model()
        self.escola_user = user_model.objects.create_user(
            username="escola-a",
            password="senha-segura",
        )
        self.escola = Escola.objects.create(
            nome="Escola A",
            usuario=self.escola_user,
        )
        self.outra_escola = Escola.objects.create(nome="Escola B")
        ano = AnoLetivo.objects.create(escola=self.escola, ano=2026)
        outro_ano = AnoLetivo.objects.create(escola=self.outra_escola, ano=2026)
        self.turma = Turma.objects.create(
            ano_letivo=ano,
            nome="6º A",
            serie="6º ano",
            turno=Turma.Turno.MANHA,
        )
        self.outra_turma = Turma.objects.create(
            ano_letivo=outro_ano,
            nome="6º B",
            serie="6º ano",
            turno=Turma.Turno.TARDE,
        )
        self.client.force_authenticate(user=self.escola_user)

    def criar_foto(self):
        conteudo = BytesIO()
        Image.new("RGB", (1, 1), color="blue").save(conteudo, format="PNG")
        return SimpleUploadedFile(
            "foto.png",
            conteudo.getvalue(),
            content_type="image/png",
        )

    def test_escola_cadastra_aluno_e_cria_matricula_na_turma(self):
        response = self.client.post(
            reverse("alunos"),
            {
                "nome_completo": "Ana Silva",
                "matricula": "A-100",
                "turma": self.turma.id,
                "foto": self.criar_foto(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        aluno = Aluno.objects.get(nome_completo="Ana Silva")
        self.assertTrue(
            Matricula.objects.filter(
                aluno=aluno,
                turma=self.turma,
                status=Matricula.Status.ATIVA,
            ).exists()
        )
        self.assertEqual(response.data["turma_nome"], str(self.turma))
        self.assertTrue(aluno.foto.name.startswith("alunos/"))

    def test_foto_e_obrigatoria_no_cadastro_de_aluno(self):
        response = self.client.post(
            reverse("alunos"),
            {"nome_completo": "Ana Silva", "turma": self.turma.id},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("foto", response.data)

    def test_escola_nao_pode_cadastrar_aluno_em_turma_de_outra_escola(self):
        response = self.client.post(
            reverse("alunos"),
            {
                "nome_completo": "Aluno Inválido",
                "turma": self.outra_turma.id,
                "foto": self.criar_foto(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Aluno.objects.filter(nome_completo="Aluno Inválido").exists())

    def test_escola_so_lista_alunos_matriculados_em_suas_turmas(self):
        aluno_proprio = Aluno.objects.create(nome_completo="Ana Silva")
        Matricula.objects.create(aluno=aluno_proprio, turma=self.turma)
        aluno_de_outra_escola = Aluno.objects.create(nome_completo="Bruno Lima")
        Matricula.objects.create(aluno=aluno_de_outra_escola, turma=self.outra_turma)

        response = self.client.get(reverse("alunos"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [aluno["nome_completo"] for aluno in response.data],
            ["Ana Silva"],
        )

    def test_escola_cadastra_professor_com_email_e_senha(self):
        response = self.client.post(
            reverse("professores"),
            {
                "nome_completo": "João Souza",
                "email": "joao@escola.com",
                "senha": "senha-professor-123",
                "confirmacao_senha": "senha-professor-123",
                "turmas": [self.turma.id],
                "foto": self.criar_foto(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        professor = Professor.objects.get(email="joao@escola.com")
        self.assertEqual(list(professor.turmas.all()), [self.turma])
        self.assertEqual(response.data["turmas_nomes"], [str(self.turma)])
        self.assertEqual(response.data["turmas_ids"], [self.turma.id])
        self.assertTrue(professor.foto.name.startswith("professores/"))
        # Verifica que a senha foi criptografada e não salva em texto puro
        self.assertNotEqual(professor.senha, "senha-professor-123")
        self.assertTrue(professor.check_password("senha-professor-123"))
        self.assertIsNotNone(professor.usuario)
        self.assertEqual(professor.usuario.username, "joao@escola.com")

    def test_confirmacao_de_senha_divergente_falha(self):
        response = self.client.post(
            reverse("professores"),
            {
                "nome_completo": "João Divergente",
                "email": "divergente@escola.com",
                "senha": "senha-professor-123",
                "confirmacao_senha": "outra-senha-456",
                "turmas": [self.turma.id],
                "foto": self.criar_foto(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("confirmacao_senha", response.data)

    def test_senha_e_email_sao_obrigatorios_no_cadastro_de_professor(self):
        response = self.client.post(
            reverse("professores"),
            {
                "nome_completo": "João Souza",
                "turmas": [self.turma.id],
                "foto": self.criar_foto(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)
        self.assertIn("senha", response.data)

    def test_foto_e_obrigatoria_no_cadastro_de_professor(self):
        response = self.client.post(
            reverse("professores"),
            {
                "nome_completo": "João Souza",
                "email": "joao@escola.com",
                "senha": "senha-professor-123",
                "turmas": [self.turma.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("foto", response.data)

    def test_escola_nao_pode_associar_professor_a_turma_de_outra_escola(self):
        response = self.client.post(
            reverse("professores"),
            {
                "nome_completo": "Professor Inválido",
                "email": "invalido@escola.com",
                "senha": "senha-professor-123",
                "turmas": [self.outra_turma.id],
                "foto": self.criar_foto(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            Professor.objects.filter(nome_completo="Professor Inválido").exists()
        )

    def test_usuario_sem_escola_nem_professor_nao_pode_acessar_cadastros(self):
        user = get_user_model().objects.create_user(
            username="sem-vinculo",
            password="senha-segura",
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse("alunos"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_login_escola_emite_token_e_tipo(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            reverse("api_login"),
            {"username": "escola-a", "password": "senha-segura"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["tipo"], "escola")

    def test_login_professor_com_email_e_senha(self):
        # Cadastra professor
        cad_response = self.client.post(
            reverse("professores"),
            {
                "nome_completo": "Professora Maria",
                "email": "maria@escola.com",
                "senha": "senha-maria-123",
                "confirmacao_senha": "senha-maria-123",
                "turmas": [self.turma.id],
                "foto": self.criar_foto(),
            },
            format="multipart",
        )
        self.assertEqual(cad_response.status_code, 201)

        # Login com o email do professor
        self.client.force_authenticate(user=None)
        login_response = self.client.post(
            reverse("api_login"),
            {"username": "maria@escola.com", "password": "senha-maria-123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertIn("token", login_response.data)
        self.assertEqual(login_response.data["tipo"], "professor")
        self.assertEqual(login_response.data["nome"], "Professora Maria")

        # Perfil do professor
        token = login_response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        perfil_response = self.client.get(reverse("api_perfil"))
        self.assertEqual(perfil_response.status_code, 200)
        self.assertEqual(perfil_response.data["tipo"], "professor")
        self.assertEqual(perfil_response.data["email"], "maria@escola.com")

        # Professor consulta turmas (vê apenas a sua turma)
        turmas_response = self.client.get(reverse("turmas"))
        self.assertEqual(turmas_response.status_code, 200)
        self.assertEqual(len(turmas_response.data), 1)
        self.assertEqual(turmas_response.data[0]["id"], self.turma.id)

        # Professor não pode cadastrar aluno
        post_aluno_response = self.client.post(
            reverse("alunos"),
            {
                "nome_completo": "Aluno Tentativa",
                "turma": self.turma.id,
                "foto": self.criar_foto(),
            },
            format="multipart",
        )
        self.assertEqual(post_aluno_response.status_code, 403)

        # Professor não pode acessar lista de professores
        prof_response = self.client.get(reverse("professores"))
        self.assertEqual(prof_response.status_code, 403)
