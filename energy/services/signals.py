# energy/services/signals.py
import logging
import threading
import time

from django.apps import AppConfig
from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_delete, post_migrate, post_save
from django.dispatch import receiver
# from django.utils import timezone

from energy.models import (
    DeviceConfiguration,
    DeviceMeasurement,
    # EnergyMeasurement,
    MQTTBroker,
)
from energy.mqtt.client import get_mqtt_client

logger = logging.getLogger("energy.mqtt")


def init_mqtt_client(sender, **kwargs):
    """Inizializza e avvia il client MQTT"""
    # logger.info("Initializing MQTT client")
    try:
        mqtt_settings = getattr(settings, "MQTT_SETTINGS", {})

        if not mqtt_settings:
            logger.error("No MQTT settings found in configuration")
            return

        client = get_mqtt_client()
        client.configure(
            host=mqtt_settings["BROKER_HOST"],
            port=mqtt_settings["BROKER_PORT"],
            username=mqtt_settings.get("USERNAME"),
            password=mqtt_settings.get("PASSWORD"),
            use_tls=mqtt_settings.get("TLS_ENABLED", False),
        )

        logger.info("Starting MQTT client")
        client.start()

    except Exception as e:
        logger.error(f"MQTT client initialization failed: {str(e)}")


def check_mqtt_status():
    """Verifica lo stato della connessione MQTT"""
    client = get_mqtt_client()
    if client.is_connected:
        # logger.info("MQTT Status: Connected")
        logger.info(f"Active topics: {len(client._subscribed_topics)}")
        for topic in client._subscribed_topics:
            logger.debug(f"Subscribed topic: {topic}")
    else:
        logger.warning("MQTT Status: Disconnected")


def delayed_mqtt_connect():
    print("\033[93m")  # Giallo per maggiore visibilità
    """Gestisce la connessione MQTT con delay iniziale"""
    try:
        # Delay iniziale
        time.sleep(5)
        print("\n=========== MQTT Startup ===========")
        print(" Inizializzazione connessione MQTT")
        print("===================================")

        client = get_mqtt_client()
        if client.is_connected:
            print(" | ✓ Client già connesso!           |")
            print("===================================\n")
            check_mqtt_status()
            return

        mqtt_broker = MQTTBroker.objects.filter(is_active=True).first()
        if mqtt_broker:
            print(f" | Broker trovato: {mqtt_broker.host}")
            print(f" | Porta: {mqtt_broker.port}")
            print("===================================")

            if not client.is_connected:
                print(" | Tentativo di connessione...      |")
                client.configure(
                    host=mqtt_broker.host,
                    port=mqtt_broker.port,
                    username=mqtt_broker.username,
                    password=mqtt_broker.password,
                    use_tls=mqtt_broker.use_tls,
                )
                client.start()

                # Verifica connessione
                time.sleep(2)
                if client.is_connected:
                    print(" | ✓ Connessione stabilita!         |")
                else:
                    print(" | ✗ Connessione fallita!           |")
                print("===================================\n")
                check_mqtt_status()
                print("\033[0m")  # Reset colore
        else:
            print(" | ✗ Nessun broker MQTT attivo!      |")
            print("===================================\n")
            logger.warning("No active MQTT broker found")
            print("\033[0m")  # Reset colore

    except Exception as e:
        print("\n========== MQTT Error =============")
        print(f" | ✗ Errore: {str(e)}")
        print("===================================\n")
        logger.error(f"MQTT connection failed: {str(e)}")


@receiver(post_save, sender=DeviceMeasurement)
def handle_new_measurement(sender, instance, created, **kwargs):
    """Gestisce nuove misurazioni"""
    if created:
        device_id = f"device_{str(instance.device_id)[-4:]}"  # GDPR compliance
        logger.debug(f"New measurement from {device_id} at {instance.timestamp}")

        cache_key = f"last_measurement_{instance.device_id}"
        cache.set(
            cache_key,
            {
                "power": instance.power,
                "voltage": instance.voltage,
                "current": instance.current,
                "timestamp": instance.timestamp.isoformat(),
            },
            timeout=3600,
        )

        client = get_mqtt_client()
        if not client.is_connected:
            logger.warning("MQTT disconnected - attempting reconnection")
            from ..mqtt.client import init_mqtt_connection

            threading.Thread(target=init_mqtt_connection, daemon=True).start()


