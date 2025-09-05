# cercollettiva/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from core.admin import admin_site

urlpatterns = [
    # Core URLs
    path('', include('core.urls')),

    # Admin URLs
    path('ceradmin/', admin_site.urls),

     # App URLs
    path('energy/', include('energy.urls')),  # Template URLs sotto /energy/
    path('api/energy/', include('energy.urls', namespace='energy-api')),  # API URLs sotto /api/energy/
    path('users/', include('users.urls')),
    path('documents/', include('documents.urls')),
    
    # Monitoring and health checks
    path('monitoring/', include('monitoring.urls')),
    
    # Monitoring API endpoints
    path('', include('core.urls_monitoring')),

    # Authentication
    path('accounts/login/', lambda request: redirect('users:login')),

]

# Static/Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)