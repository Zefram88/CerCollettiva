# 🎨 Code Formatting con Black

Questo documento spiega come utilizzare Black per mantenere uno stile di codice consistente nel progetto CerCollettiva.

## 🚀 Setup Rapido

### 1. Installazione Locale
```bash
pip install black isort pre-commit
```

### 2. Setup Pre-commit Hooks (Raccomandato)
```bash
pre-commit install
```

## 🛠️ Utilizzo

### Formattazione Manuale

#### Windows (PowerShell)
```powershell
.\scripts\format-code.ps1
```

#### Linux/Mac (Bash)
```bash
./scripts/format-code.sh
```

#### Comando Diretto
```bash
black . --exclude "venv|node_modules|tests|cercollettiva/settings"
```

### Formattazione Automatica

#### Pre-commit Hooks
I pre-commit hooks formattano automaticamente il codice prima di ogni commit:
- **Black**: Formattazione Python
- **isort**: Ordinamento import
- **flake8**: Controllo qualità codice
- **Django check**: Verifica configurazione Django

#### GitHub Actions
- **black-format.yml**: Crea PR automatici con formattazione
- **black-direct.yml**: Formatta direttamente il branch (solo develop)
- **ci.yml**: Controlla formattazione in CI

## 📁 File di Configurazione

### pyproject.toml
Configurazione centralizzata per tutti gli strumenti:
- Black: line-length=88, esclude directory specifiche
- isort: profilo Black, sezioni personalizzate
- flake8: max-line-length=88, ignore specifici
- mypy: configurazione type checking

### .pre-commit-config.yaml
Hooks pre-commit per formattazione automatica

## 🎯 Directory Escluse

I seguenti directory sono esclusi dalla formattazione:
- `venv/` - Virtual environment
- `node_modules/` - Dipendenze Node.js
- `tests/` - File di test (formattazione manuale)
- `cercollettiva/settings/` - File di configurazione Django

## 🔧 Workflow GitHub Actions

### 1. black-format.yml
- **Trigger**: Push su main/develop, PR, manuale
- **Azione**: Crea PR automatico con formattazione
- **Sicurezza**: Non modifica mai il branch principale

### 2. black-direct.yml
- **Trigger**: Solo manuale o push su develop
- **Azione**: Formatta direttamente il branch
- **Sicurezza**: Solo su develop per evitare modifiche accidentali

### 3. ci.yml (Aggiornato)
- **Trigger**: Push/PR su main/develop
- **Azione**: Controlla formattazione in CI
- **Fallimento**: CI fallisce se codice non formattato

## 🚨 Risoluzione Problemi

### CI Fallisce per Formattazione
```bash
# Formatta localmente
black . --exclude "venv|node_modules|tests|cercollettiva/settings"

# Commit e push
git add .
git commit -m "style: Format code with Black"
git push
```

### Pre-commit Hook Fallisce
```bash
# Aggiorna hooks
pre-commit autoupdate

# Re-installa
pre-commit uninstall
pre-commit install
```

### Conflitti di Formattazione
```bash
# Formatta tutto
black . --exclude "venv|node_modules|tests|cercollettiva/settings"

# Risolvi conflitti
git add .
git commit -m "style: Resolve formatting conflicts"
```

## 📋 Best Practices

1. **Sempre formattare prima del commit**
2. **Usa pre-commit hooks per automazione**
3. **Controlla CI per errori di formattazione**
4. **Non modificare file di configurazione Black**
5. **Mantieni directory escluse aggiornate**

## 🔗 Link Utili

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
