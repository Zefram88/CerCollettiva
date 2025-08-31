# PowerShell: Sanity check e migrazioni

# Porta la working directory alla root del progetto (cartella che contiene manage.py)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path (Join-Path $ScriptDir '..')

$env:DJANGO_SETTINGS_MODULE = 'cercollettiva.settings.local'
Write-Host "DJANGO_SETTINGS_MODULE=$($env:DJANGO_SETTINGS_MODULE)"

python manage.py check
python manage.py migrate --noinput
