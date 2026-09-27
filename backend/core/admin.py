from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Aluno, AnoLetivo, Escola, Matricula, Professor, Turma


@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cnpj", "usuario", "ativo")
    search_fields = ("nome", "cnpj", "usuario__username")
    list_filter = ("ativo",)


class ProfessorAdminForm(forms.ModelForm):
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
    form = ProfessorAdminForm
    list_display = ("nome_completo", "email", "matricula_funcional", "usuario", "ativo")
    search_fields = ("nome_completo", "email", "matricula_funcional", "usuario__username")
    list_filter = ("ativo",)
    exclude = ("senha",)

    def save_model(self, request, obj, form, change):
        nova_senha = form.cleaned_data.get("nova_senha")

        User = get_user_model()
        if not obj.usuario and obj.email:
            user, _ = User.objects.get_or_create(
                username=obj.email,
                defaults={"email": obj.email},
            )
            obj.usuario = user

        if nova_senha:
            obj.set_password(nova_senha)
            if obj.usuario:
                obj.usuario.set_password(nova_senha)
                obj.usuario.save()

        super().save_model(request, obj, form, change)


admin.site.register((AnoLetivo, Turma, Aluno, Matricula))
