# Guida Troubleshooting CerCollettiva

## Problemi Segnalati dagli Utenti e Soluzioni

### 1. Errore "CSRF verification failed" nei Form

**Problema**: 
```
Forbidden (403)
CSRF verification failed. Request aborted.
Reason given for failure: CSRF cookie not set.
```

**Causa**: Il progetto usa impostazioni di sicurezza per produzione anche in sviluppo.

**Soluzione**:
1. Verifica che stai usando le impostazioni di sviluppo:
   ```bash
   # Usa sempre questo comando per il server di sviluppo
   DJANGO_SETTINGS_MODULE=cercollettiva.settings.local python manage.py runserver
   ```

2. Se il problema persiste, verifica che nel file `.env` (nella root del progetto) ci sia:
   ```env
   DEBUG=True
   DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
   ```

3. **Importante**: Assicurati che nei template ci sia sempre il token CSRF:
   ```html
   <form method="post">
       {% csrf_token %}
       <!-- altri campi del form -->
   </form>
   ```

### 2. Admin Panel su `/ceradmin/` invece di `/admin/`

**Comportamento Normale**: Non è un bug!

L'interfaccia admin è **volutamente** configurata su `/ceradmin/` per maggiore sicurezza. Questo è il comportamento corretto del sistema.

- **URL Corretto**: `http://localhost:8000/ceradmin/`
- **Login**: Usa le credenziali del superuser creato

### 3. Admin Panel senza Grafica Bootstrap

**Problema**: L'interfaccia admin non ha lo stile Bootstrap.

**Soluzione**:
1. Assicurati che tutti i file statici siano raccolti:
   ```bash
   python manage.py collectstatic --noinput
   ```

2. Verifica che Bootstrap sia installato:
   ```bash
   pip install crispy-bootstrap5
   ```

3. Se stai usando il server di sviluppo, prova a forzare il reload degli statici con Ctrl+F5

### 4. Errore nella Creazione Utente

**Problema**: "L'utente non esiste" anche se è stato creato.

**Possibili Cause e Soluzioni**:

1. **Database non migrato**:
   ```bash
   python manage.py migrate
   ```

2. **Creazione superuser incompleta**:
   ```bash
   python manage.py createsuperuser
   # Compila tutti i campi richiesti
   ```

3. **Conflitto con utenti esistenti**:
   ```bash
   # Verifica utenti esistenti
   python manage.py shell
   >>> from django.contrib.auth import get_user_model
   >>> User = get_user_model()
   >>> User.objects.all()
   ```

4. **Problema con il custom user model**:
   ```bash
   # Verifica la configurazione dell'utente personalizzato
   python manage.py check
   ```

### 5. Problemi di Installazione - Setup Completo

**Script di Setup Rapido**:
```bash
#!/bin/bash
# File: quick_setup.sh

echo "=== Setup CerCollettiva ==="

# 1. Rimuovi virtual environment precedente
rm -rf venv

# 2. Crea nuovo virtual environment
echo "Creazione virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Aggiorna pip
echo "Aggiornamento pip..."
pip install --upgrade pip

# 4. Installa dipendenze core
echo "Installazione dipendenze Django..."
pip install Django==5.0 psycopg2-binary python-dotenv

# 5. Installa dipendenze aggiuntive
echo "Installazione dipendenze aggiuntive..."
pip install djangorestframework channels django-crispy-forms crispy-bootstrap5
pip install django-widget-tweaks django-filter django-extensions paho-mqtt

# 6. Installa tutte le altre dipendenze se requirements.txt esiste
if [ -f "requirements.txt" ]; then
    echo "Installazione requirements.txt..."
    pip install -r requirements.txt
fi

# 7. Crea file .env se non esiste
if [ ! -f ".env" ]; then
    echo "Creazione file .env..."
    cat > .env << EOL
DEBUG=True
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
SECRET_KEY=django-insecure-your-secret-key-for-development
DB_NAME=db.sqlite3
EOL
fi

# 8. Crea directory per i log
mkdir -p logs

# 9. Esegui migrazioni
echo "Esecuzione migrazioni..."
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local python manage.py migrate

# 10. Raccogli file statici
echo "Raccolta file statici..."
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local python manage.py collectstatic --noinput

# 11. Crea superuser (interattivo)
echo "Creazione superuser..."
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local python manage.py createsuperuser

echo ""
echo "=== SETUP COMPLETATO ==="
echo ""
echo "Per avviare il server:"
echo "DJANGO_SETTINGS_MODULE=cercollettiva.settings.local python manage.py runserver"
echo ""
echo "Admin panel disponibile su: http://localhost:8000/ceradmin/"
echo ""
```

### 6. Test di Funzionamento

**Dopo l'installazione, testa sempre**:
```bash
# 1. Verifica configurazione
python manage.py check

# 2. Test database
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print(f'Utenti nel sistema: {User.objects.count()}')
print('✓ Database OK')
"

# 3. Test server
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local python manage.py runserver &
SERVER_PID=$!
sleep 3
curl -s http://localhost:8000/ > /dev/null && echo "✓ Server OK" || echo "✗ Server NON OK"
kill $SERVER_PID

# 4. Test admin
echo "Test login admin su http://localhost:8000/ceradmin/"
```

### 7. Problemi Comuni Durante lo Sviluppo

1. **Import Error per i moduli**:
   ```bash
   # Assicurati di essere nella directory corretta
   pwd  # Deve essere /path/to/CerCollettiva
   
   # Attiva sempre il virtual environment
   source venv/bin/activate
   ```

2. **Database locked (SQLite)**:
   ```bash
   # Chiudi tutti i processi che accedono al database
   pkill -f "python manage.py runserver"
   ```

3. **Problemi con i file statici**:
   ```bash
   # Svuota la cache del browser (Ctrl+Shift+R)
   # Oppure usa il server con --insecure
   python manage.py runserver --insecure
   ```

### 8. Supporto e Debugging

**Per segnalare problemi**:
1. Includi sempre il log di errore completo
2. Specifica il sistema operativo
3. Indica i comandi eseguiti
4. Condividi il contenuto del file `.env` (senza password)

**Log di debug utili**:
```bash
# Log Django dettagliati
tail -f logs/cercollettiva.log

# Log MQTT
tail -f logs/mqtt.log

# Log di sviluppo
tail -f logs/debug.log
```

### 9. Comandi Utili per il Debug

```bash
# Verifica configurazione completa
python manage.py diffsettings

# Lista delle migrazioni
python manage.py showmigrations

# Reset delle migrazioni (ATTENZIONE: cancella dati)
python manage.py migrate core zero
python manage.py migrate

# Shell interattiva Django
python manage.py shell_plus
```