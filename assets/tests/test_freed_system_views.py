"""
Unit tests for freed system views (FreedSystemCreateView, FreedSystemEditView, FreeSystemsView).
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from assets.models import Asset, OperatingSystem, Team, IPAddress, IPRange


class TestFreeSystemsView(TestCase):
    """Test cases for FreeSystemsView."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test OS
        self.os = OperatingSystem.objects.create(name="Windows 10")
        
        # Create IP range and IP address
        self.ip_range = IPRange.objects.create(
            range_pattern="192.168.10.x",
            network_prefix="192.168.10"
        )
        self.ip = IPAddress.objects.create(
            address="192.168.10.100",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create freed assets with different health statuses
        self.freed_healthy = Asset.objects.create(
            asset_tag="BIDC001",
            system_type="Desktop",
            operating_system=self.os,
            ip_address=self.ip,
            status="freed",
            freed_date=timezone.now(),
            health_status="healthy"
        )
        
        self.freed_defective = Asset.objects.create(
            asset_tag="BIDC002",
            system_type="Laptop",
            operating_system=self.os,
            status="freed",
            freed_date=timezone.now(),
            health_status="defective",
            issues_description="Screen is cracked and keyboard not working"
        )
        
        self.freed_no_health = Asset.objects.create(
            asset_tag="BIDC003",
            system_type="Desktop",
            operating_system=self.os,
            status="freed",
            freed_date=timezone.now(),
            health_status=None
        )
        
        # Create active asset (should not appear in freed list)
        self.active_asset = Asset.objects.create(
            asset_tag="BIDC004",
            system_type="Desktop",
            operating_system=self.os,
            status="active"
        )
    
    def test_free_systems_view_requires_login(self):
        """Test that the view requires authentication."""
        response = self.client.get(reverse('freed_systems'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/login/', response.url)
    
    def test_free_systems_view_url_exists(self):
        """Test that the freed systems URL exists."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/assets/freed/')
        self.assertEqual(response.status_code, 200)
    
    def test_free_systems_view_url_by_name(self):
        """Test that the freed systems URL can be accessed by name."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('freed_systems'))
        self.assertEqual(response.status_code, 200)
    
    def test_free_systems_view_uses_correct_template(self):
        """Test that the view uses the correct template."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('freed_systems'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/freed_systems.html')
    
    def test_free_systems_view_shows_only_freed_assets(self):
        """Test that only freed assets are displayed (Requirement 4.4)."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('freed_systems'))
        self.assertEqual(response.status_code, 200)
        
        freed_assets = response.context['freed_assets']
        self.assertEqual(len(freed_assets), 3)
        
        # Verify freed assets are present
        asset_tags = [asset.asset_tag for asset in freed_assets]
        self.assertIn('BIDC001', asset_tags)
        self.assertIn('BIDC002', asset_tags)
        self.assertIn('BIDC003', asset_tags)
        
        # Verify active asset is not present
        self.assertNotIn('BIDC004', asset_tags)
    
    def test_free_systems_view_orders_by_freed_date_descending(self):
        """Test that assets are ordered by freed_date descending."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('freed_systems'))
        self.assertEqual(response.status_code, 200)
        
        freed_assets = list(response.context['freed_assets'])
        
        # Verify ordering (most recent first)
        for i in range(len(freed_assets) - 1):
            self.assertGreaterEqual(
                freed_assets[i].freed_date,
                freed_assets[i + 1].freed_date
            )
    
    def test_free_systems_view_displays_health_status(self):
        """Test that health status is available in context (Requirement 2.4)."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('freed_systems'))
        self.assertEqual(response.status_code, 200)
        
        freed_assets = response.context['freed_assets']
        
        # Find each asset and verify health_status
        for asset in freed_assets:
            if asset.asset_tag == 'BIDC001':
                self.assertEqual(asset.health_status, 'healthy')
            elif asset.asset_tag == 'BIDC002':
                self.assertEqual(asset.health_status, 'defective')
                self.assertIsNotNone(asset.issues_description)
            elif asset.asset_tag == 'BIDC003':
                self.assertIsNone(asset.health_status)
    
    def test_free_systems_view_with_no_freed_assets(self):
        """Test that the view handles empty freed list gracefully."""
        # Delete all freed assets
        Asset.objects.filter(status='freed').delete()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('freed_systems'))
        self.assertEqual(response.status_code, 200)
        
        freed_assets = response.context['freed_assets']
        self.assertEqual(len(freed_assets), 0)


class TestFreedSystemCreateView(TestCase):
    """Test cases for FreedSystemCreateView."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user',
            password='userpass123',
            is_staff=False
        )
        
        # Create test OS
        self.os = OperatingSystem.objects.create(name="Windows 10")
    
    def test_freed_system_create_view_requires_admin(self):
        """Test that non-admin users cannot access create view (Requirement 1.1)."""
        self.client.login(username='user', password='userpass123')
        response = self.client.get(reverse('freed_system_create'))
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_freed_system_create_view_allows_admin(self):
        """Test that admin users can access create view."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('freed_system_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_freed_system_create_view_displays_form(self):
        """Test that create view displays FreedSystemForm."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('freed_system_create'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
    
    def test_freed_system_create_view_uses_correct_template(self):
        """Test that create view uses correct template."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('freed_system_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/freed_system_create.html')
    
    def test_freed_system_create_view_creates_freed_asset(self):
        """Test that POST creates a new freed asset (Requirement 1.2, 1.3)."""
        self.client.login(username='admin', password='adminpass123')
        
        data = {
            'asset_tag': 'BIDC100',
            'system_type': 'Desktop',
            'operating_system': self.os.id,
            'health_status': 'healthy',
            'manual_ip': '192.168.1.50'
        }
        
        response = self.client.post(reverse('freed_system_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify asset was created
        asset = Asset.objects.get(asset_tag='BIDC100')
        self.assertEqual(asset.status, 'freed')
        self.assertEqual(asset.health_status, 'healthy')
        self.assertIsNotNone(asset.freed_date)
        self.assertIsNone(asset.assigned_to)
        self.assertIsNone(asset.team)
    
    def test_freed_system_create_view_rejects_duplicate_asset_tag(self):
        """Test that duplicate asset tags are rejected (Requirement 1.4)."""
        # Create existing asset
        Asset.objects.create(
            asset_tag='BIDC100',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        
        self.client.login(username='admin', password='adminpass123')
        
        data = {
            'asset_tag': 'BIDC100',
            'system_type': 'Laptop',
            'operating_system': self.os.id,
            'health_status': 'healthy'
        }
        
        response = self.client.post(reverse('freed_system_create'), data)
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        
        # Verify error message
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
    
    def test_freed_system_create_view_requires_health_status(self):
        """Test that health_status is required (Requirement 2.2)."""
        self.client.login(username='admin', password='adminpass123')
        
        data = {
            'asset_tag': 'BIDC100',
            'system_type': 'Desktop',
            'operating_system': self.os.id,
            # health_status missing
        }
        
        response = self.client.post(reverse('freed_system_create'), data)
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        
        # Verify error message
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
    
    def test_freed_system_create_view_defective_requires_issues(self):
        """Test that defective status requires issues_description (Requirement 3.2, 3.4)."""
        self.client.login(username='admin', password='adminpass123')
        
        data = {
            'asset_tag': 'BIDC100',
            'system_type': 'Desktop',
            'operating_system': self.os.id,
            'health_status': 'defective',
            # issues_description missing
        }
        
        response = self.client.post(reverse('freed_system_create'), data)
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        
        # Verify error message
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
    
    def test_freed_system_create_view_healthy_allows_empty_issues(self):
        """Test that healthy status allows empty issues_description (Requirement 3.3)."""
        self.client.login(username='admin', password='adminpass123')
        
        data = {
            'asset_tag': 'BIDC100',
            'system_type': 'Desktop',
            'operating_system': self.os.id,
            'health_status': 'healthy',
            'issues_description': ''  # Empty is allowed
        }
        
        response = self.client.post(reverse('freed_system_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify asset was created
        asset = Asset.objects.get(asset_tag='BIDC100')
        self.assertEqual(asset.health_status, 'healthy')
    
    def test_freed_system_create_view_success_message(self):
        """Test that success message is displayed after creation."""
        self.client.login(username='admin', password='adminpass123')
        
        data = {
            'asset_tag': 'BIDC100',
            'system_type': 'Desktop',
            'operating_system': self.os.id,
            'health_status': 'healthy'
        }
        
        response = self.client.post(reverse('freed_system_create'), data, follow=True)
        
        # Check for success message
        messages = list(response.context['messages'])
        self.assertTrue(any('created successfully' in str(m) for m in messages))


class TestFreedSystemEditView(TestCase):
    """Test cases for FreedSystemEditView."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user',
            password='userpass123',
            is_staff=False
        )
        
        # Create test OS
        self.os = OperatingSystem.objects.create(name="Windows 10")
        
        # Create freed asset
        self.freed_asset = Asset.objects.create(
            asset_tag='BIDC100',
            system_type='Desktop',
            operating_system=self.os,
            status='freed',
            freed_date=timezone.now(),
            health_status='healthy'
        )
        
        # Create active asset (should not be editable via this view)
        self.active_asset = Asset.objects.create(
            asset_tag='BIDC200',
            system_type='Laptop',
            operating_system=self.os,
            status='active'
        )
    
    def test_freed_system_edit_view_requires_admin(self):
        """Test that non-admin users cannot access edit view (Requirement 5.1)."""
        self.client.login(username='user', password='userpass123')
        response = self.client.get(
            reverse('freed_system_edit', kwargs={'pk': self.freed_asset.pk})
        )
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_freed_system_edit_view_allows_admin(self):
        """Test that admin users can access edit view."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(
            reverse('freed_system_edit', kwargs={'pk': self.freed_asset.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_freed_system_edit_view_only_shows_freed_assets(self):
        """Test that view only allows editing freed assets (Requirement 5.1)."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(
            reverse('freed_system_edit', kwargs={'pk': self.active_asset.pk})
        )
        self.assertEqual(response.status_code, 404)  # Not found
    
    def test_freed_system_edit_view_displays_form(self):
        """Test that edit view displays FreedSystemEditForm."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(
            reverse('freed_system_edit', kwargs={'pk': self.freed_asset.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
    
    def test_freed_system_edit_view_uses_correct_template(self):
        """Test that edit view uses correct template."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(
            reverse('freed_system_edit', kwargs={'pk': self.freed_asset.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/freed_system_edit.html')
    
    def test_freed_system_edit_view_form_prepopulated(self):
        """Test that form is pre-populated with current data (Requirement 5.2)."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(
            reverse('freed_system_edit', kwargs={'pk': self.freed_asset.pk})
        )
        self.assertEqual(response.status_code, 200)
        
        form = response.context['form']
        self.assertEqual(form.initial.get('health_status') or form.instance.health_status, 'healthy')
    
    def test_freed_system_edit_view_updates_asset(self):
        """Test that POST updates the asset (Requirement 5.5)."""
        self.client.login(username='admin', password='adminpass123')
        
        data = {
            'health_status': 'defective',
            'issues_description': 'Hard drive failed',
            'particulars': 'Needs replacement'
        }
        
        response = self.client.post(
            reverse('freed_system_edit', kwargs={'pk': self.freed_asset.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify asset was updated
        self.freed_asset.refresh_from_db()
        self.assertEqual(self.freed_asset.health_status, 'defective')
        self.assertEqual(self.freed_asset.issues_description, 'Hard drive failed')
    
    def test_freed_system_edit_view_defective_requires_issues(self):
        """Test that changing to defective requires issues_description (Requirement 5.3)."""
        self.client.login(username='admin', password='adminpass123')
        
        data = {
            'health_status': 'defective',
            'issues_description': '',  # Empty
        }
        
        response = self.client.post(
            reverse('freed_system_edit', kwargs={'pk': self.freed_asset.pk}),
            data
        )
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        
        # Verify error message
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
    
    def test_freed_system_edit_view_healthy_allows_clearing_issues(self):
        """Test that changing to healthy allows clearing issues_description (Requirement 5.4)."""
        # First set asset to defective with issues
        self.freed_asset.health_status = 'defective'
        self.freed_asset.issues_description = 'Some issue'
        self.freed_asset.save()
        
        self.client.login(username='admin', password='adminpass123')
        
        data = {
            'health_status': 'healthy',
            'issues_description': '',  # Cleared
        }
        
        response = self.client.post(
            reverse('freed_system_edit', kwargs={'pk': self.freed_asset.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify asset was updated
        self.freed_asset.refresh_from_db()
        self.assertEqual(self.freed_asset.health_status, 'healthy')
    
    def test_freed_system_edit_view_success_message(self):
        """Test that success message is displayed after update."""
        self.client.login(username='admin', password='adminpass123')
        
        data = {
            'health_status': 'defective',
            'issues_description': 'Hard drive failed'
        }
        
        response = self.client.post(
            reverse('freed_system_edit', kwargs={'pk': self.freed_asset.pk}),
            data,
            follow=True
        )
        
        # Check for success message
        messages = list(response.context['messages'])
        self.assertTrue(any('updated successfully' in str(m) for m in messages))
