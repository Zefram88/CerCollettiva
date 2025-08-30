# Specifica Topic MQTT

## Convenzioni Topic (Shelly e simili)
Base: `<vendor>/<pod_code>/<device_id>/status/...`

### Topic principali
- Potenza istantanea: `.../status/em:0`
- Energia cumulativa: `.../status/emdata:0`

Esempio:
```
SHELLY/IT001E12345678/DEV123/status/em:0
SHELLY/IT001E12345678/DEV123/status/emdata:0
```

## Mapping Topic → Device
Il `DeviceManager` determina il `DeviceConfiguration` confrontando il topic ricevuto con i template configurati dei device attivi.

## ACL (broker)
- Consentire publish al device solo sui topic assegnati al suo `device_id`.
- Deny su wildcard e su topic di altri device.

