"""
Test configuration and fixtures for CerCollettiva test suite
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command
from decimal import Decimal
from datetime import date
from core.main_models import CERConfiguration, Plant, CERMembership
from energy.models import DeviceConfiguration, MQTTBroker

User = get_user_model()


class TestFixtures:
    """Test fixtures for consistent test data"""
    
    @staticmethod
    def create_test_user(username='testuser', email='test@example.com', **kwargs):
        """Create a test user with default values"""
        defaults = {
            'password': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        defaults.update(kwargs)
        return User.objects.create_user(username=username, email=email, **defaults)
    
    @staticmethod
    def create_test_admin(username='admin', email='admin@example.com', **kwargs):
        """Create a test admin user with default values"""
        defaults = {
            'password': 'AdminPass123!',
            'first_name': 'Admin',
            'last_name': 'User'
        }
        defaults.update(kwargs)
        return User.objects.create_superuser(username=username, email=email, **defaults)
    
    @staticmethod
    def create_test_cer(name='Test CER', code='CER001', **kwargs):
        """Create a test CER with default values"""
        defaults = {
            'primary_substation': 'Cabina Primaria Test',
            'description': 'Test CER Description'
        }
        defaults.update(kwargs)
        return CERConfiguration.objects.create(name=name, code=code, **defaults)
    
    @staticmethod
    def create_test_plant(owner, cer, name='Test Plant', **kwargs):
        """Create a test plant with default values"""
        defaults = {
            'plant_type': 'PRODUCER',
            'power_kw': Decimal('10.5'),
            'commissioning_date': date(2023, 1, 1),
            'pod': 'IT001E12345678',
            'address': 'Via Test 123, 00100 Roma',
            'city': 'Roma',
            'zip_code': '00100',
            'province': 'RM',
            'latitude': Decimal('41.9028'),
            'longitude': Decimal('12.4964'),
            'connection_voltage': '400V',
            'installation_date': date(2023, 1, 1)
        }
        defaults.update(kwargs)
        return Plant.objects.create(owner=owner, cer_configuration=cer, name=name, **defaults)
    
    @staticmethod
    def create_test_membership(user, cer, role='MEMBER', **kwargs):
        """Create a test CER membership with default values"""
        defaults = {
            'share_percentage': Decimal('10.0'),
            'joined_date': date(2023, 1, 1)
        }
        defaults.update(kwargs)
        return CERMembership.objects.create(user=user, cer_configuration=cer, role=role, **defaults)
    
    @staticmethod
    def create_test_device(plant, device_id='DEV001', **kwargs):
        """Create a test device configuration with default values"""
        defaults = {
            'name': 'Test Device',
            'device_type': 'INVERTER',
            'vendor': 'TEST_VENDOR',
            'model': 'Test Model',
            'is_active': True
        }
        defaults.update(kwargs)
        return DeviceConfiguration.objects.create(plant=plant, device_id=device_id, **defaults)
    
    @staticmethod
    def create_test_mqtt_broker(name='Test Broker', **kwargs):
        """Create a test MQTT broker with default values"""
        defaults = {
            'host': 'localhost',
            'port': 1883,
            'username': 'testuser',
            'password': 'testpass',
            'is_active': True,
            'keepalive': 60,
            'qos_level': 1
        }
        defaults.update(kwargs)
        return MQTTBroker.objects.create(name=name, **defaults)


class TestDataSetup:
    """Helper class for setting up comprehensive test data"""
    
    def __init__(self):
        self.users = {}
        self.cers = {}
        self.plants = {}
        self.memberships = {}
        self.devices = {}
        self.brokers = {}
    
    def setup_basic_data(self):
        """Set up basic test data structure"""
        # Create users
        self.users['admin'] = TestFixtures.create_test_admin()
        self.users['user1'] = TestFixtures.create_test_user('user1', 'user1@example.com')
        self.users['user2'] = TestFixtures.create_test_user('user2', 'user2@example.com')
        
        # Create CERs
        self.cers['cer1'] = TestFixtures.create_test_cer('Test CER 1', 'CER001')
        self.cers['cer2'] = TestFixtures.create_test_cer('Test CER 2', 'CER002')
        
        # Create plants
        self.plants['plant1'] = TestFixtures.create_test_plant(
            self.users['user1'], self.cers['cer1'], 'Test Plant 1'
        )
        self.plants['plant2'] = TestFixtures.create_test_plant(
            self.users['user2'], self.cers['cer2'], 'Test Plant 2'
        )
        
        # Create memberships
        self.memberships['membership1'] = TestFixtures.create_test_membership(
            self.users['user1'], self.cers['cer1']
        )
        self.memberships['membership2'] = TestFixtures.create_test_membership(
            self.users['user2'], self.cers['cer2']
        )
        
        # Create devices
        self.devices['device1'] = TestFixtures.create_test_device(
            self.plants['plant1'], 'DEV001'
        )
        self.devices['device2'] = TestFixtures.create_test_device(
            self.plants['plant2'], 'DEV002'
        )
        
        # Create MQTT brokers
        self.brokers['broker1'] = TestFixtures.create_test_mqtt_broker('Test Broker 1')
        self.brokers['broker2'] = TestFixtures.create_test_mqtt_broker('Test Broker 2')
        
        return self


# Pytest fixtures for use with pytest
@pytest.fixture
def test_fixtures():
    """Provide access to test fixtures"""
    return TestFixtures


@pytest.fixture
def test_data():
    """Provide comprehensive test data setup"""
    return TestDataSetup().setup_basic_data()


@pytest.fixture
def admin_user():
    """Provide an admin user for tests"""
    return TestFixtures.create_test_admin()


@pytest.fixture
def regular_user():
    """Provide a regular user for tests"""
    return TestFixtures.create_test_user()


@pytest.fixture
def test_cer():
    """Provide a test CER for tests"""
    return TestFixtures.create_test_cer()


@pytest.fixture
def test_plant(regular_user, test_cer):
    """Provide a test plant for tests"""
    return TestFixtures.create_test_plant(regular_user, test_cer)


@pytest.fixture
def test_membership(regular_user, test_cer):
    """Provide a test membership for tests"""
    return TestFixtures.create_test_membership(regular_user, test_cer)


@pytest.fixture
def test_device(test_plant):
    """Provide a test device for tests"""
    return TestFixtures.create_test_device(test_plant)


@pytest.fixture
def test_mqtt_broker():
    """Provide a test MQTT broker for tests"""
    return TestFixtures.create_test_mqtt_broker()


# Django test case mixins
class TestCaseWithFixtures(TestCase):
    """Base test case with fixture support"""
    
    def setUp(self):
        super().setUp()
        self.fixtures = TestFixtures()
        self.test_data = TestDataSetup().setup_basic_data()
    
    def create_test_user(self, **kwargs):
        """Create a test user"""
        return self.fixtures.create_test_user(**kwargs)
    
    def create_test_admin(self, **kwargs):
        """Create a test admin"""
        return self.fixtures.create_test_admin(**kwargs)
    
    def create_test_cer(self, **kwargs):
        """Create a test CER"""
        return self.fixtures.create_test_cer(**kwargs)
    
    def create_test_plant(self, owner, cer, **kwargs):
        """Create a test plant"""
        return self.fixtures.create_test_plant(owner, cer, **kwargs)
    
    def create_test_membership(self, user, cer, **kwargs):
        """Create a test membership"""
        return self.fixtures.create_test_membership(user, cer, **kwargs)
    
    def create_test_device(self, plant, **kwargs):
        """Create a test device"""
        return self.fixtures.create_test_device(plant, **kwargs)
    
    def create_test_mqtt_broker(self, **kwargs):
        """Create a test MQTT broker"""
        return self.fixtures.create_test_mqtt_broker(**kwargs)
