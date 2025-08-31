# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CerCollettiva is a Django-based Energy Community Management System (Comunità Energetica Rinnovabile - CER) with IoT device integration via MQTT. The system manages renewable energy communities, energy plants, IoT devices, and document processing including GAUDI (Italian grid integration) documents.

## Project Structure

```
CerCollettiva/
├── cercollettiva/       # Django project settings and configuration
├── core/                # Main CER management application
├── energy/              # IoT devices and energy measurements
├── documents/           # Document management with GAUDI processor
├── users/               # User authentication and profiles
├── templates/           # Django templates
├── static/              # Static files (CSS, JS, images)
├── media/               # User uploaded files
├── scripts/             # Server management scripts
├── utilities/           # Python utilities
├── docs/                # Documentation
│   └── install/         # Installation scripts
├── venv/                # Python virtual environment
├── manage.py            # Django management script
└── .env                 # Environment configuration

```

Note: The old `app/` directory structure has been flattened to the project root for simpler management.

## Development Commands

### Virtual Environment and Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install core Django dependencies first
pip install Django==5.0 psycopg2-binary python-dotenv

# Install other core dependencies
pip install djangorestframework channels django-crispy-forms crispy-bootstrap5
pip install django-widget-tweaks django-filter django-extensions paho-mqtt Pillow

# Install all remaining dependencies from requirements file
pip install -r requirements.txt

# Alternative: Install dependencies step by step if encountering issues
# pip install django djangorestframework channels paho-mqtt
# pip install psycopg2-binary python-dotenv django-crispy-forms crispy-bootstrap5  
# pip install django-widget-tweaks django-filters whitenoise geopy
# pip install openpyxl pandas django-extensions django-cors-headers
# pip install daphne channels-redis cryptography django-encrypted-model-fields Pillow
```

### Database Management
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Make migrations after model changes
python manage.py makemigrations
```

### Development Server
```bash
# Run development server
python manage.py runserver

# Run with specific settings
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local python manage.py runserver
```

### Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core
python manage.py test energy
python manage.py test documents
```

### Static Files
```bash
# Collect static files
python manage.py collectstatic --noinput
```

### Custom Management Commands
```bash
# Update plant coordinates from addresses
python manage.py update_plant_coordinates

# Debug MQTT configuration
python manage.py debug_config
```

## Architecture

### Django Apps Structure

1. **core** - Main application logic for CER management
   - Models: CERConfiguration, Plant, Alert, CERMembership
   - Views: Dashboard, CER management, Plant CRUD operations
   - Admin interface customization at `/ceradmin/`

2. **energy** - IoT device and energy measurement management
   - MQTT client for real-time device communication
   - Device registry system with vendor-specific implementations (Shelly, Tasmota, Huawei)
   - Energy calculation services with aggregation and caching
   - Models: DeviceConfiguration, Measurement, MQTTBroker

3. **documents** - Document management with GAUDI processor
   - GAUDI document parsing and validation
   - Document storage with user association
   - Excel/PDF processing capabilities

4. **users** - User authentication and profile management
   - Custom user profiles with GDPR compliance
   - CER membership management

### MQTT Architecture

The system uses a sophisticated MQTT client (`energy/mqtt/client.py`) with:
- Thread-safe message handling with queue and buffer management
- Device auto-discovery and registration
- Real-time measurement processing
- ACL-based topic authorization
- Automatic reconnection with exponential backoff

Device data flow:
1. IoT devices publish to `energia/<device_type>/<device_id>/...`
2. MQTT client processes messages via DeviceManager
3. Measurements stored in PostgreSQL with time-series optimization
4. Energy calculator aggregates data for reporting

### Key Configuration Files

- **Settings**: `cercollettiva/settings/` (base.py, local.py, production.py)
- **Environment**: `.env` file with database, MQTT, and Django settings
- **URLs**: Modular URL configuration with API and template namespacing

### Database

PostgreSQL database with:
- Connection pooling (CONN_MAX_AGE: 600)
- Test database: `test_cercollettiva`
- Migrations in each app's `migrations/` directory

### Frontend

- Django templates with Bootstrap 5
- Custom admin dashboard with energy statistics
- Real-time MQTT status monitoring
- Chart.js for power consumption visualization

## Important Implementation Details

### MQTT Connection
- Initialized on app startup via `energy/apps.py`
- Runs in daemon thread to avoid blocking
- Disabled during testing (checks `settings.TESTING`)
- Credentials stored in environment variables

### Geocoding Service
- Uses Nominatim for address-to-coordinates conversion
- Implements retry logic with timeouts
- Caches results to minimize API calls

### Document Processing
- GAUDI documents parsed with `openpyxl`
- Extracts plant data, POD codes, and grid information
- Validates against Italian energy regulations

### Security Considerations
- Field-level encryption for sensitive data
- GDPR compliance tracking for user documents
- Admin interface restricted to `/ceradmin/` path
- CSRF protection enabled
- User role-based access control (ADMIN, MEMBER, VIEWER)

## Troubleshooting Installation Issues

### Common Problems and Solutions

1. **"Couldn't import Django" error:**
   ```bash
   # Reinstall Django specifically
   pip uninstall django -y
   pip install Django==5.0
   ```

2. **"No module named 'rest_framework'" error:**
   ```bash
   # Install Django REST Framework
   pip install djangorestframework
   ```

3. **"No module named 'paho'" error:**
   ```bash
   # Install MQTT client
   pip install paho-mqtt
   ```

4. **"No module named 'django_extensions'" error:**
   ```bash
   # Install Django Extensions
   pip install django-extensions
   ```

5. **Virtual environment issues on WSL/Linux:**
   ```bash
   # If getting externally-managed-environment error
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   ```

6. **Database connection issues:**
   - Verify PostgreSQL is running
   - Check database credentials in .env file
   - Ensure database `cercollettiva_dev` exists

### Quick Setup Script
```bash
#!/bin/bash
# Quick setup script for CerCollettiva

# Remove old venv if exists
rm -rf venv

# Create new virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install Django==5.0 psycopg2-binary python-dotenv
pip install djangorestframework channels django-crispy-forms crispy-bootstrap5
pip install django-widget-tweaks django-filter django-extensions paho-mqtt

# Install all dependencies (if requirements.txt exists)
if [ -f "app/requirements.txt" ]; then
    pip install -r app/requirements.txt
fi

# Run migrations
python manage.py migrate

# Create superuser (optional)
# python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## Development Workflow

When modifying energy device integrations:
1. Check device vendor implementation in `energy/devices/vendors/`
2. Update device registry if adding new device types
3. Test MQTT message handling with `debug_config` command
4. Verify measurements are stored correctly

When working with GAUDI documents:
1. Review processor in `documents/processors/gaudi.py`
2. Test with sample GAUDI Excel files
3. Ensure plant data extraction is accurate
4. Validate coordinate geocoding

When updating CER management:
1. Models in `core/models.py` define CER structure
2. Views handle member management and plant associations
3. Admin customizations in `core/admin.py`
4. Dashboard aggregates energy statistics