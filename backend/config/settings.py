"""
Configurações Principais do Projeto Django - Carômetro Escolar.

Estrutura Modular por Domínios:
- apps.autenticacao: Gestão de acessos, tokens DRF e perfis de usuário.
- apps.academico: Gestão de escola, anos letivos e turmas.
- apps.comunidade: Gestão cadastral de alunos, professores e matrículas escolares.
- apps.processamento: Visão computacional com OpenCV, enquadramento inteligente 500x500 e worker assíncrono.
"""

import sys
from pathlib import Path

# Diretório base do backend ('backend/')
BASE_DIR = Path(__file__).resolve().parent.parent

# Chave secreta de desenvolvimento (em produção, recomenda-se passar via variável de ambiente)
SECRET_KEY = 'django-insecure-_!ap6i^f%2_-la9a80plzl908!b9x7rwu-i#wcevjuj^(kky81'

# Modo de depuração ativo para desenvolvimento local
DEBUG = True

# Hosts permitidos para permitir acesso via localhost e túnel HTTPS (Localtunnel)
ALLOWED_HOSTS = ["*"]


# Definição de Aplicativos Instalados
INSTALLED_APPS = [
    # Aplicativos nativos do Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Bibliotecas de terceiros
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',

    # Aplicativos modulares de negócio (Clean Architecture)
    'apps.autenticacao',
    'apps.academico',
    'apps.comunidade',
    'apps.processamento',
]

# Middlewares de segurança e requisição HTTP
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # CORS para comunicação com o Angular
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Banco de Dados (SQLite local)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Validadores de senha padrão do Django
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internacionalização e Fuso Horário
LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Arquivos Estáticos (CSS, JS do Django Admin)
STATIC_URL = 'static/'

# Isolamento de Mídias e Fotos do Carômetro
# Salva arquivos na pasta 'backend/media/' (ignorada no git para proteção de dados)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# Configuração de E-mail para desenvolvimento
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}

# Configurações de CORS e CSRF para suporte a HTTPS no celular via Localtunnel
CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = [
    "https://*.loca.lt",
]

# Processamento de Imagens em Segundo Plano (Thread Worker Assíncrono)
# Em ambiente de execução real (runserver), roda assíncrono para respostas HTTP instantâneas (<100ms).
# Em ambiente de testes automatizados ('test' no argv), executa síncrono para garantir previsibilidade.
TESTING = "test" in sys.argv
CAROMETRO_ASYNC_IMAGE_PROCESSING = not TESTING
