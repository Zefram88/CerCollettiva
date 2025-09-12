# Script per deploy in modalità produzione
# PowerShell script per Windows

Write-Host "🚀 Deploy CerCollettiva in modalità PRODUZIONE" -ForegroundColor Red

# Carica configurazione
if (Test-Path "config.env") {
    Get-Content "config.env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

# Override per produzione
$env:DEPLOYMENT_MODE = "prod"
$env:DEBUG = "False"
$env:NGINX_ENV = "prod"
$env:ALLOWED_HOSTS = "your-domain.com,www.your-domain.com"
$env:SECURE_SSL_REDIRECT = "True"

Write-Host "📋 Configurazione:" -ForegroundColor Yellow
Write-Host "  - DEPLOYMENT_MODE: $env:DEPLOYMENT_MODE"
Write-Host "  - DEBUG: $env:DEBUG"
Write-Host "  - NGINX_ENV: $env:NGINX_ENV"
Write-Host "  - ALLOWED_HOSTS: $env:ALLOWED_HOSTS"
Write-Host "  - SECURE_SSL_REDIRECT: $env:SECURE_SSL_REDIRECT"

# Verifica certificati SSL
if ($env:NGINX_ENV -eq "prod") {
    Write-Host "🔒 Verifica certificati SSL..." -ForegroundColor Yellow
    if (-not (Test-Path "config/ssl/cert.pem")) {
        Write-Host "⚠️  Certificati SSL non trovati. Eseguire: scripts/setup-letsencrypt.sh" -ForegroundColor Red
        exit 1
    }
}

# Avvia stack
Write-Host "🐳 Avvio stack Docker..." -ForegroundColor Blue
docker-compose up -d

Write-Host "✅ Deploy completato!" -ForegroundColor Green
Write-Host "🌐 Applicazione disponibile su: https://your-domain.com" -ForegroundColor Cyan
Write-Host "🔧 Admin disponibile su: https://your-domain.com/ceradmin/" -ForegroundColor Cyan
