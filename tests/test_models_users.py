"""
Test suite for Users app models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

User = get_user_model()


class CustomUserModelTest(TestCase):
    """Test cases for CustomUser model"""
    
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'fiscal_code': 'RSSMRA80A01H501X',
            'phone': '+393331234567'
        }
    
    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name']
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('TestPass123!'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User'
        )
        
        self.assertEqual(admin_user.username, 'admin')
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_active)
    
    def test_user_str_method(self):
        """Test the string representation of user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        self.assertEqual(str(user), 'testuser (Privato)')
    
    def test_user_full_name(self):
        """Test user full name property"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user.get_full_name(), 'John Doe')
    
    def test_unique_username(self):
        """Test that username must be unique"""
        User.objects.create_user(
            username='testuser',
            email='test1@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='testuser',
                email='test2@example.com',
                password='TestPass123!',
                first_name='Test',
                last_name='User'
            )
    
    def test_email_field(self):
        """Test email field validation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        # Test valid email format
        user.email = 'newemail@example.com'
        user.full_clean()  # Should not raise
        
        # Test invalid email format
        user.email = 'invalid-email'
        with self.assertRaises(ValidationError):
            user.full_clean()
    
    def test_user_permissions(self):
        """Test user permission methods"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        # Regular user shouldn't have any permissions by default
        self.assertFalse(user.has_perm('core.add_plant'))
        self.assertFalse(user.has_module_perms('core'))
        
        # Superuser should have all permissions
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User'
        )
        self.assertTrue(admin.has_perm('core.add_plant'))
        self.assertTrue(admin.has_module_perms('core'))
    
    def test_user_groups(self):
        """Test user group relationships"""
        from django.contrib.auth.models import Group
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        group = Group.objects.create(name='CER Members')
        user.groups.add(group)
        
        self.assertIn(group, user.groups.all())
        self.assertEqual(user.groups.count(), 1)
    
    def test_user_profile_fields(self):
        """Test custom profile fields if they exist"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        # Test fiscal code field if it exists
        if hasattr(user, 'fiscal_code'):
            user.fiscal_code = 'RSSMRA80A01H501X'
            user.save()
            self.assertEqual(user.fiscal_code, 'RSSMRA80A01H501X')
        
        # Test phone field if it exists
        if hasattr(user, 'phone'):
            user.phone = '+393331234567'
            user.save()
            self.assertEqual(user.phone, '+393331234567')
    
    def test_user_timestamps(self):
        """Test that user has timestamp fields"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        self.assertIsNotNone(user.date_joined)
        self.assertTrue(hasattr(user, 'last_login'))
    
    def test_user_active_status(self):
        """Test user active/inactive status"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        # User should be active by default
        self.assertTrue(user.is_active)
        
        # Deactivate user
        user.is_active = False
        user.save()
        
        # Inactive user shouldn't be able to authenticate
        from django.contrib.auth import authenticate
        auth_user = authenticate(username='testuser', password='TestPass123!')
        self.assertIsNone(auth_user)