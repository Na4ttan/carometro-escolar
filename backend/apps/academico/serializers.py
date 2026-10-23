"""
Serializadores REST para o Domínio Acadêmico.

Converte instâncias de Escola e Turma em formatos JSON para consumo pela interface web e mobile.
"""

from rest_framework import serializers

from .models import AnoLetivo, Escola, Turma


class EscolaSerializer(serializers.ModelSerializer):
    """Serializador resumido com as informações básicas da escola."""

    class Meta:
        model = Escola
        fields = ("id", "nome")


class AnoLetivoSerializer(serializers.ModelSerializer):
    """Dados de ano letivo gerenciados pela escola autenticada."""

    class Meta:
        model = AnoLetivo
        fields = ("id", "ano", "data_inicio", "data_fim", "ativo")
        read_only_fields = ("id",)

    def validate(self, attrs):
        data_inicio = attrs.get("data_inicio")
        data_fim = attrs.get("data_fim")
        if data_inicio and data_fim and data_fim < data_inicio:
            raise serializers.ValidationError({"data_fim": "A data final deve ser posterior à data inicial."})
        return attrs


class TurmaSerializer(serializers.ModelSerializer):
    """
    Serializador de Turmas para listagens e dropdowns de seleção no Carômetro.
    Extrai o número do ano letivo de forma achatada (read-only) para facilitar o consumo no frontend.
    """

    ano = serializers.IntegerField(source="ano_letivo.ano", read_only=True)
    ano_letivo = serializers.PrimaryKeyRelatedField(queryset=AnoLetivo.objects.all(), write_only=True)

    def validate_nome(self, nome):
        nome = nome.strip().upper()
        if not nome or not nome.isalpha():
            raise serializers.ValidationError("Informe a identificação da turma usando letras, como A, B ou C.")
        return nome

    class Meta:
        model = Turma
        fields = ("id", "nome", "nivel_ensino", "serie", "turno", "sala", "ano", "ano_letivo", "ativo")
        read_only_fields = ("id", "ano", "ativo")

    def validate_ano_letivo(self, ano_letivo):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        escola = getattr(user, "escola", None) if user else None
        if not escola or ano_letivo.escola_id != escola.id:
            raise serializers.ValidationError("Selecione um ano letivo da sua escola.")
        return ano_letivo

    def validate(self, attrs):
        nivel = attrs.get("nivel_ensino", getattr(self.instance, "nivel_ensino", None))
        serie = attrs.get("serie", getattr(self.instance, "serie", None))
        limite = 9 if nivel == Turma.NivelEnsino.FUNDAMENTAL else 3
        if serie is not None and not 1 <= serie <= limite:
            descricao = "1ª a 9ª" if nivel == Turma.NivelEnsino.FUNDAMENTAL else "1ª a 3ª"
            raise serializers.ValidationError({"serie": f"No nível selecionado, informe uma série da {descricao}."})
        return attrs
