#energy/views/debug_views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from ..models import DeviceConfiguration


@login_required
def debug_device_status(request):
    devices = DeviceConfiguration.objects.filter(
        plant__name="Bernardi Srl"
    ).values('id', 'device_id', 'is_active', 'plant__name')
    return JsonResponse({'devices': list(devices)})

@login_required
def debug_mqtt_config(request):
    from ..models import DeviceConfiguration
    configs = DeviceConfiguration.objects.filter(is_active=True)
    return JsonResponse({
        'active_configs': list(configs.values('device_id', 'mqtt_topic_template', 'is_active')),
        'total_configs': DeviceConfiguration.objects.count()
    })