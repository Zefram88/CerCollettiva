# energy/logging.py
import logging

# Configurazione logger principale
logger = logging.getLogger("energy")

# Sotto-logger specifici
mqtt_logger = logging.getLogger("energy.mqtt")
device_logger = logging.getLogger("energy.devices")
measurement_logger = logging.getLogger("energy.measurements")


# Formattatori personalizzati per diverse categorie
class MQTTFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, "topic"):
            # Maschera dati sensibili nel topic per GDPR
            topic_parts = record.topic.split("/")
            if len(topic_parts) >= 3:
                topic_parts[2] = f"{topic_parts[2][:3]}...{topic_parts[2][-3:]}"
            record.topic = "/".join(topic_parts)
        return super().format(record)


def setup_logging():
    # Formatter per messaggi MQTT
    mqtt_formatter = MQTTFormatter("%(asctime)s [MQTT] %(levelname)s: %(message)s")

    # Formatter per misurazioni
    measurement_formatter = logging.Formatter(
        "%(asctime)s [MEASUREMENT] %(levelname)s: %(message)s"
    )

    # Formatter per dispositivi
    device_formatter = logging.Formatter(
        "%(asctime)s [DEVICE] %(levelname)s: %(message)s"
    )

    # Configurazione handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(mqtt_formatter)

    # Configurazione livelli di log
    mqtt_logger.setLevel(logging.INFO)
    device_logger.setLevel(logging.INFO)
    measurement_logger.setLevel(logging.INFO)
