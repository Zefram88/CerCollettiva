# energy/devices/registry.py
import logging
from typing import Dict, List, Optional, Tuple, Type

# from ..models.device import DeviceConfiguration
from .base.device import BaseDevice
from .vendors.shelly.em import ShellyEM
from .vendors.shelly.em_3 import ShellyEM3
from .vendors.shelly.plus_plug_s import ShellyPlusPlugS

# Importazione dei dispositivi supportati
from .vendors.shelly.pro_3em import ShellyPro3EM
from .vendors.shelly.pro_em import ShellyProEM

logger = logging.getLogger(__name__)


class DeviceRegistry:
    """Registry centralizzato per tutti i dispositivi supportati"""

    _devices: Dict[str, Type[BaseDevice]] = {}

    @classmethod
    def register(cls, device_class: Type[BaseDevice]) -> None:
        try:
            device = device_class()
            key = "_".join([device.vendor, device.model]).upper()
            if not key:
                raise ValueError(
                    f"Device {device_class.__name__} non ha un device_type valido"
                )
            cls._devices[key] = device_class
            # Riduci i log a una sola riga per dispositivo registrato
            # logger.info(f"Registrato dispositivo: {key}")
        except Exception as e:
            logger.error(
                f"Errore registrazione dispositivo {device_class.__name__}: {e}"
            )
            raise

    @classmethod
    def unregister(cls, device_type: str) -> None:
        """
        Rimuove un dispositivo dal registro

        Args:
            device_type: Tipo di dispositivo da rimuovere
        """
        if device_type in cls._devices:
            del cls._devices[device_type]
            logger.debug(f"Rimosso dispositivo: {device_type}")

    @classmethod
    def get_device(
        cls, device_type: str, vendor: str = None, model: str = None
    ) -> Optional[BaseDevice]:
        """
        Ottiene un'istanza di dispositivo dal registro

        Args:
            device_type: Tipo di dispositivo o vendor
            vendor: (opzionale) Nome del vendor se usato con model
            model: (opzionale) Nome del model se usato con vendor

        Returns:
            Optional[BaseDevice]: Istanza del dispositivo o None se non trovato
        """
        if vendor and model:
            return cls.get_device_by_vendor_model(vendor, model)

        device_class = cls._devices.get(device_type)
        return device_class() if device_class else None

    @classmethod
    def list_devices(cls) -> List[Tuple[str, str]]:
        """
        Lista tutti i dispositivi registrati

        Returns:
            List[Tuple[str, str]]: Lista di tuple (device_type, display_name)
        """
        return [
            (key, device().get_display_name()) for key, device in cls._devices.items()
        ]

    @classmethod
    def get_device_by_key(cls, key: str) -> Optional[BaseDevice]:
        """
        Ottiene un'istanza di dispositivo usando la chiave

        Args:
            key: Chiave del dispositivo (device_type)

        Returns:
            Optional[BaseDevice]: Istanza del dispositivo o None se non trovato
        """
        return cls.get_device(key)

    @classmethod
    def get_device_by_vendor_model(
        cls, vendor: str, model: str
    ) -> Optional[BaseDevice]:
        try:
            vendor = vendor.strip().upper()
            model = model.strip().upper()

            # logger.info(f"DEBUG - Input: vendor={vendor}, model={model}")
            # logger.info(f"DEBUG - Devices registered: {cls._devices.keys()}")

            # Prova match diretto
            key = f"{vendor}_{model}"
            if key in cls._devices:
                return cls._devices[key]()

            # Prova match con model senza underscore
            key_no_underscore = f"{vendor}_{model.replace('_', '')}"
            if key_no_underscore in cls._devices:
                return cls._devices[key_no_underscore]()

            # Se nessun match, prova con device_type
            for device_class in cls._devices.values():
                device = device_class()
                if device.vendor.upper() == vendor and device.model.upper() == model:
                    return device_class()

            logger.warning(f"No match found for {key}")
            return None
        except Exception as e:
            logger.error(f"Error in get_device_by_vendor_model: {e}")
            return None

    @classmethod
    def validate_device(cls, vendor: str, model: str) -> bool:
        """
        Valida se un dispositivo è supportato

        Args:
            vendor: Nome del vendor
            model: Nome del modello

        Returns:
            bool: True se il dispositivo è supportato, False altrimenti
        """
        if not vendor or not model:
            return False
        key = "_".join([vendor, model]).upper()
        return key in cls._devices

    @classmethod
    def get_supported_vendors(cls) -> List[str]:
        """
        Restituisce la lista dei vendor supportati

        Returns:
            List[str]: Lista dei vendor supportati
        """
        return sorted(set(device().vendor for device in cls._devices.values()))

    @classmethod
    def get_supported_models(cls, vendor: str) -> List[str]:
        """
        Restituisce la lista dei modelli supportati per un vendor

        Args:
            vendor: Nome del vendor

        Returns:
            List[str]: Lista dei modelli supportati
        """
        return sorted(
            [
                device().model
                for device in cls._devices.values()
                if device().vendor.upper() == vendor.upper()
            ]
        )


def register_devices():
    """
    Registra tutti i dispositivi supportati.
    Questa funzione viene chiamata all'avvio dell'applicazione.
    """
    try:
        # Shelly
        DeviceRegistry.register(ShellyPro3EM)  # Trifase professionale
        DeviceRegistry.register(ShellyProEM)  # Monofase professionale
        DeviceRegistry.register(ShellyEM3)  # Trifase prima generazione
        DeviceRegistry.register(ShellyEM)  # Monofase prima generazione
        DeviceRegistry.register(ShellyPlusPlugS)  # Smart plug con misurazione

        # logger.info("Dispositivi registrati con successo")
    except Exception:
        # logger.error(f"Errore durante la registrazione dei dispositivi: {e}")
        raise


# Registra i dispositivi all'importazione del modulo
register_devices()
