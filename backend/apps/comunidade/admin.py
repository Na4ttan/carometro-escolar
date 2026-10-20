"""
Painel Administrativo do Domínio de Comunidade Escolar.

Configuração do Django Admin para Aluno, Matrícula e Professor.
Permite aos administradores de suporte redefinirem senhas de professores de forma transparente,
criptografando o novo hash e sincronizando com a conta de autenticação do Django.
"""

from django import forms
from django.contrib import admin

from apps.comunidade.services.professor_service import ProfessorService
from .models import Aluno, Matricula, Professor


class ProfessorAdminForm(forms.ModelForm):
    """
    Formulário customizado para o cadastro e edição de Professores no Django Admin:
    - Oculta o campo de hash interno ('senha').
    - Adiciona campos amigáveis de 'Nova senha' e 'Confirmação de senha' com validação.
    """

    nova_senha = forms.CharField(
        label="Nova senha de acesso",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Informe para cadastrar ou alterar a senha do professor (mínimo 6 caracteres). Deixe em branco para manter a atual.",
    )
    confirmar_nova_senha = forms.CharField(
        label="Confirmar nova senha",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Repita a nova senha para confirmação.",
    )

    class Meta:
        model = Professor
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        nova_senha = cleaned_data.get("nova_senha")
        confirmar_nova_senha = cleaned_data.get("confirmar_nova_senha")

        if nova_senha:
            if len(nova_senha) < 6:
                self.add_error("nova_senha", "A senha deve ter no mínimo 6 caracteres.")
            if nova_senha != confirmar_nova_senha:
                self.add_error("confirmar_nova_senha", "A confirmação de senha não confere.")

        return cleaned_data


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    """Configuração da interface administrativa de Professores."""

    form = ProfessorAdminForm
    list_display = ("nome_completo", "email", "matricula_funcional", "usuario", "ativo")
    search_fields = ("nome_completo", "email", "matricula_funcional", "usuario__username")
    list_filter = ("ativo",)
    exclude = ("senha",)  # Oculta o hash bruto da visualização

    def save_model(self, request, obj, form, change):
        """Salva o professor e, caso uma nova senha tenha sido digitada, delega à Service Layer."""
        nova_senha = form.cleaned_data.get("nova_senha")
        super().save_model(request, obj, form, change)
        if nova_senha:
            ProfessorService.redefinir_senha(obj, nova_senha)


# Registro padrão para Alunos e Matrículas
admin.site.register((Aluno, Matricula))
