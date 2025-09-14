# energy/mqtt/router.py

import logging
import re
import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from django.utils import timezone

logger = logging.getLogger("energy.mqtt")


@dataclass
class Route:
    """Definisce una route per il routing dei messaggi MQTT"""

    pattern: str
    handler: Callable
    priority: int = 0
    enabled: bool = True
    description: str = ""


@dataclass
class MessageContext:
    """Contesto del messaggio per il routing"""

    topic: str
    payload: Dict[str, Any]
    timestamp: datetime
    qos: int = 0
    retain: bool = False
    device_id: Optional[str] = None
    plant_id: Optional[str] = None
    vendor: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MQTTMessageRouter:
    """
    Router centralizzato per i messaggi MQTT
    Gestisce il routing dei messaggi basato su pattern di topic
    """

    def __init__(self):
        self._routes: List[Route] = []
        self._lock = threading.Lock()
        self._message_stats = defaultdict(int)
        self._error_stats = defaultdict(int)
        self._last_message_time = None

        # Registra le route predefinite
        self._register_default_routes()

    def _register_default_routes(self):
        """Registra le route predefinite per i messaggi MQTT"""
        # Route per messaggi di potenza
        self.register_route(
            pattern="cercollettiva/+/+/status/em:0",
            handler=self._handle_power_message,
            priority=10,
            description="Power measurements from CerCollettiva devices",
        )

        self.register_route(
            pattern="VePro/+/+/status/em:0",
            handler=self._handle_power_message,
            priority=10,
            description="Power measurements from VePro devices",
        )

        # Route per messaggi di energia
        self.register_route(
            pattern="cercollettiva/+/+/status/emdata:0",
            handler=self._handle_energy_message,
            priority=10,
            description="Energy measurements from CerCollettiva devices",
        )

        self.register_route(
            pattern="VePro/+/+/status/emdata:0",
            handler=self._handle_energy_message,
            priority=10,
            description="Energy measurements from VePro devices",
        )

        # Route per messaggi di stato
        self.register_route(
            pattern="+/+/status",
            handler=self._handle_status_message,
            priority=5,
            description="Device status messages",
        )

        # Route di fallback per messaggi non riconosciuti
        self.register_route(
            pattern="+",
            handler=self._handle_unknown_message,
            priority=1,
            description="Fallback for unknown messages",
        )

    def register_route(
        self, pattern: str, handler: Callable, priority: int = 0, description: str = ""
    ) -> None:
        """Registra una nuova route per il routing dei messaggi"""
        with self._lock:
            route = Route(
                pattern=pattern,
                handler=handler,
                priority=priority,
                description=description,
            )

            # Inserisce la route in ordine di priorità (priorità più alta prima)
            inserted = False
            for i, existing_route in enumerate(self._routes):
                if priority > existing_route.priority:
                    self._routes.insert(i, route)
                    inserted = True
                    break

            if not inserted:
                self._routes.append(route)

            logger.info(f"Registered MQTT route: {pattern} (priority: {priority})")

    def unregister_route(self, pattern: str) -> bool:
        """Rimuove una route registrata"""
        with self._lock:
            for i, route in enumerate(self._routes):
                if route.pattern == pattern:
                    del self._routes[i]
                    logger.info(f"Unregistered MQTT route: {pattern}")
                    return True
            return False

    def route_message(
        self, topic: str, payload: Any, qos: int = 0, retain: bool = False
    ) -> bool:
        """
        Instrada un messaggio MQTT alle route appropriate
        Restituisce True se il messaggio è stato gestito con successo
        """
        try:
            # Crea il contesto del messaggio
            context = self._create_message_context(topic, payload, qos, retain)

            # Trova le route che corrispondono al topic
            matching_routes = self._find_matching_routes(topic)

            if not matching_routes:
                logger.warning(f"No routes found for topic: {topic}")
                self._error_stats["no_route"] += 1
                return False

            # Esegui le route in ordine di priorità
            success = False
            for route in matching_routes:
                if not route.enabled:
                    continue

                try:
                    result = route.handler(context)
                    if result:
                        success = True
                        self._message_stats[route.pattern] += 1
                        logger.debug(f"Message routed successfully via {route.pattern}")
                        break  # Prima route che gestisce il messaggio vince

                except Exception as e:
                    logger.error(f"Error in route handler {route.pattern}: {e}")
                    self._error_stats[route.pattern] += 1

            # Aggiorna statistiche
            self._last_message_time = timezone.now()
            if success:
                self._message_stats["total_processed"] += 1
            else:
                self._message_stats["total_failed"] += 1
                self._error_stats["handler_failed"] += 1

            return success

        except Exception as e:
            logger.error(f"Error routing message: {e}")
            self._error_stats["routing_error"] += 1
            return False

    def _create_message_context(
        self, topic: str, payload: Any, qos: int, retain: bool
    ) -> MessageContext:
        """Crea il contesto del messaggio con informazioni estratte"""
        # Parse del payload
        parsed_payload = self._parse_payload(payload)

        # Estrai informazioni dal topic
        device_id, plant_id, vendor = self._extract_topic_info(topic)

        return MessageContext(
            topic=topic,
            payload=parsed_payload,
            timestamp=timezone.now(),
            qos=qos,
            retain=retain,
            device_id=device_id,
            plant_id=plant_id,
            vendor=vendor,
        )

    def _parse_payload(self, payload: Any) -> Dict[str, Any]:
        """Parse del payload in modo sicuro"""
        try:
            if isinstance(payload, bytes):
                import json

                return json.loads(payload.decode("utf-8"))
            elif isinstance(payload, str):
                import json

                return json.loads(payload)
            elif isinstance(payload, dict):
                return payload
            else:
                return {}
        except Exception as e:
            logger.error(f"Error parsing payload: {e}")
            return {}

    def _extract_topic_info(
        self, topic: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Estrae informazioni dal topic (device_id, plant_id, vendor)"""
        try:
            parts = topic.split("/")
            vendor = parts[0] if len(parts) > 0 else None

            # Pattern per CerCollettiva: cercollettiva/{device_id}/status/...
            if vendor == "cercollettiva" and len(parts) >= 2:
                device_id = parts[1]
                return device_id, None, vendor

            # Pattern per VePro: VePro/{pod_code}/{device_id}/status/...
            elif vendor == "VePro" and len(parts) >= 3:
                pod_code = parts[1]
                device_id = parts[2]
                return device_id, pod_code, vendor

            return None, None, vendor

        except Exception as e:
            logger.error(f"Error extracting topic info: {e}")
            return None, None, None

    def _find_matching_routes(self, topic: str) -> List[Route]:
        """Trova le route che corrispondono al topic"""
        matching_routes = []

        for route in self._routes:
            if self._topic_matches_pattern(topic, route.pattern):
                matching_routes.append(route)

        return matching_routes

    def _topic_matches_pattern(self, topic: str, pattern: str) -> bool:
        """Verifica se un topic corrisponde a un pattern MQTT"""
        try:
            # Converti il pattern MQTT in regex
            regex_pattern = pattern.replace("+", "[^/]+").replace("#", ".*")
            return bool(re.match(f"^{regex_pattern}$", topic))
        except Exception as e:
            logger.error(f"Error matching topic pattern: {e}")
            return False

    def _handle_power_message(self, context: MessageContext) -> bool:
        """Handler per messaggi di potenza"""
        try:
            # Use the handler registry to find the appropriate handler
            from .handlers.interface import get_handler_registry

            registry = get_handler_registry()
            handler = registry.find_handler(context)

            if handler:
                return handler.handle(context)
            else:
                logger.warning(f"No handler found for power message: {context.topic}")
                return False
        except Exception as e:
            logger.error(f"Error handling power message: {e}")
            return False

    def _handle_energy_message(self, context: MessageContext) -> bool:
        """Handler per messaggi di energia"""
        try:
            # Use the handler registry to find the appropriate handler
            from .handlers.interface import get_handler_registry

            registry = get_handler_registry()
            handler = registry.find_handler(context)

            if handler:
                return handler.handle(context)
            else:
                logger.warning(f"No handler found for energy message: {context.topic}")
                return False
        except Exception as e:
            logger.error(f"Error handling energy message: {e}")
            return False

    def _handle_status_message(self, context: MessageContext) -> bool:
        """Handler per messaggi di stato"""
        try:
            # Use the handler registry to find the appropriate handler
            from .handlers.interface import get_handler_registry

            registry = get_handler_registry()
            handler = registry.find_handler(context)

            if handler:
                return handler.handle(context)
            else:
                logger.warning(f"No handler found for status message: {context.topic}")
                return False
        except Exception as e:
            logger.error(f"Error handling status message: {e}")
            return False

    def _handle_unknown_message(self, context: MessageContext) -> bool:
        """Handler di fallback per messaggi non riconosciuti"""
        logger.warning(f"Unknown message received on topic: {context.topic}")
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Restituisce le statistiche del router"""
        with self._lock:
            return {
                "total_routes": len(self._routes),
                "message_stats": dict(self._message_stats),
                "error_stats": dict(self._error_stats),
                "last_message_time": self._last_message_time,
                "routes": [
                    {
                        "pattern": route.pattern,
                        "priority": route.priority,
                        "enabled": route.enabled,
                        "description": route.description,
                    }
                    for route in self._routes
                ],
            }

    def enable_route(self, pattern: str) -> bool:
        """Abilita una route"""
        with self._lock:
            for route in self._routes:
                if route.pattern == pattern:
                    route.enabled = True
                    logger.info(f"Enabled route: {pattern}")
                    return True
            return False

    def disable_route(self, pattern: str) -> bool:
        """Disabilita una route"""
        with self._lock:
            for route in self._routes:
                if route.pattern == pattern:
                    route.enabled = False
                    logger.info(f"Disabled route: {pattern}")
                    return True
            return False

    def clear_stats(self) -> None:
        """Pulisce le statistiche"""
        with self._lock:
            self._message_stats.clear()
            self._error_stats.clear()
            self._last_message_time = None
            logger.info("Router statistics cleared")


# Singleton instance
_router = None


def get_mqtt_router() -> MQTTMessageRouter:
    """Ottiene l'istanza singleton del router MQTT"""
    global _router
    if _router is None:
        _router = MQTTMessageRouter()
    return _router
