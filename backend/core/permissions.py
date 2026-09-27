from rest_framework.permissions import BasePermission, SAFE_METHODS


class PertenceAEscola(BasePermission):
    message = "Esta conta não está vinculada a uma escola ativa."

    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated
            and hasattr(user, "escola")
            and user.escola.ativo
        )


class PodeVisualizarOuEscolaCria(BasePermission):
    message = "Apenas a administração da escola pode realizar cadastros."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return hasattr(user, "escola") and user.escola.ativo
