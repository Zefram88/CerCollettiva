# energy/validators.py
"""
Validatori unificati per l'app energy
Consolida pattern di validazione duplicati in un sistema centralizzato
"""

import logging
import re
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.validators import APIValidationMixin, BaseValidator, ValidationMixin

logger = logging.getLogger(__name__)


class EnergyDataValidator(BaseValidator):
    """
    Validatore unificato per dati energetici
    Consolida validazioni per device, measurement e MQTT data
    """

    def __init__(self, field_name=None, error_message=None):
        super().__init__(field_name, error_message)
        self.validation_errors = []

    def get_default_error_message(self):
        return _("Dato energetico non valido")

    def validate_device_id(self, value, cleaned_data=None):
        """Valida ID dispositivo"""
        if not value:
            return value

        value = value.strip()
        if len(value) < 3:
            raise ValidationError(_("L'ID dispositivo deve avere almeno 3 caratteri"))

        # Verifica caratteri validi (alphanumeric + underscore + dash)
        if not re.match(r"^[A-Za-z0-9_-]+$", value):
            raise ValidationError(
                _(
                    "L'ID dispositivo può contenere solo lettere, numeri, "
                    "underscore e trattini"
                )
            )

        return value

    def validate_mqtt_topic(self, value, cleaned_data=None):
        """Valida template MQTT topic"""
        if not value:
            return value

        value = value.strip()
        if not value.startswith("/"):
            raise ValidationError(_("Il template MQTT deve iniziare con '/'"))

        # Verifica caratteri validi per MQTT topic
        if not re.match(r"^/[A-Za-z0-9_/]+$", value):
            raise ValidationError(
                _(
                    "Il template MQTT può contenere solo lettere, numeri, "
                    "underscore e slash"
                )
            )

        return value

    def validate_power(self, value, cleaned_data=None):
        """Valida misurazione potenza"""
        if value is None:
            return value

        if value < 0:
            raise ValidationError(_("La potenza non può essere negativa"))

        # Limite ragionevole per potenza (1MW)
        if abs(value) > 1000000:
            raise ValidationError(_("La potenza non può superare ±1MW"))

        return value

    def validate_voltage(self, value, cleaned_data=None):
        """Valida misurazione tensione"""
        if value is None:
            return value

        if value < 0 or value > 1000:
            raise ValidationError(_("La tensione deve essere tra 0 e 1000V"))

        return value

    def validate_current(self, value, cleaned_data=None):
        """Valida misurazione corrente"""
        if value is None:
            return value

        if value < 0:
            raise ValidationError(_("La corrente non può essere negativa"))

        # Limite ragionevole per corrente (1000A)
        if value > 1000:
            raise ValidationError(_("La corrente non può superare 1000A"))

        return value

    def validate_power_factor(self, value, cleaned_data=None):
        """Valida fattore di potenza"""
        if value is None:
            return value

        if value < -1 or value > 1:
            raise ValidationError(_("Il fattore di potenza deve essere tra -1 e 1"))

        return value

    def validate_energy_total(self, value, cleaned_data=None):
        """Valida energia totale"""
        if value is None:
            return value

        if value < 0:
            raise ValidationError(_("L'energia totale non può essere negativa"))

        return value

    def validate_phase_data(self, value, cleaned_data=None):
        """Valida dati delle fasi"""
        if not value:
            return value

        required_fields = ["voltage", "current", "power"]

        for phase, data in value.items():
            if not isinstance(data, dict):
                raise ValidationError(
                    _("I dati delle fasi devono essere un dizionario")
                )

            for field in required_fields:
                if field not in data:
                    raise ValidationError(
                        _(f"Campo '{field}' mancante per la fase '{phase}'")
                    )

                if data[field] is None:
                    raise ValidationError(
                        _(f"Campo '{field}' non può essere nullo per la fase '{phase}'")
                    )

        return value

    def validate_measurement_timestamp(self, value, cleaned_data=None):
        """Valida timestamp misurazione"""
        if not value:
            return value

        now = timezone.now()

        # Non può essere nel futuro
        if value > now:
            raise ValidationError(_("Il timestamp non può essere nel futuro"))

        # Non può essere troppo vecchio (1 anno)
        one_year_ago = now - timedelta(days=365)
        if value < one_year_ago:
            raise ValidationError(
                _("Il timestamp non può essere più vecchio di 1 anno")
            )

        return value

    def validate_date_range(self, start_date, end_date, cleaned_data=None):
        """Valida range di date"""
        if not start_date or not end_date:
            return start_date, end_date

        if end_date <= start_date:
            raise ValidationError(
                _("La data di fine deve essere successiva alla data di inizio")
            )

        # Verifica range ragionevole (max 1 anno)
        if (end_date - start_date).days > 365:
            raise ValidationError(_("Il range di date non può superare 1 anno"))

        return start_date, end_date

    def validate_period_appropriateness(
        self, period, start_date, end_date, cleaned_data=None
    ):
        """Valida appropriatezza del periodo per il range di date"""
        if not all([period, start_date, end_date]):
            return period

        time_diff = end_date - start_date

        period_limits = {
            "15M": timedelta(days=1),  # 1 giorno
            "1H": timedelta(days=7),  # 1 settimana
            "1D": timedelta(days=30),  # 1 mese
            "1W": timedelta(days=90),  # 3 mesi
            "1M": timedelta(days=365),  # 1 anno
        }

        if period in period_limits:
            if time_diff > period_limits[period]:
                raise ValidationError(
                    _(
                        f"Il periodo {period} non è appropriato per range "
                        f"superiori a {period_limits[period].days} giorni"
                    )
                )

        return period

    def validate_device_config(self, device_config, cleaned_data=None):
        """Valida configurazione dispositivo"""
        if not device_config:
            raise ValidationError(_("Configurazione dispositivo richiesta"))

        if not hasattr(device_config, "plant") or not device_config.plant:
            raise ValidationError(_("Dispositivo deve essere associato a un impianto"))

        return device_config

    def validate_plant_ownership(self, plant, user, cleaned_data=None):
        """Valida ownership dell'impianto"""
        if not plant:
            raise ValidationError(_("Impianto richiesto"))

        if not user:
            raise ValidationError(_("Utente richiesto"))

        # Staff può accedere a tutti gli impianti
        if user.is_staff:
            return plant

        # Utenti normali solo ai propri impianti
        if hasattr(plant, "owner") and plant.owner != user:
            raise ValidationError(_("Accesso negato: impianto non di proprietà"))

        return plant

    def validate_online_status(self, device_config, max_minutes=5, cleaned_data=None):
        """Valida stato online del dispositivo"""
        if not device_config:
            return False

        if not hasattr(device_config, "last_seen") or not device_config.last_seen:
            return False

        now = timezone.now()
        time_threshold = now - timedelta(minutes=max_minutes)

        return device_config.last_seen > time_threshold

    def validate_measurement_quality(self, value, cleaned_data=None):
        """Valida qualità della misurazione"""
        if not value:
            return value

        valid_qualities = ["GOOD", "FAIR", "POOR", "BAD", "UNKNOWN"]
        if value not in valid_qualities:
            raise ValidationError(
                _(
                    f"Qualità non valida. Valori consentiti: "
                    f"{', '.join(valid_qualities)}"
                )
            )

        return value

    def validate_measurement_type(self, value, cleaned_data=None):
        """Valida tipo di misurazione"""
        if not value:
            return value

        valid_types = [
            "POWER",
            "ENERGY",
            "VOLTAGE",
            "CURRENT",
            "FREQUENCY",
            "POWER_FACTOR",
        ]
        if value not in valid_types:
            raise ValidationError(
                _(
                    f"Tipo misurazione non valido. Valori consentiti: "
                    f"{', '.join(valid_types)}"
                )
            )

        return value

    def validate(self, value, cleaned_data=None):
        """Metodo principale di validazione - da implementare nelle sottoclassi"""
        raise NotImplementedError("Subclasses must implement validate method")


