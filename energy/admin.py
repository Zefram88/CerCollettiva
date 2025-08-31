# energy/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    DeviceMeasurement, 
    DeviceMeasurementDetail,
    EnergyMeasurement,
    EnergyAggregate,
    EnergyInterval,
    DeviceConfiguration,
    MQTTBroker,
    MQTTConfiguration,
)
from .models.device import DeviceType, Device

@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'model', 'is_active']
    list_filter = ['vendor', 'is_active']
    search_fields = ['name', 'vendor', 'model']
    fieldsets = (
        (None, {
            'fields': ('name', 'vendor', 'model', 'description', 'is_active')
        }),
        ('Misure Supportate', {
            'fields': (
                'supports_voltage', 'supports_current', 'supports_power',
                'supports_energy', 'supports_frequency', 'supports_power_factor'
            )
        }),
        ('Configurazione MQTT', {
            'fields': ('mqtt_topic_template', 'mqtt_payload_format')
        })
    )

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'device_type', 'serial_number', 'is_active']
    list_filter = ['device_type', 'is_active', 'installation_date']
    search_fields = ['name', 'serial_number']
    date_hierarchy = 'installation_date'
    raw_id_fields = ['device_type']

class DeviceMeasurementDetailInline(admin.TabularInline):
    model = DeviceMeasurementDetail
    extra = 0
    readonly_fields = ['apparent_power', 'reactive_power']
    can_delete = False

@admin.register(DeviceMeasurement)
class DeviceMeasurementAdmin(admin.ModelAdmin):
    list_display = [
        'device_id', 
        'plant_name',
        'power_display',
        'voltage',
        'current',
        'quality',
        'timestamp'
    ]
    list_filter = ['quality', 'device', 'plant']
    search_fields = ['device__device_id', 'plant__name']
    date_hierarchy = 'timestamp'
    readonly_fields = ['apparent_power', 'reactive_power']
    inlines = [DeviceMeasurementDetailInline]

    def device_id(self, obj):
        return obj.device.device_id
    device_id.short_description = "Device ID"

    def plant_name(self, obj):
        return obj.plant.name
    plant_name.short_description = "Plant"

    def power_display(self, obj):
        color = 'green' if obj.power >= 0 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f} W</span>',
            color, obj.power
        )
    power_display.short_description = "Power"

@admin.register(EnergyInterval)
class EnergyIntervalAdmin(admin.ModelAdmin):
    list_display = [
        'device_id',
        'start_time',
        'end_time',
        'energy_value',
        'interval_duration',
        'is_valid_interval'
    ]
    list_filter = ['device', 'start_time']
    search_fields = ['device__device_id']
    date_hierarchy = 'start_time'
    readonly_fields = ['interval_duration', 'is_valid_interval', 'created_at']

    def device_id(self, obj):
        return obj.device.device_id
    device_id.short_description = "Device ID"

    def interval_duration(self, obj):
        return f"{obj.interval_duration} min"
    interval_duration.short_description = "Durata"

@admin.register(EnergyMeasurement)
class EnergyMeasurementAdmin(admin.ModelAdmin):
    list_display = [
        'measurement_type',
        'value_display',
        'unit',
        'quality',
        'device_id',
        'timestamp'
    ]
    list_filter = ['measurement_type', 'unit', 'quality']
    search_fields = ['device_measurement__device__device_id']
    date_hierarchy = 'timestamp'

    def device_id(self, obj):
        return obj.device_measurement.device.device_id
    device_id.short_description = "Device ID"

    def value_display(self, obj):
        return f"{obj.value:.2f}"
    value_display.short_description = "Value"

@admin.register(EnergyAggregate)
class EnergyAggregateAdmin(admin.ModelAdmin):
    list_display = [
        'device_id',
        'period',
        'start_time',
        'energy_in',
        'energy_out',
        'net_energy',
        'peak_power'
    ]
    list_filter = ['period', 'device']
    search_fields = ['device__device_id']
    date_hierarchy = 'start_time'
    readonly_fields = ['net_energy']

    def device_id(self, obj):
        return obj.device.device_id
    device_id.short_description = "Device ID"

@admin.register(MQTTBroker)
class MQTTBrokerAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'host',
        'port',
        'is_active',
        'use_tls',
        'created_at',
        'updated_at'
    ]
    list_filter = ['is_active', 'use_tls', 'verify_cert']
    search_fields = ['name', 'host']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'is_active')
        }),
        ('Connection Settings', {
            'fields': ('host', 'port', 'username', 'password')
        }),
        ('Security', {
            'fields': ('use_tls', 'verify_cert', 'ca_cert')
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MQTTConfiguration)
class MQTTConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'device_id',
        'mqtt_username',
        'is_active',
        'last_connected',
        'updated_at'
    ]
    list_filter = ['is_active', 'last_connected']
    search_fields = ['mqtt_username', 'device__device_id']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Device', {
            'fields': ('device',)
        }),
        ('Credentials', {
            'fields': ('mqtt_username', 'mqtt_password', 'is_active')
        }),
        ('Status', {
            'fields': ('last_connected', 'created_at', 'updated_at')
        }),
    )

    def device_id(self, obj):
        return obj.device.device_id if obj.device else None
    device_id.short_description = "Device ID"
