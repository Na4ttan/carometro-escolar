"""
Comando de Linha de Comando (CLI): python manage.py redimensionar_fotos

Permite aos administradores de sistema reprocessar em lote todo o acervo de fotos do banco:
- Aplica o enquadramento facial inteligente com OpenCV.
- Redimensiona para a resolução padrão de 500x500px (ou customizada via parâmetros).
- Otimiza o tamanho dos arquivos no disco.
"""

from django.core.management.base import BaseCommand
from apps.comunidade.models import Aluno, Professor
from apps.processamento.services.imagem_service import ImagemService


class Command(BaseCommand):
    help = "Redimensiona todas as fotos cadastradas de alunos e professores para 500x500 pixels."

    def add_arguments(self, parser):
        """Parâmetros opcionais para customizar a resolução de saída."""
        parser.add_argument(
            "--largura",
            type=int,
            default=ImagemService.FOTO_SIZE[0],
            help="Largura alvo em pixels (padrão: 500)",
        )
        parser.add_argument(
            "--altura",
            type=int,
            default=ImagemService.FOTO_SIZE[1],
            help="Altura alvo em pixels (padrão: 500)",
        )

    def handle(self, *args, **options):
        """Varre o banco de dados e processa fotos de alunos e professores."""
        size = (options["largura"], options["altura"])
        self.stdout.write(
            self.style.NOTICE(f"Iniciando redimensionamento para {size[0]}x{size[1]}px...")
        )

        total_alunos = 0
        for aluno in Aluno.objects.all():
            if aluno.foto:
                processado = ImagemService.processar_foto(aluno.foto, size=size, force=True)
                if processado:
                    aluno._skip_async = True
                    aluno.save(update_fields=["foto", "foto_base64", "atualizado_em"])
                    total_alunos += 1
                    self.stdout.write(f"  [Aluno] {aluno.nome_completo}: redimensionado com sucesso.")

        total_professores = 0
        for prof in Professor.objects.all():
            if prof.foto:
                processado = ImagemService.processar_foto(prof.foto, size=size, force=True)
                if processado:
                    prof._skip_async = True
                    prof.save(update_fields=["foto", "foto_base64", "atualizado_em"])
                    total_professores += 1
                    self.stdout.write(f"  [Professor] {prof.nome_completo}: redimensionado com sucesso.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Concluído! {total_alunos} foto(s) de alunos e {total_professores} foto(s) de professores processadas."
            )
        )
