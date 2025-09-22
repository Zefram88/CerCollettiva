# cercollettiva/settings/base.py

import logging.config
import os
from pathlib import Path

from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Import security settings
try:
    from .security import *
except ImportError:
    # Fallback se il file security.py non esiste
    pass

# Configurazioni di base
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = os.getenv(
    "SECRET_KEY", "django-insecure-test-key-for-development-only-change-in-production"
)
FIELD_ENCRYPTION_KEY = os.getenv(
    "FIELD_ENCRYPTION_KEY", "7OmLozExKYcMJCO7Jof_OGnnRm2-P1zYpnY3eLG7EWE="
)
ENCRYPTED_FIELDS_KEYDIR = None  # Usa la chiave in settings invece di file

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Host consentiti di base (vuoto per sicurezza, da sovrascrivere in local/production)
ALLOWED_HOSTS = []

# Applicazioni
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = [
    "users.apps.UsersConfig",
    "core.apps.CoreConfig",
    "energy.apps.EnergyConfig",
    "documents.apps.DocumentsConfig",
    "monitoring.apps.MonitoringConfig",
    "cer.apps.CerConfig",
]

THIRD_PARTY_APPS = [
    "channels",
    "rest_framework",
    "crispy_forms",
    "crispy_bootstrap5",
    "widget_tweaks",
    "django_filters",
    "django_extensions",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # Per gestione multilingua
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Sicurezza e throttling dopo che request.user è disponibile
    "core.middleware.rate_limiting.RateLimitMiddleware",  # Rate limiting
    "core.middleware.security_headers.SecurityHeadersMiddleware",  # Security headers
]

ROOT_URLCONF = "cercollettiva.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
            ],
        },
    },
]

# WSGI/ASGI
WSGI_APPLICATION = "cercollettiva.wsgi.application"
ASGI_APPLICATION = "cercollettiva.asgi.application"

# Database PostgreSQL di default
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "cercollettiva"),
        "USER": os.getenv("DB_USER", "cercollettiva_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", "cercollettiva_pass"),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "connect_timeout": 10,
        },
        "TEST": {
            "NAME": "test_cercollettiva",
        },
    }
}

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Configurazione rate limiting
RATE_LIMIT_SETTINGS = {
    "default": {"requests": 100, "window": 3600},  # 100 req/hour
    "api": {"requests": 200, "window": 3600},  # 200 req/hour
    "login": {"requests": 5, "window": 900},  # 5 req/15min
    "upload": {"requests": 10, "window": 3600},  # 10 req/hour
}

# Validazione password
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 10,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internazionalizzazione
LANGUAGE_CODE = "it"
TIME_ZONE = "Europe/Rome"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ("it", "Italiano"),
    ("en", "English"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# File statici e media
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
os.makedirs(os.path.join(MEDIA_ROOT, "documents", "gaudi"), exist_ok=True)

# Sicurezza - Configurazione SSL per ambiente
# Nota: in produzione i valori sono forzati in production.py
if DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Rest Framework
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/day", "user": "1000/day"},
}

# Configurazioni app
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.CustomUser"

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Autenticazione
LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "users:login"
LOGOUT_URL = "users:logout"

# Messaggi
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@cercollettiva.it")

# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")],
        },
    },
}

# MQTT Settings
MQTT_SETTINGS = {
    "BROKER_HOST": os.getenv("MQTT_HOST", "localhost"),
    "BROKER_PORT": int(os.getenv("MQTT_PORT", 1883)),
    "USERNAME": os.getenv("MQTT_USER", ""),
    "PASSWORD": os.getenv("MQTT_PASS", ""),
    "QOS_LEVEL": int(os.getenv("MQTT_QOS", 1)),
    "KEEPALIVE": int(os.getenv("MQTT_KEEPALIVE", 60)),
    "TLS_ENABLED": os.getenv("MQTT_TLS", "False") == "True",
    "CLEAN_SESSION": True,
    "TOPIC_PREFIX": "CerCollettiva/",
    "STATUS_TOPIC": "CerCollettiva/status",
    "ERROR_TOPIC": "CerCollettiva/errors",
}

# Logging
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} [{levelname}] {name} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "cercollettiva.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "mqtt_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "mqtt.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "energy": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "energy.mqtt": {
            "handlers": ["console", "mqtt_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "WARNING",
    },
}

# File upload
FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
