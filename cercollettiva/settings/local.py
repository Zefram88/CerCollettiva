# cercollettiva/settings/local.py

from .base import *
import socket

ENVIRONMENT = 'local'

# Debug
DEBUG = True


GEOCODING_SETTINGS = {
    'TIMEOUT': 5,  # Aumentato da 1 a 5 secondi
    'MAX_RETRIES': 2,
    'OPTIONAL': True,
    'CACHE_TIMEOUT': 86400  # 24 ore di cache
}

# Host consentiti per sviluppo
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '[::1]',
]

# Aggiungi automaticamente l'IP locale per development
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
ALLOWED_HOSTS.extend([ip for ip in ips])

# Apps installate
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'channels',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'django_extensions',
    'django_filters',

    # Local apps
    'users.apps.UsersConfig',
    'core.apps.CoreConfig',
    'energy.apps.EnergyConfig',
    'documents.apps.DocumentsConfig',
]

# Middleware (senza debug_toolbar)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configurazione database - usa SQLite per sviluppo rapido
# Per PostgreSQL, decommentare la sezione sotto e installare/configurare PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Database PostgreSQL (decommentare quando PostgreSQL è installato e configurato)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'cercollettiva_dev',
#         'USER': 'cercollettiva_user',
#         'PASSWORD': 'your_password_here',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }


# Cache per sviluppo
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Email backend per sviluppo
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configurazione logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'mqtt': {
            'format': '%(asctime)s [MQTT] %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'measurement': {
            'format': '%(asctime)s [MEASUREMENT] %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'device': {
            'format': '%(asctime)s [DEVICE] %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'document_processor': {
            'format': '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/debug.log',
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
        'mqtt_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/mqtt.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'mqtt',
            'level': 'INFO',
        },
        'measurement_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/measurements.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'measurement',
            'level': 'INFO',
        },
        'device_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/devices.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'device',
            'level': 'INFO',
        },
        'general_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/cercollettiva.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'INFO',
        },
        'gaudi_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/gaudi.log',
            'formatter': 'verbose',
        },
        'document_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/documents.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'document_processor',
            'level': 'INFO',
        },
        'document_error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/documents_error.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'document_processor',
            'level': 'ERROR',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'general_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'energy': {
            'handlers': ['console', 'general_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'energy.mqtt': {
            'handlers': ['console', 'mqtt_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'energy.measurements': {
            'handlers': ['console', 'measurement_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'energy.devices': {
            'handlers': ['console', 'device_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'geocoding': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'documents': {
            'handlers': ['console', 'document_file', 'document_error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'documents.processors': {
            'handlers': ['console', 'document_file', 'document_error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'documents.processors.gaudi': {
            'handlers': ['console', 'document_file', 'document_error_file', 'gaudi_file'],
            'level': 'DEBUG',
            'propagate': False,  # Modificato da True a False
        }
    },
    'root': {
        'handlers': ['console', 'general_file'],
        'level': 'WARNING',
    }
}


# Configurazioni aggiuntive per i log
LOG_RETENTION_DAYS = 30
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5


# MQTT Settings
MQTT_SETTINGS = {
    'BROKER_HOST': os.getenv('MQTT_HOST', '195.43.182.22'),
    'BROKER_PORT': int(os.getenv('MQTT_PORT', 2607)),
    'USERNAME': os.getenv('MQTT_USER', 'IoT_01'),
    'PASSWORD': os.getenv('MQTT_PASS', 'mqtt_password_here'),
    'QOS_LEVEL': 1,
    'KEEPALIVE': 60,
    'MAX_RETRIES': 5,
    'RECONNECT_DELAY': 5,
    'CONNECTION_TIMEOUT': 10,
    'CLEAN_SESSION': True,
    'TLS_ENABLED': False,
    'TOPIC_PREFIX': 'CerCollettiva/',
    'STATUS_TOPIC': 'CerCollettiva/status',
    'ERROR_TOPIC': 'CerCollettiva/errors',
    'DEBUG': True,
}

# Media e Static files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

os.makedirs(os.path.join(MEDIA_ROOT, 'documents', 'gaudi'), exist_ok=True)


STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Security settings per development
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# CORS settings per development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Configurazione Crispy Forms
CRISPY_FAIL_SILENTLY = not DEBUG