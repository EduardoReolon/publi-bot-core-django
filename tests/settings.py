"""Settings dos testes: SQLite em memoria, para provar que nada depende do
Postgres. O CI roda tambem contra Postgres e MySQL (ver .github/workflows)."""

import os
import tempfile

SECRET_KEY = "so-para-testes"
DEBUG = False
ALLOWED_HOSTS = ["*"]
USE_TZ = True
TIME_ZONE = "America/Sao_Paulo"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "publibot_core",
]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
ROOT_URLCONF = "tests.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]
        },
    }
]

_BANCO = os.environ.get("BANCO", "sqlite")
if _BANCO == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "publibot_core"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        }
    }
elif _BANCO == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "publibot_core"),
            "USER": os.environ.get("DB_USER", "root"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "root"),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "/static/"
MEDIA_ROOT = tempfile.mkdtemp(prefix="publibot-core-")
MEDIA_URL = "/media/"
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024

PUBLIBOT_API_KEY = "chave-de-teste"
PUBLIBOT_SIGNING_SECRET = "segredo-de-teste"
PUBLIBOT_PUBLIC_URL = "https://exemplo.com.br"
PUBLIBOT_SITE_TITLE = "Site de teste"
PUBLIBOT_HOME_TEXT = "Texto da home."
PUBLIBOT_REQUIRE_HTTPS = False
