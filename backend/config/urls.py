"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from pathlib import Path
from django.contrib import admin
from django.conf import settings
from django.urls import path, re_path, include
from django.views.static import serve
from django.http import HttpResponse

FRONTEND_DIR = settings.BASE_DIR.parent / "frontend" / "dist" / "frontend" / "browser"


def serve_frontend(request, path=""):
    if not FRONTEND_DIR.exists():
        return HttpResponse(
            "Frontend não compilado. Execute 'npm run build' na pasta frontend.",
            status=503,
            content_type="text/plain; charset=utf-8",
        )
    if path and (FRONTEND_DIR / path).is_file():
        return serve(request, path, document_root=str(FRONTEND_DIR))
    return serve(request, "index.html", document_root=str(FRONTEND_DIR))


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path(
            "media/alunos/<path:path>",
            serve,
            {"document_root": settings.BASE_DIR / "alunos"},
        ),
        path(
            "media/professores/<path:path>",
            serve,
            {"document_root": settings.BASE_DIR / "professores"},
        ),
    ]

urlpatterns += [
    path("", serve_frontend, {"path": ""}),
    re_path(r"^(?P<path>.*)$", serve_frontend),
]
