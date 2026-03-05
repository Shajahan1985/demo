"""
Tests for warranty email functionality.
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.core import mail
from django.contrib.auth.models import User
from assets.models import Asset, OperatingSystem, Team, IPAddress, IPRange
from assets.services.warranty_service import WarrantyService


@pytest.mark.django_db
class TestWarrantyEmail:
    """Test warranty email sending functionality."""
    
    @pytest.fixture
    def admin_user(self):
        """Create an admin user with email."""
        return User.objects.create_user(
            username='admin',
            email='admin@example.com',
            is_staff=True,
            is_active=True
        )
    
    @pytest.fixture
    def operating_system(self):
        """Create an operating system."""
        return OperatingSystem.objects.create(name='Windows 10')
    
    @pytest.fixture
    def team(self):
        """Create a team."""
        return Team.objects.create(name='IT Department')
    
    @pytest.fixture
    def ip_range(self):
        """Create an IP range."""
        return IPRange.objects.create(
            range_pattern='192.168.10.x',
            network_prefix='192.168.10'
        )
    
    @pytest.fixture
    def ip_address(self, ip_range):
        """Create an IP address."""
        return IPAddress.objects.create(
            address='192.168.10.100',
            ip_range=ip_range,
            is_assigned=True
        )
    
    def test_send_warranty_alert_email(self, admin_user, operating_system, team, ip_address):
        """Test that warranty alert emails are sent correctly."""
        # Create asset with warranty expiring in 5 days
        today = timezone.now().date()
        expiry_date = today + timedelta(days=5)
        
        asset = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=operating_system,
            ip_address=ip_address,
            assigned_to='John Doe',
            team=team,
            status='active',
            warranty_expiration=expiry_date
        )
        
        # Get expiring assets
        expiring_assets = WarrantyService.check_expiring_warranties()
        assert expiring_assets.count() == 1
        
        # Send warranty alerts
        WarrantyService.send_warranty_alerts(expiring_assets)
        
        # Check that one email was sent
        assert len(mail.outbox) == 1
        
        # Check email details
        email = mail.outbox[0]
        assert email.subject == 'Asset Warranty Expiration Alert'
        assert 'admin@example.com' in email.to
        assert 'BIDC001' in email.body
        assert 'Desktop' in email.body
        assert '5 day' in email.body
        
        # Check HTML alternative exists
        assert len(email.alternatives) == 1
        html_content = email.alternatives[0][0]
        assert 'BIDC001' in html_content
        assert 'Desktop' in html_content
    
    def test_no_email_sent_when_no_expiring_assets(self, admin_user):
        """Test that no email is sent when there are no expiring assets."""
        # Get expiring assets (should be empty)
        expiring_assets = WarrantyService.check_expiring_warranties()
        assert expiring_assets.count() == 0
        
        # Send warranty alerts
        WarrantyService.send_warranty_alerts(expiring_assets)
        
        # Check that no email was sent
        assert len(mail.outbox) == 0
    
    def test_no_email_sent_when_no_admin_users(self, operating_system, ip_address):
        """Test that no email is sent when there are no admin users with email."""
        # Create asset with warranty expiring in 5 days
        today = timezone.now().date()
        expiry_date = today + timedelta(days=5)
        
        Asset.objects.create(
            asset_tag='BIDC002',
            system_type='Laptop',
            operating_system=operating_system,
            ip_address=ip_address,
            status='active',
            warranty_expiration=expiry_date
        )
        
        # Get expiring assets
        expiring_assets = WarrantyService.check_expiring_warranties()
        assert expiring_assets.count() == 1
        
        # Send warranty alerts (no admin users exist)
        WarrantyService.send_warranty_alerts(expiring_assets)
        
        # Check that no email was sent
        assert len(mail.outbox) == 0
    
    def test_email_sent_to_multiple_admins(self, operating_system, ip_address):
        """Test that email is sent to all admin users."""
        # Create multiple admin users
        User.objects.create_user(
            username='admin1',
            email='admin1@example.com',
            is_staff=True,
            is_active=True
        )
        User.objects.create_user(
            username='admin2',
            email='admin2@example.com',
            is_staff=True,
            is_active=True
        )
        
        # Create asset with warranty expiring in 3 days
        today = timezone.now().date()
        expiry_date = today + timedelta(days=3)
        
        Asset.objects.create(
            asset_tag='BIDC003',
            system_type='All-in-One PC',
            operating_system=operating_system,
            ip_address=ip_address,
            status='active',
            warranty_expiration=expiry_date
        )
        
        # Get expiring assets
        expiring_assets = WarrantyService.check_expiring_warranties()
        
        # Send warranty alerts
        WarrantyService.send_warranty_alerts(expiring_assets)
        
        # Check that one email was sent to both admins
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert 'admin1@example.com' in email.to
        assert 'admin2@example.com' in email.to
    
    def test_email_includes_multiple_expiring_assets(self, admin_user, operating_system, ip_range):
        """Test that email includes all expiring assets."""
        # Create multiple IP addresses
        ip1 = IPAddress.objects.create(
            address='192.168.10.101',
            ip_range=ip_range,
            is_assigned=True
        )
        ip2 = IPAddress.objects.create(
            address='192.168.10.102',
            ip_range=ip_range,
            is_assigned=True
        )
        
        # Create multiple assets with warranties expiring soon
        today = timezone.now().date()
        
        Asset.objects.create(
            asset_tag='BIDC004',
            system_type='Desktop',
            operating_system=operating_system,
            ip_address=ip1,
            status='active',
            warranty_expiration=today + timedelta(days=2)
        )
        
        Asset.objects.create(
            asset_tag='BIDC005',
            system_type='Laptop',
            operating_system=operating_system,
            ip_address=ip2,
            status='active',
            warranty_expiration=today + timedelta(days=6)
        )
        
        # Get expiring assets
        expiring_assets = WarrantyService.check_expiring_warranties()
        assert expiring_assets.count() == 2
        
        # Send warranty alerts
        WarrantyService.send_warranty_alerts(expiring_assets)
        
        # Check email content
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert 'BIDC004' in email.body
        assert 'BIDC005' in email.body
        assert 'Desktop' in email.body
        assert 'Laptop' in email.body
