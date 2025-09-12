# cercollettiva/settings/test.py

from .base import *

# Test settings
DEBUG = False
TESTING = True

# Database PostgreSQL per test - usa lo stesso container Docker
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_cercollettiva",
        "USER": "cercollettiva_user",
        "PASSWORD": "cercollettiva_pass",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {
            "NAME": "test_cercollettiva_ci",
        },
    }
}

# Disabilita cache per test
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Disabilita logging per test
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
        },
        "energy": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    },
}

# Disabilita MQTT per test
MQTT_ENABLED = False

# Password hasher veloce per test
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disabilita middleware non necessari per test
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Disabilita static files per test
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Disabilita email per test
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disabilita channels per test
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}
