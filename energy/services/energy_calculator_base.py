# energy/services/energy_calculator_base.py

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# from django.core.cache import cache
# from django.db import transaction
# from django.db.models import Avg, F, Max, Min, Sum
from django.utils import timezone

from ..models import DeviceConfiguration

logger = logging.getLogger("energy.calculator")


class EnergyCalculatorBase:
    """
    Classe base per il calcolo dell'energia con configurazioni e costanti.
    Gestisce le impostazioni di base e fornisce metodi di utilità comuni.
    """

    # Costanti per gli intervalli
    INTERVAL_MINUTES = 15
    MAX_INTERVAL_SECONDS = 1200  # 20 minuti
    MAX_ENERGY_PER_INTERVAL = 100  # 100 kWh max per intervallo di 15 min
    HOURS_IN_DAY = 24
    INTERVALS_PER_HOUR = 60 // INTERVAL_MINUTES

    # Tipi di intervallo disponibili
    INTERVAL_TYPES = {
        "15MIN": timedelta(minutes=15),
        "1H": timedelta(hours=1),
        "1D": timedelta(days=1),
        "1M": "MONTH",  # Gestito separatamente
        "1Y": "YEAR",  # Gestito separatamente
    }

    # Cache timeouts per diversi tipi di aggregazione
    CACHE_TIMEOUTS = {
        "15MIN": 3600,  # 1 ora
        "1H": 7200,  # 2 ore
        "1D": 86400,  # 1 giorno
        "1M": 604800,  # 1 settimana
        "1Y": 2592000,  # 1 mese
    }

    def __init__(self):
        """Inizializza il calcolatore con impostazioni di base"""
        # Impostazioni di base
        self.cache_enabled = True
        self.cache_timeout = 3600  # 1 ora di default
        self.strict_validation = True  # Validazione rigorosa dei dati

        # Prefissi per le chiavi cache
        self._cache_prefixes = {
            "15MIN": "energy_15min_",
            "1H": "energy_hour_",
            "1D": "energy_day_",
            "1M": "energy_month_",
            "1Y": "energy_year_",
        }

        # Inizializzazione logger
        self._setup_logging()
        logger.info("Energy Calculator initialized with base settings")

    def _setup_logging(self):
        """Configura il logging avanzato"""
        self._log_format = """
            %(asctime)s [%(levelname)s]:
            Device: %(device_id)s
            Operation: %(operation)s
            Details: %(message)s
        """

    def _validate_interval_type(self, interval_type: str) -> bool:
        """
        Valida il tipo di intervallo

        Args:
            interval_type: Tipo di intervallo da validare

        Returns:
            bool: True se valido, False altrimenti
        """
        return interval_type in self.INTERVAL_TYPES

    def _validate_timestamp(self, timestamp: datetime) -> bool:
        """
        Valida un timestamp

        Args:
            timestamp: Timestamp da validare

        Returns:
            bool: True se valido, False altrimenti
        """
        now = timezone.now()
        min_date = now - timedelta(days=365 * 2)  # Max 2 anni indietro
        return min_date <= timestamp <= now

    def _validate_energy_value(self, energy: float) -> bool:
        """
        Valida un valore di energia

        Args:
            energy: Valore di energia in kWh da validare

        Returns:
            bool: True se valido, False altrimenti
        """
        return 0 <= energy <= self.MAX_ENERGY_PER_INTERVAL

    def _round_to_interval(self, dt: datetime) -> datetime:
        """
        Arrotonda un timestamp al più vicino intervallo di 15 minuti

        Args:
            dt: Datetime da arrotondare

        Returns:
            datetime: Datetime arrotondato
        """
        minutes = dt.minute
        rounded_minutes = (minutes // self.INTERVAL_MINUTES) * self.INTERVAL_MINUTES
        return dt.replace(minute=rounded_minutes, second=0, microsecond=0)

    def _get_interval_bounds(self, timestamp: datetime, interval_type: str) -> tuple:
        """
        Calcola l'inizio e la fine di un intervallo

        Args:
            timestamp: Timestamp di riferimento
            interval_type: Tipo di intervallo

        Returns:
            tuple: (start_time, end_time)
        """
        if interval_type == "15MIN":
            start_time = self._round_to_interval(timestamp)
            end_time = start_time + timedelta(minutes=self.INTERVAL_MINUTES)
        elif interval_type == "1H":
            start_time = timestamp.replace(minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
        elif interval_type == "1D":
            start_time = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=1)
        elif interval_type == "1M":
            start_time = timestamp.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if start_time.month == 12:
                end_time = start_time.replace(year=start_time.year + 1, month=1)
            else:
                end_time = start_time.replace(month=start_time.month + 1)
        else:  # '1Y'
            start_time = timestamp.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end_time = start_time.replace(year=start_time.year + 1)

        return start_time, end_time

    def _get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera informazioni sul dispositivo in modo GDPR-compliant

        Args:
            device_id: ID del dispositivo

        Returns:
            Optional[Dict[str, Any]]: Informazioni sul dispositivo o None
        """
        try:
            device = DeviceConfiguration.objects.get(device_id=device_id)
            # Mascheramento dati sensibili
            masked_id = f"{device_id[:3]}...{device_id[-3:]}"
            return {
                "id": masked_id,
                "type": device.device_type,
                "is_active": device.is_active,
                "last_seen": device.last_seen,
            }
        except DeviceConfiguration.DoesNotExist:
            logger.warning(f"Device {device_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving device info: {str(e)}")
            return None

    def get_supported_intervals(self) -> list:
        """
        Restituisce la lista degli intervalli supportati

        Returns:
            list: Lista degli intervalli supportati
        """
        return list(self.INTERVAL_TYPES.keys())
