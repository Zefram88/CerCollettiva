import json
import random
import time
from typing import Optional

import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand, CommandError

from energy.models import DeviceConfiguration, MQTTBroker, MQTTConfiguration


class Command(BaseCommand):
    help = (
        "Pubblica messaggi demo MQTT per un DeviceConfiguration: em:0 (potenza) e emdata:0 (energia cumulativa).\n"
        "Usa le credenziali per-device se presenti, altrimenti quelle globali dei settings."
    )

    def add_arguments(self, parser):
        parser.add_argument("device_id", type=str, help="ID del dispositivo (DeviceConfiguration.device_id)")
        parser.add_argument("--count", type=int, default=1, help="Numero di cicli di pubblicazione (default: 1)")
        parser.add_argument("--interval", type=float, default=2.0, help="Intervallo tra i cicli (secondi, default: 2)")
        parser.add_argument(
            "--base-topic",
            type=str,
            default=None,
            help="Base topic override (es. cercollettiva/<POD>/<DEVICE_ID>) senza suffissi /status/*",
        )
        parser.add_argument("--qos", type=int, default=1, choices=[0, 1, 2], help="QoS da usare (default 1)")

    def handle(self, *args, **opts):
        device_id: str = opts["device_id"].strip()
        count: int = max(1, int(opts["count"]))
        interval: float = max(0.1, float(opts["interval"]))
        qos: int = int(opts["qos"])

        try:
            device = DeviceConfiguration.objects.select_related("plant").get(device_id=device_id)
        except DeviceConfiguration.DoesNotExist:
            raise CommandError(f"DeviceConfiguration con device_id='{device_id}' non trovato")

        broker = MQTTBroker.objects.filter(is_active=True).first()
        if not broker:
            raise CommandError("Nessun MQTTBroker attivo configurato. Esegui 'init_mqtt_broker'.")

        # Determina base topic
        base_topic = opts.get("base_topic")
        if not base_topic:
            base_topic = (device.mqtt_topic_template or "").split("/status")[0]
        if not base_topic and getattr(device, "plant", None) and getattr(device.plant, "pod_code", None):
            vendor_prefix = device.vendor.replace("_", "")
            base_topic = f"{vendor_prefix}/{device.plant.pod_code}/{device.device_id}"

        if not base_topic:
            raise CommandError(
                "Impossibile dedurre il base topic. Specificare --base-topic oppure impostare mqtt_topic_template o plant.pod_code."
            )

        # Determina credenziali (per-device preferite)
        username: Optional[str] = None
        password: Optional[str] = None
        cfg = MQTTConfiguration.objects.filter(device=device, is_active=True).first()
        if cfg:
            username = cfg.mqtt_username
            password = cfg.mqtt_password  # EncryptedCharField restituisce il valore in chiaro

        # Fallback a credenziali globali se non presenti
        if not username:
            from django.conf import settings

            username = (getattr(settings, "MQTT_SETTINGS", {}) or {}).get("USERNAME")
            password = (getattr(settings, "MQTT_SETTINGS", {}) or {}).get("PASSWORD")

        # Setup client
        client_id = f"cercollettiva-pub-{int(time.time())}"
        client = mqtt.Client(client_id=client_id, clean_session=True)
        if username:
            client.username_pw_set(username, password)
        if broker.use_tls:
            client.tls_set()

        connected = {"ok": False}

        def on_connect(c, u, flags, rc, properties=None):
            connected["ok"] = (rc == 0)

        client.on_connect = on_connect
        client.connect(broker.host, broker.port, keepalive=60)
        client.loop_start()

        # Attende connessione
        t0 = time.time()
        while not connected["ok"] and (time.time() - t0) < 5:
            time.sleep(0.1)

        if not connected["ok"]:
            client.loop_stop()
            client.disconnect()
            raise CommandError("Connessione al broker fallita (timeout)")

        self.stdout.write(self.style.SUCCESS(f"Connesso a {broker.host}:{broker.port} (TLS={broker.use_tls})"))
        self.stdout.write(f"Base topic: {base_topic}")

        # Pubblica messaggi demo
        energy_wh = 100000.0  # punto di partenza (Wh)
        for i in range(count):
            # em:0
            total_power = round(random.uniform(100.0, 2500.0), 1)
            payload_em = {
                "total_act_power": total_power,
                "total_pf": round(random.uniform(0.90, 1.00), 2),
                "a_voltage": 230.0,
                "a_current": round(total_power / 230.0, 2),
                "a_act_power": total_power,
                "b_voltage": 230.0,
                "b_current": 0.0,
                "c_voltage": 230.0,
                "c_current": 0.0,
            }
            topic_em = f"{base_topic}/status/em:0"
            client.publish(topic_em, json.dumps(payload_em), qos=qos, retain=False)
            self.stdout.write(f"→ {topic_em} {payload_em}")

            # emdata:0 (energia cumulativa in Wh)
            energy_wh += random.uniform(50.0, 500.0)
            payload_energy = {"total_act": round(energy_wh, 3)}
            topic_energy = f"{base_topic}/status/emdata:0"
            client.publish(topic_energy, json.dumps(payload_energy), qos=qos, retain=False)
            self.stdout.write(f"→ {topic_energy} {payload_energy}")

            if i < count - 1:
                time.sleep(interval)

        client.loop_stop()
        client.disconnect()
        self.stdout.write(self.style.SUCCESS("Pubblicazione demo completata"))

