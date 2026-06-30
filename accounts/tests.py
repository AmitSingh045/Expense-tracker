from django.test import TestCase
from django.urls import reverse
from accounts.models import User, Profile
from rest_framework.test import APITestCase
from rest_framework import status

class AccountModelTests(TestCase):
    def test_user_creation_signal_creates_profile(self):
        # Create a new user
        user = User.objects.create_user(username='testuser', email='test@example.com', password='Password123')
        
        # Verify user exists
        self.assertEqual(user.username, 'testuser')
        
        # Verify profile was automatically created by signal
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.preferred_currency, 'USD')

class AccountAPITests(APITestCase):
    def test_api_registration(self):
        url = reverse('api_register')
        data = {
            'username': 'apiuser',
            'email': 'apiuser@example.com',
            'password': 'Password123',
            'first_name': 'API',
            'last_name': 'User'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'apiuser')
        self.assertEqual(User.objects.filter(username='apiuser').count(), 1)

    def test_api_profile_requires_auth(self):
        url = reverse('api_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class AdminPanelTests(TestCase):
    def setUp(self):
        from django.core.management import call_command
        # Setup roles and groups
        call_command('setup_roles')

    def test_groups_exist(self):
        from django.contrib.auth.models import Group
        self.assertTrue(Group.objects.filter(name='Manager').exists())
        self.assertTrue(Group.objects.filter(name='Staff').exists())
        self.assertTrue(Group.objects.filter(name='Read-Only Auditor').exists())
        
        # Verify Auditor has view permissions
        auditor = Group.objects.get(name='Read-Only Auditor')
        self.assertTrue(auditor.permissions.filter(codename='view_transaction').exists())
        # Auditor should NOT have add/change/delete permissions
        self.assertFalse(auditor.permissions.filter(codename='delete_transaction').exists())

    def test_user_admin_lock_action(self):
        # Create users
        u1 = User.objects.create_user(username='u1', email='u1@example.com', password='Pass')
        u2 = User.objects.create_user(username='u2', email='u2@example.com', password='Pass')
        
        from accounts.admin import UserAdmin
        from django.contrib.admin.sites import AdminSite
        
        site = AdminSite()
        user_admin = UserAdmin(User, site)
        from django.test import RequestFactory
        from django.contrib.messages.storage.cookie import CookieStorage
        
        factory = RequestFactory()
        request = factory.post('/admin/')
        setattr(request, '_messages', CookieStorage(request))
        
        queryset = User.objects.filter(username__in=['u1', 'u2'])
        user_admin.lock_accounts(request, queryset)
        
        u1.refresh_from_db()
        u2.refresh_from_db()
        self.assertFalse(u1.is_active)
        self.assertFalse(u2.is_active)

