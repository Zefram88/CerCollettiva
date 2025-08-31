# Scripts

Questa directory contiene gli script di gestione del server:

- `logs.sh` - Visualizza i log dell'applicazione
- `restart.sh` - Riavvia il server
- `rundev.sh` - Avvia il server di sviluppo (Linux/macOS)
- `rundev.ps1` - Avvia il server di sviluppo (Windows PowerShell)
- `check.sh` - Esegue `manage.py check` e `migrate` (Linux/macOS)
- `check.ps1` - Esegue `manage.py check` e `migrate` (Windows PowerShell)
- `start_gunicorn.sh` - Avvia il server Gunicorn per produzione
- `update.sh` - Aggiorna il progetto

Esempi d'uso:

- Unix: `bash scripts/rundev.sh --bind 127.0.0.1 --port 8000`
- Windows: `pwsh scripts/rundev.ps1 -BindAddress 127.0.0.1 -Port 8000`
 - Unix (sanity check + migrazioni): `bash scripts/check.sh`
 - Windows (sanity check + migrazioni): `pwsh scripts/check.ps1`
