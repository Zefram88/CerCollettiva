# Script di setup automatico per CerCollettiva (PowerShell)
# Questo script configura l'ambiente di sviluppo completo su Windows

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("local", "docker", "production")]
    [string]$SetupType = "local"
)

# Configurazione
$ErrorActionPreference = "Stop"

# Funzioni per logging
function Write-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# Banner
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║                    CerCollettiva Setup                       ║" -ForegroundColor Blue
Write-Host "║              Sistema di gestione CER/CEC                     ║" -ForegroundColor Blue
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# Verifica prerequisiti
Write-Log "Verifica prerequisiti..."

# Python 3.11+
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+\.\d+)") {
        $version = [version]$matches[1]
        if ($version -ge [version]"3.11") {
            Write-Success "Python $($matches[1]) trovato"
        } else {
            Write-Error "Python 3.11+ richiesto, trovato $($matches[1])"
            exit 1
        }
    } else {
        Write-Error "Python non trovato"
        exit 1
    }
} catch {
    Write-Error "Python non trovato"
    exit 1
}

# pip
try {
    pip --version | Out-Null
    Write-Success "pip trovato"
} catch {
    Write-Error "pip non trovato"
    exit 1
}

# Git
try {
    git --version | Out-Null
    Write-Success "Git trovato"
} catch {
    Write-Error "Git non trovato"
    exit 1
}

# Docker (opzionale)
$dockerAvailable = $false
try {
    docker --version | Out-Null
    Write-Success "Docker trovato"
    $dockerAvailable = $true
} catch {
    Write-Warning "Docker non trovato (opzionale per sviluppo)"
}

# Docker Compose (opzionale)
$dockerComposeAvailable = $false
try {
    docker-compose --version | Out-Null
    Write-Success "Docker Compose trovato"
    $dockerComposeAvailable = $true
} catch {
    Write-Warning "Docker Compose non trovato (opzionale per sviluppo)"
}

Write-Host ""

# Verifica modalità di setup
if ($SetupType -eq "docker" -and (-not $dockerAvailable -or -not $dockerComposeAvailable)) {
    Write-Error "Docker e Docker Compose richiesti per la modalità Docker"
    exit 1
}

Write-Log "Setup modalità: $SetupType"

# Crea ambiente virtuale
Write-Log "Creazione ambiente virtuale Python..."
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Success "Ambiente virtuale creato"
} else {
    Write-Warning "Ambiente virtuale già esistente"
}

# Attiva ambiente virtuale
Write-Log "Attivazione ambiente virtuale..."
& "venv\Scripts\Activate.ps1"
Write-Success "Ambiente virtuale attivato"

# Aggiorna pip
Write-Log "Aggiornamento pip..."
python -m pip install --upgrade pip
Write-Success "pip aggiornato"

# Installa dipendenze
Write-Log "Installazione dipendenze Python..."
pip install -r requirements.txt
Write-Success "Dipendenze installate"

# Configurazione ambiente
Write-Log "Configurazione variabili d'ambiente..."

if (-not (Test-Path ".env")) {
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Success "File .env creato da template"
    } else {
        Write-Warning "File env.example non trovato, creazione .env manuale"
        $secretKey = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
        $encryptionKey = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        
        $envContent = @"
DEBUG=True
SECRET_KEY=$secretKey
FIELD_ENCRYPTION_KEY=$encryptionKey
DB_NAME=cercollettiva
DB_USER=cercollettiva_user
DB_PASSWORD=cercollettiva_pass
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/1
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USER=mqtt_user
MQTT_PASS=mqtt_pass
"@
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-Success "File .env creato con valori di default"
    }
} else {
    Write-Warning "File .env già esistente"
}

# Configurazione specifica per modalità
switch ($SetupType) {
    "local" {
        Write-Log "Configurazione per sviluppo locale..."
        (Get-Content ".env") -replace "DEBUG=False", "DEBUG=True" | Set-Content ".env"
        (Get-Content ".env") -replace "DB_NAME=cercollettiva", "DB_NAME=db.sqlite3" | Set-Content ".env"
        Write-Success "Configurazione locale completata"
    }
    "docker" {
        Write-Log "Configurazione per Docker..."
        (Get-Content ".env") -replace "DB_HOST=localhost", "DB_HOST=db" | Set-Content ".env"
        (Get-Content ".env") -replace "REDIS_URL=redis://localhost:6379/1", "REDIS_URL=redis://:redis_pass@redis:6379/1" | Set-Content ".env"
        (Get-Content ".env") -replace "MQTT_HOST=localhost", "MQTT_HOST=mqtt" | Set-Content ".env"
        Write-Success "Configurazione Docker completata"
    }
    "production" {
        Write-Log "Configurazione per produzione..."
        (Get-Content ".env") -replace "DEBUG=True", "DEBUG=False" | Set-Content ".env"
        Write-Warning "Ricorda di configurare SECRET_KEY e password per produzione!"
        Write-Success "Configurazione produzione completata"
    }
}

