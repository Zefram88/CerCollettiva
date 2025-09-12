# energy/mqtt/handlers/interface.py

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..router import MessageContext

logger = logging.getLogger("energy.mqtt")


class MQTTHandlerInterface(ABC):
    """
    Interfaccia standardizzata per gli handler MQTT
    Definisce il contratto che tutti gli handler devono implementare
    """

    def __init__(self):
        self._handler_name = self.__class__.__name__
        self._message_count = 0
        self._error_count = 0
        self._last_message_time = None

    @abstractmethod
    def can_handle(self, context: MessageContext) -> bool:
        """
        Determina se questo handler può gestire il messaggio
        """
        pass

    @abstractmethod
    def handle(self, context: MessageContext) -> bool:
        """
        Gestisce il messaggio MQTT
        Restituisce True se il messaggio è stato gestito con successo
        """
        pass

    def get_handler_name(self) -> str:
        """Restituisce il nome dell'handler"""
        return self._handler_name

    def get_stats(self) -> Dict[str, Any]:
        """Restituisce le statistiche dell'handler"""
        return {
            "handler_name": self._handler_name,
            "message_count": self._message_count,
            "error_count": self._error_count,
            "last_message_time": self._last_message_time,
            "success_rate": self._calculate_success_rate(),
        }

    def _calculate_success_rate(self) -> float:
        """Calcola la percentuale di successo"""
        total = self._message_count + self._error_count
        if total == 0:
            return 0.0
        return (self._message_count / total) * 100

    def _increment_message_count(self):
        """Incrementa il contatore dei messaggi"""
        self._message_count += 1

    def _increment_error_count(self):
        """Incrementa il contatore degli errori"""
        self._error_count += 1

    def _update_last_message_time(self):
        """Aggiorna il timestamp dell'ultimo messaggio"""
        from django.utils import timezone

        self._last_message_time = timezone.now()


class PowerMeasurementHandler(MQTTHandlerInterface):
    """
    Handler specializzato per messaggi di misurazione di potenza
    """

    def can_handle(self, context: MessageContext) -> bool:
        """Verifica se il messaggio è una misurazione di potenza"""
        return context.topic.endswith("/em:0")

    def handle(self, context: MessageContext) -> bool:
        """Gestisce una misurazione di potenza"""
        try:
            from ...services.measurement_service import MeasurementService

            service = MeasurementService()
            result = service.process_power_measurement(context)

            if result:
                self._increment_message_count()
            else:
                self._increment_error_count()

            self._update_last_message_time()
            return result

        except Exception as e:
            logger.error(f"Error in PowerMeasurementHandler: {e}")
            self._increment_error_count()
            return False


class EnergyMeasurementHandler(MQTTHandlerInterface):
    """
    Handler specializzato per messaggi di misurazione di energia
    """

    def can_handle(self, context: MessageContext) -> bool:
        """Verifica se il messaggio è una misurazione di energia"""
        return context.topic.endswith("/emdata:0")

    def handle(self, context: MessageContext) -> bool:
        """Gestisce una misurazione di energia"""
        try:
            from ...services.measurement_service import MeasurementService

            service = MeasurementService()
            result = service.process_energy_measurement(context)

            if result:
                self._increment_message_count()
            else:
                self._increment_error_count()

            self._update_last_message_time()
            return result

        except Exception as e:
            logger.error(f"Error in EnergyMeasurementHandler: {e}")
            self._increment_error_count()
            return False


class DeviceStatusHandler(MQTTHandlerInterface):
    """
    Handler specializzato per messaggi di stato del dispositivo
    """

    def can_handle(self, context: MessageContext) -> bool:
        """Verifica se il messaggio è uno stato del dispositivo"""
        return (
            context.topic.endswith("/status")
            and not context.topic.endswith("/em:0")
            and not context.topic.endswith("/emdata:0")
        )

    def handle(self, context: MessageContext) -> bool:
        """Gestisce un messaggio di stato del dispositivo"""
        try:
            from ...services.device_service import DeviceService

            service = DeviceService()
            result = service.process_status_message(context)

            if result:
                self._increment_message_count()
            else:
                self._increment_error_count()

            self._update_last_message_time()
            return result

        except Exception as e:
            logger.error(f"Error in DeviceStatusHandler: {e}")
            self._increment_error_count()
            return False


class HandlerRegistry:
    """
    Registry per la gestione degli handler MQTT
    """

    def __init__(self):
        self._handlers: list[MQTTHandlerInterface] = []
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Registra gli handler predefiniti"""
        self.register_handler(PowerMeasurementHandler())
        self.register_handler(EnergyMeasurementHandler())
        self.register_handler(DeviceStatusHandler())

    def register_handler(self, handler: MQTTHandlerInterface) -> None:
        """Registra un nuovo handler"""
        self._handlers.append(handler)
        logger.info(f"Registered MQTT handler: {handler.get_handler_name()}")

    def unregister_handler(self, handler_name: str) -> bool:
        """Rimuove un handler registrato"""
        for i, handler in enumerate(self._handlers):
            if handler.get_handler_name() == handler_name:
                del self._handlers[i]
                logger.info(f"Unregistered MQTT handler: {handler_name}")
                return True
        return False

    def find_handler(self, context: MessageContext) -> Optional[MQTTHandlerInterface]:
        """Trova l'handler appropriato per il messaggio"""
        for handler in self._handlers:
            if handler.can_handle(context):
                return handler
        return None

    def get_all_handlers(self) -> list[MQTTHandlerInterface]:
        """Restituisce tutti gli handler registrati"""
        return self._handlers.copy()

    def get_handler_stats(self) -> Dict[str, Any]:
        """Restituisce le statistiche di tutti gli handler"""
        stats = {}
        for handler in self._handlers:
            stats[handler.get_handler_name()] = handler.get_stats()
        return stats


# Singleton instance
_handler_registry = None


def get_handler_registry() -> HandlerRegistry:
    """Ottiene l'istanza singleton del registry degli handler"""
    global _handler_registry
    if _handler_registry is None:
        _handler_registry = HandlerRegistry()
    return _handler_registry
