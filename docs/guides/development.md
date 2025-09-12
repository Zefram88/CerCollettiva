# Guida per Sviluppatori CerCollettiva

## Panoramica

Questa guida fornisce informazioni dettagliate per sviluppatori che vogliono contribuire al progetto CerCollettiva o estendere le sue funzionalità.

## Prerequisiti

### Software Richiesto
- **Python 3.11+**: Linguaggio principale
- **PostgreSQL 14+**: Database principale
- **Redis 6+**: Cache e sessioni
- **Git**: Controllo versione
- **Docker & Docker Compose**: Containerizzazione (opzionale)

### Strumenti di Sviluppo
- **IDE**: VS Code, PyCharm, o qualsiasi editor Python
- **Terminal**: Bash, PowerShell, o Zsh
- **Browser**: Chrome, Firefox, Safari per testing

## Setup Ambiente di Sviluppo

### 1. Clonazione Repository
```bash
git clone https://github.com/atomozero/CerCollettiva.git
cd CerCollettiva
```

### 2. Setup Automatico
```bash
# Linux/macOS
chmod +x scripts/setup.sh
./scripts/setup.sh

# Windows PowerShell
.\scripts\setup.ps1
```

### 3. Setup Manuale
```bash
# Crea ambiente virtuale
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\Activate.ps1  # Windows

# Installa dipendenze
pip install -r requirements.txt

# Configura ambiente
cp env.example .env
# Modifica .env con le tue configurazioni

# Setup database
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## Struttura del Progetto

```
CerCollettiva/
├── cercollettiva/          # Configurazioni Django
│   ├── settings/          # Settings per ambiente
│   ├── urls.py           # URL principali
│   └── wsgi.py           # WSGI application
├── core/                  # App principale CER
│   ├── models.py         # Modelli business
│   ├── views/            # Views organizzate
│   ├── admin.py          # Admin interface
│   └── templates/        # Template HTML
├── energy/                # App monitoraggio energetico
│   ├── mqtt/             # Client MQTT
│   ├── devices/          # Gestione dispositivi
│   ├── services/         # Logica business
│   └── models/           # Modelli energetici
├── documents/             # App gestione documenti
│   ├── processors/       # Elaborazione GAUDI
│   └── models.py         # Modelli documenti
├── users/                 # App gestione utenti
│   ├── models.py         # Modello utente custom
│   ├── forms.py          # Form registrazione
│   └── views.py          # Views autenticazione
├── monitoring/            # App monitoring sistema
│   └── views.py          # Health checks
├── tests/                 # Test suite
├── docs/                  # Documentazione
├── scripts/               # Script di automazione
├── config/                # Configurazioni servizi
└── static/                # File statici
```

## Convenzioni di Codice

### Python Style Guide
- **PEP 8**: Standard Python
- **Black**: Formattazione automatica
- **isort**: Ordinamento import
- **flake8**: Linting

### Django Best Practices
- **DRY**: Don't Repeat Yourself
- **Fat Models, Thin Views**: Logica business nei modelli
- **Generic Views**: Usa Class-Based Views quando possibile
- **Form Validation**: Validazione lato server sempre

### Naming Conventions
```python
# Modelli: PascalCase
class CERConfiguration(models.Model):
    pass

# Funzioni: snake_case
def calculate_energy_consumption():
    pass

# Costanti: UPPER_CASE
MAX_POWER_KW = 1000

# Variabili: snake_case
device_configuration = DeviceConfiguration.objects.get(id=1)
```

## Architettura e Pattern

### Service Layer Pattern
```python
# energy/services/energy_calculator.py
class EnergyCalculator:
    def calculate_daily_consumption(self, device_id, date):
        # Logica business isolata
        pass
```

### Repository Pattern
```python
# energy/repositories/measurement_repository.py
class MeasurementRepository:
    def get_latest_measurements(self, device_id):
        # Accesso dati centralizzato
        pass
```

### Observer Pattern (Django Signals)
```python
# core/signals.py
@receiver(post_save, sender=Plant)
def plant_created(sender, instance, created, **kwargs):
    if created:
        # Azioni automatiche
        pass
```

## Sviluppo di Nuove Funzionalità

### 1. Creazione di una Nuova App
```bash
python manage.py startapp new_feature
```

### 2. Struttura App Standard
```
new_feature/
├── __init__.py
├── apps.py
├── models.py
├── views.py
├── urls.py
├── admin.py
├── forms.py
├── serializers.py
├── services.py
├── tests.py
└── templates/
    └── new_feature/
