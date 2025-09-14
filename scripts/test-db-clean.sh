#!/bin/bash
# Script per testare database pulito

set -e

echo "🧪 Test Database Pulito - CerCollettiva"
echo "========================================"

# Verifica connessione database
echo "📊 Verifica connessione database..."
docker exec cercollettiva_web python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT version()'); print('PostgreSQL:', cursor.fetchone()[0])"

# Verifica migrazioni
echo "📋 Verifica migrazioni..."
docker exec cercollettiva_web python manage.py showmigrations --plan

# Conteggio record per tabella
echo "📈 Conteggio record per tabella..."
docker exec cercollettiva_web python manage.py shell -c "
from django.contrib.contenttypes.models import ContentType
from django.db import connection

# Ottieni tutte le tabelle
with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    \"\"\")
    tables = [row[0] for row in cursor.fetchall()]

print('📊 Conteggio record per tabella:')
for table in tables:
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT COUNT(*) FROM {table};')
            count = cursor.fetchone()[0]
            print(f'  {table}: {count} record')
    except Exception as e:
        print(f'  {table}: ERRORE - {e}')
"

# Verifica superuser
echo "👤 Verifica superuser..."
docker exec cercollettiva_web python manage.py shell -c "
from users.models import CustomUser
superusers = CustomUser.objects.filter(is_superuser=True)
print(f'Superuser trovati: {superusers.count()}')
for user in superusers:
    print(f'  - {user.username} ({user.email})')
"

# Verifica configurazioni CER
echo "🏢 Verifica configurazioni CER..."
docker exec cercollettiva_web python manage.py shell -c "
from core.main_models import CERConfiguration
cers = CERConfiguration.objects.all()
print(f'Configurazioni CER: {cers.count()}')
for cer in cers:
    print(f'  - {cer.name} ({cer.code})')
"

# Verifica dispositivi
echo "🔌 Verifica dispositivi..."
docker exec cercollettiva_web python manage.py shell -c "
from energy.models import Device
devices = Device.objects.all()
print(f'Dispositivi: {devices.count()}')
for device in devices:
    print(f'  - {device.name} ({device.device_type})')
"

# Test endpoint API
echo "🌐 Test endpoint API..."
echo "  - Health check:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/monitoring/health/ && echo " ✅" || echo " ❌"

echo "  - Homepage:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ && echo " ✅" || echo " ❌"

echo "  - Admin:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/ && echo " ✅" || echo " ❌"

echo ""
echo "✅ Test database pulito completato!"
echo "📝 Il database contiene dati di test/demo, non è completamente pulito"
echo "💡 Per database completamente pulito, eseguire: docker-compose down -v && docker-compose up -d"
