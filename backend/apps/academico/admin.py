"""
Painel Administrativo do Domínio Acadêmico.

Configuração de visualização e busca no Django Admin para Escola, AnoLetivo e Turma.
"""

from django.contrib import admin

from .models import AnoLetivo, Escola, Turma


@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    """Configuração do painel de administração da Escola."""

    list_display = ("nome", "cnpj", "usuario", "ativo")
    search_fields = ("nome", "cnpj", "usuario__username")
    list_filter = ("ativo",)


# Registro simplificado para Anos Letivos e Turmas
admin.site.register((AnoLetivo, Turma))
