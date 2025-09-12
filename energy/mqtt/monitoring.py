# energy/mqtt/monitoring.py

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger("energy.mqtt")


class HealthStatus(Enum):
    """Stati di salute del sistema MQTT"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Metrica di salute del sistema"""

    name: str
    value: float
    unit: str
    status: HealthStatus
    timestamp: datetime
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    description: str = ""


@dataclass
class SystemHealth:
    """Stato di salute generale del sistema"""

    overall_status: HealthStatus
    timestamp: datetime
    metrics: List[HealthMetric]
    uptime: float
    message_rate: float
    error_rate: float


class MQTTHealthMonitor:
    """
    Monitor per la salute del sistema MQTT
    """

    def __init__(self):
        self._start_time = timezone.now()
        self._last_message_time = None
        self._message_count = 0
        self._error_count = 0
        self._connection_count = 0
        self._disconnection_count = 0
        self._lock = threading.Lock()

        # Soglie per gli stati di salute
        self._thresholds = {
            "message_rate_warning": 0.1,  # Messaggi al secondo
            "message_rate_critical": 0.01,
            "error_rate_warning": 0.05,  # 5% di errori
            "error_rate_critical": 0.1,  # 10% di errori
            "uptime_warning": 3600,  # 1 ora
            "uptime_critical": 1800,  # 30 minuti
            "connection_failures_warning": 3,
            "connection_failures_critical": 5,
        }

        # Avvia il thread di monitoring
        self._monitoring_thread = threading.Thread(
            target=self._monitor_loop, daemon=True
        )
        self._monitoring_thread.start()

    def record_message(self) -> None:
        """Registra un messaggio ricevuto"""
        with self._lock:
            self._message_count += 1
            self._last_message_time = timezone.now()

    def record_error(self) -> None:
        """Registra un errore"""
        with self._lock:
            self._error_count += 1

    def record_connection(self) -> None:
        """Registra una connessione"""
        with self._lock:
            self._connection_count += 1

    def record_disconnection(self) -> None:
        """Registra una disconnessione"""
        with self._lock:
            self._disconnection_count += 1

    def get_system_health(self) -> SystemHealth:
        """
        Restituisce lo stato di salute generale del sistema
        """
        try:
            with self._lock:
                now = timezone.now()
                uptime = (now - self._start_time).total_seconds()

                # Calcola le metriche
                metrics = self._calculate_metrics(now, uptime)

                # Determina lo stato generale
                overall_status = self._determine_overall_status(metrics)

                # Calcola i tassi
                message_rate = self._calculate_message_rate(now)
                error_rate = self._calculate_error_rate()

                return SystemHealth(
                    overall_status=overall_status,
                    timestamp=now,
                    metrics=metrics,
                    uptime=uptime,
                    message_rate=message_rate,
                    error_rate=error_rate,
                )

        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return self._create_error_health_status()

    def _calculate_metrics(self, now: datetime, uptime: float) -> List[HealthMetric]:
        """Calcola le metriche di salute"""
        metrics = []

        # Metrica del tasso di messaggi
        message_rate = self._calculate_message_rate(now)
        metrics.append(
            HealthMetric(
                name="message_rate",
                value=message_rate,
                unit="messages/sec",
                status=self._get_metric_status(message_rate, "message_rate"),
                timestamp=now,
                threshold_warning=self._thresholds["message_rate_warning"],
                threshold_critical=self._thresholds["message_rate_critical"],
                description="Rate of incoming MQTT messages",
            )
        )

        # Metrica del tasso di errori
        error_rate = self._calculate_error_rate()
        metrics.append(
            HealthMetric(
                name="error_rate",
                value=error_rate,
                unit="%",
                status=self._get_metric_status(error_rate, "error_rate"),
                timestamp=now,
                threshold_warning=self._thresholds["error_rate_warning"] * 100,
                threshold_critical=self._thresholds["error_rate_critical"] * 100,
                description="Percentage of failed message processing",
            )
        )

        # Metrica dell'uptime
        metrics.append(
            HealthMetric(
                name="uptime",
                value=uptime,
                unit="seconds",
                status=self._get_metric_status(uptime, "uptime"),
                timestamp=now,
                threshold_warning=self._thresholds["uptime_warning"],
                threshold_critical=self._thresholds["uptime_critical"],
                description="System uptime in seconds",
            )
        )

        # Metrica delle connessioni
        connection_failures = self._disconnection_count
        metrics.append(
            HealthMetric(
                name="connection_failures",
                value=connection_failures,
                unit="count",
                status=self._get_metric_status(
                    connection_failures, "connection_failures"
                ),
                timestamp=now,
                threshold_warning=self._thresholds["connection_failures_warning"],
                threshold_critical=self._thresholds["connection_failures_critical"],
                description="Number of connection failures",
            )
        )

        return metrics

    def _calculate_message_rate(self, now: datetime) -> float:
        """Calcola il tasso di messaggi al secondo"""
        if not self._last_message_time:
            return 0.0

        time_diff = (now - self._last_message_time).total_seconds()
        if time_diff == 0:
            return 0.0

        # Calcola il tasso basato sugli ultimi 60 secondi
        recent_messages = self._get_recent_message_count(60)
        return recent_messages / 60.0

    def _calculate_error_rate(self) -> float:
        """Calcola il tasso di errori"""
        total_operations = self._message_count + self._error_count
        if total_operations == 0:
            return 0.0

        return (self._error_count / total_operations) * 100

    def _get_recent_message_count(self, seconds: int) -> int:
        """Ottiene il numero di messaggi negli ultimi N secondi"""
        # Implementazione semplificata - in un sistema reale si userebbe una coda temporale
        return min(self._message_count, seconds * 10)  # Stima approssimativa

    def _get_metric_status(self, value: float, metric_type: str) -> HealthStatus:
        """Determina lo stato di una metrica"""
        if metric_type == "message_rate":
            if value >= self._thresholds["message_rate_warning"]:
                return HealthStatus.HEALTHY
            elif value >= self._thresholds["message_rate_critical"]:
                return HealthStatus.WARNING
            else:
                return HealthStatus.CRITICAL

        elif metric_type == "error_rate":
            if value <= self._thresholds["error_rate_warning"] * 100:
                return HealthStatus.HEALTHY
            elif value <= self._thresholds["error_rate_critical"] * 100:
                return HealthStatus.WARNING
            else:
                return HealthStatus.CRITICAL

        elif metric_type == "uptime":
            if value >= self._thresholds["uptime_warning"]:
                return HealthStatus.HEALTHY
            elif value >= self._thresholds["uptime_critical"]:
                return HealthStatus.WARNING
            else:
                return HealthStatus.CRITICAL

        elif metric_type == "connection_failures":
            if value <= self._thresholds["connection_failures_warning"]:
                return HealthStatus.HEALTHY
            elif value <= self._thresholds["connection_failures_critical"]:
                return HealthStatus.WARNING
            else:
                return HealthStatus.CRITICAL

        return HealthStatus.UNKNOWN

    def _determine_overall_status(self, metrics: List[HealthMetric]) -> HealthStatus:
        """Determina lo stato generale basato sulle metriche"""
        if not metrics:
            return HealthStatus.UNKNOWN

        # Se qualsiasi metrica è critica, il sistema è critico
        if any(metric.status == HealthStatus.CRITICAL for metric in metrics):
            return HealthStatus.CRITICAL

        # Se qualsiasi metrica è in warning, il sistema è in warning
        if any(metric.status == HealthStatus.WARNING for metric in metrics):
            return HealthStatus.WARNING

        # Se tutte le metriche sono healthy, il sistema è healthy
        if all(metric.status == HealthStatus.HEALTHY for metric in metrics):
            return HealthStatus.HEALTHY

        return HealthStatus.UNKNOWN

    def _create_error_health_status(self) -> SystemHealth:
        """Crea uno stato di salute di errore"""
        return SystemHealth(
            overall_status=HealthStatus.CRITICAL,
            timestamp=timezone.now(),
            metrics=[],
            uptime=0.0,
            message_rate=0.0,
            error_rate=100.0,
        )

    def _monitor_loop(self) -> None:
        """Loop principale del monitor"""
        while True:
            try:
                # Controlla la salute del sistema ogni 30 secondi
                health = self.get_system_health()

                # Log dello stato se non è healthy
                if health.overall_status != HealthStatus.HEALTHY:
                    logger.warning(f"MQTT system health: {health.overall_status.value}")
                    for metric in health.metrics:
                        if metric.status != HealthStatus.HEALTHY:
                            logger.warning(
                                f"  {metric.name}: {metric.value} {metric.unit} ({metric.status.value})"
                            )

                # Salva le metriche nella cache per accesso rapido
                cache.set("mqtt_health", health, timeout=60)

                time.sleep(30)

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(30)

    def get_health_summary(self) -> Dict[str, Any]:
        """Restituisce un riassunto della salute del sistema"""
        try:
            health = self.get_system_health()

            return {
                "status": health.overall_status.value,
                "uptime": health.uptime,
                "message_rate": health.message_rate,
                "error_rate": health.error_rate,
                "timestamp": health.timestamp.isoformat(),
                "metrics": [
                    {
                        "name": metric.name,
                        "value": metric.value,
                        "unit": metric.unit,
                        "status": metric.status.value,
                        "description": metric.description,
                    }
                    for metric in health.metrics
                ],
            }

        except Exception as e:
            logger.error(f"Error getting health summary: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

    def reset_stats(self) -> None:
        """Reset delle statistiche"""
        with self._lock:
            self._message_count = 0
            self._error_count = 0
            self._connection_count = 0
            self._disconnection_count = 0
            self._last_message_time = None
            self._start_time = timezone.now()
            logger.info("MQTT health monitor stats reset")


# Singleton instance
_health_monitor = None


def get_health_monitor() -> MQTTHealthMonitor:
    """Ottiene l'istanza singleton del monitor di salute"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = MQTTHealthMonitor()
    return _health_monitor
