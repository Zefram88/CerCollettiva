# energy/apps.py
import logging
import os
import sys
import threading

# from functools import partial
from logging.handlers import RotatingFileHandler

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger("energy.apps")


def init_mqtt_after_ready(sender, **kwargs):
    """Inizializza MQTT dopo che tutte le app sono pronte"""
    from energy.services.signals import delayed_mqtt_connect

    print("\n=========== MQTT INIT =============")
    print(" Inizializzazione MQTT in corso...")

    # Controlla solo se siamo in modalità test
    is_testing = getattr(settings, "TESTING", False)

    if is_testing:
        print(" | ✗ Test mode - MQTT disabilitato  |")
        print("==================================\n")
        return

    print(" | Avvio thread MQTT...             |")
    threading.Thread(target=delayed_mqtt_connect, daemon=True).start()
    print("==================================\n")


class EnergyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "energy"

    def ready(self):
        # Evita la doppia esecuzione causata dall'autoreloader
        if os.environ.get("RUN_MAIN"):
            print("\n========= ENERGY APP =============")
            print(" Inizializzazione applicazione...")

            try:
                # Setup della rotazione dei log
                self.setup_log_rotation()
                print(" | ✓ Log rotation configurata      |")

                # Controlla se siamo in modalità test
                is_testing = (
                    "test" in sys.argv
                    or "pytest" in sys.modules
                    or os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith("test")
                    or getattr(settings, "TESTING", False)
                )

                if not is_testing:
                    # Import qui per evitare import circolari
                    from .mqtt.client import init_mqtt_connection

                    print(" | Avvio diretto thread MQTT...    |")
                    threading.Thread(target=init_mqtt_connection, daemon=True).start()
                    print(" | ✓ Thread MQTT avviato           |")
                else:
                    print(" | ✗ Test mode - MQTT disabilitato |")

                print("==================================\n")

            except Exception as e:
                print(f" | ✗ Errore: {str(e)}")
                print("==================================\n")
                logger.error(f"Error in app initialization: {e}")

    def setup_log_rotation(self):
        """Configura la rotazione dei file di log"""
        try:
            # Costanti per la rotazione dei log
            MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
            LOG_BACKUP_COUNT = 5

            # Crea la directory dei log se non esiste
            log_dir = os.path.join(settings.BASE_DIR, "logs")
            os.makedirs(log_dir, exist_ok=True)

            # Configura i file handler per ogni categoria
            log_categories = {
                "mqtt": {"file": "mqtt.log", "logger": "energy.mqtt"},
                "device": {"file": "device.log", "logger": "energy.devices"},
                "measurement": {
                    "file": "measurement.log",
                    "logger": "energy.measurements",
                },
            }

            for category, config in log_categories.items():
                handler = RotatingFileHandler(
                    filename=os.path.join(log_dir, config["file"]),
                    maxBytes=MAX_LOG_SIZE,
                    backupCount=LOG_BACKUP_COUNT,
                    encoding="utf-8",
                )

                formatter = logging.Formatter(
                    "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                handler.setFormatter(formatter)

                logger = logging.getLogger(config["logger"])
                logger.addHandler(handler)
                logger.setLevel(logging.INFO)

                print(f" | ✓ Logger {category} configurato     |")

        except Exception as e:
            logger.error(
                f"Errore nella configurazione della rotazione dei log: {str(e)}"
            )
            raise
