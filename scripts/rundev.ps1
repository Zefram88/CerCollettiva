# PowerShell: Avvio server di sviluppo
param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000
)

$env:DJANGO_SETTINGS_MODULE = 'cercollettiva.settings.local'
Write-Host "DJANGO_SETTINGS_MODULE=$($env:DJANGO_SETTINGS_MODULE)"

python manage.py runserver "$Host`:$Port"

