"""
Fachada do Serviço de Alunos.
Reexporta AlunoService e criar_aluno para uso simplificado.
"""

from apps.comunidade.services.aluno_service import AlunoService, criar_aluno

__all__ = ["AlunoService", "criar_aluno"]
