"""
Unit tests for Django admin configuration.
Tests admin registration, list displays, and filters for OperatingSystem, Team, and IPRange models.
"""
import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from assets.models import OperatingSystem, Team, IPRange
from assets.admin import OperatingSystemAdmin, TeamAdmin, IPRangeAdmin


class AdminRegistrationTests(TestCase):
    """Test that models are properly registered in Django admin."""

    def test_operating_system_registered(self):
        """Test that OperatingSystem model is registered in admin (Requirement 9.1)."""
        self.assertIn(OperatingSystem, admin.site._registry)
        self.assertIsInstance(admin.site._registry[OperatingSystem], OperatingSystemAdmin)

    def test_team_registered(self):
        """Test that Team model is registered in admin (Requirement 10.1)."""
        self.assertIn(Team, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Team], TeamAdmin)

    def test_ip_range_registered(self):
        """Test that IPRange model is registered in admin (Requirement 11.1)."""
        self.assertIn(IPRange, admin.site._registry)
        self.assertIsInstance(admin.site._registry[IPRange], IPRangeAdmin)


class OperatingSystemAdminTests(TestCase):
    """Test OperatingSystem admin configuration."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')

    def test_list_display_fields(self):
        """Test that OperatingSystem admin shows correct list display fields."""
        admin_instance = admin.site._registry[OperatingSystem]
        self.assertEqual(admin_instance.list_display, ['name', 'created_at'])

    def test_search_fields(self):
        """Test that OperatingSystem admin has search functionality."""
        admin_instance = admin.site._registry[OperatingSystem]
        self.assertEqual(admin_instance.search_fields, ['name'])

    def test_list_filter(self):
        """Test that OperatingSystem admin has filter functionality."""
        admin_instance = admin.site._registry[OperatingSystem]
        self.assertEqual(admin_instance.list_filter, ['created_at'])

    def test_admin_can_add_operating_system(self):
        """Test that admin users can add operating systems through admin interface."""
        response = self.client.post(
            reverse('admin:assets_operatingsystem_add'),
            {'name': 'Windows 11'}
        )
        self.assertEqual(OperatingSystem.objects.filter(name='Windows 11').count(), 1)

    def test_admin_can_view_operating_system_list(self):
        """Test that admin users can view operating system list."""
        OperatingSystem.objects.create(name='Ubuntu 22.04')
        response = self.client.get(reverse('admin:assets_operatingsystem_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ubuntu 22.04')


class TeamAdminTests(TestCase):
    """Test Team admin configuration."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')

    def test_list_display_fields(self):
        """Test that Team admin shows correct list display fields."""
        admin_instance = admin.site._registry[Team]
        self.assertEqual(admin_instance.list_display, ['name', 'created_at'])

    def test_search_fields(self):
        """Test that Team admin has search functionality."""
        admin_instance = admin.site._registry[Team]
        self.assertEqual(admin_instance.search_fields, ['name'])

    def test_list_filter(self):
        """Test that Team admin has filter functionality."""
        admin_instance = admin.site._registry[Team]
        self.assertEqual(admin_instance.list_filter, ['created_at'])

    def test_admin_can_add_team(self):
        """Test that admin users can add teams through admin interface."""
        response = self.client.post(
            reverse('admin:assets_team_add'),
            {'name': 'Engineering'}
        )
        self.assertEqual(Team.objects.filter(name='Engineering').count(), 1)

    def test_admin_can_view_team_list(self):
        """Test that admin users can view team list."""
        Team.objects.create(name='Marketing')
        response = self.client.get(reverse('admin:assets_team_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marketing')


class IPRangeAdminTests(TestCase):
    """Test IPRange admin configuration."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')

    def test_list_display_fields(self):
        """Test that IPRange admin shows correct list display fields."""
        admin_instance = admin.site._registry[IPRange]
        self.assertEqual(admin_instance.list_display, ['range_pattern', 'network_prefix', 'created_at'])

    def test_search_fields(self):
        """Test that IPRange admin has search functionality."""
        admin_instance = admin.site._registry[IPRange]
        self.assertEqual(admin_instance.search_fields, ['range_pattern', 'network_prefix'])

    def test_list_filter(self):
        """Test that IPRange admin has filter functionality."""
        admin_instance = admin.site._registry[IPRange]
        self.assertEqual(admin_instance.list_filter, ['created_at'])

    def test_admin_can_add_ip_range(self):
        """Test that admin users can add IP ranges through admin interface."""
        response = self.client.post(
            reverse('admin:assets_iprange_add'),
            {'range_pattern': '192.168.10.x', 'network_prefix': '192.168.10'}
        )
        self.assertEqual(IPRange.objects.filter(range_pattern='192.168.10.x').count(), 1)

    def test_admin_can_view_ip_range_list(self):
        """Test that admin users can view IP range list."""
        IPRange.objects.create(range_pattern='192.168.11.x', network_prefix='192.168.11')
        response = self.client.get(reverse('admin:assets_iprange_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '192.168.11.x')


class AdminPermissionTests(TestCase):
    """Test that only admin users can access the admin interface."""

    def setUp(self):
        self.regular_user = User.objects.create_user(
            username='user',
            password='userpass123'
        )
        self.client = Client()

    def test_non_admin_cannot_access_operating_system_admin(self):
        """Test that non-admin users cannot access OperatingSystem admin."""
        self.client.login(username='user', password='userpass123')
        response = self.client.get(reverse('admin:assets_operatingsystem_changelist'))
        # Should redirect to login or show 403
        self.assertIn(response.status_code, [302, 403])

    def test_non_admin_cannot_access_team_admin(self):
        """Test that non-admin users cannot access Team admin."""
        self.client.login(username='user', password='userpass123')
        response = self.client.get(reverse('admin:assets_team_changelist'))
        # Should redirect to login or show 403
        self.assertIn(response.status_code, [302, 403])

    def test_non_admin_cannot_access_ip_range_admin(self):
        """Test that non-admin users cannot access IPRange admin."""
        self.client.login(username='user', password='userpass123')
        response = self.client.get(reverse('admin:assets_iprange_changelist'))
        # Should redirect to login or show 403
        self.assertIn(response.status_code, [302, 403])