# Setup database
Write-Log "Setup database..."

switch ($SetupType) {
    "local" {
        Write-Log "Esecuzione migrazioni SQLite..."
        python manage.py migrate
        Write-Success "Database SQLite configurato"
    }
    "docker" {
        Write-Log "Avvio servizi Docker..."
        docker-compose up -d db redis mqtt
        Write-Log "Attesa servizi..."
        Start-Sleep -Seconds 10
        Write-Log "Esecuzione migrazioni PostgreSQL..."
        python manage.py migrate
        Write-Success "Database PostgreSQL configurato"
    }
    "production" {
        Write-Log "Esecuzione migrazioni PostgreSQL..."
        python manage.py migrate
        Write-Success "Database PostgreSQL configurato"
    }
}

# Creazione superuser
Write-Log "Creazione superuser..."
Write-Host ""
Write-Host "Creazione account amministratore:"
python manage.py createsuperuser
Write-Success "Superuser creato"

# Raccolta file statici
Write-Log "Raccolta file statici..."
python manage.py collectstatic --noinput
Write-Success "File statici raccolti"

# Creazione directory necessarie
Write-Log "Creazione directory necessarie..."
New-Item -ItemType Directory -Force -Path "logs", "media", "staticfiles" | Out-Null
Write-Success "Directory create"

# Setup MQTT (se non Docker)
if ($SetupType -ne "docker") {
    Write-Log "Configurazione MQTT..."
    Write-Warning "Ricorda di installare e configurare Mosquitto MQTT broker"
    Write-Warning "Configurazione: config/mosquitto/mosquitto.conf"
}

# Setup monitoring
Write-Log "Configurazione monitoring..."
if ($SetupType -eq "docker") {
    Write-Log "Avvio servizi monitoring..."
    docker-compose up -d prometheus grafana
    Write-Success "Monitoring configurato"
} else {
    Write-Warning "Monitoring disponibile solo con Docker"
}

# Test configurazione
Write-Log "Test configurazione..."
python manage.py check
Write-Success "Configurazione Django verificata"

# Avvio servizi
Write-Host ""
Write-Log "Setup completato con successo!"
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    Setup Completato!                        ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

switch ($SetupType) {
    "local" {
        Write-Host "Per avviare il server di sviluppo:" -ForegroundColor Blue
        Write-Host "  venv\Scripts\Activate.ps1"
        Write-Host "  python manage.py runserver"
        Write-Host ""
        Write-Host "Accesso:" -ForegroundColor Blue
        Write-Host "  Applicazione: http://127.0.0.1:8000/"
        Write-Host "  Admin: http://127.0.0.1:8000/ceradmin/"
    }
    "docker" {
        Write-Host "Per avviare tutti i servizi:" -ForegroundColor Blue
        Write-Host "  docker-compose up -d"
        Write-Host ""
        Write-Host "Per avviare solo l'applicazione:" -ForegroundColor Blue
        Write-Host "  venv\Scripts\Activate.ps1"
        Write-Host "  python manage.py runserver"
        Write-Host ""
        Write-Host "Accesso:" -ForegroundColor Blue
        Write-Host "  Applicazione: http://127.0.0.1:8000/"
        Write-Host "  Admin: http://127.0.0.1:8000/ceradmin/"
        Write-Host "  Grafana: http://127.0.0.1:3000/ (admin/admin)"
        Write-Host "  Prometheus: http://127.0.0.1:9090/"
    }
    "production" {
        Write-Host "Per avviare in produzione:" -ForegroundColor Blue
        Write-Host "  gunicorn --bind 0.0.0.0:8000 cercollettiva.wsgi:application"
        Write-Host ""
        Write-Host "O con Docker:" -ForegroundColor Blue
        Write-Host "  docker-compose -f docker-compose.prod.yml up -d"
        Write-Host ""
        Write-Host "Ricorda di:" -ForegroundColor Yellow
        Write-Host "  - Configurare SSL/HTTPS"
        Write-Host "  - Configurare backup automatici"
        Write-Host "  - Configurare monitoring"
        Write-Host "  - Aggiornare SECRET_KEY e password"
    }
}

Write-Host ""
Write-Host "Documentazione:" -ForegroundColor Blue
Write-Host "  - Architettura: docs/ARCHITECTURE.md"
Write-Host "  - API: docs/API_DOCUMENTATION.md"
Write-Host "  - Troubleshooting: TROUBLESHOOTING.md"
Write-Host ""
Write-Host "Buon lavoro con CerCollettiva! 🚀" -ForegroundColor Green
