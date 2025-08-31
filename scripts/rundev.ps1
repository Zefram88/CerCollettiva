# PowerShell: Avvio server di sviluppo
param(
    [string]$BindAddress = "127.0.0.1",
    [int]$Port = 8000
)

# Porta la working directory alla root del progetto (cartella che contiene manage.py)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path (Join-Path $ScriptDir '..')

$env:DJANGO_SETTINGS_MODULE = 'cercollettiva.settings.local'
Write-Host "DJANGO_SETTINGS_MODULE=$($env:DJANGO_SETTINGS_MODULE)"

$endpoint = "{0}:{1}" -f $BindAddress, $Port
python manage.py runserver $endpoint
