"""
Classes de Permissão Customizadas para o Django REST Framework (DRF).

Controlam as regras de autorização de acordo com o perfil do usuário logado:
- Escola (Administração): permissão total de leitura e escrita (cadastro de alunos/professores/turmas).
- Professor: permissão de somente leitura (consulta ao carômetro de suas turmas atribuídas).
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class PertenceAEscola(BasePermission):
    """
    Permissão restrita à equipe de gestão/administração da escola.
    Exige que o usuário autenticado esteja vinculado a um registro de Escola ativo.
    Utilizada para operações exclusivas da escola (ex: cadastro de professores).
    """

    message = "Esta conta não está vinculada a uma escola ativa."

    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated
            and hasattr(user, "escola")
            and user.escola.ativo
        )


class PodeVisualizarOuEscolaCria(BasePermission):
    """
    Permissão mista para recursos compartilhados (como a lista de alunos):
    - Métodos seguros (GET, HEAD, OPTIONS): permitidos para qualquer usuário autenticado (Escola ou Professor).
    - Métodos de escrita (POST, PUT, PATCH, DELETE): restritos à administração da Escola.
    """

    message = "Apenas a administração da escola pode realizar cadastros."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False

        # Leitura é permitida tanto para administradores quanto para professores
        if request.method in SAFE_METHODS:
            return True

        # Criação/edição exige perfil da escola
        return hasattr(user, "escola") and user.escola.ativo


class PodeEditarAluno(BasePermission):
    """Escola e professores ativos podem editar; exclusão é exclusiva da escola."""

    message = "Apenas a escola ou um professor ativo pode gerenciar alunos."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        escola_ativa = hasattr(user, "escola") and user.escola.ativo
        professor_ativo = hasattr(user, "professor") and user.professor.ativo
        return escola_ativa or professor_ativo

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method == "DELETE":
            return hasattr(user, "escola") and user.escola.ativo
        return True
