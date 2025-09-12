# energy/api/mixins.py
from rest_framework import status
from rest_framework.response import Response

from django.core.cache import cache
from django.utils import timezone

from .exceptions import DeviceOfflineError


class DeviceOnlineCheckMixin:
    """Mixin per verificare lo stato online del dispositivo"""

    def check_device_online(self, device):
        last_seen = device.last_seen
        if (
            not last_seen or (timezone.now() - last_seen).total_seconds() > 300
        ):  # 5 minuti
            raise DeviceOfflineError()


class CachedRetrieveMixin:
    """Mixin per implementare caching nelle retrieve"""

    cache_timeout = 60  # 1 minuto default

    def get_cache_key(self, obj):
        return f"{self.__class__.__name__}_{obj.pk}"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = self.get_cache_key(instance)

        # Prova a ottenere dal cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # Se non in cache, serializza e salva
        serializer = self.get_serializer(instance)
        data = serializer.data
        cache.set(cache_key, data, self.cache_timeout)

        return Response(data)


class BulkCreateMixin:
    """Mixin per supportare la creazione in bulk"""

    def bulk_create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_bulk_create(self, serializer):
        serializer.save()
