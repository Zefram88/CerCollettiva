"""
Rate Limiting Middleware for CerCollettiva
Implements protection against DoS attacks and abuse
"""

import logging
# import time

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware per implementare rate limiting su endpoint API e viste sensibili.
    Protegge il sistema da attacchi DoS e abuso.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Configurazione rate limits per tipo di endpoint
        self.rate_limits = getattr(
            settings,
            "RATE_LIMIT_SETTINGS",
            {
                "default": {"requests": 100, "window": 3600},  # 100 req/hour
                "api": {"requests": 200, "window": 3600},  # 200 req/hour
                "login": {"requests": 5, "window": 900},  # 5 req/15min
                "upload": {"requests": 10, "window": 3600},  # 10 req/hour
            },
        )

    def __call__(self, request):
        # Determinare il tipo di endpoint
        endpoint_type = self._get_endpoint_type(request)

        # Ottenere identificatore utente/IP
        identifier = self._get_identifier(request)

        # Verificare rate limit
        if self._is_rate_limited(identifier, endpoint_type):
            logger.warning(
                f"Rate limit exceeded for {identifier} on {endpoint_type} "
                f"endpoint: {request.path}"
            )
            return self._rate_limit_response(request)

        # Incrementare contatore
        self._increment_counter(identifier, endpoint_type)

        return self.get_response(request)

    def _get_endpoint_type(self, request):
        """Determina il tipo di endpoint basato sul path"""
        path = request.path

        if path.startswith("/api/login/") or path.startswith("/users/login/"):
            return "login"
        elif path.startswith("/api/upload/") or path.startswith("/documents/upload/"):
            return "upload"
        elif path.startswith("/api/"):
            return "api"
        else:
            return "default"

    def _get_identifier(self, request):
        """Ottiene l'identificatore per il rate limiting"""
        if request.user.is_authenticated:
            return f"user:{request.user.id}"
        else:
            return f"ip:{self._get_client_ip(request)}"

    def _get_client_ip(self, request):
        """Ottiene l'IP del client considerando proxy e load balancer"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
        return ip

    def _is_rate_limited(self, identifier, endpoint_type):
        """Verifica se l'identificatore ha superato il rate limit"""
        limit_config = self.rate_limits.get(endpoint_type, self.rate_limits["default"])
        key = f"rate_limit:{endpoint_type}:{identifier}"

        current_count = cache.get(key, 0)
        return current_count >= limit_config["requests"]

    def _increment_counter(self, identifier, endpoint_type):
        """Incrementa il contatore per l'identificatore"""
        limit_config = self.rate_limits.get(endpoint_type, self.rate_limits["default"])
        key = f"rate_limit:{endpoint_type}:{identifier}"

        current_count = cache.get(key, 0)
        cache.set(key, current_count + 1, limit_config["window"])

        # Log per monitoring
        if current_count + 1 > limit_config["requests"] * 0.8:  # 80% del limite
            logger.info(
                f"Rate limit warning: {identifier} approaching limit "
                f"({current_count + 1}/{limit_config['requests']}) for {endpoint_type}"
            )

    def _rate_limit_response(self, request):
        """Restituisce una risposta di rate limit appropriata"""
        if request.path.startswith("/api/"):
            return JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 3600,  # 1 hour
                },
                status=429,
            )
        else:
            return HttpResponse(
                "Rate limit exceeded. Please try again later.", status=429
            )
