"""
Fachada do Serviço de Imagens e Visão Computacional.
Reexporta ImagemService para processamento de fotos do carômetro.
"""

from apps.processamento.services.imagem_service import ImagemService

__all__ = ["ImagemService"]
