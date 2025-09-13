# energy/mqtt/event_bus.py
# import asyncio
import logging
import threading
from collections import defaultdict

# from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from django.utils import timezone

from .message_queue import MessageQueue, QueuedMessage
from .router import MessageContext

logger = logging.getLogger("energy.mqtt.event_bus")


@dataclass
class Event:
    """Evento standardizzato per il sistema event-driven"""

    event_type: str
    topic: str
    payload: Dict[str, Any]
    timestamp: datetime
    context: Optional[MessageContext] = None
    priority: int = 5  # 1=highest, 10=lowest
    retry_count: int = 0
    max_retries: int = 3
    metadata: Optional[Dict[str, Any]] = None
    source: Optional[str] = None


class EventBus:
    """
    Event Bus asincrono per decoupling dei MQTT handlers
    Gestisce routing eventi e processing asincrono
    """

    def __init__(self, max_queue_size: int = 10000):
        self._max_queue_size = max_queue_size
        self._message_queue = MessageQueue(max_size=max_queue_size)
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._running = False
        self._lock = threading.Lock()
        self._stats = {
            "events_processed": 0,
            "events_failed": 0,
            "events_retried": 0,
            "handlers_registered": 0,
        }

        # Thread pool per processing asincrono
        self._worker_threads = []
        self._num_workers = 3

    def start(self) -> None:
        """Avvia l'Event Bus e i worker threads"""
        try:
            with self._lock:
                if self._running:
                    logger.warning("EventBus already running")
                    return

                self._running = True
                logger.info(
                    "Starting EventBus with {} workers".format(self._num_workers)
                )

                # Avvia worker threads
                for i in range(self._num_workers):
                    worker = threading.Thread(
                        target=self._worker_loop,
                        name=f"EventBus-Worker-{i}",
                        daemon=True,
                    )
                    worker.start()
                    self._worker_threads.append(worker)

                logger.info("EventBus started successfully")

        except Exception as e:
            logger.error(f"Error starting EventBus: {e}")
            self._running = False
            raise

    def stop(self) -> None:
        """Arresta l'Event Bus e pulisce le risorse"""
        try:
            with self._lock:
                if not self._running:
                    return

                logger.info("Stopping EventBus...")
                self._running = False

                # Attendi che tutti i worker finiscano
                for worker in self._worker_threads:
                    if worker.is_alive():
                        worker.join(timeout=5.0)

                self._worker_threads.clear()

                # Pulisci la coda
                self._message_queue.clear()

                logger.info("EventBus stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping EventBus: {e}")

    def register_handler(
        self, event_type: str, handler: Callable[[Event], bool]
    ) -> None:
        """
        Registra un handler per un tipo di evento
        """
        try:
            with self._lock:
                self._event_handlers[event_type].append(handler)
                self._stats["handlers_registered"] += 1
                logger.debug(f"Registered handler for event type: {event_type}")

        except Exception as e:
            logger.error(f"Error registering handler for {event_type}: {e}")

    def unregister_handler(
        self, event_type: str, handler: Callable[[Event], bool]
    ) -> bool:
        """
        Rimuove un handler per un tipo di evento
        """
        try:
            with self._lock:
                if event_type in self._event_handlers:
                    if handler in self._event_handlers[event_type]:
                        self._event_handlers[event_type].remove(handler)
                        self._stats["handlers_registered"] -= 1
                        logger.debug(
                            f"Unregistered handler for event type: {event_type}"
                        )
                        return True
                return False

        except Exception as e:
            logger.error(f"Error unregistering handler for {event_type}: {e}")
            return False

    def publish_event(self, event: Event) -> bool:
        """
        Pubblica un evento nella coda per processing asincrono
        """
        try:
            if not self._running:
                logger.warning("EventBus not running, cannot publish event")
                return False

            # Verifica se ci sono handler per questo tipo di evento
            if event.event_type not in self._event_handlers:
                logger.debug(
                    f"No handlers registered for event type: {event.event_type}"
                )
                return True  # Non è un errore, semplicemente nessun handler

            # Aggiungi alla coda
            queued_message = QueuedMessage(
                event_type=event.event_type,
                topic=event.topic,
                payload=event.payload,
                timestamp=event.timestamp,
                priority=event.priority,
                retry_count=event.retry_count,
                max_retries=event.max_retries,
                context=event.context,
            )

            success = self._message_queue.enqueue(queued_message)
            if success:
                logger.debug(
                    f"Event published: {event.event_type} for topic: {event.topic}"
                )
            else:
                logger.warning(f"Failed to enqueue event: {event.event_type}")

            return success

        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            return False

    def publish_mqtt_message(
        self,
        topic: str,
        payload: Dict[str, Any],
        context: Optional[MessageContext] = None,
    ) -> bool:
        """
        Pubblica un messaggio MQTT come evento
        """
        try:
            # Determina il tipo di evento basato sul topic
            event_type = self._determine_event_type(topic)

            event = Event(
                event_type=event_type,
                topic=topic,
                payload=payload,
                timestamp=timezone.now(),
                context=context,
                priority=self._get_priority_for_topic(topic),
            )

            return self.publish_event(event)

        except Exception as e:
            logger.error(f"Error publishing MQTT message: {e}")
            return False

    def _worker_loop(self) -> None:
        """Loop principale del worker thread"""
        logger.debug(f"EventBus worker {threading.current_thread().name} started")

        while self._running:
            try:
                # Prendi un messaggio dalla coda (bloccante con timeout)
                message = self._message_queue.dequeue(timeout=1.0)
                if message is None:
                    continue

                # Processa il messaggio
                self._process_message(message)

            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                # Continua il loop anche in caso di errore

    def _process_message(self, message: QueuedMessage) -> None:
        """Processa un singolo messaggio"""
        try:
            event_type = message.event_type

            # Trova gli handler per questo tipo di evento
            handlers = self._event_handlers.get(event_type, [])
            if not handlers:
                logger.debug(f"No handlers for event type: {event_type}")
                return

            # Crea l'evento
            event = Event(
                event_type=event_type,
                topic=message.topic,
                payload=message.payload,
                timestamp=message.timestamp,
                context=message.context,
                priority=message.priority,
                retry_count=message.retry_count,
                max_retries=message.max_retries,
            )

            # Esegui tutti gli handler
            success_count = 0
            for handler in handlers:
                try:
                    if handler(event):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Handler error for {event_type}: {e}")

            # Aggiorna statistiche
            if success_count > 0:
                self._stats["events_processed"] += 1
            else:
                self._stats["events_failed"] += 1

                # Retry logic
                if message.retry_count < message.max_retries:
                    message.retry_count += 1
                    self._message_queue.enqueue(message)
                    self._stats["events_retried"] += 1
                    logger.warning(
                        f"Retrying event {event_type} (attempt {message.retry_count})"
                    )

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self._stats["events_failed"] += 1

    def _determine_event_type(self, topic: str) -> str:
        """Determina il tipo di evento basato sul topic"""
        try:
            if "/status/em:0" in topic:
                return "power_measurement"
            elif "/status/emdata:0" in topic:
                return "energy_measurement"
            elif "/status" in topic:
                return "device_status"
            elif "SolarMQTT" in topic and "/status" in topic:
                return "solar_status"  # SolarMQTT status topics
            elif "SolarMQTT" in topic:
                return "solar_power"  # SolarMQTT power topics
            else:
                return "unknown_message"

        except Exception:
            return "unknown_message"

    def _get_priority_for_topic(self, topic: str) -> int:
        """Determina la priorità basata sul topic"""
        try:
            if "/status/em:0" in topic or "/status/emdata:0" in topic:
                return 1  # Alta priorità per misurazioni
            elif "SolarMQTT" in topic:
                return 2  # Alta priorità per dati solari
            elif "/status" in topic:
                return 3  # Media priorità per status
            else:
                return 5  # Bassa priorità per altri messaggi

        except Exception:
            return 5

    def get_stats(self) -> Dict[str, Any]:
        """Restituisce le statistiche dell'Event Bus"""
        try:
            with self._lock:
                return {
                    **self._stats,
                    "queue_size": self._message_queue.size(),
                    "running": self._running,
                    "active_workers": len(
                        [w for w in self._worker_threads if w.is_alive()]
                    ),
                    "registered_event_types": list(self._event_handlers.keys()),
                }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    def clear_stats(self) -> None:
        """Pulisce le statistiche"""
        try:
            with self._lock:
                self._stats = {
                    "events_processed": 0,
                    "events_failed": 0,
                    "events_retried": 0,
                    "handlers_registered": self._stats["handlers_registered"],
                }

        except Exception as e:
            logger.error(f"Error clearing stats: {e}")


# Singleton instance
_event_bus = None


def get_event_bus() -> EventBus:
    """Restituisce l'istanza singleton dell'Event Bus"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
