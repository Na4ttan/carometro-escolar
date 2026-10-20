"""
Fachada Unificada de Serviços (Service Layer Facade).

Centraliza a importação dos serviços de negócio da aplicação para facilitar o acesso
por qualquer módulo, comando ou script do Django sem acoplamento a caminhos internos:
- AlunoService: Regras de negócio, validação de matrícula e cadastro de alunos.
- ProfessorService: Regras de negócio, hashing de senhas e sincronização de usuários.
- ImagemService: Visão computacional com OpenCV, enquadramento facial inteligente e tratamento 500x500px.
"""

from apps.comunidade.services.aluno_service import AlunoService, criar_aluno
from apps.comunidade.services.professor_service import ProfessorService, criar_professor
from apps.processamento.services.imagem_service import ImagemService

__all__ = [
    "AlunoService",
    "criar_aluno",
    "ProfessorService",
    "criar_professor",
    "ImagemService",
]
