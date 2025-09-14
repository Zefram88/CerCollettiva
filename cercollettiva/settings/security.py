"""
Security settings for CerCollettiva
Implementa security headers moderni per proteggere da vulnerabilità web comuni
"""

# Security Headers Base
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# SSL/TLS Configuration
SECURE_SSL_REDIRECT = True
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
CSRF_TRUSTED_ORIGINS = [
    "https://cercollettiva.com",
    "https://www.cercollettiva.com",
    "https://api.cercollettiva.com",
]

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'", "https://api.cercollettiva.com")
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)

# Referrer Policy
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Permissions Policy
PERMISSIONS_POLICY = {
    "camera": [],
    "microphone": [],
    "geolocation": [],
    "payment": [],
    "usb": [],
    "magnetometer": [],
    "gyroscope": [],
    "accelerometer": [],
    "ambient-light-sensor": [],
    "autoplay": [],
    "battery": [],
    "bluetooth": [],
    "display-capture": [],
    "fullscreen": [],
    "gamepad": [],
    "midi": [],
    "notifications": [],
    "persistent-storage": [],
    "push": [],
    "screen-wake-lock": [],
    "speaker-selection": [],
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
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
}
