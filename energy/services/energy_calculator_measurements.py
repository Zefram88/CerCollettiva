# energy/services/energy_calculator_measurements.py

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from django.core.cache import cache
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from ..models import DeviceMeasurement, EnergyInterval
from .energy_calculator_base import EnergyCalculatorBase

logger = logging.getLogger("energy.calculator")


class EnergyCalculatorMeasurements(EnergyCalculatorBase):
    """
    Gestione delle misurazioni energetiche e salvataggio intervalli.
    Estende EnergyCalculatorBase per ereditare le configurazioni di base.
    """

    def process_new_measurement(
        self, device_id: str, timestamp: datetime, total_energy: float
    ) -> None:
        """
        Processa una nuova misurazione di energia totale e calcola l'energia nell'intervallo

        Args:
            device_id: ID del dispositivo
            timestamp: Timestamp della misurazione
            total_energy: Energia totale misurata in kWh
        """
        try:
            # Validazione dei dati in ingresso
            if not self._validate_timestamp(timestamp):
                logger.error(
                    f"""
                    Invalid timestamp:
                    - Device: {device_id}
                    - Timestamp: {timestamp}
                """
                )
                return

            if not self._validate_energy_value(total_energy):
                logger.error(
                    f"""
                    Invalid energy value:
                    - Device: {device_id}
                    - Energy: {total_energy}
                """
                )
                return

            logger.info(
                f"""
                Processing new measurement:
                - Device: {device_id}
                - Timestamp: {timestamp}
                - Total Energy: {total_energy:.3f} kWh
            """
            )

            # Chiave cache per l'ultima misurazione
            cache_key = f"last_energy_measurement_{device_id}"
            last_measurement = cache.get(cache_key)

            if last_measurement:
                # Calcola il tempo trascorso
                time_diff = (timestamp - last_measurement["timestamp"]).total_seconds()

                if time_diff <= self.MAX_INTERVAL_SECONDS:
                    # Calcola l'energia nell'intervallo
                    interval_energy = total_energy - last_measurement["total_energy"]

                    if 0 <= interval_energy <= self.MAX_ENERGY_PER_INTERVAL:
                        # Arrotonda al quarto d'ora più vicino
                        interval_start = self._round_to_interval(
                            last_measurement["timestamp"]
                        )
                        interval_end = interval_start + timedelta(
                            minutes=self.INTERVAL_MINUTES
                        )

                        # Salva con transazione atomica
                        with transaction.atomic():
                            # Salva l'intervallo base
                            saved = self._save_interval_energy(
                                device_id=device_id,
                                start_time=interval_start,
                                end_time=interval_end,
                                energy=interval_energy,
                                interval_type="15MIN",
                            )

                            if saved:
                                # Invalida le cache degli intervalli superiori
                                self._invalidate_higher_caches(
                                    device_id, interval_start
                                )

                                logger.info(
                                    f"""
                                    Energy interval saved:
                                    - Device: {device_id}
                                    - Start: {interval_start}
                                    - End: {interval_end}
                                    - Energy: {interval_energy:.3f} kWh
                                """
                                )
                    else:
                        logger.warning(
                            f"""
                            Energy value out of range:
                            - Device: {device_id}
                            - Energy: {interval_energy:.3f} kWh
                            - Max allowed: {self.MAX_ENERGY_PER_INTERVAL} kWh
                        """
                        )
                else:
                    logger.warning(
                        f"""
                        Time interval too long:
                        - Device: {device_id}
                        - Interval: {time_diff:.1f} seconds
                        - Max allowed: {self.MAX_INTERVAL_SECONDS} seconds
                    """
                    )

            # Aggiorna la cache con la nuova misurazione
            cache.set(
                cache_key,
                {"timestamp": timestamp, "total_energy": total_energy},
                self.cache_timeout,
            )

        except Exception as e:
            logger.error(
                f"Error processing measurement for device {device_id}: {str(e)}"
            )

    @transaction.atomic
    def _save_interval_energy(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
        energy: float,
        interval_type: str,
    ) -> bool:
        """
        Salva l'energia misurata in un intervallo

        Args:
            device_id: ID del dispositivo
            start_time: Inizio dell'intervallo
            end_time: Fine dell'intervallo
            energy: Energia misurata in kWh
            interval_type: Tipo di intervallo ('15MIN', '1H', '1D', '1M', '1Y')

        Returns:
            bool: True se il salvataggio è riuscito, False altrimenti
        """
        try:
            # Validazioni
            if not all(
                [
                    self._validate_timestamp(start_time),
                    self._validate_timestamp(end_time),
                    self._validate_interval_type(interval_type),
                    self._validate_energy_value(energy),
                ]
            ):
                logger.error("Validation failed for interval energy")
                return False

            # Crea o aggiorna l'intervallo
            interval, created = EnergyInterval.objects.get_or_create(
                device_id=device_id,
                start_time=start_time,
                interval_type=interval_type,
                defaults={"end_time": end_time, "energy_value": energy},
            )

            if not created:
                interval.energy_value = energy
                interval.save(update_fields=["energy_value"])

            logger.info(
                f"""
                Interval {'created' if created else 'updated'}:
                - Device: {device_id}
                - Type: {interval_type}
                - Start: {start_time}
                - End: {end_time}
                - Energy: {energy:.3f} kWh
            """
            )

            return True

        except Exception as e:
            logger.error(f"Error saving interval energy: {str(e)}")
            return False

    def get_latest_interval(
        self, device_id: str, interval_type: str = "15MIN"
    ) -> Optional[Dict[str, Any]]:
        """
        Recupera l'ultimo intervallo di energia per un dispositivo

        Args:
            device_id: ID del dispositivo
            interval_type: Tipo di intervallo (default '15MIN')

        Returns:
            Optional[Dict[str, Any]]: Dati dell'ultimo intervallo o None
        """
        try:
            interval = (
                EnergyInterval.objects.filter(
                    device_id=device_id, interval_type=interval_type
                )
                .order_by("-start_time")
                .first()
            )

            if interval:
                return {
                    "start_time": interval.start_time,
                    "end_time": interval.end_time,
                    "energy": interval.energy_value,
                    "type": interval_type,
                }
            return None

        except Exception as e:
            logger.error(f"Error getting latest interval: {str(e)}")
            return None

    def get_intervals_in_range(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
        interval_type: str = "15MIN",
    ) -> list:
        """
        Recupera tutti gli intervalli in un range temporale

        Args:
            device_id: ID del dispositivo
            start_time: Inizio del range
            end_time: Fine del range
            interval_type: Tipo di intervallo (default '15MIN')

        Returns:
            list: Lista degli intervalli trovati
        """
        try:
            intervals = EnergyInterval.objects.filter(
                device_id=device_id,
                interval_type=interval_type,
                start_time__gte=start_time,
                end_time__lte=end_time,
            ).order_by("start_time")

            return [
                {
                    "start_time": interval.start_time,
                    "end_time": interval.end_time,
                    "energy": interval.energy_value,
                    "type": interval_type,
                }
                for interval in intervals
            ]

        except Exception as e:
            logger.error(f"Error getting intervals in range: {str(e)}")
            return []

    def calculate_total_system_power(self, user=None, time_window_minutes=5):
        """
        Calcola la potenza totale del sistema per tutti gli impianti o per un utente specifico.

        Args:
            user: Utente per cui calcolare la potenza (None per tutti gli impianti)
            time_window_minutes: Finestra temporale in minuti per le misurazioni valide

        Returns:
            float: Potenza totale in kW
        """
        time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)

        # Costruisci la query base
        query = DeviceMeasurement.objects.filter(
            device__is_active=True, timestamp__gte=time_threshold, quality="GOOD"
        )

        # Filtra per utente se specificato
        if user and not user.is_staff:
            query = query.filter(device__plant__owner=user)

        # Usa la cache se abilitata
        if self.cache_enabled:
            cache_key = f"total_power_{user.id if user else 'all'}"
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

        # Calcola potenza totale
        total_power = (
            query.values("device")
            .annotate(latest_power=Max("power"))
            .aggregate(total=Sum("latest_power"))["total"]
            or 0
        )

        # Converti in kW e arrotonda
        result = round(total_power / 1000.0, 2)

        # Salva in cache se abilitata
        if self.cache_enabled:
            cache.set(cache_key, result, timeout=300)  # Cache per 5 minuti

        logger.info(f"Total system power calculated: {result} kW")
        return result

    def calculate_plant_power(self, plant_id, time_window_minutes=5):
        """
        Calcola la potenza totale per un singolo impianto.

        Args:
            plant_id: ID dell'impianto
            time_window_minutes: Finestra temporale in minuti

        Returns:
            float: Potenza totale dell'impianto in kW
        """
        # Sfrutta la cache esistente se possibile
        cache_key = f"plant_power_{plant_id}"
        cached_value = self.get_cached_energy_interval(
            plant_id, timezone.now(), None, "5MIN"
        )
        if cached_value is not None:
            return cached_value

        time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)

        total_power = (
            DeviceMeasurement.objects.filter(
                device__plant_id=plant_id,
                device__is_active=True,
                timestamp__gte=time_threshold,
                quality="GOOD",
            )
            .values("device")
            .annotate(latest_power=Max("power"))
            .aggregate(total=Sum("latest_power"))["total"]
            or 0
        )

        result = round(total_power / 1000.0, 2)

        # Salva il risultato in cache
        if self.cache_enabled:
            self.set_cached_energy_interval(
                plant_id, timezone.now(), None, "5MIN", result
            )

        return result
