"""
Test suite for Core app models
"""

from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TransactionTestCase

from core.main_models import Alert, CERConfiguration, CERMembership, Plant

User = get_user_model()


class CERConfigurationModelTest(TransactionTestCase):
    """Test cases for CERConfiguration model"""

    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="User",
        )

        # Use unique identifiers to avoid conflicts
        import time
        unique_id = str(int(time.time() * 1000))[-6:]  # Last 6 digits of timestamp
        self.cer_data = {
            "name": f"Test CER Community {unique_id}",
            "code": f"CER{unique_id}",
            "primary_substation": "Cabina Primaria Test",
            "description": "Test CER Description",
        }

    def test_create_cer_configuration(self):
        """Test creating a CER configuration"""
        cer = CERConfiguration.objects.create(**self.cer_data)

        self.assertEqual(cer.name, self.cer_data["name"])
        self.assertEqual(cer.code, self.cer_data["code"])
        self.assertEqual(cer.primary_substation, "Cabina Primaria Test")
        self.assertEqual(cer.description, "Test CER Description")
        self.assertTrue(cer.is_active)

    def test_cer_str_method(self):
        """Test string representation of CER"""
        cer = CERConfiguration.objects.create(**self.cer_data)
        expected_str = f"{self.cer_data['name']} ({self.cer_data['code']})"
        self.assertEqual(str(cer), expected_str)

    def test_cer_unique_code(self):
        """Test that CER code must be unique"""
        CERConfiguration.objects.create(**self.cer_data)

        duplicate_data = self.cer_data.copy()
        duplicate_data["name"] = "Another CER"

        with self.assertRaises(Exception):
            CERConfiguration.objects.create(**duplicate_data)

    def test_cer_timestamps(self):
        """Test CER has timestamp fields"""
        cer = CERConfiguration.objects.create(**self.cer_data)

        self.assertIsNotNone(cer.created_at)
        self.assertIsNotNone(cer.updated_at)
        self.assertIsInstance(cer.created_at, datetime)
        self.assertIsInstance(cer.updated_at, datetime)

    def test_cer_active_status(self):
        """Test CER active/inactive status"""
        cer = CERConfiguration.objects.create(**self.cer_data)

        # Should be active by default
        self.assertTrue(cer.is_active)

        # Deactivate
        cer.is_active = False
        cer.save()
        self.assertFalse(cer.is_active)


