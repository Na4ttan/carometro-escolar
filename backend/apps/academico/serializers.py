"""
Serializadores REST para o Domínio Acadêmico.

Converte instâncias de Escola e Turma em formatos JSON para consumo pela interface web e mobile.
"""

from rest_framework import serializers

from .models import Escola, Turma


class EscolaSerializer(serializers.ModelSerializer):
    """Serializador resumido com as informações básicas da escola."""

    class Meta:
        model = Escola
        fields = ("id", "nome")


class TurmaSerializer(serializers.ModelSerializer):
    """
    Serializador de Turmas para listagens e dropdowns de seleção no Carômetro.
    Extrai o número do ano letivo de forma achatada (read-only) para facilitar o consumo no frontend.
    """

    ano = serializers.IntegerField(source="ano_letivo.ano", read_only=True)

    class Meta:
        model = Turma
        fields = ("id", "nome", "serie", "turno", "ano")
