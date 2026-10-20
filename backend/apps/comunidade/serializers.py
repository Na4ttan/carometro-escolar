"""
Serializadores REST para o Domínio de Comunidade Escolar (Alunos e Professores).

Responsabilidades:
1. Validação de formato de dados HTTP e arquivos multipart/form-data (uploads de fotos).
2. Delegação das regras de negócio para a Service Layer (AlunoService e ProfessorService).
3. Eliminação de consultas N+1 ao banco de dados através do reaproveitamento dos atributos pré-carregados (Prefetch).
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.academico.models import Turma
from apps.comunidade.services.aluno_service import AlunoService
from apps.comunidade.services.professor_service import ProfessorService
from .models import Aluno, Matricula, Professor


class AlunoSerializer(serializers.ModelSerializer):
    """
    Serializador de entrada e saída para Alunos:
    - Entrada (write_only): recebe o campo 'turma' (ID) para matricular o aluno.
    - Saída: expõe 'turma_id' e 'turma_nome' da matrícula ativa calculada de forma otimizada.
    """

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
        """Valida se a turma pertence à escola do usuário logado via Service."""
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not hasattr(user, "escola"):
            raise serializers.ValidationError(
                "Apenas a administração da escola pode vincular turmas a alunos."
            )
        try:
            return AlunoService.validar_turma(turma, escola=user.escola)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict.get("turma", exc.messages))

    def validate_matricula(self, matricula):
        """Valida duplicidade de matrícula escolar via Service."""
        if matricula:
            instance_id = self.instance.id if self.instance else None
            try:
                AlunoService.validar_matricula(matricula, aluno_id=instance_id)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.message_dict.get("matricula", exc.messages))
        return matricula

    def get_turma_nome(self, aluno):
        """Retorna o nome da turma em que o aluno possui matrícula ativa."""
        matricula = self.get_matricula_ativa(aluno)
        return str(matricula.turma) if matricula else None

    def get_turma_id(self, aluno):
        """Retorna o ID da turma da matrícula ativa."""
        matricula = self.get_matricula_ativa(aluno)
        return matricula.turma_id if matricula else None

    def get_matricula_ativa(self, aluno):
        """
        Obtém a matrícula ativa do aluno:
        - Prioridade 1 (Otimização O(1)): Se o queryset utilizou Prefetch(..., to_attr="matriculas_ativas"),
          lê a lista em memória sem disparar nenhuma nova query SQL (elimina o gargalo N+1).
        - Fallback: Consulta o banco pontualmente se chamado fora de listagens com prefetch.
        """
        if hasattr(aluno, "matriculas_ativas"):
            return aluno.matriculas_ativas[0] if aluno.matriculas_ativas else None

        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user:
            return None
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

    def create(self, validated_data):
        """Delega a criação de aluno e matrícula para a Service Layer."""
        turma = validated_data.pop("turma")
        request = self.context.get("request")
        escola = getattr(request.user, "escola", None) if request else None
        try:
            return AlunoService.criar_aluno(validated_data, turma=turma, escola=escola)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class ProfessorSerializer(serializers.ModelSerializer):
    """
    Serializador de entrada e saída para Professores:
    - Entrada (write_only): senha com confirmação e lista de turmas atribuídas.
    - Saída: expõe IDs e nomes das turmas sem expor a senha nem o hash.
    """

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
        """Valida se o e-mail é único entre os professores."""
        instance_id = self.instance.id if self.instance else None
        try:
            return ProfessorService.validar_email(email, professor_id=instance_id)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict.get("email", exc.messages))

    def validate_turmas(self, turmas):
        """Valida se as turmas selecionadas pertencem à escola do gestor."""
        request = self.context.get("request")
        escola = getattr(request.user, "escola", None) if request else None
        try:
            return ProfessorService.validar_turmas(turmas, escola=escola)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict.get("turmas", exc.messages))

    def validate(self, attrs):
        """Valida consistência da senha e confirmação de senha."""
        senha = attrs.get("senha")
        confirmacao_senha = attrs.get("confirmacao_senha")
        try:
            ProfessorService.validar_senha(senha, confirmacao_senha)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
        return attrs

    def get_turmas_nomes(self, professor):
        """Retorna os nomes legíveis das turmas do professor."""
        return [str(turma) for turma in self.get_turmas_da_escola(professor)]

    def get_turmas_ids(self, professor):
        """Retorna os IDs numéricos das turmas do professor."""
        return [turma.id for turma in self.get_turmas_da_escola(professor)]

    def get_turmas_da_escola(self, professor):
        """
        Obtém as turmas do professor:
        - Prioridade 1 (Otimização O(1)): Lê o atributo pré-carregado 'turmas_da_escola'
          gerado pelo Prefetch na view, eliminando consultas N+1.
        - Fallback: Consulta o banco pontualmente se necessário.
        """
        if hasattr(professor, "turmas_da_escola"):
            return professor.turmas_da_escola

        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and hasattr(user, "escola"):
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

    def create(self, validated_data):
        """Delega a criação de professor, usuário Django e senhas para a Service Layer."""
        turmas = validated_data.pop("turmas")
        request = self.context.get("request")
        escola = getattr(request.user, "escola", None) if request else None
        try:
            return ProfessorService.criar_professor(validated_data, turmas=turmas, escola=escola)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
