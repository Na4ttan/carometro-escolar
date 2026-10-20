"""
Fachada do Serviço de Professores.
Reexporta ProfessorService e criar_professor para uso simplificado.
"""

from apps.comunidade.services.professor_service import ProfessorService, criar_professor

__all__ = ["ProfessorService", "criar_professor"]
