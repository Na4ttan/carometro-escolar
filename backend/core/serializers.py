from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Aluno, Escola, Matricula, Professor, Turma


class EscolaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escola
        fields = ("id", "nome")


class TurmaSerializer(serializers.ModelSerializer):
    ano = serializers.IntegerField(source="ano_letivo.ano", read_only=True)

    class Meta:
        model = Turma
        fields = ("id", "nome", "serie", "turno", "ano")


class AlunoSerializer(serializers.ModelSerializer):
    foto = serializers.ImageField(required=True)
    turma = serializers.PrimaryKeyRelatedField(
        queryset=Turma.objects.all(), write_only=True
    )
    turma_id = serializers.SerializerMethodField()
    turma_nome = serializers.SerializerMethodField()

    class Meta:
        model = Aluno
        fields = (
            "id",
            "nome_completo",
            "nome_social",
            "data_nascimento",
            "matricula",
            "foto",
            "ativo",
            "turma",
            "turma_id",
            "turma_nome",
        )
        read_only_fields = ("id", "ativo", "turma_id", "turma_nome")

    def validate_turma(self, turma):
        user = self.context["request"].user
        if not hasattr(user, "escola"):
            raise serializers.ValidationError(
                "Apenas a administração da escola pode vincular turmas a alunos."
            )
        escola = user.escola
        if (
            not turma.ativo
            or not turma.ano_letivo.ativo
            or turma.ano_letivo.escola_id != escola.id
        ):
            raise serializers.ValidationError(
                "Selecione uma turma ativa da sua escola."
            )
        return turma

    def get_turma_nome(self, aluno):
        matricula = self.get_matricula_ativa(aluno)
        return str(matricula.turma) if matricula else None

    def get_turma_id(self, aluno):
        matricula = self.get_matricula_ativa(aluno)
        return matricula.turma_id if matricula else None

    def get_matricula_ativa(self, aluno):
        user = self.context["request"].user
        if hasattr(user, "escola"):
            return (
                aluno.matriculas.filter(
                    turma__ano_letivo__escola=user.escola,
                    status=Matricula.Status.ATIVA,
                )
                .select_related("turma")
                .first()
            )
        elif hasattr(user, "professor"):
            return (
                aluno.matriculas.filter(
                    turma__in=user.professor.turmas.all(),
                    status=Matricula.Status.ATIVA,
                )
                .select_related("turma")
                .first()
            )
        return None

    @transaction.atomic
    def create(self, validated_data):
        turma = validated_data.pop("turma")
        aluno = Aluno.objects.create(**validated_data)
        Matricula.objects.create(aluno=aluno, turma=turma)
        return aluno


class ProfessorSerializer(serializers.ModelSerializer):
    foto = serializers.ImageField(required=True)
    email = serializers.EmailField(required=True)
    senha = serializers.CharField(write_only=True, required=True, min_length=6)
    confirmacao_senha = serializers.CharField(
        write_only=True, required=False, min_length=6
    )
    turmas = serializers.PrimaryKeyRelatedField(
        queryset=Turma.objects.all(), many=True, write_only=True
    )
    turmas_ids = serializers.SerializerMethodField()
    turmas_nomes = serializers.SerializerMethodField()

    class Meta:
        model = Professor
        fields = (
            "id",
            "nome_completo",
            "email",
            "senha",
            "confirmacao_senha",
            "matricula_funcional",
            "foto",
            "ativo",
            "turmas",
            "turmas_ids",
            "turmas_nomes",
        )
        read_only_fields = ("id", "ativo", "turmas_ids", "turmas_nomes")

    def validate_email(self, email):
        email_clean = email.strip().lower()
        query = Professor.objects.filter(email__iexact=email_clean)
        if self.instance:
            query = query.exclude(id=self.instance.id)
        if query.exists():
            raise serializers.ValidationError("Já existe um professor cadastrado com este e-mail.")
        return email_clean

    def validate_turmas(self, turmas):
        escola = self.context["request"].user.escola
        if not turmas:
            raise serializers.ValidationError(
                "Associe o professor a pelo menos uma turma."
            )
        if any(
            not turma.ativo
            or not turma.ano_letivo.ativo
            or turma.ano_letivo.escola_id != escola.id
            for turma in turmas
        ):
            raise serializers.ValidationError(
                "Todas as turmas devem ser ativas e pertencer à sua escola."
            )
        return turmas

    def validate(self, attrs):
        senha = attrs.get("senha")
        confirmacao_senha = attrs.get("confirmacao_senha")
        if confirmacao_senha is not None and senha != confirmacao_senha:
            raise serializers.ValidationError(
                {"confirmacao_senha": "A senha e a confirmação de senha não coincidem."}
            )
        return attrs

    def get_turmas_nomes(self, professor):
        return [str(turma) for turma in self.get_turmas_da_escola(professor)]

    def get_turmas_ids(self, professor):
        return [turma.id for turma in self.get_turmas_da_escola(professor)]

    def get_turmas_da_escola(self, professor):
        user = self.context["request"].user
        if hasattr(user, "escola"):
            return list(
                professor.turmas.filter(
                    ano_letivo__escola=user.escola
                )
                .select_related("ano_letivo")
                .order_by("serie", "nome")
            )
        return list(
            professor.turmas.all()
            .select_related("ano_letivo")
            .order_by("serie", "nome")
        )

    @transaction.atomic
    def create(self, validated_data):
        turmas = validated_data.pop("turmas")
        senha = validated_data.pop("senha")
        validated_data.pop("confirmacao_senha", None)
        professor = Professor(**validated_data)
        professor.set_password(senha)

        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username=professor.email,
            defaults={"email": professor.email},
        )
        user.set_password(senha)
        user.save()

        professor.usuario = user
        professor.save()
        professor.turmas.set(turmas)
        return professor
