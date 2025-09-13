# energy/api/serializers.py
from django.core.exceptions import ValidationError

from rest_framework import serializers

# from ..devices.models import DeviceConfiguration
from core.models import Plant  # Import diretto da core
from core.validators import (
    POD_VALIDATOR,
    POWER_VALIDATOR,
    APIValidationMixin,
    ValidationMixin,
)

from ..models import (
    DeviceConfiguration,
    DeviceMeasurement,
    DeviceMeasurementDetail,
    EnergyAggregate,
    EnergyMeasurement,
)
from ..validators import (  # EnergyAPIValidationMixin,; EnergyValidationMixin,
    API_REQUEST_VALIDATOR,
    DEVICE_VALIDATOR,
    MEASUREMENT_VALIDATOR,
)


class PlantSerializer(serializers.ModelSerializer, ValidationMixin, APIValidationMixin):
    device_count = serializers.SerializerMethodField()

    class Meta:
        model = Plant
        fields = [
            "id",
            "name",
            "pod_code",
            "plant_type",
            "owner",
            "cer_configuration",
            "nominal_power",
            "connection_voltage",
            "installation_date",
            "address",
            "city",
            "zip_code",
            "province",
            "is_active",
            "mqtt_connected",
            "created_at",
            "updated_at",
            "device_count",
        ]
        read_only_fields = [
            "owner",
            "mqtt_connected",
            "created_at",
            "updated_at",
            "device_count",
        ]

    def validate_pod_code(self, value):
        """Validate POD code using centralized validator"""
        if value:
            return POD_VALIDATOR(value)
        return value

    def validate_nominal_power(self, value):
        """Validate nominal power using centralized validator"""
        if value is not None:
            return POWER_VALIDATOR(value)
        return value

    def validate(self, data):
        """Additional cross-field validation"""
        # Validate required fields based on plant type
        if data.get("plant_type") == "PRODUCER" and not data.get("nominal_power"):
            self.add_validation_error(
                "nominal_power",
                "La potenza nominale è obbligatoria per impianti di produzione",
            )

        return data

    def get_device_count(self, obj):
        return obj.devices.count() if hasattr(obj, "devices") else 0

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Aggiungi il plant_type in formato display
        data["plant_type_display"] = instance.get_plant_type_display()
        # Se l'istanza ha una CER configurata, includi il suo nome
        if instance.cer_configuration:
            data["cer_configuration_name"] = instance.cer_configuration.name
        return data


class DeviceConfigurationSerializer(serializers.ModelSerializer):
    plant = PlantSerializer(read_only=True)

    class Meta:
        model = DeviceConfiguration
        fields = [
            "id",
            "device_id",
            "device_type",
            "vendor",
            "model",
            "mqtt_topic_template",
            "is_active",
            "plant",
            "last_seen",
        ]

    def validate_device_id(self, value):
        """Validate device ID format using unified validator"""
        return DEVICE_VALIDATOR.validate_device_id(value, self.cleaned_data)

    def validate_mqtt_topic_template(self, value):
        """Validate MQTT topic template format using unified validator"""
        return DEVICE_VALIDATOR.validate_mqtt_topic(value, self.cleaned_data)


class DeviceMeasurementDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceMeasurementDetail
        fields = [
            "phase",
            "voltage",
            "current",
            "power",
            "power_factor",
            "frequency",
            "apparent_power",
            "reactive_power",
        ]


class DeviceMeasurementSerializer(serializers.ModelSerializer):
    phase_details = DeviceMeasurementDetailSerializer(many=True, read_only=True)
    device_detail = DeviceConfigurationSerializer(source="device", read_only=True)
    apparent_power = serializers.FloatField(read_only=True)
    reactive_power = serializers.FloatField(read_only=True)

    class Meta:
        model = DeviceMeasurement
        fields = [
            "id",
            "timestamp",
            "power",
            "voltage",
            "current",
            "energy_total",
            "power_factor",
            "quality",
            "phase_details",
            "apparent_power",
            "reactive_power",
            "device",
            "plant",
            "measurement_type",
            "device_detail",
        ]

    def validate_power(self, value):
        """Validate power measurement using unified validator"""
        return MEASUREMENT_VALIDATOR.validate_power(value, self.initial_data)

    def validate_voltage(self, value):
        """Validate voltage measurement using unified validator"""
        return MEASUREMENT_VALIDATOR.validate_voltage(value, self.initial_data)

    def validate_current(self, value):
        """Validate current measurement using unified validator"""
        return MEASUREMENT_VALIDATOR.validate_current(value, self.initial_data)

    def validate_power_factor(self, value):
        """Validate power factor using unified validator"""
        return MEASUREMENT_VALIDATOR.validate_power_factor(value, self.initial_data)


class EnergyMeasurementSerializer(serializers.ModelSerializer):
    device = serializers.CharField(source="device_measurement.device.device_id")
    plant = serializers.CharField(source="device_measurement.plant.name")

    class Meta:
        model = EnergyMeasurement
        fields = [
            "id",
            "timestamp",
            "measurement_type",
            "value",
            "unit",
            "quality",
            "device",
            "plant",
        ]


class EnergyAggregateSerializer(serializers.ModelSerializer):
    device = DeviceConfigurationSerializer(read_only=True)
    net_energy = serializers.FloatField(read_only=True)

    class Meta:
        model = EnergyAggregate
        fields = [
            "id",
            "period",
            "start_time",
            "end_time",
            "energy_in",
            "energy_out",
            "peak_power",
            "avg_power",
            "net_energy",
            "device",
        ]


# Serializzatori per richieste specifiche
class EnergyAggregateRequestSerializer(serializers.Serializer):
    device_id = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    period = serializers.ChoiceField(
        choices=["15M", "1H", "1D", "1W", "1M"], default="1H"
    )

    def validate_device_id(self, value):
        """Validate device ID format using unified validator"""
        return API_REQUEST_VALIDATOR.validate_device_id(value, self.cleaned_data)

    def validate(self, data):
        """Validate date range and period consistency using unified validator"""
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        period = data.get("period")

        if start_date and end_date:
            # Use unified validator for date range validation
            try:
                API_REQUEST_VALIDATOR.validate_date_range(start_date, end_date, data)
            except ValidationError as e:
                self.add_validation_error("end_date", str(e))

            # Use unified validator for period appropriateness
            if period:
                try:
                    API_REQUEST_VALIDATOR.validate_period_appropriateness(
                        period, start_date, end_date, data
                    )
                except ValidationError as e:
                    self.add_validation_error("period", str(e))

        return data