@receiver(post_save, sender=DeviceConfiguration)
def handle_device_configuration(sender, instance, created, **kwargs):
    """Gestisce modifiche alle configurazioni dei dispositivi"""
    try:
        # action = "created" if created else "updated"  # Unused variable
        # logger.info(f"Device {instance.device_id} {action}")

        client = get_mqtt_client()
        if client and client.is_connected:
            active_devices = DeviceConfiguration.objects.filter(is_active=True)
            active_topics = []

            for device in active_devices:
                device_topics = device.get_mqtt_topics()
                active_topics.extend(device_topics)

            logger.info(
                f"Refreshing MQTT subscriptions - {len(active_topics)} active topics"
            )

            # Aggiorna sottoscrizioni
            client.refresh_subscriptions()
            check_mqtt_status()

    except Exception as e:
        logger.error(f"Error handling device configuration: {str(e)}")


@receiver(post_save, sender=MQTTBroker)
def mqtt_broker_changed(sender, instance, created, **kwargs):
    """
    Signal handler chiamato quando viene salvata/modificata una configurazione
    del broker MQTT
    """
    if instance.is_active:
        client = get_mqtt_client()
        if not client.is_connected:
            logger.info(
                f"Initiating delayed MQTT connection after broker "
                f"configuration change for {instance.name}"
            )
            threading.Thread(target=delayed_mqtt_connect, daemon=True).start()


@receiver(post_migrate)
def on_post_migrate(sender, **kwargs):
    """Avvia il client MQTT dopo la migrazione del database"""
    if isinstance(sender, AppConfig) and sender.name == "energy":
        init_mqtt_client(sender)


@receiver(post_save, sender=DeviceConfiguration)
def handle_device_created(sender, instance, created, **kwargs):
    """Handler per la creazione/modifica di un dispositivo"""
    try:
        if created:
            logger.info(f"Nuovo dispositivo creato: {instance.device_id}")
        else:
            logger.info(f"Dispositivo aggiornato: {instance.device_id}")

        client = get_mqtt_client()
        if client and client.is_connected:
            # Ottieni tutti i topic attivi
            active_devices = DeviceConfiguration.objects.filter(is_active=True)
            active_topics = []

            for device in active_devices:
                device_topics = device.get_mqtt_topics()
                active_topics.extend(device_topics)

            logger.info(f"Topics attivi: {active_topics}")

            # Annulla tutte le sottoscrizioni esistenti
            client.unsubscribe("#")

            # Sottoscrivi i nuovi topics
            for topic in active_topics:
                logger.info(f"Sottoscrizione a: {topic}")
                client.subscribe(topic)

            if not active_topics:
                # Se non ci sono topic specifici, usa il wildcard
                default_topic = "cercollettiva/+/+/value"
                logger.info(
                    f"Nessun topic specifico, sottoscrizione a: {default_topic}"
                )
                client.subscribe(default_topic)

    except Exception as e:
        logger.error(f"Errore nell'aggiornamento delle sottoscrizioni MQTT: {str(e)}")


@receiver(post_delete, sender=DeviceConfiguration)
def handle_device_deleted(sender, instance, **kwargs):
    """Handler per l'eliminazione di un dispositivo"""
    try:
        logger.info(f"Dispositivo eliminato: {instance.device_id}")

        client = get_mqtt_client()
        if client and client.is_connected:
            # Se il dispositivo aveva dei topic specifici, annullane la sottoscrizione
            device_topics = instance.get_mqtt_topics()
            for topic in device_topics:
                logger.info(f"Annullamento sottoscrizione a: {topic}")
                client.unsubscribe(topic)

            # Aggiorna la lista completa dei topic
            active_devices = DeviceConfiguration.objects.filter(is_active=True)
            active_topics = []

            for device in active_devices:
                device_topics = device.get_mqtt_topics()
                active_topics.extend(device_topics)

            if not active_topics:
                # Se non ci sono più dispositivi attivi, torna al wildcard
                default_topic = "cercollettiva/+/+/value"
                logger.info(f"Nessun topic attivo, sottoscrizione a: {default_topic}")
                client.subscribe(default_topic)

    except Exception as e:
        logger.error(f"Errore nella rimozione delle sottoscrizioni MQTT: {str(e)}")
