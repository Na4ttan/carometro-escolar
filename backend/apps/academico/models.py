"""
Modelos de Dados do Domínio Acadêmico.

Representa a estrutura física e organizacional da instituição escolar:
1. Escola: A instituição de ensino, vinculada a um usuário administrador.
2. AnoLetivo: Ciclo letivo anual da escola (ex: 2026).
3. Turma: Agrupamento de alunos por série, turno e sala de aula no ano letivo.
"""

from django.conf import settings
from django.db import models


class Escola(models.Model):
    """
    Representa a instituição de ensino administradora.
    Possui vínculo OneToOne com a conta de usuário do Django para login administrativo.
    """

    nome = models.CharField(max_length=200, help_text="Nome oficial da escola")
    cnpj = models.CharField(max_length=18, blank=True, null=True, help_text="CNPJ da instituição (opcional)")
    endereco = models.CharField(max_length=255, blank=True, null=True, help_text="Endereço físico completo")
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="escola",
        blank=True,
        null=True,
        help_text="Conta de usuário utilizada para acessar o painel administrativo da escola",
    )
    ativo = models.BooleanField(default=True, help_text="Indica se a escola está com acesso ativo")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    class Meta:
        db_table = "core_escola"  # Preserva compatibilidade com tabelas pré-existentes do SQLite
        verbose_name = "Escola"
        verbose_name_plural = "Escolas"
        ordering = ["nome"]


class AnoLetivo(models.Model):
    """
    Representa um período letivo específico da escola (ex: 2026).
    Evita misturar turmas de anos anteriores com o ano corrente.
    """

    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name="anos_letivos",
        help_text="Escola à qual este ano letivo pertence",
    )
    ano = models.PositiveIntegerField(help_text="Ano calendário (ex: 2026)")
    data_inicio = models.DateField(blank=True, null=True, help_text="Início oficial das aulas")
    data_fim = models.DateField(blank=True, null=True, help_text="Término oficial das aulas")
    ativo = models.BooleanField(default=True, help_text="Indica se é o ano letivo em vigência")

    def __str__(self):
        return f"{self.escola.nome} - {self.ano}"

    class Meta:
        db_table = "core_anoletivo"
        verbose_name = "Ano Letivo"
        verbose_name_plural = "Anos Letivos"
        ordering = ["-ano"]
        constraints = [
            # Impede cadastrar o mesmo ano duas vezes para uma única escola
            models.UniqueConstraint(fields=["escola", "ano"], name="ano_unico_por_escola")
        ]


class Turma(models.Model):
    """
    Representa uma sala ou agrupamento de alunos (ex: '6º Ano A', '9º Ano B').
    """

    class Turno(models.TextChoices):
        MANHA = "manha", "Manhã"
        TARDE = "tarde", "Tarde"
        NOITE = "noite", "Noite"
        INTEGRAL = "integral", "Integral"

    ano_letivo = models.ForeignKey(
        AnoLetivo,
        on_delete=models.CASCADE,
        related_name="turmas",
        help_text="Ano letivo associado à turma",
    )
    nome = models.CharField(max_length=100, help_text="Identificação da turma (ex: 6º A, 1º B)")
    serie = models.CharField(max_length=100, help_text="Série ou etapa escolar (ex: 6º ano)")
    turno = models.CharField(max_length=10, choices=Turno.choices, help_text="Turno das aulas")
    sala = models.CharField(max_length=50, blank=True, null=True, help_text="Número ou nome da sala de aula")
    ativo = models.BooleanField(default=True, help_text="Turma ativa para matrículas e carômetro")

    def __str__(self):
        return f"{self.nome} - {self.ano_letivo.ano}"

    class Meta:
        db_table = "core_turma"
        verbose_name = "Turma"
        verbose_name_plural = "Turmas"
        ordering = ["serie", "nome"]
        constraints = [
            # Garante que não haja duas turmas com mesmo nome no mesmo ano letivo
            models.UniqueConstraint(fields=["ano_letivo", "nome"], name="turma_unica_por_ano")
        ]
