# cercollettiva/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from core.admin import admin_site
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

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

    # Authentication
    path('accounts/login/', lambda request: redirect('users:login')),

]

# Static/Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # API Docs (Swagger/Redoc) in debug
    schema_view = get_schema_view(
        openapi.Info(
            title="CerCollettiva API",
            default_version='v1',
            description="Documentazione API di CerCollettiva",
        ),
        public=True,
        permission_classes=[permissions.AllowAny],
    )

    urlpatterns += [
        re_path(r'^api/docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        re_path(r'^api/redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
        re_path(r'^api/schema(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    ]
