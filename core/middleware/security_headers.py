"""
Security Headers Middleware for CerCollettiva
Implementa security headers moderni per proteggere da vulnerabilità web
"""

import logging

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware per aggiungere security headers moderni alle risposte HTTP.
    Protegge l'applicazione da XSS, clickjacking e altre vulnerabilità web.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.security_headers = getattr(settings, "CUSTOM_SECURITY_HEADERS", {})
        self.csp_enabled = hasattr(settings, "CSP_DEFAULT_SRC")

    def __call__(self, request):
        response = self.get_response(request)

        # Aggiungere security headers personalizzati
        for header, value in self.security_headers.items():
            response[header] = value

        # Content Security Policy
        if self.csp_enabled:
            csp_policy = self._build_csp_policy()
            if csp_policy:
                response["Content-Security-Policy"] = csp_policy

        # Permissions Policy
        if hasattr(settings, "PERMISSIONS_POLICY"):
            permissions_policy = self._build_permissions_policy()
            if permissions_policy:
                response["Permissions-Policy"] = permissions_policy

        # Log security headers per monitoring
        if hasattr(request, "user") and request.user.is_authenticated:
            logger.debug(
                f"Security headers applied for user {request.user.id} on {request.path}"
            )

        return response

    def _build_csp_policy(self):
        """Costruisce la Content Security Policy"""
        policy_parts = []

        # Default source
        if hasattr(settings, "CSP_DEFAULT_SRC"):
            policy_parts.append(f"default-src {' '.join(settings.CSP_DEFAULT_SRC)}")

        # Script source
        if hasattr(settings, "CSP_SCRIPT_SRC"):
            policy_parts.append(f"script-src {' '.join(settings.CSP_SCRIPT_SRC)}")

        # Style source
        if hasattr(settings, "CSP_STYLE_SRC"):
            policy_parts.append(f"style-src {' '.join(settings.CSP_STYLE_SRC)}")

        # Font source
        if hasattr(settings, "CSP_FONT_SRC"):
            policy_parts.append(f"font-src {' '.join(settings.CSP_FONT_SRC)}")

        # Image source
        if hasattr(settings, "CSP_IMG_SRC"):
            policy_parts.append(f"img-src {' '.join(settings.CSP_IMG_SRC)}")

        # Connect source
        if hasattr(settings, "CSP_CONNECT_SRC"):
            policy_parts.append(f"connect-src {' '.join(settings.CSP_CONNECT_SRC)}")

        # Frame ancestors
        if hasattr(settings, "CSP_FRAME_ANCESTORS"):
            policy_parts.append(
                f"frame-ancestors {' '.join(settings.CSP_FRAME_ANCESTORS)}"
            )

        # Base URI
        if hasattr(settings, "CSP_BASE_URI"):
            policy_parts.append(f"base-uri {' '.join(settings.CSP_BASE_URI)}")

        # Object source
        if hasattr(settings, "CSP_OBJECT_SRC"):
            policy_parts.append(f"object-src {' '.join(settings.CSP_OBJECT_SRC)}")

        return "; ".join(policy_parts) if policy_parts else None

    def _build_permissions_policy(self):
        """Costruisce la Permissions Policy"""
        if not hasattr(settings, "PERMISSIONS_POLICY"):
            return None

        permissions = settings.PERMISSIONS_POLICY
        policy_parts = []

        for feature, allowlist in permissions.items():
            if allowlist:
                policy_parts.append(f"{feature}=({' '.join(allowlist)})")
            else:
                policy_parts.append(f"{feature}=()")

        return ", ".join(policy_parts) if policy_parts else None
