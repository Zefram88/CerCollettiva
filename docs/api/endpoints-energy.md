# Energy API (DRF)

Router base: `/energy/api/` e `/api/energy/`

## PlantViewSet
- CRUD piante
- GET /plants/{id}/statistics/ — potenza corrente, dispositivi attivi/totali, produzione daily/monthly
- GET /plants/{id}/device_status/ — stato dettagliato dispositivi

## DeviceConfigurationViewSet
- CRUD dispositivi
- GET /devices/{id}/latest_measurement/ — ultima misurazione

## DeviceMeasurementViewSet
- List/filtri/ordinamento
- GET /measurements/latest/?device_id=DEV123 — ultima per device

### Filtri (principali)
- `start_date`, `end_date`, `power_min`, `power_max`, `device_id`, `plant_id`, `plant_name`

