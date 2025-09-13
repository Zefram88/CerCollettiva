# energy/services/energy_calculator_cache.py

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from django.conf import settings
from django.core.cache import cache

# from ..models import EnergyInterval
from .energy_calculator_aggregations import EnergyCalculatorAggregations

# from django.db import transaction
# from django.db.models import Sum
# from django.db.models import F
# from django.utils import timezone


logger = logging.getLogger("energy.calculator.cache")


class EnergyCalculatorCache(EnergyCalculatorAggregations):
    """
    Sistema avanzato di caching multi-livello per i dati energetici.
    Estende EnergyCalculatorAggregations per ereditare la logica di calcolo
    e fornisce funzionalità di caching con invalidazione intelligente.
    """

    CACHE_TIMEOUTS = {
        "15MIN": getattr(settings, "CACHE_TIMEOUT_15MIN", 3600),
        "1H": getattr(settings, "CACHE_TIMEOUT_1H", 7200),
        "1D": getattr(settings, "CACHE_TIMEOUT_1D", 86400),
        "1M": getattr(settings, "CACHE_TIMEOUT_1M", 604800),
        "1Y": getattr(settings, "CACHE_TIMEOUT_1Y", 2592000),
    }

    def __init__(self):
        """Inizializza il gestore della cache."""
        super().__init__()
        self.cache_enabled = getattr(settings, "ENERGY_CACHE_ENABLED", True)
        logger.info(
            f"Energy Calculator Cache initialized. Cache enabled: {self.cache_enabled}"
        )

    def _get_cache_key(
        self, device_id: str, interval_type: str, timestamp: datetime
    ) -> str:
        """
        Genera una chiave di cache univoca.

        Args:
            device_id: ID del dispositivo.
            interval_type: Tipo di intervallo ('15MIN', '1H', '1D', '1M', '1Y').
            timestamp: Timestamp di riferimento per l'intervallo.

        Returns:
            str: Chiave di cache univoca.
        """
        prefix = self._cache_prefixes.get(interval_type)
        if not prefix:
            raise ValueError(f"Invalid interval type: {interval_type}")

        if interval_type == "1M":
            date_str = timestamp.strftime("%Y%m")
        elif interval_type == "1Y":
            date_str = timestamp.strftime("%Y")
        else:
            date_str = timestamp.strftime("%Y%m%d%H%M")

        return f"{prefix}{device_id}_{date_str}"

    def get_cached_energy_interval(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
        interval_type: str,
    ) -> Optional[float]:
        """
        Recupera un intervallo di energia dalla cache, se disponibile.

        Args:
            device_id: ID del dispositivo.
            start_time: Timestamp di inizio dell'intervallo.
            end_time: Timestamp di fine dell'intervallo.
            interval_type: Tipo di intervallo ('15MIN', '1H', '1D', '1M', '1Y').

        Returns:
            Optional[float]: Valore dell'energia in kWh se presente in cache,
            altrimenti None.
        """
        if not self.cache_enabled:
            return None

        cache_key = self._get_cache_key(device_id, interval_type, start_time)
        cached_value = cache.get(cache_key)

        if cached_value is not None:
            logger.debug(
                f"Cache HIT - Device: {device_id}, Interval: {interval_type}, "
                f"Start: {start_time}"
            )
            return cached_value
        else:
            logger.debug(
                f"Cache MISS - Device: {device_id}, Interval: {interval_type}, "
                f"Start: {start_time}"
            )
            return None

    def set_cached_energy_interval(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
        interval_type: str,
        energy: float,
    ):
        """
        Salva un intervallo di energia nella cache.

        Args:
            device_id: ID del dispositivo.
            start_time: Timestamp di inizio dell'intervallo.
            end_time: Timestamp di fine dell'intervallo.
            interval_type: Tipo di intervallo ('15MIN', '1H', '1D', '1M', '1Y').
            energy: Valore dell'energia in kWh da salvare.
        """
        if not self.cache_enabled:
            return

        cache_key = self._get_cache_key(device_id, interval_type, start_time)
        timeout = self.CACHE_TIMEOUTS.get(interval_type)

        cache.set(cache_key, energy, timeout)
        logger.debug(
            f"Cache SET - Device: {device_id}, Interval: {interval_type}, "
            f"Start: {start_time}, Energy: {energy:.3f} kWh"
        )

    def _invalidate_higher_caches(self, device_id: str, timestamp: datetime):
        """
        Invalida le cache degli intervalli superiori a quello appena salvato.

        Args:
            device_id: ID del dispositivo.
            timestamp: Timestamp di riferimento dell'intervallo appena salvato.
        """
        if not self.cache_enabled:
            return

        for interval_type in ["1H", "1D", "1M", "1Y"]:
            cache_key = self._get_cache_key(device_id, interval_type, timestamp)
            cache.delete(cache_key)
            logger.debug(
                f"Cache INVALIDATED - Device: {device_id}, "
                f"Interval: {interval_type}, Time: {timestamp}"
            )

    def clear_device_cache(self, device_id: str):
        """
        Pulisce la cache per un dispositivo specifico.

        Args:
            device_id: ID del dispositivo.
        """
        if not self.cache_enabled:
            return

        try:
            for interval_type in self.INTERVAL_TYPES:
                # Costruisci un pattern per eliminare tutte le chiavi relative
                # al dispositivo
                if interval_type == "1M":
                    pattern = f"{self._cache_prefixes[interval_type]}{device_id}_*"
                elif interval_type == "1Y":
                    pattern = f"{self._cache_prefixes[interval_type]}{device_id}_*"
                else:
                    pattern = f"{self._cache_prefixes[interval_type]}{device_id}_*"

                # Usa le wildcards per eliminare le chiavi in modo efficiente
                cache.delete_pattern(pattern)
                logger.info(
                    f"Cache CLEARED for device: {device_id}, "
                    f"interval type: {interval_type}"
                )

        except Exception as e:
            logger.error(f"Error clearing cache for device {device_id}: {str(e)}")

    def bulk_update_cache(
        self, intervals: List[Tuple[str, datetime, datetime, str, float]]
    ):
        """
        Aggiorna la cache con più intervalli in un'unica operazione.

        Args:
            intervals: Lista di tuple (device_id, start_time, end_time,
            interval_type, energy).
        """
        if not self.cache_enabled:
            return

        cache_data = {}
        for device_id, start_time, end_time, interval_type, energy in intervals:
            cache_key = self._get_cache_key(device_id, interval_type, start_time)
            timeout = self.CACHE_TIMEOUTS.get(interval_type)
            cache_data[cache_key] = (energy, timeout)

        cache.set_many(
            {k: v[0] for k, v in cache_data.items()},
            timeout=max(v[1] for v in cache_data.values()),
        )
        logger.info(f"Bulk cache update completed for {len(intervals)} intervals")

        # Invalida le cache superiori per ogni intervallo aggiornato
        for device_id, start_time, _, _, _ in intervals:
            self._invalidate_higher_caches(device_id, start_time)

    def _recalculate_and_cache_aggregations(
        self, device_id: str, start_time: datetime, interval_type: str
    ):
        """
        Ricalcola le aggregazioni per gli intervalli superiori e le salva
        in cache.

        Args:
            device_id: ID del dispositivo.
            start_time: Timestamp di inizio dell'intervallo modificato.
            interval_type: Tipo di intervallo modificato
            ('15MIN', '1H', '1D', '1M', '1Y').
        """
        if not self.cache_enabled:
            return

        if interval_type == "15MIN":
            # Ricalcola orario
            hour_start = start_time.replace(minute=0, second=0, microsecond=0)
            hourly_energy = self.calculate_hourly_energy(device_id, hour_start)
            self.set_cached_energy_interval(
                device_id,
                hour_start,
                hour_start + timedelta(hours=1),
                "1H",
                hourly_energy,
            )

            # Ricalcola giornaliero
            day_start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            daily_energy = self.calculate_daily_energy(device_id, day_start)
            self.set_cached_energy_interval(
                device_id, day_start, day_start + timedelta(days=1), "1D", daily_energy
            )

        elif interval_type == "1H":
            # Ricalcola giornaliero
            day_start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            daily_energy = self.calculate_daily_energy(device_id, day_start)
            self.set_cached_energy_interval(
                device_id, day_start, day_start + timedelta(days=1), "1D", daily_energy
            )

        # Ricalcola mensile per tutti i casi inferiori al mese
        if interval_type in ["15MIN", "1H", "1D"]:
            month_start = start_time.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            monthly_energy = self.calculate_monthly_energy(
                device_id, month_start.year, month_start.month
            )
            if monthly_energy is not None:
                self.set_cached_energy_interval(
                    device_id,
                    month_start,
                    month_start + timedelta(days=30),
                    "1M",
                    monthly_energy,
                )

            # Ricalcola annuale
            year_start = start_time.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            yearly_energy = self.calculate_yearly_energy(device_id, year_start.year)
            if yearly_energy is not None:
                self.set_cached_energy_interval(
                    device_id,
                    year_start,
                    year_start + timedelta(days=365),
                    "1Y",
                    yearly_energy,
                )

        logger.info(
            f"Aggregations recalculated and cached for device: {device_id}, "
            f"starting from: {start_time}, interval type: {interval_type}"
        )