```

### 3. Modelli Django
```python
# new_feature/models.py
from django.db import models
from core.models import BaseTimestampModel

class NewFeature(BaseTimestampModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "New Feature"
        verbose_name_plural = "New Features"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
```

### 4. Views e URL
```python
# new_feature/views.py
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import NewFeature

class NewFeatureListView(LoginRequiredMixin, ListView):
    model = NewFeature
    template_name = 'new_feature/list.html'
    context_object_name = 'features'
    paginate_by = 20

# new_feature/urls.py
from django.urls import path
from . import views

app_name = 'new_feature'

urlpatterns = [
    path('', views.NewFeatureListView.as_view(), name='list'),
    path('<int:pk>/', views.NewFeatureDetailView.as_view(), name='detail'),
]
```

### 5. Template HTML
```html
<!-- new_feature/templates/new_feature/list.html -->
{% extends 'base.html' %}
{% load static %}

{% block title %}New Features{% endblock %}

{% block content %}
<div class="container">
    <h1>New Features</h1>
    <div class="row">
        {% for feature in features %}
        <div class="col-md-4 mb-3">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">{{ feature.name }}</h5>
                    <p class="card-text">{{ feature.description }}</p>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

## Testing

### Struttura Test
```python
# new_feature/tests.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import NewFeature

User = get_user_model()

class NewFeatureModelTest(TestCase):
    def setUp(self):
        self.feature = NewFeature.objects.create(
            name="Test Feature",
            description="Test Description"
        )
    
    def test_feature_creation(self):
        self.assertEqual(self.feature.name, "Test Feature")
        self.assertTrue(self.feature.is_active)
    
    def test_feature_str_method(self):
        self.assertEqual(str(self.feature), "Test Feature")

class NewFeatureViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
    
    def test_feature_list_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('new_feature:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Features')
```

### Esecuzione Test
```bash
# Tutti i test
python manage.py test

# Test specifici
python manage.py test new_feature
python manage.py test new_feature.tests.NewFeatureModelTest

# Con coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## API Development

### Django REST Framework
```python
# new_feature/serializers.py
from rest_framework import serializers
from .models import NewFeature

class NewFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewFeature
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

# new_feature/views.py
from rest_framework import viewsets, permissions
from .models import NewFeature
from .serializers import NewFeatureSerializer

class NewFeatureViewSet(viewsets.ModelViewSet):
    queryset = NewFeature.objects.all()
    serializer_class = NewFeatureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']
```

### Documentazione API
```python
# new_feature/schemas.py
from drf_yasg import openapi

feature_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'name': openapi.Schema(type=openapi.TYPE_STRING),
        'description': openapi.Schema(type=openapi.TYPE_STRING),
        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
    }
)
```

## Database e Migrazioni

### Creazione Migrazioni
```bash
# Dopo modifiche ai modelli
python manage.py makemigrations

# Applica migrazioni
python manage.py migrate

# Migrazione specifica
python manage.py migrate new_feature 0001
```

### Migrazioni Personalizzate
```python
# new_feature/migrations/0002_custom_migration.py
from django.db import migrations, models

def populate_default_data(apps, schema_editor):
    NewFeature = apps.get_model('new_feature', 'NewFeature')
    NewFeature.objects.create(
        name="Default Feature",
        description="Auto-created feature"
    )

class Migration(migrations.Migration):
    dependencies = [
        ('new_feature', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(populate_default_data),
    ]
```

## MQTT Integration

### Aggiunta Nuovo Device Type
```python
# energy/devices/vendors/new_vendor/device.py
from energy.devices.base.device import BaseDevice

class NewVendorDevice(BaseDevice):
    vendor = "NEW_VENDOR"
    model = "MODEL_X"
    
    def parse_message(self, topic, data):
        # Implementa parsing specifico
        return MeasurementData(
            power=data.get('power', 0),
            voltage=data.get('voltage', 0),
            current=data.get('current', 0)
        )
```

### Registrazione Device
```python
# energy/devices/registry.py
from .vendors.new_vendor.device import NewVendorDevice

# Registra automaticamente
DeviceRegistry.register(NewVendorDevice)
```

## Frontend Development

### JavaScript Custom
```javascript
// static/js/new-feature.js
class NewFeatureManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.bindEvents();
    }
    
    bindEvents() {
        document.addEventListener('DOMContentLoaded', () => {
            // Eventi specifici
        });
    }
    
    async fetchData() {
        try {
            const response = await fetch('/api/new-feature/');
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }
}

