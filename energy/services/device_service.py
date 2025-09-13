# energy/services/device_service.py

import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from ..models import DeviceConfiguration
from ..mqtt.router import MessageContext

logger = logging.getLogger("energy.services")


class DeviceService:
    """
    Servizio per la gestione dei dispositivi
    Separa la logica di business dalla gestione MQTT
    """

    def __init__(self):
        self._device_status_cache = {}
        self._cache_timeout = 300  # 5 minuti

    def process_status_message(self, context: MessageContext) -> bool:
        """
        Processa un messaggio di stato del dispositivo
        """
        try:
            # Trova la configurazione del dispositivo
            device_config = self._find_device_config(context)
            if not device_config:
                logger.warning(
                    f"No device config found for status topic: {context.topic}"
                )
                return False

            # Estrai le informazioni di stato
            status_data = self._extract_status_data(context.payload)
            if not status_data:
                return False

            # Aggiorna lo stato del dispositivo
            success = self._update_device_status(device_config, status_data, context)

            if success:
                # Aggiorna last_seen
                self._update_device_last_seen(device_config)

                # Cache dello stato
                self._cache_device_status(device_config, status_data)

            return success

        except Exception as e:
            logger.error(f"Error processing status message: {e}")
            return False

    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera lo stato di un dispositivo
        """
        try:
            # Prima controlla la cache
            cached_status = self._device_status_cache.get(device_id)
            if cached_status:
                return cached_status

            # Se non in cache, recupera dal database
            device_config = (
                DeviceConfiguration.objects.select_related("plant")
                .filter(device_id=device_id, is_active=True)
                .first()
            )

            if not device_config:
                return None

            # Determina lo stato basato su last_seen
            status = self._determine_device_status(device_config)

            # Cache il risultato
            self._device_status_cache[device_id] = status

            return status

        except Exception as e:
            logger.error(f"Error getting device status: {e}")
            return None

    def get_all_device_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Recupera lo stato di tutti i dispositivi attivi
        """
        try:
            devices = DeviceConfiguration.objects.filter(is_active=True).select_related(
                "plant"
            )
            statuses = {}

            for device in devices:
                status = self._determine_device_status(device)
                statuses[device.device_id] = status

            return statuses

        except Exception as e:
            logger.error(f"Error getting all device statuses: {e}")
            return {}

    def _find_device_config(
        self, context: MessageContext
    ) -> Optional[DeviceConfiguration]:
        """
        Trova la configurazione del dispositivo basata sul contesto del messaggio
        """
        try:
            if not context.device_id:
                return None

            return (
                DeviceConfiguration.objects.select_related("plant")
                .filter(device_id=context.device_id, is_active=True)
                .first()
            )

        except Exception as e:
            logger.error(f"Error finding device config: {e}")
            return None

    def _extract_status_data(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Estrae i dati di stato dal payload
        """
        try:
            # Estrai informazioni di stato comuni
            status_data = {
                "online": payload.get("online", True),
                "timestamp": timezone.now(),
                "raw_data": payload,
            }

            # Estrai informazioni specifiche se disponibili
            if "status" in payload:
                status_data["status"] = payload["status"]

            if "error" in payload:
                status_data["error"] = payload["error"]

            if "uptime" in payload:
                status_data["uptime"] = payload["uptime"]

            return status_data

        except Exception as e:
            logger.error(f"Error extracting status data: {e}")
            return None

    def _update_device_status(
        self,
        device_config: DeviceConfiguration,
        status_data: Dict[str, Any],
        context: MessageContext,
    ) -> bool:
        """
        Aggiorna lo stato del dispositivo nel database
        """
        try:
            with transaction.atomic():
                # Aggiorna i campi di stato se disponibili
                update_fields = ["last_seen"]

                # Se il dispositivo ha un campo di stato, aggiornalo
                if hasattr(device_config, "status"):
                    device_config.status = status_data.get("status", "UNKNOWN")
                    update_fields.append("status")

                # Se il dispositivo ha un campo di errore, aggiornalo
                if hasattr(device_config, "error_message"):
                    device_config.error_message = status_data.get("error", "")
                    update_fields.append("error_message")

                device_config.save(update_fields=update_fields)

                logger.debug(
                    f"Device status updated - Device: {device_config.device_id} "
                    f"Status: {status_data.get('status', 'UNKNOWN')}"
                )

                return True

        except Exception as e:
            logger.error(f"Error updating device status: {e}")
            return False

    def _determine_device_status(
        self, device_config: DeviceConfiguration
    ) -> Dict[str, Any]:
        """
        Determina lo stato del dispositivo basato su last_seen
        """
        try:
            now = timezone.now()
            last_seen = device_config.last_seen

            if not last_seen:
                return {
                    "device_id": device_config.device_id,
                    "status": "UNKNOWN",
                    "online": False,
                    "last_seen": None,
                    "uptime": None,
                }

            # Calcola il tempo dall'ultimo contatto
            time_diff = now - last_seen

            # Determina se il dispositivo è online (ultimo contatto < 5 minuti)
            is_online = time_diff < timedelta(minutes=5)

            # Determina lo stato
            if is_online:
                status = "ONLINE"
            elif time_diff < timedelta(minutes=30):
                status = "WARNING"
            else:
                status = "OFFLINE"

            return {
                "device_id": device_config.device_id,
                "status": status,
                "online": is_online,
                "last_seen": last_seen,
                "uptime": time_diff.total_seconds(),
                "plant_name": (
                    device_config.plant.name if device_config.plant else "Unknown"
                ),
                "device_type": device_config.device_type,
            }

        except Exception as e:
            logger.error(f"Error determining device status: {e}")
            return {
                "device_id": device_config.device_id,
                "status": "ERROR",
                "online": False,
                "last_seen": None,
                "uptime": None,
                "error": str(e),
            }

    def _update_device_last_seen(self, device_config: DeviceConfiguration) -> None:
        """
        Aggiorna il timestamp dell'ultimo contatto del dispositivo
        """
        try:
            device_config.last_seen = timezone.now()
            device_config.save(update_fields=["last_seen"])
        except Exception as e:
            logger.error(f"Error updating device last_seen: {e}")

    def _cache_device_status(
        self, device_config: DeviceConfiguration, status_data: Dict[str, Any]
    ) -> None:
        """
        Cache dello stato del dispositivo
        """
        try:
            cache_key = f"device_status_{device_config.device_id}"
            cache.set(cache_key, status_data, timeout=self._cache_timeout)

            # Aggiorna anche la cache interna
            self._device_status_cache[device_config.device_id] = status_data

        except Exception as e:
            logger.error(f"Error caching device status: {e}")

    def clear_device_cache(self, device_id: Optional[str] = None) -> None:
        """
        Pulisce la cache degli stati dei dispositivi
        """
        try:
            if device_id:
                # Pulisce la cache per un dispositivo specifico
                cache_key = f"device_status_{device_id}"
                cache.delete(cache_key)
                self._device_status_cache.pop(device_id, None)
            else:
                # Pulisce tutta la cache
                self._device_status_cache.clear()

        except Exception as e:
            logger.error(f"Error clearing device cache: {e}")

    def get_device_stats(self) -> Dict[str, Any]:
        """
        Restituisce le statistiche dei dispositivi
        """
        try:
            total_devices = DeviceConfiguration.objects.filter(is_active=True).count()
            online_devices = 0
            offline_devices = 0
            warning_devices = 0

            now = timezone.now()
            for device in DeviceConfiguration.objects.filter(is_active=True):
                if device.last_seen:
                    time_diff = now - device.last_seen
                    if time_diff < timedelta(minutes=5):
                        online_devices += 1
                    elif time_diff < timedelta(minutes=30):
                        warning_devices += 1
                    else:
                        offline_devices += 1
                else:
                    offline_devices += 1

            return {
                "total_devices": total_devices,
                "online_devices": online_devices,
                "warning_devices": warning_devices,
                "offline_devices": offline_devices,
                "cached_statuses": len(self._device_status_cache),
            }

        except Exception as e:
            logger.error(f"Error getting device stats: {e}")
            return {}
