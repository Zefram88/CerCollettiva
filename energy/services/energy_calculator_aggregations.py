# energy/services/energy_calculator_aggregations.py

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from django.core.cache import cache
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from ..models import EnergyInterval
from .energy_calculator_measurements import EnergyCalculatorMeasurements

logger = logging.getLogger("energy.calculator")


class EnergyCalculatorAggregations(EnergyCalculatorMeasurements):
    """
    Gestione delle aggregazioni energetiche per diversi intervalli temporali.
    Estende EnergyCalculatorMeasurements per accedere alle funzionalità di base
    e alla gestione delle misurazioni.
    """

    def calculate_hourly_energy(self, device_id: str, hour_start: datetime) -> float:
        """
        Calcola l'energia oraria sommando gli intervalli di 15 minuti

        Args:
            device_id: ID del dispositivo
            hour_start: Inizio dell'ora da calcolare

        Returns:
            float: Energia totale dell'ora in kWh
        """
        try:
            # Normalizza l'ora di inizio
            hour_start = hour_start.replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)

            # Verifica cache
            cache_key = self._get_cache_key(device_id, "1H", hour_start)
            cached_value = cache.get(cache_key) if self.cache_enabled else None

            if cached_value is not None:
                logger.debug(
                    f"Cache hit for hourly energy - Device: {device_id}, Hour: {hour_start}"
                )
                return cached_value

            # Recupera intervalli di 15 minuti
            intervals = EnergyInterval.objects.filter(
                device_id=device_id,
                start_time__gte=hour_start,
                end_time__lt=hour_end,
                interval_type="15MIN",
            ).order_by("start_time")

            # Calcola totale
            total_energy = intervals.aggregate(total=Sum("energy_value"))["total"] or 0
            intervals_count = intervals.count()

            # Verifica completezza
            if intervals_count < self.INTERVALS_PER_HOUR:
                logger.warning(
                    f"""
                    Incomplete hourly data:
                    - Device: {device_id}
                    - Hour: {hour_start}
                    - Intervals found: {intervals_count}/{self.INTERVALS_PER_HOUR}
                    - Energy calculated: {total_energy:.3f} kWh
                """
                )
            else:
                logger.info(
                    f"""
                    Hourly energy calculated:
                    - Device: {device_id}
                    - Hour: {hour_start}
                    - Energy: {total_energy:.3f} kWh
                """
                )

                if self.cache_enabled:
                    cache.set(cache_key, total_energy, self.CACHE_TIMEOUTS["1H"])

            return total_energy

        except Exception as e:
            logger.error(f"Error calculating hourly energy: {str(e)}")
            return 0

    def calculate_daily_energy(self, device_id: str, date: datetime) -> float:
        """
        Calcola l'energia giornaliera sommando gli intervalli orari

        Args:
            device_id: ID del dispositivo
            date: Data per cui calcolare l'energia

        Returns:
            float: Energia totale del giorno in kWh
        """
        try:
            # Normalizza la data
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            # Verifica cache
            cache_key = self._get_cache_key(device_id, "1D", day_start)
            cached_value = cache.get(cache_key) if self.cache_enabled else None

            if cached_value is not None:
                logger.debug(
                    f"Cache hit for daily energy - Device: {device_id}, Date: {date.date()}"
                )
                return cached_value

            # Recupera intervalli orari
            intervals = EnergyInterval.objects.filter(
                device_id=device_id,
                start_time__gte=day_start,
                end_time__lt=day_end,
                interval_type="1H",
            ).order_by("start_time")

            # Calcola totale
            total_energy = intervals.aggregate(total=Sum("energy_value"))["total"] or 0
            intervals_count = intervals.count()

            expected_intervals = self.HOURS_IN_DAY
            if intervals_count < expected_intervals:
                logger.warning(
                    f"""
                    Incomplete daily data:
                    - Device: {device_id}
                    - Date: {date.date()}
                    - Intervals found: {intervals_count}/{expected_intervals}
                    - Energy calculated: {total_energy:.3f} kWh
                """
                )
            else:
                logger.info(
                    f"""
                    Daily energy calculated:
                    - Device: {device_id}
                    - Date: {date.date()}
                    - Energy: {total_energy:.3f} kWh
                """
                )

                if self.cache_enabled:
                    cache.set(cache_key, total_energy, self.CACHE_TIMEOUTS["1D"])

            return total_energy

        except Exception as e:
            logger.error(f"Error calculating daily energy: {str(e)}")
            return 0

    def calculate_monthly_energy(
        self, device_id: str, year: int, month: int
    ) -> Optional[float]:
        """
        Calcola l'energia mensile sommando i dati giornalieri

        Args:
            device_id: ID del dispositivo
            year: Anno
            month: Mese (1-12)

        Returns:
            Optional[float]: Energia totale del mese in kWh o None se errore
        """
        try:
            # Calcola inizio e fine mese
            month_start = datetime(year, month, 1)
            if month == 12:
                month_end = datetime(year + 1, 1, 1)
            else:
                month_end = datetime(year, month + 1, 1)

            # Verifica cache
            cache_key = self._get_cache_key(device_id, "1M", month_start)
            cached_value = cache.get(cache_key) if self.cache_enabled else None

            if cached_value is not None:
                logger.debug(
                    f"Cache hit for monthly energy - Device: {device_id}, Month: {month_start}"
                )
                return cached_value

            # Recupera intervalli giornalieri
            intervals = EnergyInterval.objects.filter(
                device_id=device_id,
                start_time__gte=month_start,
                end_time__lt=month_end,
                interval_type="1D",
            ).order_by("start_time")

            # Calcola totale
            total_energy = intervals.aggregate(total=Sum("energy_value"))["total"] or 0
            intervals_count = intervals.count()

            days_in_month = (month_end - month_start).days
            if intervals_count < days_in_month:
                logger.warning(
                    f"""
                    Incomplete monthly data:
                    - Device: {device_id}
                    - Month: {month_start.strftime('%Y-%m')}
                    - Days found: {intervals_count}/{days_in_month}
                    - Energy calculated: {total_energy:.3f} kWh
                """
                )
            else:
                logger.info(
                    f"""
                    Monthly energy calculated:
                    - Device: {device_id}
                    - Month: {month_start.strftime('%Y-%m')}
                    - Energy: {total_energy:.3f} kWh
                """
                )

                if self.cache_enabled:
                    cache.set(cache_key, total_energy, self.CACHE_TIMEOUTS["1M"])

            return total_energy

        except Exception as e:
            logger.error(f"Error calculating monthly energy: {str(e)}")
            return None

    def calculate_yearly_energy(self, device_id: str, year: int) -> Optional[float]:
        """
        Calcola l'energia annuale sommando i dati mensili

        Args:
            device_id: ID del dispositivo
            year: Anno

        Returns:
            Optional[float]: Energia totale dell'anno in kWh o None se errore
        """
        try:
            # Calcola inizio e fine anno
            year_start = datetime(year, 1, 1)
            year_end = datetime(year + 1, 1, 1)

            # Verifica cache
            cache_key = self._get_cache_key(device_id, "1Y", year_start)
            cached_value = cache.get(cache_key) if self.cache_enabled else None

            if cached_value is not None:
                logger.debug(
                    f"Cache hit for yearly energy - Device: {device_id}, Year: {year}"
                )
                return cached_value

            # Recupera intervalli mensili
            intervals = EnergyInterval.objects.filter(
                device_id=device_id,
                start_time__gte=year_start,
                end_time__lt=year_end,
                interval_type="1M",
            ).order_by("start_time")

            # Calcola totale
            total_energy = intervals.aggregate(total=Sum("energy_value"))["total"] or 0
            intervals_count = intervals.count()

            if intervals_count < 12:
                logger.warning(
                    f"""
                    Incomplete yearly data:
                    - Device: {device_id}
                    - Year: {year}
                    - Months found: {intervals_count}/12
                    - Energy calculated: {total_energy:.3f} kWh
                """
                )
            else:
                logger.info(
                    f"""
                    Yearly energy calculated:
                    - Device: {device_id}
                    - Year: {year}
                    - Energy: {total_energy:.3f} kWh
                """
                )

                if self.cache_enabled:
                    cache.set(cache_key, total_energy, self.CACHE_TIMEOUTS["1Y"])

            return total_energy

        except Exception as e:
            logger.error(f"Error calculating yearly energy: {str(e)}")
            return None

    def get_energy_summary(
        self, device_id: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, float]:
        """
        Ottiene un riepilogo dell'energia per tutti gli intervalli disponibili

        Args:
            device_id: ID del dispositivo
            start_time: Inizio periodo
            end_time: Fine periodo

        Returns:
            Dict[str, float]: Dizionario con i totali per tipo di intervallo
        """
        summary = {}
        for interval_type in self.INTERVAL_TYPES.keys():
            intervals = EnergyInterval.objects.filter(
                device_id=device_id,
                interval_type=interval_type,
                start_time__gte=start_time,
                end_time__lte=end_time,
            )
            total = intervals.aggregate(total=Sum("energy_value"))["total"] or 0
            summary[interval_type] = total

        return summary
