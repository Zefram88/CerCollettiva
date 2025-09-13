# energy/devices/vendors/shelly/base.py
# import json
import logging

# from datetime import datetime
from typing import Any, Optional

# from typing import Dict

from ....models import DeviceMeasurement
from ...base.meter import BaseMeter

# Configurazione del logger
logger = logging.getLogger(__name__)


class BaseShellyMeter(BaseMeter):
    """
    Classe base per i dispositivi Shelly.
    Fornisce l'implementazione comune per tutti i dispositivi Shelly e definisce
    l'interfaccia che le classi figlie devono implementare.
    """

    def __init__(self):
        """
        Inizializza un dispositivo Shelly base.
        Imposta il vendor comune a tutti i dispositivi Shelly.
        """
        super().__init__()
        self._vendor = "SHELLY"

    def parse_message(self, topic: str, data: Any) -> Optional[DeviceMeasurement]:
        """
        Elabora un messaggio MQTT da un dispositivo Shelly.
        Implementa la logica comune di parsing e delega il parsing specifico
        alle classi figlie.

        Args:
            topic (str): Il topic MQTT del messaggio
            data (Any): I dati del messaggio (possono essere dict, int, etc.)

        Returns:
            Optional[DeviceMeasurement]: L'oggetto misurazione se il parsing
            ha successo, None altrimenti
        """
        try:
            # Log per debug iniziale
            logger.debug(f"Ricevuto messaggio - Topic: {topic}")
            logger.debug(f"Tipo dati: {type(data)}")
            logger.debug(f"Contenuto dati: {data}")

            # Estrai il tipo di messaggio dal topic
            topic_parts = topic.split("/")
            if len(topic_parts) < 4:
                logger.debug(f"Topic non valido (troppo corto): {topic}")
                return None

            # Il tipo di messaggio è la penultima parte del topic
            message_type = topic_parts[-2]

            # Verifica se il tipo di messaggio è supportato
            if message_type not in ["power", "energy", "emeter", "em"]:
                logger.debug(f"Tipo messaggio non supportato: {message_type}")
                return None

            # Delega il parsing specifico alla classe figlia
            measurement_data = self.parse_shelly_data(message_type, data)
            if not measurement_data:
                logger.debug("Parsing specifico fallito")
                return None

            # Valida i dati ottenuti
            if not self.validate_measurement(measurement_data):
                logger.warning(f"Dati misurazione non validi: {data}")
                return None

            return measurement_data

        except Exception as e:
            logger.error(
                f"Errore durante il parsing del messaggio Shelly: {str(e)}",
                exc_info=True,
            )
            logger.debug(f"Topic: {topic}")
            logger.debug(f"Dati problematici: {data}")
            return None

    def parse_shelly_data(
        self, message_type: str, data: Any
    ) -> Optional[DeviceMeasurement]:
        """
        Metodo astratto per il parsing specifico dei dati Shelly.
        Deve essere implementato dalle classi figlie per gestire
        il formato dati specifico di ogni modello.

        Args:
            message_type (str): Il tipo di messaggio (power, energy, emeter, em)
            data (Any): I dati da parsare

        Returns:
            Optional[DeviceMeasurement]: L'oggetto misurazione se il parsing
            ha successo, None altrimenti

        Raises:
            NotImplementedError: Se la classe figlia non implementa questo metodo
        """
        raise NotImplementedError(
            "Le classi figlie devono implementare parse_shelly_data"
        )

    def get_topics(self, base_topic: str) -> list:
        """
        Restituisce la lista dei topic MQTT da sottoscrivere per questo dispositivo.
        Può essere sovrascritto dalle classi figlie per topic specifici.

        Args:
            base_topic (str): Il topic base del dispositivo

        Returns:
            list: Lista dei topic da sottoscrivere
        """
        return [
            f"{base_topic}/status/power",
            f"{base_topic}/status/emeter/#",
            f"{base_topic}/status/energy",
        ]

    @property
    def model(self) -> str:
        """
        Proprietà astratta per il modello del dispositivo.
        Deve essere implementata dalle classi figlie.

        Returns:
            str: Il modello del dispositivo

        Raises:
            NotImplementedError: Se la classe figlia non implementa questa proprietà
        """
        raise NotImplementedError(
            "Le classi figlie devono implementare la proprietà model"
        )

    def validate_measurement(self, measurement: DeviceMeasurement) -> bool:
        """
        Valida i dati di una misurazione.
        Può essere sovrascritto dalle classi figlie per validazioni specifiche.

        Args:
            measurement (DeviceMeasurement): La misurazione da validare

        Returns:
            bool: True se la misurazione è valida, False altrimenti
        """
        # Implementare qui la logica di validazione base
        # Per ora ritorna sempre True
        return True
