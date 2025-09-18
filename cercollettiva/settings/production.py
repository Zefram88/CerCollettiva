# cercollettiva/settings/production.py

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *

# Disabilita il debug
DEBUG = False

# Impedisci abilità accidentale di DEBUG via variabile d'ambiente
if os.getenv("DEBUG", "").lower() == "true":
    raise ValueError("DEBUG deve essere False in produzione")

# Chiave segreta da variabile d'ambiente
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY non impostata nelle variabili d'ambiente")

# Host consentiti
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS non impostato nelle variabili d'ambiente")
if "*" in [h.strip() for h in ALLOWED_HOSTS if h is not None]:
    raise ValueError("ALLOWED_HOSTS non può contenere '*' in produzione")

# Database PostgreSQL produzione
# 
# SSL DATABASE vs SSL UI (HTTPS) - CONFIGURAZIONI INDIPENDENTI:
# - SSL Database: comunicazione app ↔ database (questa configurazione)
# - SSL UI: comunicazione browser ↔ server (configurata in Nginx, sempre attiva)
#
# SSL Database è SEMPRE DISABILITATO perché:
# - Database Docker interno: traffico non esce dalla rete Docker
# - SSL non aggiunge sicurezza per comunicazione interna container
# - Per database esterni: usare configurazione dedicata (es. AWS RDS)
#
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            # SSL Database: sempre disabilitato per Docker interno
            # NOTA: SSL UI (HTTPS) rimane attivo e indipendente da questa configurazione
            "sslmode": "disable",  # Docker interno sempre sicuro
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
        "TEST": {"NAME": None},  # Disabilita i test in produzione
    }
}

# Cache Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL"),
    }
}

# Cache del template in produzione
TEMPLATES[0]["APP_DIRS"] = False  # Disabilita APP_DIRS quando loaders è definito
TEMPLATES[0]["OPTIONS"]["loaders"] = [
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    ),
]

# Configurazione Channels per produzione
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL")],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}

# Configurazione email produzione
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

# Sicurezza
# SECURE_SSL_REDIRECT = True  # Temporaneamente disabilitato per debug
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 31536000  # 1 anno
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REFERRER_POLICY = "same-origin"
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Disabilita debug toolbar o configurazioni dev se accidentalmente presenti
if 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')
if 'debug_toolbar.middleware.DebugToolbarMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')

# Middleware di setup per produzione - dopo AuthenticationMiddleware
MIDDLEWARE += [
    "core.middleware.FirstInstallationMiddleware",
]

# Configurazione session
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 86400  # 24 ore
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = "__Secure-sessionid"
SESSION_COOKIE_SAMESITE = "Lax"

# File statici e media
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# MQTT produzione
MQTT_SETTINGS = {
    "BROKER_HOST": os.getenv("MQTT_HOST"),
    "BROKER_PORT": int(os.getenv("MQTT_PORT", 8883)),  # Porta TLS standard
    "USERNAME": os.getenv("MQTT_USER"),
    "PASSWORD": os.getenv("MQTT_PASS"),
    "QOS_LEVEL": 2,  # QoS massimo per affidabilità
    "KEEPALIVE": 60,
    "TLS_ENABLED": True,
    "MAX_RETRIES": 5,
    "RECONNECT_DELAY": 5,
    "CONNECTION_TIMEOUT": 10,
    "CLEAN_SESSION": True,
    "TOPIC_PREFIX": "CerCollettiva/",
    "STATUS_TOPIC": "CerCollettiva/status",
    "ERROR_TOPIC": "CerCollettiva/errors",
    "LAST_WILL_TOPIC": "CerCollettiva/status",
    "LAST_WILL_MESSAGE": "offline",
}

# Rest Framework produzione
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/day", "user": "1000/day"},
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}

# Sentry per monitoraggio errori
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[
            DjangoIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=float(os.getenv("SENTRY_SAMPLE_RATE", "0.2")),
        send_default_pii=False,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
    )

# Logging produzione
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "cercollettiva.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "mqtt_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "mqtt.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 10,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": True,
        },
        "django.security": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": False,
        },
        "energy": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
        },
        "energy.mqtt": {
            "handlers": ["mqtt_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Limiti upload file in produzione
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Configurazione Admin
ADMIN_URL = os.getenv("DJANGO_ADMIN_URL", "admin/")  # URL personalizzato per l'admin

# Configurazioni aggiuntive di sicurezza
SILENCED_SYSTEM_CHECKS = []

# Configurazione AWS S3 per storage file (opzionale)
if os.getenv("USE_S3", "False") == "True":
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
    AWS_DEFAULT_ACL = "private"
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
