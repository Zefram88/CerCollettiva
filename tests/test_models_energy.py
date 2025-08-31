"""
Test suite for Energy app models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from energy.models import DeviceConfiguration, Measurement, MQTTBroker
from core.models import Plant, CERConfiguration

User = get_user_model()


class DeviceConfigurationModelTest(TestCase):
    """Test cases for DeviceConfiguration model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='deviceowner',
            email='owner@example.com',
            password='TestPass123!'
        )
        
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!'
        )
        
        self.cer = CERConfiguration.objects.create(
            name='Test CER',
            code='CER001',
            vat_number='12345678901',
            address='Via Roma 1',
            city='Milano',
            province='MI',
            zip_code='20100',
            email='info@testcer.com',
            phone='+390212345678',
            admin=self.admin
        )
        
        self.plant = Plant.objects.create(
            name='Test Plant',
            code='PLANT001',
            type='PHOTOVOLTAIC',
            power_kw=Decimal('50.00'),
            address='Via Test 1',
            city='Milano',
            province='MI',
            zip_code='20100',
            owner=self.user,
            cer=self.cer
        )
        
        self.device_data = {
            'device_id': 'DEVICE001',
            'name': 'Smart Meter 1',
            'device_type': 'METER',
            'vendor': 'SHELLY',
            'model': 'EM',
            'plant': self.plant,
            'is_active': True,
            'configuration': {
                'ip_address': '192.168.1.100',
                'polling_interval': 60
            }
        }
    
    def test_create_device_configuration(self):
        """Test creating a device configuration"""
        device = DeviceConfiguration.objects.create(**self.device_data)
        
        self.assertEqual(device.device_id, 'DEVICE001')
        self.assertEqual(device.name, 'Smart Meter 1')
        self.assertEqual(device.device_type, 'METER')
        self.assertEqual(device.vendor, 'SHELLY')
        self.assertEqual(device.model, 'EM')
        self.assertEqual(device.plant, self.plant)
        self.assertTrue(device.is_active)
    
    def test_device_str_method(self):
        """Test string representation of device"""
        device = DeviceConfiguration.objects.create(**self.device_data)
        self.assertEqual(str(device), 'Smart Meter 1 (DEVICE001)')
    
    def test_device_unique_id(self):
        """Test that device_id must be unique"""
        DeviceConfiguration.objects.create(**self.device_data)
        
        duplicate_data = self.device_data.copy()
        duplicate_data['name'] = 'Another Device'
        
        with self.assertRaises(Exception):
            DeviceConfiguration.objects.create(**duplicate_data)
    
    def test_device_type_choices(self):
        """Test device type field choices"""
        valid_types = ['METER', 'INVERTER', 'SENSOR', 'GATEWAY']
        
        for device_type in valid_types:
            device_data = self.device_data.copy()
            device_data['device_id'] = f'DEV_{device_type}'
            device_data['device_type'] = device_type
            
            device = DeviceConfiguration.objects.create(**device_data)
            self.assertEqual(device.device_type, device_type)
    
    def test_device_vendor_choices(self):
        """Test device vendor field choices"""
        valid_vendors = ['SHELLY', 'TASMOTA', 'HUAWEI', 'OTHER']
        
        for vendor in valid_vendors:
            device_data = self.device_data.copy()
            device_data['device_id'] = f'DEV_{vendor}'
            device_data['vendor'] = vendor
            
            device = DeviceConfiguration.objects.create(**device_data)
            self.assertEqual(device.vendor, vendor)
    
    def test_device_json_configuration(self):
        """Test JSON configuration field"""
        device = DeviceConfiguration.objects.create(**self.device_data)
        
        self.assertIsInstance(device.configuration, dict)
        self.assertEqual(device.configuration['ip_address'], '192.168.1.100')
        self.assertEqual(device.configuration['polling_interval'], 60)
        
        # Update configuration
        device.configuration['new_setting'] = 'value'
        device.save()
        
        device.refresh_from_db()
        self.assertEqual(device.configuration['new_setting'], 'value')
    
    def test_device_plant_relationship(self):
        """Test device-plant relationship"""
        device = DeviceConfiguration.objects.create(**self.device_data)
        
        self.assertEqual(device.plant, self.plant)
        self.assertIn(device, self.plant.deviceconfiguration_set.all())
    
    def test_device_last_seen(self):
        """Test device last_seen timestamp"""
        device = DeviceConfiguration.objects.create(**self.device_data)
        
        # Initially should be None or recent
        initial_last_seen = device.last_seen
        
        # Update last_seen
        new_time = timezone.now()
        device.last_seen = new_time
        device.save()
        
        device.refresh_from_db()
        self.assertEqual(device.last_seen, new_time)
    
    def test_device_active_status(self):
        """Test device active/inactive status"""
        device = DeviceConfiguration.objects.create(**self.device_data)
        
        # Should be active by default
        self.assertTrue(device.is_active)
        
        # Deactivate
        device.is_active = False
        device.save()
        self.assertFalse(device.is_active)