class PlantModelTest(TransactionTestCase):
    """Test cases for Plant model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="TestPass123!",
            first_name="Plant",
            last_name="Owner",
        )

        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="User",
        )

        # Use unique identifier to avoid conflicts
        import time
        unique_id = str(int(time.time() * 1000))[-6:]
        self.cer = CERConfiguration.objects.create(
            name=f"Test CER {unique_id}",
            code=f"CER{unique_id}",
            primary_substation="Cabina Primaria Test",
            description="Test CER Description",
        )

        self.plant_data = {
            "name": "Solar Plant 1",
            "code": "PLANT001",
            "type": "PRODUCER",
            "power_kw": Decimal("100.50"),
            "address": "Via Milano 10",
            "city": "Milano",
            "province": "MI",
            "zip_code": "20100",
            "latitude": Decimal("45.4642"),
            "longitude": Decimal("9.1900"),
            "owner": self.user,
            "cer_configuration": self.cer,
            "is_active": True,
            "connection_voltage": "400V",
            "installation_date": "2023-01-01",
        }

    def test_create_plant(self):
        """Test creating a plant"""
        plant = Plant.objects.create(**self.plant_data)

        self.assertEqual(plant.name, "Solar Plant 1")
        self.assertEqual(plant.code, "PLANT001")
        self.assertEqual(plant.type, "PRODUCER")
        self.assertEqual(plant.power_kw, Decimal("100.50"))
        self.assertEqual(plant.owner, self.user)
        self.assertEqual(plant.cer_configuration, self.cer)
        self.assertTrue(plant.is_active)

    def test_plant_str_method(self):
        """Test string representation of plant"""
        plant = Plant.objects.create(**self.plant_data)
        self.assertEqual(str(plant), "Solar Plant 1 (PLANT001)")

    def test_plant_coordinates(self):
        """Test plant geographical coordinates"""
        plant = Plant.objects.create(**self.plant_data)

        self.assertEqual(plant.latitude, Decimal("45.4642"))
        self.assertEqual(plant.longitude, Decimal("9.1900"))

        # Test coordinate validation bounds
        plant.latitude = Decimal("91.0")  # Invalid latitude
        with self.assertRaises(ValidationError):
            plant.full_clean()

    def test_plant_power_validation(self):
        """Test plant power validation"""
        plant_data = self.plant_data.copy()

        # Test negative power
        plant_data["power_kw"] = Decimal("-10.0")
        plant = Plant(**plant_data)

        with self.assertRaises(ValidationError):
            plant.full_clean()

    def test_plant_type_choices(self):
        """Test plant type field choices"""
        valid_types = ["CONSUMER", "PRODUCER", "PROSUMER"]

        for plant_type in valid_types:
            plant_data = self.plant_data.copy()
            plant_data["code"] = f"PLANT_{plant_type}"
            plant_data["type"] = plant_type

            plant = Plant.objects.create(**plant_data)
            self.assertEqual(plant.type, plant_type)

    def test_plant_owner_relationship(self):
        """Test plant-owner relationship"""
        plant = Plant.objects.create(**self.plant_data)

        self.assertEqual(plant.owner, self.user)
        self.assertIn(plant, self.user.plants.all())

    def test_plant_cer_relationship(self):
        """Test plant-CER relationship"""
        plant = Plant.objects.create(**self.plant_data)

        self.assertEqual(plant.cer_configuration, self.cer)
        self.assertIn(plant, self.cer.plants.all())

    def test_plant_timestamps(self):
        """Test plant timestamp fields"""
        plant = Plant.objects.create(**self.plant_data)

        self.assertIsNotNone(plant.created_at)
        self.assertIsNotNone(plant.updated_at)

    def test_plant_pod_field(self):
        """Test POD (Point of Delivery) field"""
        plant_data = self.plant_data.copy()
        plant_data["pod"] = "IT001E12345678"

        plant = Plant.objects.create(**plant_data)
        self.assertEqual(plant.pod, "IT001E12345678")

    def test_plant_commissioning_date(self):
        """Test plant commissioning date"""
        plant_data = self.plant_data.copy()
        plant_data["commissioning_date"] = date(2023, 1, 15)

        plant = Plant.objects.create(**plant_data)
        self.assertEqual(plant.commissioning_date, date(2023, 1, 15))


class CERMembershipModelTest(TransactionTestCase):
    """Test cases for CERMembership model"""

    def setUp(self):
        """Set up test data"""
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="User",
        )

        self.member = User.objects.create_user(
            email="member@example.com",
            password="TestPass123!",
            first_name="Member",
            last_name="User",
        )

        # Use unique identifier to avoid conflicts
        import time
        unique_id = str(int(time.time() * 1000))[-6:]
        self.cer = CERConfiguration.objects.create(
            name=f"Test CER {unique_id}",
            code=f"CER{unique_id}",
            primary_substation="Cabina Primaria Test",
            description="Test CER Description",
        )

    def test_create_membership(self):
        """Test creating a CER membership"""
        membership = CERMembership.objects.create(
            cer_configuration=self.cer,
            user=self.member,
            role="MEMBER",
            share_percentage=Decimal("10.00"),
        )

        self.assertEqual(membership.cer_configuration, self.cer)
        self.assertEqual(membership.user, self.member)
        self.assertEqual(membership.role, "MEMBER")
        self.assertEqual(membership.share_percentage, Decimal("10.00"))
        self.assertTrue(membership.is_active)

    def test_membership_str_method(self):
        """Test string representation of membership"""
        membership = CERMembership.objects.create(
            cer_configuration=self.cer, user=self.member, role="MEMBER"
        )
        expected = f"{self.member.username} - {self.cer.name}"
        self.assertEqual(str(membership), expected)

    def test_membership_role_choices(self):
        """Test membership role field choices"""
        valid_roles = ["ADMIN", "MEMBER", "TECHNICAL"]

        for role in valid_roles:
            membership = CERMembership.objects.create(
                cer_configuration=self.cer,
                user=User.objects.create_user(
                    email=f"{role}@example.com",
                    password="TestPass123!",
                    first_name="Test",
                    last_name="User",
                ),
                role=role,
            )
            self.assertEqual(membership.role, role)

    def test_membership_unique_constraint(self):
        """Test that a user can only have one membership per CER"""
        CERMembership.objects.create(
            cer_configuration=self.cer, user=self.member, role="MEMBER"
        )

        # Try to create duplicate membership
        with self.assertRaises(Exception):
            CERMembership.objects.create(
                cer_configuration=self.cer, user=self.member, role="TECHNICAL"
            )

    def test_membership_share_percentage_validation(self):
        """Test share percentage validation"""
        membership = CERMembership(
            cer_configuration=self.cer,
            user=self.member,
            role="MEMBER",
            share_percentage=Decimal("150.00"),  # Invalid: > 100%
        )

        with self.assertRaises(ValidationError):
            membership.full_clean()

    def test_membership_dates(self):
        """Test membership date fields"""
        membership = CERMembership.objects.create(
            cer_configuration=self.cer,
            user=self.member,
            role="MEMBER",
            joined_date=date(2024, 1, 1),
        )

        self.assertEqual(membership.joined_date, date(2024, 1, 1))
        self.assertIsNotNone(membership.joined_at)
        self.assertIsNotNone(membership.created_at)
        self.assertIsNotNone(membership.updated_at)


class AlertModelTest(TransactionTestCase):
    """Test cases for Alert model"""

    def setUp(self):
        """Set up test data"""
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="User",
        )

        self.user = User.objects.create_user(
            email="user@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User",
        )

        # Use unique identifier to avoid conflicts
        import time
        unique_id = str(int(time.time() * 1000))[-6:]
        self.cer = CERConfiguration.objects.create(
            name=f"Test CER {unique_id}",
            code=f"CER{unique_id}",
            primary_substation="Cabina Primaria Test",
            description="Test CER Description",
        )

        self.plant = Plant.objects.create(
            name="Test Plant",
            code="PLANT001",
            type="PRODUCER",
            power_kw=Decimal("50.00"),
            address="Via Test 1",
            city="Milano",
            province="MI",
            zip_code="20100",
            owner=self.user,
            cer_configuration=self.cer,
            connection_voltage="400V",
            installation_date="2023-01-01",
        )

    def test_create_alert(self):
        """Test creating an alert"""
        alert = Alert.objects.create(
            type="WARNING",
            title="Low Production Alert",
            message="Plant production below threshold",
            plant=self.plant,
            user=self.user,
        )

        self.assertEqual(alert.type, "WARNING")
        self.assertEqual(alert.title, "Low Production Alert")
        self.assertEqual(alert.plant, self.plant)
        self.assertEqual(alert.user, self.user)
        self.assertFalse(alert.is_read)

    def test_alert_str_method(self):
        """Test string representation of alert"""
        alert = Alert.objects.create(
            type="ERROR", title="System Error", message="Critical system error detected"
        )
        self.assertEqual(str(alert), "ERROR: System Error")

    def test_alert_type_choices(self):
        """Test alert type field choices"""
        valid_types = ["INFO", "WARNING", "ERROR", "CRITICAL"]

        for alert_type in valid_types:
            alert = Alert.objects.create(
                type=alert_type,
                title=f"{alert_type} Alert",
                message=f"This is a {alert_type} alert",
            )
            self.assertEqual(alert.type, alert_type)

    def test_alert_read_status(self):
        """Test alert read/unread status"""
        alert = Alert.objects.create(
            type="INFO", title="Info Alert", message="Informational message"
        )

        # Should be unread by default
        self.assertFalse(alert.is_read)

        # Mark as read
        alert.is_read = True
        alert.save()
        self.assertTrue(alert.is_read)

    def test_alert_relationships(self):
        """Test alert relationships with plant and user"""
        alert = Alert.objects.create(
            type="WARNING",
            title="Plant Alert",
            message="Plant-specific alert",
            plant=self.plant,
            user=self.user,
        )

        self.assertEqual(alert.plant, self.plant)
        self.assertEqual(alert.user, self.user)
        self.assertIn(alert, self.plant.alerts.all())
        self.assertIn(alert, self.user.alerts.all())

    def test_alert_timestamps(self):
        """Test alert timestamp fields"""
        alert = Alert.objects.create(
            type="INFO", title="Test Alert", message="Test message"
        )

        self.assertIsNotNone(alert.created_at)
        self.assertIsNotNone(alert.updated_at)
