# cercollettiva/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from core.admin import admin_site

urlpatterns = [
    # Favicon - prevent 500 errors
    path("favicon.ico", lambda request: HttpResponse(status=204)),  # No Content
    # Core URLs
    path("", include("core.urls")),
    # Admin URLs
    path("ceradmin/", admin_site.urls),
    # App URLs
    path("energy/", include("energy.urls")),  # Template URLs sotto /energy/
    path(
        "api/energy/", include("energy.urls", namespace="energy-api")
    ),  # API URLs sotto /api/energy/
    path("users/", include("users.urls")),
    path("documents/", include("documents.urls")),
    path("cer/", include("cer.urls")),
    # Monitoring and health checks
    path("monitoring/", include("monitoring.urls")),
    # Monitoring API endpoints
    path("", include("core.urls_monitoring")),
    # Authentication
    path("accounts/login/", lambda request: redirect("users:login")),
]

# Static/Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug Toolbar URLs - solo se esplicitamente abilitato
    if getattr(settings, 'ENABLE_DEBUG_TOOLBAR', False) and settings.DEBUG:
        try:
            import debug_toolbar
            urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
        except ImportError:
            pass