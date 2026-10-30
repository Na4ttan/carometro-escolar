"""
Modelos de Dados do Domínio de Comunidade Escolar.

Contém os registros dos indivíduos que compõem o ambiente escolar:
1. Aluno: Cadastro dos estudantes e armazenamento de suas fotos do carômetro.
2. Matricula: Associação formal do aluno a uma turma, controlando status de atividade.
3. Professor: Cadastro docente, fotos, credenciais de acesso e vinculação a turmas.
"""

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class Aluno(models.Model):
    """
    Representa o estudante cadastrado no carômetro.
    Possui foto de identificação processada com enquadramento facial inteligente (500x500).
    """

    nome_completo = models.CharField(max_length=200, help_text="Nome civil completo do aluno")
    nome_social = models.CharField(max_length=200, blank=True, null=True, help_text="Nome social (se aplicável)")
    data_nascimento = models.DateField(blank=True, null=True, help_text="Data de nascimento")
    matricula = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Código identificador único de matrícula do aluno",
    )
    foto = models.ImageField(
        upload_to="alunos/",
        blank=True,
        null=True,
        help_text="Foto do aluno, salva em backend/media/alunos/",
    )
    foto_base64 = models.TextField(
        blank=True,
        null=True,
        editable=False,
        help_text="Foto processada em Data URI (Base64) armazenada no banco de dados",
    )
    ativo = models.BooleanField(default=True, help_text="Indica se o aluno está ativo na instituição")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Sobrescreve o salvamento padrão:
        - Persiste o registro no banco e grava o arquivo de imagem no disco.
        - Se houver foto e não estiver em reprocessamento interno (_skip_async),
          gera o Base64 de fallback e enfileira a tarefa assíncrona de visão computacional (OpenCV 500x500).
        """
        if not self.foto:
            self.foto_base64 = None
        elif not getattr(self, "_skip_async", False):
            from apps.processamento.services.imagem_service import ImagemService
            b64 = ImagemService.arquivo_para_data_uri(self.foto)
            if b64:
                self.foto_base64 = b64
        super().save(*args, **kwargs)
        if self.foto and not getattr(self, "_skip_async", False):
            from apps.processamento.async_worker import enfileirar_processamento_aluno
            enfileirar_processamento_aluno(self.id)

    def __str__(self):
        return self.nome_completo

    class Meta:
        db_table = "core_aluno"
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
        ordering = ["nome_completo"]


class Matricula(models.Model):
    """
    Representa o vínculo entre um aluno e uma turma específica.
    Permite histórico escolar de transferências e conclusões de séries.
    """

    class Status(models.TextChoices):
        ATIVA = "ativa", "Ativa"
        TRANSFERIDA = "transferida", "Transferida"
        CONCLUIDA = "concluida", "Concluída"
        CANCELADA = "cancelada", "Cancelada"

    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="matriculas")
    turma = models.ForeignKey("academico.Turma", on_delete=models.CASCADE, related_name="matriculas")
    data_matricula = models.DateField(auto_now_add=True)
    data_saida = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ATIVA)

    def __str__(self):
        return f"{self.aluno.nome_completo} - {self.turma}"

    class Meta:
        db_table = "core_matricula"
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"
        ordering = ["aluno__nome_completo"]
        constraints = [
            # Um aluno só pode estar matriculado uma vez na mesma turma
            models.UniqueConstraint(fields=["aluno", "turma"], name="matricula_unica_por_turma")
        ]


class Professor(models.Model):
    """
    Representa o docente cadastrado.
    Possui login por e-mail, senha criptografada e vinculação a uma ou mais turmas.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="professor",
        blank=True,
        null=True,
        help_text="Usuário de autenticação do Django gerado automaticamente para o professor",
    )
    nome_completo = models.CharField(max_length=200, help_text="Nome completo do professor")
    email = models.EmailField(unique=True, help_text="E-mail funcional e login de acesso")
    senha = models.CharField(
        max_length=128,
        default="",
        help_text="Hash criptográfico PBKDF2 da senha de acesso do professor",
    )
    matricula_funcional = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Matrícula funcional ou registro do professor",
    )
    foto = models.ImageField(
        upload_to="professores/",
        blank=True,
        null=True,
        help_text="Foto do professor, salva em backend/media/professores/",
    )
    foto_base64 = models.TextField(
        blank=True,
        null=True,
        editable=False,
        help_text="Foto processada em Data URI (Base64) armazenada no banco de dados",
    )
    ativo = models.BooleanField(default=True, help_text="Professor com acesso ativo ao carômetro")
    turmas = models.ManyToManyField(
        "academico.Turma",
        related_name="professores",
        blank=True,
        db_table="core_professor_turmas",
        help_text="Turmas às quais o professor ministra aulas e pode consultar no carômetro",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        """Gera o hash seguro da senha com o algoritmo padrão do Django."""
        self.senha = make_password(raw_password)

    def check_password(self, raw_password):
        """Valida a senha informada contra o hash armazenado."""
        return check_password(raw_password, self.senha)

    def save(self, *args, **kwargs):
        """
        Salva o professor e enfileira o processamento de imagem em segundo plano
        caso uma nova foto tenha sido fornecida.
        """
        if not self.foto:
            self.foto_base64 = None
        elif not getattr(self, "_skip_async", False):
            from apps.processamento.services.imagem_service import ImagemService
            b64 = ImagemService.arquivo_para_data_uri(self.foto)
            if b64:
                self.foto_base64 = b64
        super().save(*args, **kwargs)
        if self.foto and not getattr(self, "_skip_async", False):
            from apps.processamento.async_worker import enfileirar_processamento_professor
            enfileirar_processamento_professor(self.id)

    def __str__(self):
        return self.nome_completo

    class Meta:
        db_table = "core_professor"
        verbose_name = "Professor"
        verbose_name_plural = "Professores"
        ordering = ["nome_completo"]
