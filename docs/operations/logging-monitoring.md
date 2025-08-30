# Logging e Monitoring

## Logging
- Configurato via `LOGGING` nei settings (local/production specifici).
- Evitare handler creati a runtime (es. in `users/signals.py`): centralizzare nei settings.
- File principali:
  - App generale: `logs/cercollettiva.log`
  - MQTT: `logs/mqtt.log`
  - Documents/Gaudi: `logs/documents.log`, `logs/gaudi.log`

### Linee Guida
- Livelli: INFO per eventi business, WARNING/ERROR per anomalie; DEBUG solo in debugging local.
- Mascherare POD/device_id nei log (già previsto in vari servizi) per GDPR.

## Monitoring / Health
- Endpoints in `monitoring/urls.py`:
  - `/monitoring/health/`
  - `/monitoring/health/database/`
  - `/monitoring/health/mqtt/`
  - `/monitoring/health/cache/`
  - `/monitoring/health/system/`
  - `/monitoring/status/` (aggregato)
  - `/monitoring/metrics/` (Prometheus-style se implementato)

### Metriche MQTT suggerite
- Messaggi ricevuti totali e per device_type
- Errori decoding/persistenza
- Tempo medio processing

