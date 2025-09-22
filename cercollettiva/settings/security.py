"""
Security settings for CerCollettiva
Implementa security headers moderni per proteggere da vulnerabilità web comuni
Condizionati via variabili d'ambiente per domini/proxy.
"""

import os

# Security Headers Base
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# SSL/TLS Configuration
# SECURE_SSL_REDIRECT = True  # Disabilitato per evitare loop con proxy Docker
SECURE_SSL_REDIRECT = False  # Nginx gestisce HTTPS, Django serve HTTP
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REDIRECT_EXEMPT = []

# Session Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_AGE = 3600  # 1 hour

# CSRF Security
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"
# Domini configurabili via ambiente (produzione) con fallback locale
_DOMAIN = os.getenv("DOMAIN", "")
_WWW_DOMAIN = os.getenv("WWW_DOMAIN", "")
_API_DOMAIN = os.getenv("API_DOMAIN", "")

def _ensure_https(domain: str) -> str:
    if not domain:
        return ""
    return domain if domain.startswith("http://") or domain.startswith("https://") else f"https://{domain}"

_trusted = {"https://localhost", "https://127.0.0.1"}
for _d in (_DOMAIN, _WWW_DOMAIN, _API_DOMAIN):
    _u = _ensure_https(_d)
    if _u:
        _trusted.add(_u)

CSRF_TRUSTED_ORIGINS = sorted(_trusted)

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
# Consenti CSS esterni usati (Bootstrap e Font Awesome)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://fonts.googleapis.com",
    "https://cdn.jsdelivr.net",
    "https://cdnjs.cloudflare.com",
)
# Consenti font da Google, CDNJS (Font Awesome) e jsdelivr (Bootstrap Icons)
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:", "https:")
_connect_src = ["'self'", "https://cdn.jsdelivr.net"]
if _API_DOMAIN:
    _connect_src.append(_ensure_https(_API_DOMAIN))
CSP_CONNECT_SRC = tuple(_connect_src)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)

# Referrer Policy
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Permissions Policy - Solo feature supportate universalmente
PERMISSIONS_POLICY = {
    "camera": [],
    "microphone": [],
    "geolocation": [],
    "payment": [],
    "usb": [],
    "magnetometer": [],
    "gyroscope": [],
    "accelerometer": [],
    "autoplay": [],
    "bluetooth": [],
    "display-capture": [],
    "fullscreen": [],
    "gamepad": [],
    "midi": [],
    "screen-wake-lock": [],
    "sync-xhr": [],
    "web-share": [],
    "xr-spatial-tracking": [],
}

# Additional Security Settings
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_EMBEDDER_POLICY = "require-corp"

# Custom Security Headers
CUSTOM_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=(), autoplay=(), bluetooth=(), display-capture=(), fullscreen=(), gamepad=(), midi=(), screen-wake-lock=(), sync-xhr=(), web-share=(), xr-spatial-tracking=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
}
