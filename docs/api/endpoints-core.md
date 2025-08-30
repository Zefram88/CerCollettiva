# Core API Endpoints

Base path: vedi `core/urls.py`

## GET /core/api/plants/{pk}/data/
- Ritorna serie potenza (W), daily energy, info impianto
- Query: `hours` (max 48), `interval`

## GET /core/api/plants/{plant_id}/measurements/
- Serie completa: `timestamp`, `power`, `voltage`, `current`, `energy_total`, `quality`
- Query: `hours` (max 48)

## GET /core/api/cer-power/
- Potenze aggregate (kW) per CER accessibili all’utente: producer/consumer/net

## GET /core/api/mqtt/status/{plant_id}/
- Stato connessione MQTT (connected, last_seen) per impianto

