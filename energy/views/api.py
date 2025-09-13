# energy/views/api.py
import logging
from datetime import timedelta

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from django.db.models import Max, Sum
from django.utils import timezone

from core.main_models import Plant
from energy.models import DeviceConfiguration, DeviceMeasurement

from ..api.filters import get_filters
from ..api.mixins import BulkCreateMixin, CachedRetrieveMixin, DeviceOnlineCheckMixin
from ..api.pagination import CustomPageNumberPagination
from ..api.permissions import IsDeviceOwner, IsStaffOrReadOnly
from ..api.serializers import (
    DeviceConfigurationSerializer,
    DeviceMeasurementSerializer,
    PlantSerializer,
)

logger = logging.getLogger(__name__)


class DeviceConfigurationViewSet(viewsets.ModelViewSet):
    queryset = DeviceConfiguration.objects.select_related("plant")
    serializer_class = DeviceConfigurationSerializer
    permission_classes = [IsAuthenticated, IsDeviceOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = get_filters()["DeviceConfigurationFilter"]
    search_fields = ["device_id", "plant__name"]
    throttle_classes = [UserRateThrottle]
    pagination_class = CustomPageNumberPagination
    basename = "energy-devices"

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(plant__owner=self.request.user)

    @action(detail=True)
    def latest_measurement(self, request, pk=None):
        device = self.get_object()
        try:
            measurement = (
                DeviceMeasurement.objects.filter(device=device)
                .select_related("device", "plant")
                .latest("timestamp")
            )

            logger.info(
                f"Latest measurement for device {device.id} found: "
                f"{measurement.timestamp}"
            )
            return Response(DeviceMeasurementSerializer(measurement).data)

        except DeviceMeasurement.DoesNotExist:
            logger.warning(f"No measurements found for device {device.id}")
            return Response(
                {"detail": "No measurements found"}, status=status.HTTP_404_NOT_FOUND
            )


class DeviceMeasurementViewSet(
    DeviceOnlineCheckMixin, CachedRetrieveMixin, BulkCreateMixin, viewsets.ModelViewSet
):
    """
    ViewSet per la gestione delle misurazioni dei dispositivi.
    """

    serializer_class = DeviceMeasurementSerializer
    permission_classes = [IsAuthenticated, IsDeviceOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = get_filters()["DeviceMeasurementFilter"]
    ordering_fields = ["timestamp", "power", "voltage", "current"]
    ordering = ["-timestamp"]
    throttle_classes = [UserRateThrottle]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        base_queryset = DeviceMeasurement.objects.select_related(
            "device", "plant"
        ).prefetch_related("phase_details")

        if self.request.user.is_staff:
            return base_queryset
        return base_queryset.filter(plant__owner=self.request.user)

    @action(detail=False)
    def latest(self, request):
        device_id = request.query_params.get("device_id")
        if device_id:
            try:
                measurement = (
                    self.get_queryset()
                    .filter(device__device_id=device_id)
                    .latest("timestamp")
                )
                return Response(self.get_serializer(measurement).data)
            except DeviceMeasurement.DoesNotExist:
                return Response(
                    {"detail": "No measurements found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # SICURO: Utilizzo ORM Django invece di query raw
        # Ottieni l'ultima misurazione per ogni dispositivo usando ORM
        device_ids = self.get_queryset().values_list("device_id", flat=True).distinct()
        latest_measurements = []

        for device_id in device_ids:
            latest = (
                self.get_queryset()
                .filter(device_id=device_id)
                .order_by("-timestamp")
                .first()
            )
            if latest:
                latest_measurements.append(latest)

        return Response(self.get_serializer(latest_measurements, many=True).data)

    def perform_create(self, serializer):
        device = serializer.validated_data.get("device")
        self.check_device_online(device)
        super().perform_create(serializer)


class PlantViewSet(viewsets.ModelViewSet):
    """
    ViewSet per la gestione degli impianti energetici.
    Fornisce operazioni CRUD standard più endpoint personalizzati per
    statistiche e analytics.
    """

    serializer_class = PlantSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    plant_filter = get_filters()["PlantFilter"]
    search_fields = ["name", "pod"]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        """
        Restituisce il queryset degli impianti filtrato in base ai permessi dell'utente.
        Staff può vedere tutti gli impianti, utenti normali solo i propri.
        """
        base_queryset = Plant.objects.select_related("owner").prefetch_related(
            "devices"
        )
        if self.request.user.is_staff:
            return base_queryset
        return base_queryset.filter(owner=self.request.user)

    def retrieve(self, request, pk=None):
        """
        Override del retrieve per includere il tipo di impianto nella risposta
        """
        plant = self.get_object()
        data = self.get_serializer(plant).data
        data["plant_type"] = plant.get_plant_type_display()
        return Response(data)

    @action(detail=True, methods=["get"])
    def type(self, request, pk=None):
        """
        Endpoint dedicato per ottenere il tipo di impianto
        """
        plant = self.get_object()
        return Response(
            {"type": plant.get_plant_type_display(), "id": plant.id, "name": plant.name}
        )

    @action(detail=True, methods=["get"])
    def statistics(self, request, pk=None):
        """
        Fornisce statistiche dettagliate per un singolo impianto.
        Include:
        - Potenza totale attuale
        - Conteggio dispositivi attivi/totali
        - Ultimo aggiornamento
        - Statistiche di produzione giornaliere/mensili
        """
        try:
            plant = self.get_object()
            now = timezone.now()

            # Get active devices and their latest measurements
            devices = DeviceConfiguration.objects.filter(plant=plant)
            latest_measurements = DeviceMeasurement.objects.filter(
                device__in=devices, timestamp__gte=now - timedelta(minutes=5)
            ).select_related("device")

            # Calculate current power statistics
            current_stats = {
                "total_power": latest_measurements.aggregate(Sum("power"))["power__sum"]
                or 0,
                "active_devices": latest_measurements.count(),
                "total_devices": devices.count(),
                "last_update": latest_measurements.aggregate(Max("timestamp"))[
                    "timestamp__max"
                ],
            }

            # Calculate daily production
            daily_production = (
                DeviceMeasurement.objects.filter(
                    device__in=devices, timestamp__date=now.date()
                ).aggregate(Sum("power"))["power__sum"]
                or 0
            )

            # Calculate monthly production
            monthly_production = (
                DeviceMeasurement.objects.filter(
                    device__in=devices,
                    timestamp__year=now.year,
                    timestamp__month=now.month,
                ).aggregate(Sum("power"))["power__sum"]
                or 0
            )

            response_data = {
                "plant_id": plant.id,
                "plant_name": plant.name,
                "current_stats": current_stats,
                "daily_production": round(daily_production, 2),
                "monthly_production": round(monthly_production, 2),
                "is_active": current_stats["active_devices"] > 0,
                "health_status": self._calculate_health_status(current_stats),
            }

            return Response(response_data)

        except Plant.DoesNotExist:
            logger.error(f"Plant with id {pk} not found")
            return Response(
                {"error": "Plant not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting statistics for plant {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def device_status(self, request, pk=None):
        """
        Fornisce lo stato dettagliato di tutti i dispositivi dell'impianto
        """
        try:
            plant = self.get_object()
            devices = DeviceConfiguration.objects.filter(plant=plant)

            device_statuses = []
            for device in devices:
                try:
                    latest = DeviceMeasurement.objects.filter(device=device).latest(
                        "timestamp"
                    )

                    device_statuses.append(
                        {
                            "device_id": device.id,
                            "name": device.name,
                            "is_online": latest.timestamp
                            > timezone.now() - timedelta(minutes=5),
                            "last_seen": latest.timestamp,
                            "current_power": latest.power,
                            "status": "active" if latest.power > 0 else "idle",
                        }
                    )
                except DeviceMeasurement.DoesNotExist:
                    device_statuses.append(
                        {
                            "device_id": device.id,
                            "name": device.name,
                            "is_online": False,
                            "last_seen": None,
                            "current_power": 0,
                            "status": "offline",
                        }
                    )

            return Response(device_statuses)

        except Exception as e:
            logger.error(f"Error getting device status for plant {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _calculate_health_status(self, stats):
        """
        Calcola lo stato di salute dell'impianto basato su varie metriche
        """
        if stats["active_devices"] == 0:
            return "offline"
        if stats["active_devices"] < stats["total_devices"]:
            return "degraded"
        if stats["total_power"] > 0:
            return "healthy"
        return "idle"
