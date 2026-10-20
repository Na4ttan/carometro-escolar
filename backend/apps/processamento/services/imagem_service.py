"""
Serviço Especializado de Processamento de Imagens e Visão Computacional.

Responsabilidades:
1. Isolação do OpenCV e Pillow da camada HTTP e de Models.
2. Detecção facial com OpenCV Haar Cascades (haarcascade_frontalface_default.xml).
3. Recuperação de rotação para fotos capturadas sem metadados EXIF.
4. Enquadramento e corte proporcional em 500x500px com margem superior (headroom) para avatares circulares.
5. Preservação de transparência em PNGs e fidelidade de perfis de cores ICC (sRGB, Display P3).
"""

import os
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.base import ContentFile


class ImagemService:
    """
    Motor de processamento de fotos do carômetro.
    Garante uniformidade visual em 500x500px e otimização de armazenamento em disco.
    """

    FOTO_SIZE = (500, 500)
    FOTO_QUALITY = 90
    _FACE_DETECTOR = None

    @classmethod
    def get_face_detector(cls):
        """
        Carrega o classificador Haar Cascade do OpenCV em cache (Singleton).
        Evita recarregar o arquivo XML do disco a cada foto processada.
        """
        if cls._FACE_DETECTOR is None:
            try:
                import cv2

                cascade_path = (
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                )
                detector = cv2.CascadeClassifier(cascade_path)
                cls._FACE_DETECTOR = detector if not detector.empty() else False
            except Exception:
                cls._FACE_DETECTOR = False
        return cls._FACE_DETECTOR if cls._FACE_DETECTOR is not False else None

    @classmethod
    def detectar_faces(cls, pil_img):
        """
        Executa a detecção de rostos humanos na imagem utilizando OpenCV:
        - Converte a imagem Pillow para escala de cinza (grayscale).
        - Aplica detectMultiScale com escala 1.1 e vizinhança mínima 4.
        - Retorna uma tupla de retângulos (x, y, largura, altura).
        """
        detector = cls.get_face_detector()
        if not detector:
            return ()
        try:
            import cv2
            import numpy as np

            rgb_img = pil_img.convert("RGB")
            gray = cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2GRAY)
            return detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(30, 30),
            )
        except Exception:
            return ()

    @classmethod
    def tem_transparencia(cls, img):
        """
        Verifica se a imagem contém pixels translúcidos ou transparentes no canal Alfa.
        Permite decidir se o arquivo final deve ser salvo em PNG ou JPEG otimizado.
        """
        try:
            if img.mode in ("RGBA", "LA"):
                alpha = img.getchannel("A")
                min_alpha, _ = alpha.getextrema()
                return min_alpha < 255
            if img.mode == "P" and "transparency" in img.info:
                return True
        except Exception:
            pass
        return False

    @classmethod
    def enquadrar_e_redimensionar(cls, img, size=None):
        """
        Aplica o algoritmo inteligente de enquadramento facial:
        1. Se nenhum rosto for detectado na orientação original, testa rotações (270°, 90°, 180°)
           para o caso de fotos capturadas na vertical mas enviadas deitadas sem tag EXIF.
        2. Se encontrar rosto(s):
           - Seleciona o rosto predominante (maior área detectada).
           - Define uma janela de corte de ~2.2x o tamanho da face.
           - Posiciona o centro do rosto em ~40% do topo da janela (headroom perfeito para crachás e carômetros).
           - Recorta e redimensiona com interpolação Lanczos de alta qualidade para 500x500px.
        3. Fallback: Se nenhum rosto for detectado, aplica corte centralizado com leve inclinação ao topo (35%).
        """
        target_size = size or cls.FOTO_SIZE
        faces = cls.detectar_faces(img)

        # Se nenhum rosto foi detectado na orientação atual, testa rotações caso EXIF tenha sido descartado
        if len(faces) == 0:
            rotations = (
                Image.Transpose.ROTATE_270,
                Image.Transpose.ROTATE_90,
                Image.Transpose.ROTATE_180,
            )
            for rot in rotations:
                candidate = img.transpose(rot)
                cand_faces = cls.detectar_faces(candidate)
                if len(cand_faces) > 0:
                    img = candidate
                    faces = cand_faces
                    break

        W, H = img.size

        if len(faces) > 0:
            # Seleciona o rosto principal (maior área detectada)
            fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])

            # Tamanho do corte: aproximadamente 2.2x o tamanho do rosto
            crop_size = min(int(max(fw, fh) * 2.2), min(W, H))

            # Centro geométrico do rosto
            cx = fx + fw / 2.0
            cy = fy + fh / 2.0

            # Posiciona o rosto em ~40% do topo do corte (enquadramento clássico de carômetro)
            crop_x = int(cx - crop_size / 2.0)
            crop_y = int(cy - 0.40 * crop_size)

            # Garante que o retângulo permaneça dentro dos limites físicos da imagem
            crop_x = max(0, min(crop_x, W - crop_size))
            crop_y = max(0, min(crop_y, H - crop_size))

            cropped = img.crop((crop_x, crop_y, crop_x + crop_size, crop_y + crop_size))
            return cropped.resize(target_size, Image.Resampling.LANCZOS)
        else:
            # Fallback inteligente: centralizado na horizontal e inclinado 35% no topo
            return ImageOps.fit(
                img,
                target_size,
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.35),
            )

    @classmethod
    def processar_foto(
        cls,
        foto_field,
        size=None,
        quality=None,
        force=False,
    ):
        """
        Executa a esteira completa de processamento de um campo ImageField do Django:
        - Respeita orientação EXIF nativa (exif_transpose).
        - Preserva perfis de cores ICC originais.
        - Enquadra e redimensiona para 500x500px.
        - Converte para JPEG com compressão otimizada ou PNG se houver transparência alfa.
        - Remove com segurança o arquivo antigo do disco caso a extensão tenha mudado (.jpg <-> .png).
        """
        if not foto_field:
            return False

        if getattr(foto_field, "_committed", True) and not force:
            return False

        target_size = size or cls.FOTO_SIZE
        target_quality = quality or cls.FOTO_QUALITY

        old_path = None
        try:
            if hasattr(foto_field, "path") and os.path.exists(foto_field.path):
                old_path = foto_field.path
        except Exception:
            old_path = None

        try:
            foto_field.open()
            with Image.open(foto_field) as img:
                # 1. Ajusta rotação baseada em metadados EXIF
                img = ImageOps.exif_transpose(img)
                icc_profile = img.info.get("icc_profile")

                # 2. Executa enquadramento facial e redimensionamento 500x500
                img = cls.enquadrar_e_redimensionar(img, size=target_size)
                tem_alpha = cls.tem_transparencia(img)

                buffer = BytesIO()
                nome_original = os.path.basename(foto_field.name or "foto.jpg")
                nome_base, _ = os.path.splitext(nome_original)

                save_kwargs = {}
                if icc_profile:
                    save_kwargs["icc_profile"] = icc_profile

                # 3. Salva em formato adequado
                if tem_alpha:
                    img = img.convert("RGBA")
                    img.save(buffer, format="PNG", optimize=True, **save_kwargs)
                    novo_nome = f"{nome_base}.png"
                else:
                    img = img.convert("RGB")
                    img.save(
                        buffer,
                        format="JPEG",
                        quality=target_quality,
                        optimize=True,
                        **save_kwargs,
                    )
                    novo_nome = f"{nome_base}.jpg"

                buffer.seek(0)
                foto_field.save(novo_nome, ContentFile(buffer.read()), save=False)

                # 4. Remove o arquivo anterior do disco se foi renomeado
                if old_path and hasattr(foto_field, "path") and old_path != foto_field.path:
                    try:
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except OSError:
                        pass

                return True
        except Exception:
            return False
