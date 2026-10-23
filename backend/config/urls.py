"""
Configuração Principal de Rotas (URLs) do Projeto Carômetro.

Este arquivo centraliza o roteamento de toda a aplicação:
1. /admin/ : Painel administrativo oficial do Django.
2. /api/   : Endpoints REST divididos por domínio (autenticação, acadêmico, comunidade).
3. /media/ : Servimento das fotos processadas de alunos e professores em modo DEBUG.
4. /*      : Roteamento SPA (Single Page Application) servindo a distribuição Angular compilada.
"""

from pathlib import Path
from django.contrib import admin
from django.conf import settings
from django.urls import path, re_path, include
from django.views.static import serve
from django.http import HttpResponse

# Caminho absoluto para a pasta onde o build de produção do Angular é gerado ('dist/frontend/browser')
FRONTEND_DIR = settings.BASE_DIR.parent / "frontend" / "dist" / "frontend" / "browser"


def serve_frontend(request, path=""):
    """
    Controlador para servir a aplicação Angular (Single Page Application):
    - Se o arquivo físico solicitado existir (ex: .js, .css, imagens), serve diretamente.
    - Se for uma rota de navegação do frontend (ex: /login, /consulta), devolve o index.html,
      permitindo que o roteador do Angular assuma o controle no navegador.
    - Se o frontend ainda não tiver sido compilado com 'npm run build', orienta o desenvolvedor.
    """
    if not FRONTEND_DIR.exists():
        return HttpResponse(
            "Frontend não compilado. Execute 'npm run build' na pasta frontend.",
            status=503,
            content_type="text/plain; charset=utf-8",
        )
    if path and (FRONTEND_DIR / path).is_file():
        return serve(request, path, document_root=str(FRONTEND_DIR))
    return serve(request, "index.html", document_root=str(FRONTEND_DIR))


# Rotas primárias do sistema
urlpatterns = [
    # Painel Administrativo do Django
    path("admin/", admin.site.urls),

    # APIs REST modularizadas por domínio sob o prefixo /api/
    path("api/", include("apps.autenticacao.urls")),
    path("api/", include("apps.academico.urls")),
    path("api/", include("apps.comunidade.urls")),
]

urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]

# Rota 'catch-all' (deve ser a última da lista): qualquer URL não capturada acima é entregue ao Angular
urlpatterns += [
    path("", serve_frontend, {"path": ""}),
    re_path(r"^(?P<path>.*)$", serve_frontend),
]
