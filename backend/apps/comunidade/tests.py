from io import BytesIO
import tempfile

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse
from django.test import override_settings, TestCase
from PIL import Image
from rest_framework.test import APITestCase

from apps.academico.models import AnoLetivo, Escola, Turma
from apps.comunidade.services.aluno_service import AlunoService
from apps.comunidade.services.professor_service import ProfessorService
from .models import Aluno, Matricula, Professor


class ComunidadeApiTests(APITestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        user_model = get_user_model()
        self.escola_user = user_model.objects.create_user(
            username="escola-comunidade",
            password="senha-segura",
        )
        self.escola = Escola.objects.create(
            nome="Escola Comunidade",
            usuario=self.escola_user,
        )
        self.outra_escola = Escola.objects.create(nome="Escola Externa")
        ano = AnoLetivo.objects.create(escola=self.escola, ano=2026)
        outro_ano = AnoLetivo.objects.create(escola=self.outra_escola, ano=2026)
        self.turma = Turma.objects.create(
            ano_letivo=ano,
            nome="A",
            nivel_ensino=Turma.NivelEnsino.FUNDAMENTAL,
            serie=6,
            turno=Turma.Turno.MANHA,
        )
        self.outra_turma = Turma.objects.create(
            ano_letivo=outro_ano,
            nome="B",
            nivel_ensino=Turma.NivelEnsino.FUNDAMENTAL,
            serie=6,
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

    def test_escola_so_lista_alunos_matriculados_em_suas_turmas_paginados(self):
        aluno_proprio = Aluno.objects.create(nome_completo="Ana Silva")
        Matricula.objects.create(aluno=aluno_proprio, turma=self.turma)
        aluno_de_outra_escola = Aluno.objects.create(nome_completo="Bruno Lima")
        Matricula.objects.create(aluno=aluno_de_outra_escola, turma=self.outra_turma)

        response = self.client.get(reverse("alunos"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            [aluno["nome_completo"] for aluno in response.data["results"]],
            ["Ana Silva"],
        )

    def test_busca_otimizada_alunos_por_nome_e_matricula(self):
        aluno1 = Aluno.objects.create(nome_completo="Carlos Eduardo", matricula="CE-001")
        Matricula.objects.create(aluno=aluno1, turma=self.turma)
        aluno2 = Aluno.objects.create(nome_completo="Fernanda Souza", matricula="FS-002")
        Matricula.objects.create(aluno=aluno2, turma=self.turma)

        # Busca por nome
        resp_nome = self.client.get(reverse("alunos"), {"search": "Carlos"})
        self.assertEqual(resp_nome.status_code, 200)
        self.assertEqual(resp_nome.data["count"], 1)
        self.assertEqual(resp_nome.data["results"][0]["nome_completo"], "Carlos Eduardo")

        # Busca por matrícula
        resp_mat = self.client.get(reverse("alunos"), {"search": "FS-002"})
        self.assertEqual(resp_mat.status_code, 200)
        self.assertEqual(resp_mat.data["count"], 1)
        self.assertEqual(resp_mat.data["results"][0]["nome_completo"], "Fernanda Souza")

    def test_filtro_alunos_por_turma(self):
        nova_turma = Turma.objects.create(
            ano_letivo=self.turma.ano_letivo,
            nome="A",
            nivel_ensino=Turma.NivelEnsino.FUNDAMENTAL,
            serie=7,
            turno=Turma.Turno.MANHA,
        )
        aluno1 = Aluno.objects.create(nome_completo="Aluno Turma 6")
        Matricula.objects.create(aluno=aluno1, turma=self.turma)
        aluno2 = Aluno.objects.create(nome_completo="Aluno Turma 7")
        Matricula.objects.create(aluno=aluno2, turma=nova_turma)

        response = self.client.get(reverse("alunos"), {"turma": nova_turma.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["nome_completo"], "Aluno Turma 7")

    def test_bypass_paginacao_alunos(self):
        aluno = Aluno.objects.create(nome_completo="Aluno Sem Pag")
        Matricula.objects.create(aluno=aluno, turma=self.turma)

        response = self.client.get(reverse("alunos"), {"sem_paginacao": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)

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

    def test_salvar_aluno_redimensiona_foto_para_500x500(self):
        conteudo = BytesIO()
        Image.new("RGB", (1920, 1080), color="red").save(conteudo, format="JPEG")
        foto_hd = SimpleUploadedFile("foto_hd.jpg", conteudo.getvalue(), content_type="image/jpeg")

        response = self.client.post(
            reverse("alunos"),
            {
                "nome_completo": "Aluno Foto HD",
                "matricula": "HD-100",
                "turma": self.turma.id,
                "foto": foto_hd,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        aluno = Aluno.objects.get(matricula="HD-100")
        img_salva = Image.open(aluno.foto.path)
        self.assertEqual(img_salva.size, (500, 500))
        self.assertEqual(img_salva.format, "JPEG")

    def test_salvar_professor_preserva_transparencia_png_e_redimensiona(self):
        conteudo = BytesIO()
        Image.new("RGBA", (1200, 800), color=(0, 128, 255, 180)).save(conteudo, format="PNG")
        foto_hd = SimpleUploadedFile("prof_hd.png", conteudo.getvalue(), content_type="image/png")

        response = self.client.post(
            reverse("professores"),
            {
                "nome_completo": "Professora Resolução",
                "email": "resolucao@escola.com",
                "senha": "senha-valida-123",
                "confirmacao_senha": "senha-valida-123",
                "turmas": [self.turma.id],
                "foto": foto_hd,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        professor = Professor.objects.get(email="resolucao@escola.com")
        img_salva = Image.open(professor.foto.path)
        self.assertEqual(img_salva.size, (500, 500))
        self.assertEqual(img_salva.format, "PNG")
        self.assertEqual(img_salva.mode, "RGBA")

    def test_comando_redimensionar_fotos(self):
        conteudo = BytesIO()
        Image.new("RGB", (800, 400), color="green").save(conteudo, format="JPEG")
        aluno = Aluno.objects.create(
            nome_completo="Aluno Teste Cmd",
            foto=SimpleUploadedFile("foto_antiga.jpg", conteudo.getvalue(), content_type="image/jpeg"),
        )
        call_command("redimensionar_fotos")
        aluno.refresh_from_db()
        img = Image.open(aluno.foto.path)
        self.assertEqual(img.size, (500, 500))


class ServiceLayerUnitTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        self.escola = Escola.objects.create(nome="Escola Service Test")
        self.ano = AnoLetivo.objects.create(escola=self.escola, ano=2026)
        self.turma = Turma.objects.create(
            ano_letivo=self.ano,
            nome="A",
            nivel_ensino=Turma.NivelEnsino.FUNDAMENTAL,
            serie=9,
            turno=Turma.Turno.MANHA,
        )

    def test_aluno_service_cria_aluno_e_matricula_direto(self):
        conteudo = BytesIO()
        Image.new("RGB", (600, 600), color="yellow").save(conteudo, format="JPEG")
        foto = SimpleUploadedFile("foto.jpg", conteudo.getvalue(), content_type="image/jpeg")

        aluno = AlunoService.criar_aluno(
            dados={
                "nome_completo": "Aluno Service",
                "matricula": "SERV-1",
                "foto": foto,
            },
            turma=self.turma,
            escola=self.escola,
        )

        self.assertIsNotNone(aluno.id)
        self.assertTrue(
            Matricula.objects.filter(aluno=aluno, turma=self.turma, status="ativa").exists()
        )
        img = Image.open(aluno.foto.path)
        self.assertEqual(img.size, (500, 500))

    def test_aluno_service_valida_duplicidade_matricula(self):
        Aluno.objects.create(nome_completo="Aluno Existente", matricula="MAT-123")
        with self.assertRaises(ValidationError):
            AlunoService.validar_matricula("MAT-123")

    def test_professor_service_cria_usuario_e_hash(self):
        conteudo = BytesIO()
        Image.new("RGB", (600, 600), color="purple").save(conteudo, format="JPEG")
        foto = SimpleUploadedFile("prof.jpg", conteudo.getvalue(), content_type="image/jpeg")

        professor = ProfessorService.criar_professor(
            dados={
                "nome_completo": "Prof Service",
                "email": "prof_service@escola.com",
                "senha": "senha-forte-123",
                "foto": foto,
            },
            turmas=[self.turma],
            escola=self.escola,
        )

        self.assertEqual(professor.email, "prof_service@escola.com")
        self.assertTrue(professor.check_password("senha-forte-123"))
        self.assertIsNotNone(professor.usuario)
        self.assertTrue(professor.usuario.check_password("senha-forte-123"))
        self.assertIn(self.turma, professor.turmas.all())

    def test_professor_service_redefine_senha(self):
        professor = Professor.objects.create(
            nome_completo="Prof Redefinir",
            email="redefinir@escola.com",
        )
        ProfessorService.redefinir_senha(professor, "nova-senha-456")
        self.assertTrue(professor.check_password("nova-senha-456"))
        self.assertTrue(professor.usuario.check_password("nova-senha-456"))
