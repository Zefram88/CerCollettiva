# core/middleware/first_installation.py

import logging

from django.conf import settings
# from django.shortcuts import redirect
# from django.urls import reverse

logger = logging.getLogger(__name__)


class FirstInstallationMiddleware:
    """
    Middleware per gestire la prima installazione dell'applicazione
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for static files and admin
        if (
            request.path.startswith("/static/")
            or request.path.startswith("/media/")
            or request.path.startswith("/admin/")
        ):
            return self.get_response(request)

        # Skip middleware for API endpoints during testing
        if (
            request.path.startswith("/api/")
            or hasattr(settings, "TESTING")
            and settings.TESTING
        ):
            return self.get_response(request)

        # Check if this is the first installation
        # For now, just pass through - this can be expanded later
        # to check for initial setup requirements

        response = self.get_response(request)
        return response
