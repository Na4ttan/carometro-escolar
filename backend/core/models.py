from django.db import models

class Escola(models.Model):
    nome = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Escola"
        verbose_name_plural = "Escolas"
        ordering = ["nome"]


class AnoLetivo(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name="anos_letivos")
    ano = models.PositiveIntegerField()
    data_inicio = models.DateField(blank=True, null=True)
    data_fim = models.DateField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.escola.nome} - {self.ano}"

    class Meta:
        verbose_name = "Ano Letivo"
        verbose_name_plural = "Anos Letivos"
        ordering = ["-ano"]
        constraints = [
            models.UniqueConstraint(fields=["escola", "ano"], name="ano_unico_por_escola")
        ]


class Turma(models.Model):
    class Turno(models.TextChoices):
        MANHA = "manha", "Manhã"
        TARDE = "tarde", "Tarde"
        NOITE = "noite", "Noite"
        INTEGRAL = "integral", "Integral"

    ano_letivo = models.ForeignKey(AnoLetivo, on_delete=models.CASCADE, related_name="turmas")
    nome = models.CharField(max_length=100)
    serie = models.CharField(max_length=100)
    turno = models.CharField(max_length=10, choices=Turno.choices)
    sala = models.CharField(max_length=50, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} - {self.ano_letivo.ano}"

    class Meta:
        verbose_name = "Turma"
        verbose_name_plural = "Turmas"
        ordering = ["serie", "nome"]
        constraints = [
            models.UniqueConstraint(fields=["ano_letivo", "nome"], name="turma_unica_por_ano")
        ]


class Aluno(models.Model):
    nome_completo = models.CharField(max_length=200)
    nome_social = models.CharField(max_length=200, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    matricula = models.CharField(max_length=50, unique=True, blank=True, null=True)
    foto = models.ImageField(upload_to="alunos/", blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome_completo

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
        ordering = ["nome_completo"]


class Matricula(models.Model):
    class Status(models.TextChoices):
        ATIVA = "ativa", "Ativa"
        TRANSFERIDA = "transferida", "Transferida"
        CONCLUIDA = "concluida", "Concluída"
        CANCELADA = "cancelada", "Cancelada"

    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="matriculas")
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name="matriculas")
    data_matricula = models.DateField(auto_now_add=True)
    data_saida = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ATIVA)

    def __str__(self):
        return f"{self.aluno.nome_completo} - {self.turma}"

    class Meta:
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"
        ordering = ["aluno__nome_completo"]
        constraints = [
            models.UniqueConstraint(fields=["aluno", "turma"], name="matricula_unica_por_turma")
        ]


class Professor(models.Model):
    nome_completo = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    matricula_funcional = models.CharField(max_length=50, unique=True, blank=True, null=True)
    foto = models.ImageField(upload_to="professores/", blank=True, null=True)
    ativo = models.BooleanField(default=True)
    turmas = models.ManyToManyField(Turma, related_name="professores", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome_completo

    class Meta:
        verbose_name = "Professor"
        verbose_name_plural = "Professores"
        ordering = ["nome_completo"]