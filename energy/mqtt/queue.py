# energy/mqtt/queue.py

import logging
import threading
import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from collections import deque
from enum import Enum

logger = logging.getLogger('energy.mqtt')

class MessageStatus(Enum):
    """Stati possibili di un messaggio nella coda"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    DEAD_LETTER = "dead_letter"

@dataclass
class QueuedMessage:
    """Messaggio in coda con metadati"""
    id: str
    topic: str
    payload: Dict[str, Any]
    qos: int
    retain: bool
    timestamp: datetime
    status: MessageStatus
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    processing_started: Optional[datetime] = None
    processing_completed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il messaggio in dizionario per la serializzazione"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['processing_started'] = self.processing_started.isoformat() if self.processing_started else None
        data['processing_completed'] = self.processing_completed.isoformat() if self.processing_completed else None
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueuedMessage':
        """Crea un messaggio da dizionario"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['processing_started'] = datetime.fromisoformat(data['processing_started']) if data['processing_started'] else None
        data['processing_completed'] = datetime.fromisoformat(data['processing_completed']) if data['processing_completed'] else None
        data['status'] = MessageStatus(data['status'])
        return cls(**data)

class MessageQueue:
    """
    Coda di messaggi MQTT con supporto per retry e dead letter queue
    """
    
    def __init__(self, max_size: int = 10000, retry_delay: int = 5):
        self._max_size = max_size
        self._retry_delay = retry_delay
        self._queue = deque(maxlen=max_size)
        self._dead_letter_queue = deque(maxlen=1000)
        self._processing_queue = deque()
        self._lock = threading.Lock()
        self._message_counter = 0
        self._stats = {
            'total_messages': 0,
            'processed_messages': 0,
            'failed_messages': 0,
            'retry_messages': 0,
            'dead_letter_messages': 0
        }
        
        # Avvia il thread di processing
        self._processing_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._processing_thread.start()
        
        # Avvia il thread di retry
        self._retry_thread = threading.Thread(target=self._process_retries, daemon=True)
        self._retry_thread.start()
    
    def enqueue(self, topic: str, payload: Dict[str, Any], qos: int = 0, 
                retain: bool = False) -> str:
        """
        Aggiunge un messaggio alla coda
        Restituisce l'ID del messaggio
        """
        try:
            with self._lock:
                if len(self._queue) >= self._max_size:
                    logger.warning("Message queue is full, dropping oldest message")
                    self._queue.popleft()
                
                message_id = f"msg_{self._message_counter}_{int(time.time())}"
                self._message_counter += 1
                
                message = QueuedMessage(
                    id=message_id,
                    topic=topic,
                    payload=payload,
                    qos=qos,
                    retain=retain,
                    timestamp=timezone.now(),
                    status=MessageStatus.PENDING
                )
                
                self._queue.append(message)
                self._stats['total_messages'] += 1
                
                logger.debug(f"Message enqueued: {message_id} on topic: {topic}")
                return message_id
                
        except Exception as e:
            logger.error(f"Error enqueuing message: {e}")
            raise
    
    def dequeue(self) -> Optional[QueuedMessage]:
        """
        Rimuove e restituisce il prossimo messaggio dalla coda
        """
        try:
            with self._lock:
                if not self._queue:
                    return None
                
                message = self._queue.popleft()
                message.status = MessageStatus.PROCESSING
                message.processing_started = timezone.now()
                self._processing_queue.append(message)
                
                return message
                
        except Exception as e:
            logger.error(f"Error dequeuing message: {e}")
            return None
    
    def mark_completed(self, message_id: str) -> bool:
        """
        Marca un messaggio come completato
        """
        try:
            with self._lock:
                message = self._find_message_in_processing(message_id)
                if message:
                    message.status = MessageStatus.COMPLETED
                    message.processing_completed = timezone.now()
                    self._remove_from_processing(message)
                    self._stats['processed_messages'] += 1
                    logger.debug(f"Message completed: {message_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error marking message as completed: {e}")
            return False
    
    def mark_failed(self, message_id: str, error_message: str) -> bool:
        """
        Marca un messaggio come fallito e decide se ritentare
        """
        try:
            with self._lock:
                message = self._find_message_in_processing(message_id)
                if not message:
                    return False
                
                message.error_message = error_message
                message.retry_count += 1
                
                if message.retry_count < message.max_retries:
                    # Ritenta il messaggio
                    message.status = MessageStatus.RETRY
                    message.processing_started = None
                    self._remove_from_processing(message)
                    self._queue.append(message)
                    self._stats['retry_messages'] += 1
                    logger.warning(f"Message failed, will retry: {message_id} (attempt {message.retry_count})")
                else:
                    # Messaggio morto, sposta nella dead letter queue
                    message.status = MessageStatus.DEAD_LETTER
                    message.processing_completed = timezone.now()
                    self._remove_from_processing(message)
                    self._dead_letter_queue.append(message)
                    self._stats['failed_messages'] += 1
                    self._stats['dead_letter_messages'] += 1
                    logger.error(f"Message failed permanently, moved to dead letter queue: {message_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error marking message as failed: {e}")
            return False
    
    def _find_message_in_processing(self, message_id: str) -> Optional[QueuedMessage]:
        """Trova un messaggio nella coda di processing"""
        for message in self._processing_queue:
            if message.id == message_id:
                return message
        return None
    
    def _remove_from_processing(self, message: QueuedMessage) -> None:
        """Rimuove un messaggio dalla coda di processing"""
        try:
            self._processing_queue.remove(message)
        except ValueError:
            pass  # Messaggio non trovato
    
    def _process_queue(self) -> None:
        """
        Thread principale per il processing dei messaggi
        """
        while True:
            try:
                message = self.dequeue()
                if message:
                    self._process_message(message)
                else:
                    time.sleep(0.1)  # Pausa breve se la coda è vuota
                    
            except Exception as e:
                logger.error(f"Error in message processing thread: {e}")
                time.sleep(1)
    
    def _process_message(self, message: QueuedMessage) -> None:
        """
        Processa un singolo messaggio
        """
        try:
            # Usa il router per processare il messaggio
            from .router import get_mqtt_router
            router = get_mqtt_router()
            
            # Crea il contesto del messaggio
            from .router import MessageContext
            context = MessageContext(
                topic=message.topic,
                payload=message.payload,
                timestamp=message.timestamp,
                qos=message.qos,
                retain=message.retain
            )
            
            # Processa il messaggio
            success = router.route_message(message.topic, message.payload, message.qos, message.retain)
            
            if success:
                self.mark_completed(message.id)
            else:
                self.mark_failed(message.id, "Router processing failed")
                
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            self.mark_failed(message.id, str(e))
    
    def _process_retries(self) -> None:
        """
        Thread per gestire i retry dei messaggi
        """
        while True:
            try:
                time.sleep(self._retry_delay)
                
                with self._lock:
                    # Controlla se ci sono messaggi in retry
                    retry_messages = [msg for msg in self._queue if msg.status == MessageStatus.RETRY]
                    
                    for message in retry_messages:
                        # Verifica se è passato abbastanza tempo per il retry
                        if message.processing_started:
                            time_since_failure = timezone.now() - message.processing_started
                            if time_since_failure.total_seconds() >= self._retry_delay:
                                message.status = MessageStatus.PENDING
                                message.processing_started = None
                                logger.info(f"Retrying message: {message.id}")
                
            except Exception as e:
                logger.error(f"Error in retry processing thread: {e}")
                time.sleep(1)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Restituisce le statistiche della coda
        """
        with self._lock:
            return {
                'queue_size': len(self._queue),
                'processing_size': len(self._processing_queue),
                'dead_letter_size': len(self._dead_letter_queue),
                'stats': self._stats.copy()
            }
    
    def get_dead_letter_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Restituisce i messaggi nella dead letter queue
        """
        with self._lock:
            messages = list(self._dead_letter_queue)[-limit:]
            return [msg.to_dict() for msg in messages]
    
    def clear_dead_letter_queue(self) -> int:
        """
        Pulisce la dead letter queue
        Restituisce il numero di messaggi rimossi
        """
        with self._lock:
            count = len(self._dead_letter_queue)
            self._dead_letter_queue.clear()
            logger.info(f"Cleared {count} messages from dead letter queue")
            return count
    
    def requeue_dead_letter_message(self, message_id: str) -> bool:
        """
        Rimette in coda un messaggio dalla dead letter queue
        """
        try:
            with self._lock:
                for message in self._dead_letter_queue:
                    if message.id == message_id:
                        message.status = MessageStatus.PENDING
                        message.retry_count = 0
                        message.error_message = None
                        message.processing_started = None
                        message.processing_completed = None
                        
                        self._dead_letter_queue.remove(message)
                        self._queue.append(message)
                        
                        logger.info(f"Requeued dead letter message: {message_id}")
                        return True
                return False
                
        except Exception as e:
            logger.error(f"Error requeuing dead letter message: {e}")
            return False

# Singleton instance
_message_queue = None

def get_message_queue() -> MessageQueue:
    """Ottiene l'istanza singleton della coda di messaggi"""
    global _message_queue
    if _message_queue is None:
        _message_queue = MessageQueue()
    return _message_queue
