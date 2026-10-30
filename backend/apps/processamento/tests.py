from io import BytesIO
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase, override_settings

from apps.comunidade.models import Aluno, Professor
from apps.processamento.async_worker import (
    aguardar_conclusao_tarefas,
    enfileirar_processamento_aluno,
    enfileirar_processamento_professor,
)
from apps.processamento.services.imagem_service import ImagemService


class ImagemServiceTests(TestCase):
    def test_enquadrar_e_redimensionar_retorna_500x500(self):
        img = Image.new("RGB", (1280, 720), color="blue")
        resultado = ImagemService.enquadrar_e_redimensionar(img, size=(500, 500))
        self.assertEqual(resultado.size, (500, 500))

    def test_tem_transparencia_detecta_alfa(self):
        img_transparente = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        img_opaca = Image.new("RGB", (100, 100), (255, 0, 0))

        self.assertTrue(ImagemService.tem_transparencia(img_transparente))
        self.assertFalse(ImagemService.tem_transparencia(img_opaca))


class AsyncWorkerTests(TransactionTestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

    def test_processamento_aluno_sincrono(self):
        conteudo = BytesIO()
        Image.new("RGB", (800, 600), color="orange").save(conteudo, format="JPEG")
        foto = SimpleUploadedFile("aluno_hd.jpg", conteudo.getvalue(), content_type="image/jpeg")

        aluno = Aluno.objects.create(
            nome_completo="Aluno Sync",
            foto=foto,
        )
        enfileirar_processamento_aluno(aluno.id, sync=True)
        aluno.refresh_from_db()
        img = Image.open(aluno.foto.path)
        self.assertEqual(img.size, (500, 500))
        self.assertIsNotNone(aluno.foto_base64)
        self.assertTrue(aluno.foto_base64.startswith("data:image/jpeg;base64,"))

    def test_processamento_aluno_assincrono_em_thread_pool(self):
        conteudo = BytesIO()
        Image.new("RGB", (1000, 800), color="teal").save(conteudo, format="JPEG")
        foto = SimpleUploadedFile("aluno_async.jpg", conteudo.getvalue(), content_type="image/jpeg")

        with override_settings(CAROMETRO_ASYNC_IMAGE_PROCESSING=True):
            aluno = Aluno.objects.create(
                nome_completo="Aluno Async Thread",
                foto=foto,
            )
            aguardar_conclusao_tarefas(timeout=5)

            aluno.refresh_from_db()
            img = Image.open(aluno.foto.path)
            self.assertEqual(img.size, (500, 500))

    def test_processamento_professor_assincrono_em_thread_pool(self):
        conteudo = BytesIO()
        Image.new("RGBA", (900, 700), color=(100, 200, 50, 180)).save(conteudo, format="PNG")
        foto = SimpleUploadedFile("prof_async.png", conteudo.getvalue(), content_type="image/png")

        with override_settings(CAROMETRO_ASYNC_IMAGE_PROCESSING=True):
            professor = Professor.objects.create(
                nome_completo="Professor Async Thread",
                email="async_prof@escola.com",
                foto=foto,
            )
            aguardar_conclusao_tarefas(timeout=5)

            professor.refresh_from_db()
            img = Image.open(professor.foto.path)
            self.assertEqual(img.size, (500, 500))
            self.assertEqual(img.format, "PNG")
