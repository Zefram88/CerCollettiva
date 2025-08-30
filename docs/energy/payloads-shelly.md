# Payload Shelly — Schema Atteso

## em:0 (potenza e parametri istantanei)
Esempio (JSON):
```json
{
  "total_act_power": 1234.5,
  "total_pf": 0.97,
  "a_voltage": 230.1,
  "a_current": 5.4,
  "a_act_power": 1240.0,
  "b_voltage": 229.8,
  "b_current": 0.0,
  "c_voltage": 229.9,
  "c_current": 0.0
}
```

Mapping → `DeviceMeasurement` e `DeviceMeasurementDetail` per fase (se presenti).

## emdata:0 (energia cumulativa)
Esempio (JSON):
```json
{
  "total_act": 123456.0
}
```

Il servizio calcola il delta (Wh → kWh) rispetto alla lettura precedente e salva l’intervallo energetico.

## Validazioni
- Range plausibili: potenza ±1MW, tensione 0–500V, corrente ±1000A, PF [-1..1].
- Timestamp decodificato o generato lato server; deduplica via cache su (topic, device, hash payload).

