# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CerCollettiva is a Django-based Energy Community Management System (Comunità Energetica Rinnovabile - CER) with IoT device integration via MQTT. The system manages renewable energy communities, energy plants, IoT devices, and document processing including GAUDI (Italian grid integration) documents.

## Development Commands

### Virtual Environment and Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (requirements file needs to be created)
pip install django djangorestframework channels paho-mqtt
pip install psycopg2-binary python-dotenv crispy-forms crispy-bootstrap5
pip install widget-tweaks django-filters whitenoise geopy
pip install openpyxl pandas  # For GAUDI document processing
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