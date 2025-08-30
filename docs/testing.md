# Strategia di Testing

## Unit Test
- Utils energia: filtri/aggregazioni/cache
- Modelli core: `Plant.get_total_power`, `MembershipCard` e `MemberRegistry`
- Documenti: validazioni GDPR/retention

## Integrazione MQTT (ambiente esistente)
- Usare Mosquitto già disponibile.
- Script che pubblica payload esempio su topic device e verifica:
  - Creazione `DeviceMeasurement` e `DeviceMeasurementDetail`
  - Aggiornamento `last_seen`
  - Delta energia per `emdata:0`

## Regressione API
- Smoke test endpoints principali (core e DRF) con utente autenticato.