// Inizializza
new NewFeatureManager();
```

### CSS Custom
```css
/* static/css/new-feature.css */
.new-feature-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    transition: box-shadow 0.3s ease;
}

.new-feature-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.new-feature-status {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
}

.new-feature-status.active {
    background-color: #d4edda;
    color: #155724;
}

.new-feature-status.inactive {
    background-color: #f8d7da;
    color: #721c24;
}
```

## Debugging e Profiling

### Django Debug Toolbar
```python
# settings/local.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

### Logging Personalizzato
```python
# new_feature/views.py
import logging

logger = logging.getLogger(__name__)

class NewFeatureView(LoginRequiredMixin, View):
    def get(self, request):
        logger.info(f"User {request.user.username} accessed new feature")
        # Logica view
        return render(request, 'new_feature/detail.html')
```

### Profiling Performance
```python
# new_feature/views.py
from django.db import connection
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache 15 min
class NewFeatureListView(ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Log query count
        print(f"Queries executed: {len(connection.queries)}")
        return context
```

## Deployment

### Ambiente di Sviluppo
```bash
# Avvia servizi
python manage.py runserver

# Con Docker
docker-compose up -d
```

### Ambiente di Test
```bash
# Test con database separato
python manage.py test --settings=cercollettiva.settings.test
```

### Ambiente di Produzione
```bash
# Build e deploy
docker-compose -f docker-compose.prod.yml up -d

# Migrazioni
docker-compose exec web python manage.py migrate

# Collect static
docker-compose exec web python manage.py collectstatic --noinput
```

## Contribuire al Progetto

### Workflow Git
```bash
# 1. Fork del repository
# 2. Clone del tuo fork
git clone https://github.com/yourusername/CerCollettiva.git

# 3. Crea branch feature
git checkout -b feature/new-awesome-feature

# 4. Sviluppa e committa
git add .
git commit -m "Add new awesome feature"

# 5. Push e crea Pull Request
git push origin feature/new-awesome-feature
```

### Standard di Commit
```
feat: aggiunge nuova funzionalità
fix: corregge bug
docs: aggiorna documentazione
style: formattazione codice
refactor: refactoring codice
test: aggiunge test
chore: task di manutenzione
```

### Code Review Checklist
- [ ] Codice segue PEP 8
- [ ] Test unitari aggiunti
- [ ] Documentazione aggiornata
- [ ] Migrazioni database testate
- [ ] Performance considerate
- [ ] Sicurezza verificata
- [ ] Compatibilità backward mantenuta

## Risorse Utili

### Documentazione
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

### Strumenti
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
- [Django Extensions](https://django-extensions.readthedocs.io/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [isort Import Sorter](https://pycqa.github.io/isort/)

### Community
- [Django Forum](https://forum.djangoproject.com/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/django)
- [Django Discord](https://discord.gg/xcRH6mN4fa)

## Troubleshooting

### Problemi Comuni

#### Database Connection Error
```bash
# Verifica connessione
python manage.py dbshell

# Reset database
python manage.py flush
python manage.py migrate
```

#### MQTT Connection Issues
```bash
# Test connessione MQTT
mosquitto_pub -h localhost -t test -m "hello"
mosquitto_sub -h localhost -t test
```

#### Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic --clear --noinput

# Verifica configurazione
python manage.py findstatic admin/css/base.css
```

#### Cache Issues
```bash
# Clear cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### Log Analysis
```bash
# Log Django
tail -f logs/cercollettiva.log

# Log MQTT
tail -f logs/mqtt.log

# Log Nginx
tail -f /var/log/nginx/error.log
```

## Supporto

### Canali di Supporto
- **GitHub Issues**: Per bug e feature requests
- **Discord**: Per discussioni e supporto rapido
- **Email**: team@cercollettiva.it per questioni private

### Reporting Bug
Quando riporti un bug, includi:
1. Versione Python e Django
2. Sistema operativo
3. Steps per riprodurre
4. Log di errore completi
5. Screenshot se applicabile

### Feature Requests
Per nuove funzionalità:
1. Verifica che non sia già richiesta
2. Descrivi il caso d'uso
3. Spiega i benefici
4. Considera l'implementazione

---

**Buon coding! 🚀**
