import os
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv

if getattr(sys, 'frozen', False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    BUNDLE_DIR = PROJECT_ROOT

BASE_DIR = PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BUNDLE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-buscadores-musicas-key-2026")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,*").split(",") if h.strip()]

INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Local apps
    'finder_files.apps.FinderFilesConfig',
    'ai.apps.AIConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
    "https://*.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

import dj_database_url

raw_postgres = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
POSTGRES_URL = raw_postgres.strip().strip("'\"") if raw_postgres else None

if POSTGRES_URL:
    print("[DATABASE] Configurando conexão PostgreSQL (NeonDB)...")
    DATABASES = {
        'default': dj_database_url.parse(
            POSTGRES_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    print("[DATABASE WARNING] POSTGRES_URL não definida! Usando fallback SQLite.")
    # Caminho do banco de dados SQLite persistente
    DB_PATH = Path(os.getenv("DB_PATH", str(PROJECT_ROOT / "db.sqlite3")))
    if not DB_PATH.exists() and (BUNDLE_DIR / "db.sqlite3").exists():
        try:
            shutil.copy2(BUNDLE_DIR / "db.sqlite3", DB_PATH)
        except Exception:
            pass

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': DB_PATH,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações de IA
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct:novita")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "meta_llama")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.novita.ai/v3/openai")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface")

# Configurações de Busca (Mínimo de 2 palavras por padrão)
MIN_SEARCH_WORDS = int(os.getenv("MIN_SEARCH_WORDS", "2"))
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "50"))
PASTA_DRIVE = os.getenv("PASTA_DRIVE", "https://drive.google.com/drive/folders/1GjTZ4umBib-7_PznEBx_w4EnNPZIafwU?usp=sharing")

# Configurações Composio (Google Drive API)
API_KEY_COMPOSIO = os.getenv("API_KEY_COMPOSIO", "ak_V5YoWFbGLLAPh_5LHlbl")
ACCOUNT_ID_COMPOSIO = os.getenv("ACCOUNT_ID_COMPOSIO", "ca_XhT0Ykr4jhMK")
COMPOSIO_USER = os.getenv("COMPOSIO_USER", "pg-test-2b7b0cce-325b-4393-bd0b-305f2a3097c4")
if API_KEY_COMPOSIO and not os.getenv("COMPOSIO_API_KEY"):
    os.environ["COMPOSIO_API_KEY"] = API_KEY_COMPOSIO