class DeviceDataValidator(EnergyDataValidator):
    """Validatore specifico per dati dispositivo"""

    def validate(self, data, cleaned_data=None):
        """Valida dati dispositivo completi"""
        if not isinstance(data, dict):
            raise ValidationError(_("I dati dispositivo devono essere un dizionario"))

        validated_data = {}

        # Validazione campi opzionali
        if "device_id" in data:
            validated_data["device_id"] = self.validate_device_id(
                data["device_id"], cleaned_data
            )

        if "mqtt_topic_template" in data:
            validated_data["mqtt_topic_template"] = self.validate_mqtt_topic(
                data["mqtt_topic_template"], cleaned_data
            )

        if "device_config" in data:
            validated_data["device_config"] = self.validate_device_config(
                data["device_config"], cleaned_data
            )

        return validated_data


class MeasurementDataValidator(EnergyDataValidator):
    """Validatore specifico per dati misurazione"""

    def validate(self, data, cleaned_data=None):
        """Valida dati misurazione completi"""
        if not isinstance(data, dict):
            raise ValidationError(_("I dati misurazione devono essere un dizionario"))

        validated_data = {}

        # Validazione campi numerici
        numeric_fields = {
            "power": self.validate_power,
            "voltage": self.validate_voltage,
            "current": self.validate_current,
            "power_factor": self.validate_power_factor,
            "energy_total": self.validate_energy_total,
        }

        for field, validator in numeric_fields.items():
            if field in data:
                validated_data[field] = validator(data[field], cleaned_data)

        # Validazione campi speciali
        if "timestamp" in data:
            validated_data["timestamp"] = self.validate_measurement_timestamp(
                data["timestamp"], cleaned_data
            )

        if "phase_data" in data:
            validated_data["phase_data"] = self.validate_phase_data(
                data["phase_data"], cleaned_data
            )

        if "quality" in data:
            validated_data["quality"] = self.validate_measurement_quality(
                data["quality"], cleaned_data
            )

        if "measurement_type" in data:
            validated_data["measurement_type"] = self.validate_measurement_type(
                data["measurement_type"], cleaned_data
            )

        return validated_data


