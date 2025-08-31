# OTA (Over‑the‑Air) Update – Analisi di Fattibilità

Questo documento riassume l’analisi di fattibilità per abilitare aggiornamenti OTA dei dispositivi IoT integrati nella piattaforma CerCollettiva.

## Sintesi

- Fattibilità: alta. La piattaforma ha già integrazione MQTT, ACL per topic per‑device e registry dispositivi.
- Richieste: modelli per artefatti firmware, API manifest/progress, topic MQTT di controllo e progress.
- Vendor supportati: Tasmota e Shelly espongono meccanismi OTA nativi; per device custom si implementa OTA via HTTPS + firma.

## Architettura Proposta

- Server:
  - Hosting artefatti (media/S3) con URL presignati/HTTPS,
  - API manifest (versione, URL, checksum/firma) e progress,
  - Pubblicazione comandi OTA via MQTT su topic per‑device,
  - Audit/log aggiornamenti e rollout per fasi.
- Dispositivo:
  - Download resiliente, verifica firma/checksum,
  - Applicazione update (A/B e rollback),
  - Pubblicazione progress e stato finale su MQTT.

## Estensioni Backend (minime)

- Modelli: `FirmwareArtifact` (vendor, modello, versione, file, sha256, firma, note) e `FirmwareRollout` (targeting/staged),
- Campi su `DeviceConfiguration`: `current_fw`, `desired_fw`, `last_ota_status`, `ota_policy`,
- API: endpoint manifest (GET) e progress (POST),
- MQTT: comandi su `cercollettiva/<owner>/<device_id>/cmd/ota` con payload `{url, sha256, sig, version}`,
  progress su `.../status/ota` con `{state, progress, error?}`.

## Vendor Note

- Tasmota: `cmnd/<topic>/OtaUrl <url>` e `cmnd/<topic>/Upgrade 1`.
- Shelly (Gen2/Pro): RPC `Shelly.Update` o `GET /ota?url=<url>`.
- Custom (ESP32): ESP‑IDF OTA con verifica Ed25519 e slot A/B.

## Sicurezza e Affidabilità

- Firma artefatti (Ed25519/ECDSA), anti‑downgrade,
- HTTPS obbligatorio, URL presignati, autenticazione API,
- A/B e watchdog di boot per rollback automatico,
- Canary/staged rollout e rate‑limit comandi OTA.

## Roadmap (MVP)

1. Modelli e admin upload,
2. API manifest + URL presignato,
3. Topic MQTT comando/progress + handler,
4. Integrazione Tasmota/Shelly + test,
5. Staged rollout e dashboard.

