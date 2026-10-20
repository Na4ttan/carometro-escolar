"""
Módulo de utilitários de processamento de imagens do Carômetro.
Delega a execução para a camada de serviço ImagemService.
"""
from apps.processamento.services.imagem_service import (
    CAROMETRO_FOTO_QUALITY,
    CAROMETRO_FOTO_SIZE,
    ImagemService,
    processar_foto_carometro,
)

CAROMETRO_FOTO_SIZE = ImagemService.FOTO_SIZE
CAROMETRO_FOTO_QUALITY = ImagemService.FOTO_QUALITY


def enquadrar_e_redimensionar(img, size=CAROMETRO_FOTO_SIZE):
    return ImagemService.enquadrar_e_redimensionar(img, size=size)


def redimensionar_imagem_carometro(foto_field, size=CAROMETRO_FOTO_SIZE, quality=CAROMETRO_FOTO_QUALITY, force=False):
    return ImagemService.processar_foto(foto_field, size=size, quality=quality, force=force)
