"""
Módulo de Paginação Customizada da API do Carômetro.

Fornece paginação eficiente baseada em número de página, prevenindo sobrecarga de memória
ao listar milhares de alunos em escolas de grande porte.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CarometroPagination(PageNumberPagination):
    """
    Estratégia de paginação oficial do sistema:
    - Tamanho padrão da página: 20 registros.
    - Tamanho customizável via URL: ?page_size=50 (limitado a no máximo 100 itens).
    - Desativação sob demanda (Bypass): ?sem_paginacao=true ou ?all=true para exportações ou seletores totais.

    Formato padronizado de retorno:
    {
        "count": 150,
        "total_paginas": 8,
        "pagina_atual": 1,
        "proxima": "http://.../api/alunos/?page=2",
        "anterior": null,
        "results": [ ... ]
    }
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        """
        Interrompe a paginação caso o cliente explicitamente solicite a listagem completa.
        Retornar None instrui a GenericAPIView do DRF a devolver todos os registros diretamente.
        """
        sem_pag = request.query_params.get("sem_paginacao", "").lower() in ("true", "1")
        todos = request.query_params.get("all", "").lower() in ("true", "1")
        if sem_pag or todos:
            return None
        return super().paginate_queryset(queryset, request, view=view)

    def get_paginated_response(self, data):
        """Estrutura o dicionário de resposta com metadados detalhados de paginação."""
        return Response({
            "count": self.page.paginator.count,
            "total_paginas": self.page.paginator.num_pages,
            "pagina_atual": self.page.number,
            "proxima": self.get_next_link(),
            "anterior": self.get_previous_link(),
            "results": data,
        })