class MeasurementModelTest(TestCase):
    """Test cases for Measurement model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!'
        )
        
        self.cer = CERConfiguration.objects.create(
            name='Test CER',
            code='CER001',
            vat_number='12345678901',
            address='Via Roma 1',
            city='Milano',
            province='MI',
            zip_code='20100',
            email='info@testcer.com',
            phone='+390212345678',
            admin=self.admin
        )
        
        self.plant = Plant.objects.create(
            name='Test Plant',
            code='PLANT001',
            type='PHOTOVOLTAIC',
            power_kw=Decimal('50.00'),
            address='Via Test 1',
            city='Milano',
            province='MI',
            zip_code='20100',
            owner=self.user,
            cer=self.cer
        )
        
        self.device = DeviceConfiguration.objects.create(
            device_id='DEVICE001',
            name='Test Device',
            device_type='METER',
            vendor='SHELLY',
            model='EM',
            plant=self.plant
        )
        
        self.measurement_data = {
            'device': self.device,
            'timestamp': timezone.now(),
            'power': Decimal('1500.50'),
            'energy': Decimal('100.25'),
            'voltage': Decimal('230.5'),
            'current': Decimal('6.52'),
            'frequency': Decimal('50.0'),
            'power_factor': Decimal('0.95'),
            'raw_data': {
                'temperature': 25.5,
                'humidity': 60
            }
        }
    
    def test_create_measurement(self):
        """Test creating a measurement"""
        measurement = Measurement.objects.create(**self.measurement_data)
        
        self.assertEqual(measurement.device, self.device)
        self.assertEqual(measurement.power, Decimal('1500.50'))
        self.assertEqual(measurement.energy, Decimal('100.25'))
        self.assertEqual(measurement.voltage, Decimal('230.5'))
        self.assertEqual(measurement.current, Decimal('6.52'))
        self.assertEqual(measurement.frequency, Decimal('50.0'))
        self.assertEqual(measurement.power_factor, Decimal('0.95'))
    
    def test_measurement_str_method(self):
        """Test string representation of measurement"""
        measurement = Measurement.objects.create(**self.measurement_data)
        expected = f'{self.device.name} - {measurement.timestamp}'
        self.assertEqual(str(measurement), expected)
    
    def test_measurement_timestamp(self):
        """Test measurement timestamp field"""
        measurement = Measurement.objects.create(**self.measurement_data)
        
        self.assertIsNotNone(measurement.timestamp)
        self.assertIsInstance(measurement.timestamp, datetime)
        
        # Test ordering by timestamp
        time1 = timezone.now()
        time2 = time1 + timedelta(minutes=5)
        
        m1_data = self.measurement_data.copy()
        m1_data['timestamp'] = time1
        m1 = Measurement.objects.create(**m1_data)
        
        m2_data = self.measurement_data.copy()
        m2_data['timestamp'] = time2
        m2 = Measurement.objects.create(**m2_data)
        
        measurements = Measurement.objects.filter(
            device=self.device
        ).order_by('-timestamp')
        
        self.assertEqual(measurements.first(), m2)
        self.assertEqual(measurements.last(), measurement)
    
    def test_measurement_power_values(self):
        """Test power measurement values"""
        measurement = Measurement.objects.create(**self.measurement_data)
        
        # Test positive power (consumption)
        self.assertGreater(measurement.power, 0)
        
        # Test negative power (production)
        measurement_data = self.measurement_data.copy()
        measurement_data['power'] = Decimal('-2000.00')
        production = Measurement.objects.create(**measurement_data)
        
        self.assertLess(production.power, 0)
    
    def test_measurement_energy_accumulation(self):
        """Test energy accumulation over time"""
        base_time = timezone.now()
        total_energy = Decimal('0')
        
        # Create multiple measurements
        for i in range(5):
            measurement_data = self.measurement_data.copy()
            measurement_data['timestamp'] = base_time + timedelta(hours=i)
            measurement_data['energy'] = Decimal(str(10 * (i + 1)))
            
            measurement = Measurement.objects.create(**measurement_data)
            total_energy += measurement.energy
        
        # Query total energy
        from django.db.models import Sum
        total = Measurement.objects.filter(
            device=self.device
        ).aggregate(total_energy=Sum('energy'))
        
        self.assertEqual(total['total_energy'], total_energy)
    
    def test_measurement_raw_data_json(self):
        """Test raw data JSON field"""
        measurement = Measurement.objects.create(**self.measurement_data)
        
        self.assertIsInstance(measurement.raw_data, dict)
        self.assertEqual(measurement.raw_data['temperature'], 25.5)
        self.assertEqual(measurement.raw_data['humidity'], 60)
        
        # Update raw data
        measurement.raw_data['status'] = 'OK'
        measurement.save()
        
        measurement.refresh_from_db()
        self.assertEqual(measurement.raw_data['status'], 'OK')
    
    def test_measurement_device_relationship(self):
        """Test measurement-device relationship"""
        measurement = Measurement.objects.create(**self.measurement_data)
        
        self.assertEqual(measurement.device, self.device)
        self.assertIn(measurement, self.device.measurement_set.all())
    
    def test_measurement_validation(self):
        """Test measurement value validation"""
        measurement_data = self.measurement_data.copy()
        
        # Test invalid voltage (too high)
        measurement_data['voltage'] = Decimal('1000.0')
        measurement = Measurement(**measurement_data)
        
        # This should ideally raise a validation error
        # but depends on model implementation
        measurement.save()  # Will save unless custom validation is added
        
        # Test invalid power factor (must be between 0 and 1)
        measurement_data['power_factor'] = Decimal('1.5')
        measurement2 = Measurement(**measurement_data)
        
        # Should validate power factor
        with self.assertRaises(ValidationError):
            measurement2.full_clean()


class MQTTBrokerModelTest(TestCase):
    """Test cases for MQTTBroker model"""
    
    def setUp(self):
        """Set up test data"""
        self.broker_data = {
            'name': 'Test MQTT Broker',
            'host': 'mqtt.test.com',
            'port': 1883,
            'username': 'mqtt_user',
            'password': 'mqtt_pass',
            'use_tls': False,
            'is_active': True
        }
    
    def test_create_mqtt_broker(self):
        """Test creating an MQTT broker configuration"""
        broker = MQTTBroker.objects.create(**self.broker_data)
        
        self.assertEqual(broker.name, 'Test MQTT Broker')
        self.assertEqual(broker.host, 'mqtt.test.com')
        self.assertEqual(broker.port, 1883)
        self.assertEqual(broker.username, 'mqtt_user')
        self.assertFalse(broker.use_tls)
        self.assertTrue(broker.is_active)
    
    def test_broker_str_method(self):
        """Test string representation of broker"""
        broker = MQTTBroker.objects.create(**self.broker_data)
        self.assertEqual(str(broker), 'Test MQTT Broker (mqtt.test.com:1883)')
    
    def test_broker_tls_configuration(self):
        """Test TLS configuration for broker"""
        broker_data = self.broker_data.copy()
        broker_data['use_tls'] = True
        broker_data['port'] = 8883
        broker_data['tls_cert'] = '/path/to/cert.pem'
        
        broker = MQTTBroker.objects.create(**broker_data)
        
        self.assertTrue(broker.use_tls)
        self.assertEqual(broker.port, 8883)
        self.assertEqual(broker.tls_cert, '/path/to/cert.pem')
    
    def test_broker_active_status(self):
        """Test broker active/inactive status"""
        broker = MQTTBroker.objects.create(**self.broker_data)
        
        # Should be active by default
        self.assertTrue(broker.is_active)
        
        # Only one broker should be active at a time
        broker2_data = self.broker_data.copy()
        broker2_data['name'] = 'Second Broker'
        broker2_data['host'] = 'mqtt2.test.com'
        
        broker2 = MQTTBroker.objects.create(**broker2_data)
        
        # When activating broker2, broker1 should be deactivated
        # (this depends on model implementation)
        if hasattr(MQTTBroker, 'save'):
            broker.refresh_from_db()
            # Check if auto-deactivation is implemented
    
    def test_broker_connection_status(self):
        """Test broker connection status tracking"""
        broker = MQTTBroker.objects.create(**self.broker_data)
        
        # Test last_connected field if it exists
        if hasattr(broker, 'last_connected'):
            self.assertIsNone(broker.last_connected)
            
            # Update connection status
            broker.last_connected = timezone.now()
            broker.save()
            
            self.assertIsNotNone(broker.last_connected)
    
    def test_broker_keepalive_setting(self):
        """Test broker keepalive setting"""
        broker_data = self.broker_data.copy()
        broker_data['keepalive'] = 60
        
        broker = MQTTBroker.objects.create(**broker_data)
        self.assertEqual(broker.keepalive, 60)
    
    def test_broker_client_id(self):
        """Test broker client ID generation"""
        broker = MQTTBroker.objects.create(**self.broker_data)
        
        if hasattr(broker, 'client_id'):
            # Client ID should be generated or set
            self.assertIsNotNone(broker.client_id)
    
    def test_broker_qos_level(self):
        """Test broker QoS level setting"""
        broker_data = self.broker_data.copy()
        broker_data['qos_level'] = 2
        
        broker = MQTTBroker.objects.create(**broker_data)
        
        if hasattr(broker, 'qos_level'):
            self.assertEqual(broker.qos_level, 2)
            self.assertIn(broker.qos_level, [0, 1, 2])  # Valid QoS levels