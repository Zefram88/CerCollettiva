"""
Rate Limiting Middleware for CerCollettiva
Implements protection against DoS attacks and abuse
"""

import logging

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

# import time


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
                # Login: best practice → soglia meno aggressiva e finestra breve
                # Il conteggio effettivo avviene SOLO sui fallimenti (vedi process_response)
                "login": {"requests": 10, "window": 600},  # 10 tentativi/10min per IP+username
                "upload": {"requests": 10, "window": 3600},  # 10 req/hour
            },
        )

    def __call__(self, request):
        try:
            # Determinare il tipo di endpoint
            endpoint_type = self._get_endpoint_type(request)

            # Ottenere identificatore utente/IP
            identifier = self._get_identifier(request)

            # Per login GET non si applica rate limiting (noisy e non sensibile)
            if endpoint_type == "login" and request.method != "POST":
                return self.get_response(request)

            # Verificare rate limit (anticipato per tutti tranne login POST)
            is_login_post = endpoint_type == "login" and request.method == "POST"
            effective_identifier = (
                self._get_login_identifier(request) if is_login_post else identifier
            )

            if self._is_rate_limited(effective_identifier, endpoint_type):
                logger.warning(
                    f"Rate limit exceeded for {effective_identifier} on {endpoint_type} "
                    f"endpoint: {request.path}"
                )
                return self._rate_limit_response(request, endpoint_type)

            # Incremento immediato per tutto tranne login POST.
            # Per login POST incrementiamo SOLO se fallisce (in process_response)
            if not is_login_post:
                self._increment_counter(identifier, endpoint_type)
            else:
                # Marca per gestione in process_response
                request._rate_limit_login_track = True
                request._rate_limit_login_identifier = effective_identifier
                request._rate_limit_login_endpoint = endpoint_type
        except Exception as e:
            # In caso di problemi con la cache/Redis, non bloccare la richiesta
            logger.warning(
                "RateLimitMiddleware disabled for this request due to error: %s",
                e,
            )

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
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            return f"user:{request.user.id}"
        else:
            return f"ip:{self._get_client_ip(request)}"

    def _get_login_identifier(self, request):
        """Identificatore specifico per login: IP + username/email (se fornito)."""
        client_ip = self._get_client_ip(request)
        username = (request.POST.get("username") or request.POST.get("email") or "").strip().lower()
        if username:
            return f"login:{client_ip}:{username}"
        return f"login:{client_ip}"

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
        try:
            current_count = cache.get(key, 0)
        except Exception as e:
            logger.warning("Rate limit check skipped due to cache error: %s", e)
            return False
        return current_count >= limit_config["requests"]

    def _increment_counter(self, identifier, endpoint_type):
        """Incrementa il contatore per l'identificatore"""
        limit_config = self.rate_limits.get(endpoint_type, self.rate_limits["default"])
        key = f"rate_limit:{endpoint_type}:{identifier}"
        try:
            current_count = cache.get(key, 0)
            cache.set(key, current_count + 1, limit_config["window"])
        except Exception as e:
            logger.warning("Rate limit counter increment skipped due to cache error: %s", e)
            return

        # Log per monitoring
        if current_count + 1 > limit_config["requests"] * 0.8:  # 80% del limite
            logger.info(
                f"Rate limit warning: {identifier} approaching limit "
                f"({current_count + 1}/{limit_config['requests']}) for {endpoint_type}"
            )

    def _rate_limit_response(self, request, endpoint_type):
        """Restituisce una risposta di rate limit appropriata"""
        # Comunica Retry-After basato sulla finestra
        limit_config = self.rate_limits.get(endpoint_type, self.rate_limits["default"])
        retry_after = limit_config.get("window", 60)
        if request.path.startswith("/api/"):
            resp = JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": retry_after,
                },
                status=429,
            )
            resp["Retry-After"] = str(retry_after)
            return resp
        else:
            resp = HttpResponse(
                "Rate limit exceeded. Please try again later.", status=429
            )
            resp["Retry-After"] = str(retry_after)
            return resp

    # Gestione post-risposta per login: incrementa solo su fallimento, reset su successo
    def process_response(self, request, response):
        try:
            if getattr(request, "_rate_limit_login_track", False):
                identifier = getattr(request, "_rate_limit_login_identifier", None)
                endpoint_type = getattr(request, "_rate_limit_login_endpoint", "login")
                if identifier:
                    # Heuristica: login fallito → risposta 200 (pagina login ripresentata)
                    # login riuscito → tipicamente 302 redirect
                    if response.status_code == 200:
                        self._increment_counter(identifier, endpoint_type)
                    elif response.status_code in (301, 302, 303, 307, 308):
                        # Reset contatore al successo per perdonare errori sporadici
                        key = f"rate_limit:{endpoint_type}:{identifier}"
                        try:
                            cache.delete(key)
                        except Exception:
                            pass
        except Exception as e:
            logger.warning("Rate limit post-response hook error: %s", e)
        return response
