# CerCollettiva

Software open source per la gestione delle comunità energetiche

CerCollettiva è un software open source progettato per semplificare la creazione e la gestione delle Comunità Energetiche Rinnovabili (CER) e delle Comunità Energetiche dei Cittadini (CEC) in Italia. Il software è conforme alle normative vigenti, in particolare al Decreto CACER e al TIAD, e si propone di:

- **Semplificare l'adesione alle CER e CEC**, guidando gli utenti attraverso i requisiti normativi e le procedure amministrative.
- **Ottimizzare la gestione degli impianti di produzione di energia rinnovabile**, l'acquisizione e l'analisi dei dati di misura, il calcolo degli incentivi e dei contributi, e la rendicontazione delle attività.
- **Promuovere la partecipazione attiva** dei cittadini, delle imprese e degli enti locali alla transizione energetica.
- **Garantire la conformità normativa** delle attività delle CER e CEC.
- **Massimizzare i benefici economici** derivanti dagli incentivi e dai contributi previsti dalla normativa.
- **Contribuire alla sostenibilità** promuovendo la produzione e l'autoconsumo di energia da fonti rinnovabili.

## Caratteristiche principali

- Registrazione e profilazione utenti
- Verifica automatica dei requisiti
- Costituzione guidata delle CER/CEC
- Gestione impianti e misure
- Calcolo incentivi e contributi
- Amministrazione e reporting
- Gestione delle domande di contributo PNRR

![Home Page](https://github.com/atomozero/CerCollettiva/blob/main/screenshot/homepage%20V.A.2.png)

## Tecnologie utilizzate

- **Linguaggio**: Python 3.11+
- **Framework**: Django 5.0
- **Database**: PostgreSQL (produzione) / SQLite (sviluppo)
- **Broker MQTT**: Mosquitto per IoT
- **WebSocket**: Django Channels
- **Cache**: Redis
- **Frontend**: Bootstrap 5, Chart.js

## Requisiti di sistema

- Python 3.11 o superiore
- PostgreSQL 14+ (per produzione)
- Redis (opzionale, per cache e WebSocket)
- Mosquitto MQTT broker (opzionale, per dispositivi IoT)

## Installazione

### Sviluppo locale (Quick Start)

```bash
# Clona il repository
git clone https://github.com/atomozero/CerCollettiva.git
cd CerCollettiva

# Esegui lo script di installazione per sviluppo
chmod +x install_dev.sh
./install_dev.sh

# Avvia il server di sviluppo
./runserver.sh
```

Accedi a:
- Applicazione: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/ceradmin/

### Installazione in produzione

Per l'installazione in ambiente di produzione con Nginx, Gunicorn e PostgreSQL:

```bash
cd docs/install
chmod +x install_updated.sh
./install_updated.sh
```

Lo script guiderà attraverso la configurazione di:
- Database PostgreSQL
- Server web Nginx
- WSGI server Gunicorn
- SSL/HTTPS con Certbot
- Firewall e sicurezza

### Installazione manuale

Se preferisci installare manualmente:

```bash
# Crea ambiente virtuale
python3 -m venv venv
source venv/bin/activate

# Installa dipendenze
pip install -r app/requirements.txt

# Configura il database
python manage.py migrate

# Crea superuser
python manage.py createsuperuser

# Avvia il server
python manage.py runserver
```

## Struttura del progetto

```
CerCollettiva/
├── cercollettiva/       # Configurazioni Django principali
├── core/                # App principale CER management
├── energy/              # Gestione dispositivi IoT e misure energetiche
├── documents/           # Gestione documenti e GAUDI
├── users/               # Autenticazione e profili utente
├── templates/           # Template HTML
├── static/              # File statici (CSS, JS, immagini)
├── media/               # File caricati dagli utenti
├── scripts/             # Script di gestione server
├── utilities/           # Utility Python
├── docs/                # Documentazione
│   └── install/         # Script di installazione
├── venv/                # Ambiente virtuale Python
├── manage.py            # Django management script
└── .env                 # Configurazione ambiente (non versionato)
```

## Documentazione

- [CLAUDE.md](CLAUDE.md) - Guida per lo sviluppo con Claude AI
- [CODE_OF_CONDUCT.md](docs/CODE_OF_CONDUCT.md) - Codice di condotta
- [LICENSE](LICENSE) - Licenza MIT

## Script di utilità

Dopo l'installazione, sono disponibili diversi script di utilità:

- `./runserver.sh` - Avvia il server di sviluppo
- `./migrate.sh` - Esegui le migrazioni del database
- `./shell.sh` - Apri shell Django interattiva
- `scripts/logs.sh` - Visualizza i log
- `scripts/restart.sh` - Riavvia i servizi (produzione)

## Contributi

CerCollettiva è un progetto open source e accetta contributi da parte della community. Se vuoi contribuire:

1. Fork il repository
2. Crea un branch per la tua feature (`git checkout -b feature/AmazingFeature`)
3. Commit le tue modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

Prima di contribuire, leggi il [Codice di Condotta](docs/CODE_OF_CONDUCT.md).

## Supporto

Per problemi o domande:
- Apri una [Issue su GitHub](https://github.com/atomozero/CerCollettiva/issues)
- Consulta la [documentazione](docs/)
- Contatta il team di sviluppo

## Licenza

CerCollettiva è rilasciato sotto licenza MIT. Vedi il file [LICENSE](LICENSE) per i dettagli.
