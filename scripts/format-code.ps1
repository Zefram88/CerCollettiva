# Script PowerShell per formattare il codice con Black prima del push
# Uso: .\scripts\format-code.ps1

Write-Host "🎨 Formattazione codice con Black..." -ForegroundColor Cyan

# Controlla se Black e isort sono installati
try {
    python -m black --version | Out-Null
    Write-Host "✅ Black trovato" -ForegroundColor Green
} catch {
    Write-Host "❌ Black non trovato. Installazione..." -ForegroundColor Red
    pip install black
}

try {
    python -m isort --version | Out-Null
    Write-Host "✅ isort trovato" -ForegroundColor Green
} catch {
    Write-Host "❌ isort non trovato. Installazione..." -ForegroundColor Red
    pip install isort
}

# Ordina gli import con isort
Write-Host "📝 Ordinamento import con isort..." -ForegroundColor Yellow
python -m isort . --profile black

# Formatta tutti i file Python escludendo le directory specificate
Write-Host "📝 Formattazione file Python con Black..." -ForegroundColor Yellow
python -m black . --exclude "venv|node_modules|tests|cercollettiva/settings"

# Controlla se ci sono modifiche
$changes = git diff --name-only
if ($changes.Count -eq 0) {
    Write-Host "✅ Tutti i file sono già formattati correttamente!" -ForegroundColor Green
} else {
    Write-Host "📝 File formattati. Modifiche:" -ForegroundColor Yellow
    $changes | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
    Write-Host ""
    Write-Host "💡 Ricorda di fare commit delle modifiche:" -ForegroundColor Cyan
    Write-Host "   git add ." -ForegroundColor White
    Write-Host "   git commit -m 'style: Format code with Black'" -ForegroundColor White
    Write-Host "   git push" -ForegroundColor White
}

Write-Host "🎉 Formattazione completata!" -ForegroundColor Green
