# Script per deploy in modalità sviluppo
# PowerShell script per Windows

Write-Host "🚀 Deploy CerCollettiva in modalità SVILUPPO" -ForegroundColor Green

# Carica configurazione
if (Test-Path "config.env") {
    Get-Content "config.env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

# Override per sviluppo
$env:DEPLOYMENT_MODE = "dev"
$env:DEBUG = "True"
$env:NGINX_ENV = "dev"
$env:ALLOWED_HOSTS = "*"

Write-Host "📋 Configurazione:" -ForegroundColor Yellow
Write-Host "  - DEPLOYMENT_MODE: $env:DEPLOYMENT_MODE"
Write-Host "  - DEBUG: $env:DEBUG"
Write-Host "  - NGINX_ENV: $env:NGINX_ENV"
Write-Host "  - ALLOWED_HOSTS: $env:ALLOWED_HOSTS"

# Avvia stack
Write-Host "🐳 Avvio stack Docker..." -ForegroundColor Blue
docker-compose up -d

Write-Host "✅ Deploy completato!" -ForegroundColor Green
Write-Host "🌐 Applicazione disponibile su: http://localhost" -ForegroundColor Cyan
Write-Host "🔧 Admin disponibile su: http://localhost/ceradmin/" -ForegroundColor Cyan