class MQTTDataValidator(EnergyDataValidator):
    """Validatore specifico per dati MQTT"""

    def validate(self, data, cleaned_data=None):
        """Valida dati MQTT completi"""
        if not isinstance(data, dict):
            raise ValidationError(_("I dati MQTT devono essere un dizionario"))

        validated_data = {}

        # Validazione payload MQTT
        if "payload" in data:
            payload = data["payload"]
            if not isinstance(payload, dict):
                raise ValidationError(_("Il payload MQTT deve essere un dizionario"))

            # Validazione campi numerici nel payload
            numeric_fields = ["total_act_power", "a_voltage", "a_current", "total_pf"]
            for field in numeric_fields:
                if field in payload:
                    try:
                        validated_data[field] = float(payload[field])
                    except (ValueError, TypeError):
                        raise ValidationError(
                            _(f"Campo '{field}' deve essere numerico")
                        )

        # Validazione topic
        if "topic" in data:
            validated_data["topic"] = self.validate_mqtt_topic(
                data["topic"], cleaned_data
            )

        # Validazione device_config
        if "device_config" in data:
            validated_data["device_config"] = self.validate_device_config(
                data["device_config"], cleaned_data
            )

        return validated_data


class APIRequestValidator(EnergyDataValidator):
    """Validatore specifico per richieste API"""

    def validate(self, data, cleaned_data=None):
        """Valida richieste API complete"""
        if not isinstance(data, dict):
            raise ValidationError(_("I dati API devono essere un dizionario"))

        validated_data = {}

        # Validazione device_id
        if "device_id" in data:
            validated_data["device_id"] = self.validate_device_id(
                data["device_id"], cleaned_data
            )

        # Validazione date range
        if "start_date" in data and "end_date" in data:
            start_date, end_date = self.validate_date_range(
                data["start_date"], data["end_date"], cleaned_data
            )
            validated_data["start_date"] = start_date
            validated_data["end_date"] = end_date

        # Validazione period appropriateness
        if all(key in data for key in ["period", "start_date", "end_date"]):
            validated_data["period"] = self.validate_period_appropriateness(
                data["period"], data["start_date"], data["end_date"], cleaned_data
            )

        # Validazione ownership
        if "plant" in data and "user" in data:
            validated_data["plant"] = self.validate_plant_ownership(
                data["plant"], data["user"], cleaned_data
            )

        return validated_data


# Validatori predefiniti per uso comune
DEVICE_VALIDATOR = DeviceDataValidator()
MEASUREMENT_VALIDATOR = MeasurementDataValidator()
MQTT_VALIDATOR = MQTTDataValidator()
API_REQUEST_VALIDATOR = APIRequestValidator()


class EnergyValidationMixin(ValidationMixin):
    """Mixin per validazione energetica standardizzata"""

    def validate_energy_data(self, data, validator_type="measurement"):
        """Valida dati energetici usando il validator appropriato"""
        validators = {
            "device": DEVICE_VALIDATOR,
            "measurement": MEASUREMENT_VALIDATOR,
            "mqtt": MQTT_VALIDATOR,
            "api": API_REQUEST_VALIDATOR,
        }

        validator = validators.get(validator_type, MEASUREMENT_VALIDATOR)

        try:
            return validator.validate(
                data, self.cleaned_data if hasattr(self, "cleaned_data") else None
            )
        except ValidationError as e:
            self.add_validation_error("energy_data", str(e))
            return None

    def validate_device_ownership(self, device, user):
        """Valida ownership del dispositivo"""
        try:
            return DEVICE_VALIDATOR.validate_plant_ownership(device.plant, user)
        except ValidationError as e:
            self.add_validation_error("device", str(e))
            return None

    def validate_online_status(self, device, max_minutes=5):
        """Valida stato online del dispositivo"""
        return DEVICE_VALIDATOR.validate_online_status(device, max_minutes)


class EnergyAPIValidationMixin(APIValidationMixin):
    """Mixin per validazione API energetica standardizzata"""

    def validate_energy_request(self, request_data):
        """Valida richiesta API energetica"""
        try:
            return API_REQUEST_VALIDATOR.validate(request_data)
        except ValidationError as e:
            logger.warning(f"API energy validation failed: {str(e)}")
            return None

    def get_energy_validation_errors(self):
        """Restituisce errori di validazione energetica in formato API"""
        base_errors = self.get_validation_errors()

        return {**base_errors, "energy_validation": True, "validator_version": "1.0"}
