# energy/mqtt/message_queue.py
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from .router import MessageContext

logger = logging.getLogger("energy.mqtt.message_queue")


@dataclass
class QueuedMessage:
    """Messaggio in coda per processing asincrono"""

    event_type: str
    topic: str
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int = 5
    retry_count: int = 0
    max_retries: int = 3
    context: Optional[MessageContext] = None

    def __lt__(self, other):
        """Comparazione per priority queue (min-heap)"""
        return self.priority < other.priority


class MessageQueue:
    """
    Coda thread-safe per messaggi MQTT con supporto priorità
    Implementa pattern producer-consumer con backpressure
    """

    def __init__(self, max_size: int = 10000):
        self._max_size = max_size
        self._queue = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

        # Statistiche
        self._stats = {
            "messages_enqueued": 0,
            "messages_dequeued": 0,
            "messages_dropped": 0,
            "queue_full_events": 0,
        }

    def enqueue(self, message: QueuedMessage, timeout: Optional[float] = None) -> bool:
        """
        Aggiunge un messaggio alla coda
        Returns True se successo, False se timeout o coda piena
        """
        try:
            with self._not_full:
                # Attendi spazio disponibile
                if timeout is None:
                    while len(self._queue) >= self._max_size:
                        self._not_full.wait()
                else:
                    start_time = time.time()
                    while len(self._queue) >= self._max_size:
                        remaining = timeout - (time.time() - start_time)
                        if remaining <= 0:
                            self._stats["messages_dropped"] += 1
                            self._stats["queue_full_events"] += 1
                            logger.warning(
                                f"Queue full, dropping message: {message.event_type}"
                            )
                            return False
                        self._not_full.wait(remaining)

                # Aggiungi il messaggio
                self._queue.append(message)
                self._stats["messages_enqueued"] += 1

                # Notifica i consumer
                self._not_empty.notify()

                logger.debug(
                    f"Message enqueued: {message.event_type} "
                    f"(queue size: {len(self._queue)})"
                )
                return True

        except Exception as e:
            logger.error(f"Error enqueuing message: {e}")
            return False

    def dequeue(self, timeout: Optional[float] = None) -> Optional[QueuedMessage]:
        """
        Rimuove e restituisce un messaggio dalla coda
        Returns None se timeout o coda vuota
        """
        try:
            with self._not_empty:
                # Attendi un messaggio
                if timeout is None:
                    while len(self._queue) == 0:
                        self._not_empty.wait()
                else:
                    start_time = time.time()
                    while len(self._queue) == 0:
                        remaining = timeout - (time.time() - start_time)
                        if remaining <= 0:
                            return None
                        self._not_empty.wait(remaining)

                # Rimuovi il messaggio
                message = self._queue.popleft()
                self._stats["messages_dequeued"] += 1

                # Notifica i producer
                self._not_full.notify()

                logger.debug(
                    f"Message dequeued: {message.event_type} "
                    f"(queue size: {len(self._queue)})"
                )
                return message

        except Exception as e:
            logger.error(f"Error dequeuing message: {e}")
            return None

    def peek(self) -> Optional[QueuedMessage]:
        """
        Guarda il prossimo messaggio senza rimuoverlo
        """
        try:
            with self._lock:
                return self._queue[0] if self._queue else None

        except Exception as e:
            logger.error(f"Error peeking message: {e}")
            return None

    def size(self) -> int:
        """Restituisce la dimensione corrente della coda"""
        try:
            with self._lock:
                return len(self._queue)

        except Exception as e:
            logger.error(f"Error getting queue size: {e}")
            return 0

    def is_empty(self) -> bool:
        """Verifica se la coda è vuota"""
        try:
            with self._lock:
                return len(self._queue) == 0

        except Exception as e:
            logger.error(f"Error checking if queue is empty: {e}")
            return True

    def is_full(self) -> bool:
        """Verifica se la coda è piena"""
        try:
            with self._lock:
                return len(self._queue) >= self._max_size

        except Exception as e:
            logger.error(f"Error checking if queue is full: {e}")
            return False

    def clear(self) -> None:
        """Pulisce la coda"""
        try:
            with self._lock:
                self._queue.clear()
                self._not_full.notify_all()
                logger.info("Message queue cleared")

        except Exception as e:
            logger.error(f"Error clearing queue: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Restituisce le statistiche della coda"""
        try:
            with self._lock:
                return {
                    **self._stats,
                    "current_size": len(self._queue),
                    "max_size": self._max_size,
                    "utilization": (
                        len(self._queue) / self._max_size if self._max_size > 0 else 0
                    ),
                }

        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {}

    def clear_stats(self) -> None:
        """Pulisce le statistiche"""
        try:
            with self._lock:
                self._stats = {
                    "messages_enqueued": 0,
                    "messages_dequeued": 0,
                    "messages_dropped": 0,
                    "queue_full_events": 0,
                }

        except Exception as e:
            logger.error(f"Error clearing queue stats: {e}")

    def get_messages_by_type(self, event_type: str) -> list[QueuedMessage]:
        """
        Restituisce tutti i messaggi di un tipo specifico (per debugging)
        """
        try:
            with self._lock:
                return [msg for msg in self._queue if msg.event_type == event_type]

        except Exception as e:
            logger.error(f"Error getting messages by type: {e}")
            return []

    def remove_messages_by_type(self, event_type: str) -> int:
        """
        Rimuove tutti i messaggi di un tipo specifico
        Returns il numero di messaggi rimossi
        """
        try:
            with self._lock:
                initial_size = len(self._queue)
                self._queue = deque(
                    [msg for msg in self._queue if msg.event_type != event_type],
                    maxlen=self._max_size,
                )
                removed_count = initial_size - len(self._queue)

                if removed_count > 0:
                    self._not_full.notify_all()
                    logger.info(
                        f"Removed {removed_count} messages of type: {event_type}"
                    )

                return removed_count

        except Exception as e:
            logger.error(f"Error removing messages by type: {e}")
            return 0
