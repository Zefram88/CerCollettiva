# Documentazione CerCollettiva

Questa directory contiene tutta la documentazione del progetto CerCollettiva.

## Struttura

- **install/** - Script e guide per l'installazione
  - `install_updated.sh` - Script di installazione per produzione
  - `install.sh` - Script di installazione originale
  - `install_wsl_debian.sh` - Script per WSL/Debian
  - `disinstalla_cercollettiva.sh` - Script di disinstallazione

- **CODE_OF_CONDUCT.md** - Codice di condotta per i contributori

## Guide principali

### Per sviluppatori
- [CLAUDE.md](../CLAUDE.md) - Guida per lo sviluppo con Claude AI
- [README.md](../README.md) - Documentazione principale del progetto

### Per l'installazione
- **Sviluppo locale**: Usa lo script `install_dev.sh` nella root del progetto
- **Produzione**: Usa lo script `install/install_updated.sh`

## Documentazione tecnica

### Architettura del sistema
CerCollettiva è basato su Django 5.0 e utilizza:
- PostgreSQL per il database in produzione
- MQTT per la comunicazione con dispositivi IoT
- Django Channels per WebSocket
- Redis per cache e messaggistica real-time

### API Documentation
La documentazione delle API REST è disponibile all'endpoint `/api/docs/` quando il server è in esecuzione.

### Modelli dati
- **CER**: Gestione delle Comunità Energetiche
- **Plant**: Impianti di produzione energia
- **Measurement**: Misurazioni energetiche
- **Device**: Dispositivi IoT

## Contribuire alla documentazione

Per contribuire alla documentazione:
1. Segui le linee guida nel [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
2. Usa Markdown per tutti i documenti
3. Mantieni la struttura delle directory esistente
4. Aggiorna questo README quando aggiungi nuovi documenti