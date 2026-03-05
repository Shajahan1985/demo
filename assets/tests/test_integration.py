"""
Integration tests for complete workflows.
Tests end-to-end scenarios across multiple components.
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from assets.models import Asset, OperatingSystem, Team, IPAddress, IPRange, Attachment
from assets.services.asset_service import AssetService
from assets.services.ip_management_service import IPManagementService
from assets.services.attachment_service import AttachmentService
from assets.services.warranty_service import WarrantyService
from django.core.files.uploadedfile import SimpleUploadedFile


class TestCompleteAssetLifecycleWorkflow(TestCase):
    """Test complete asset lifecycle: create → active → free → freed → scrap → scrapped."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')
        
        # Create IP range and addresses
        self.ip_range = IPRange.objects.create(
            range_pattern="192.168.10.x",
            network_prefix="192.168.10"
        )
        self.ip = IPAddress.objects.create(
            address="192.168.10.100",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create OS and Team
        self.os = OperatingSystem.objects.create(name="Windows 10")
        self.team = Team.objects.create(name="IT Department")
    
    def test_complete_asset_lifecycle(self):
        """
        Test: create asset → view on active page → free → verify on freed page → scrap → verify on scrapped page
        """
        # Step 1: Create asset
        asset_data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Desktop',
            'operating_system': self.os.id,
            'ip_address': self.ip.id,
            'particulars': 'Test asset',
            'assigned_to': 'John Doe',
            'team': self.team.id,
        }
        asset = AssetService.create_asset(asset_data, self.admin_user)
        
        # Verify asset was created
        self.assertIsNotNone(asset)
        self.assertEqual(asset.asset_tag, 'BIDC001')
        self.assertEqual(asset.status, 'active')
        
        # Step 2: View on active page
        response = self.client.get(reverse('asset_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(asset, response.context['assets'])
        self.assertContains(response, 'BIDC001')
        
        # Step 3: Free the asset
        asset = AssetService.free_asset(asset, self.admin_user, 'adminpass123')
        
        # Verify asset was freed
        self.assertEqual(asset.status, 'freed')
        self.assertIsNone(asset.assigned_to)
        self.assertIsNone(asset.team)
        self.assertIsNotNone(asset.freed_date)
        
        # Step 4: Verify on freed page
        response = self.client.get(reverse('freed_systems'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(asset, response.context['freed_assets'])
        self.assertContains(response, 'BIDC001')
        
        # Verify NOT on active page
        response = self.client.get(reverse('asset_list'))
        self.assertNotIn(asset, response.context['assets'])
        
        # Step 5: Scrap the asset
        asset = AssetService.scrap_asset(asset, self.admin_user)
        
        # Verify asset was scrapped
        self.assertEqual(asset.status, 'scrapped')
        self.assertIsNotNone(asset.scrapped_date)
        self.assertEqual(asset.asset_tag, 'BIDC001')  # Asset tag retained
        
        # Step 6: Verify on scrapped page
        response = self.client.get(reverse('scrapped_items'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(asset, response.context['scrapped_assets'])
        self.assertContains(response, 'BIDC001')
        
        # Verify NOT on freed page
        response = self.client.get(reverse('freed_systems'))
        self.assertNotIn(asset, response.context['freed_assets'])


class TestIPAssignmentWorkflow(TestCase):
    """Test IP assignment workflow: assign IP → verify not in free list → free asset → verify IP in free list."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')
        
        # Create IP range and addresses
        self.ip_range = IPRange.objects.create(
            range_pattern="192.168.10.x",
            network_prefix="192.168.10"
        )
        self.ip1 = IPAddress.objects.create(
            address="192.168.10.50",
            ip_range=self.ip_range,
            is_assigned=False
        )
        self.ip2 = IPAddress.objects.create(
            address="192.168.10.51",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create OS and Team
        self.os = OperatingSystem.objects.create(name="Ubuntu 20.04")
        self.team = Team.objects.create(name="Development")
    
    def test_ip_assignment_and_release_workflow(self):
        """
        Test: assign IP → verify not in free list → free asset → verify IP in free list
        """
        # Step 1: Verify IP is in free list initially
        response = self.client.get(reverse('free_ips'))
        self.assertEqual(response.status_code, 200)
        free_ips = response.context['ip_ranges']
        self.assertIn('192.168.10.x', free_ips)
        self.assertIn(self.ip1, free_ips['192.168.10.x'])
        
        # Step 2: Create asset and assign IP
        asset_data = {
            'asset_tag': 'BIDC100',
            'system_type': 'Laptop',
            'operating_system': self.os.id,
            'ip_address': self.ip1.id,
            'assigned_to': 'Alice Smith',
            'team': self.team.id,
        }
        asset = AssetService.create_asset(asset_data, self.admin_user)
        
        # Verify IP is assigned
        self.ip1.refresh_from_db()
        self.assertTrue(self.ip1.is_assigned)
        self.assertEqual(self.ip1.assigned_to_asset, asset)
        
        # Step 3: Verify IP is NOT in free list
        response = self.client.get(reverse('free_ips'))
        free_ips = response.context['ip_ranges']
        self.assertNotIn(self.ip1, free_ips.get('192.168.10.x', []))
        
        # Step 4: Free the asset
        asset = AssetService.free_asset(asset, self.admin_user, 'adminpass123')
        
        # Step 5: Verify IP is back in free list
        self.ip1.refresh_from_db()
        self.assertFalse(self.ip1.is_assigned)
        self.assertIsNone(self.ip1.assigned_to_asset)
        
        response = self.client.get(reverse('free_ips'))
        free_ips = response.context['ip_ranges']
        self.assertIn(self.ip1, free_ips['192.168.10.x'])


class TestWarrantyAlertWorkflow(TestCase):
    """Test warranty alert workflow: create asset with warranty → run daily check → verify email sent."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True,
            email='admin@example.com'
        )
        
        # Create IP range and address
        self.ip_range = IPRange.objects.create(
            range_pattern="192.168.10.x",
            network_prefix="192.168.10"
        )
        self.ip = IPAddress.objects.create(
            address="192.168.10.200",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create OS and Team
        self.os = OperatingSystem.objects.create(name="Windows 11")
        self.team = Team.objects.create(name="Sales")
    
    def test_warranty_alert_workflow(self):
        """
        Test: create asset with warranty → run daily check → verify email sent
        """
        # Step 1: Create asset with warranty expiring in 5 days
        warranty_date = timezone.now().date() + timedelta(days=5)
        asset_data = {
            'asset_tag': 'BIDC500',
            'system_type': 'Desktop',
            'operating_system': self.os.id,
            'ip_address': self.ip.id,
            'assigned_to': 'Bob Johnson',
            'team': self.team.id,
            'warranty_expiration': warranty_date,
        }
        asset = AssetService.create_asset(asset_data, self.admin_user)
        
        # Verify asset was created with warranty
        self.assertEqual(asset.warranty_expiration, warranty_date)
        
        # Step 2: Run daily warranty check
        expiring_assets = WarrantyService.check_expiring_warranties()
        
        # Verify asset is identified as expiring soon
        self.assertIn(asset, expiring_assets)
        
        # Step 3: Send warranty alerts
        WarrantyService.send_warranty_alerts(expiring_assets)
        
        # Step 4: Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('Warranty Expiration Alert', email.subject)
        self.assertIn('BIDC500', email.body)
        self.assertIn(self.admin_user.email, email.to)
    
    def test_warranty_not_sent_for_non_expiring(self):
        """Test that warranty alerts are not sent for assets with warranties far in the future."""
        # Create asset with warranty expiring in 30 days
        warranty_date = timezone.now().date() + timedelta(days=30)
        asset_data = {
            'asset_tag': 'BIDC501',
            'system_type': 'Laptop',
            'operating_system': self.os.id,
            'ip_address': self.ip.id,
            'assigned_to': 'Carol White',
            'team': self.team.id,
            'warranty_expiration': warranty_date,
        }
        asset = AssetService.create_asset(asset_data, self.admin_user)
        
        # Run daily warranty check
        expiring_assets = WarrantyService.check_expiring_warranties()
        
        # Verify asset is NOT identified as expiring soon
        self.assertNotIn(asset, expiring_assets)
        
        # Send alerts (should be empty)
        WarrantyService.send_warranty_alerts(expiring_assets)
        
        # Verify no email was sent
        self.assertEqual(len(mail.outbox), 0)


class TestAttachmentWorkflow(TestCase):
    """Test attachment workflow: upload attachment → verify stored → delete → verify removed."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        
        # Create IP range and address
        self.ip_range = IPRange.objects.create(
            range_pattern="192.168.10.x",
            network_prefix="192.168.10"
        )
        self.ip = IPAddress.objects.create(
            address="192.168.10.150",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create OS and Team
        self.os = OperatingSystem.objects.create(name="macOS")
        self.team = Team.objects.create(name="Design")
        
        # Create asset
        asset_data = {
            'asset_tag': 'BIDC300',
            'system_type': 'All-in-One PC',
            'operating_system': self.os.id,
            'ip_address': self.ip.id,
            'assigned_to': 'David Lee',
            'team': self.team.id,
        }
        self.asset = AssetService.create_asset(asset_data, self.admin_user)
    
    def test_attachment_upload_and_delete_workflow(self):
        """
        Test: upload attachment → verify stored → delete → verify removed
        """
        # Step 1: Upload attachment
        file_content = b'Test file content for integration test'
        test_file = SimpleUploadedFile(
            "test_document.txt",
            file_content,
            content_type="text/plain"
        )
        
        attachment = AttachmentService.upload_attachment(self.asset, test_file)
        
        # Step 2: Verify attachment was stored
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment.asset, self.asset)
        self.assertEqual(attachment.filename, "test_document.txt")
        self.assertTrue(attachment.file.name.endswith('.txt'))
        
        # Verify attachment is associated with asset
        asset_attachments = AttachmentService.get_asset_attachments(self.asset)
        self.assertIn(attachment, asset_attachments)
        self.assertEqual(asset_attachments.count(), 1)
        
        # Verify file exists in storage
        self.assertTrue(attachment.file.storage.exists(attachment.file.name))
        
        # Step 3: Delete attachment
        file_path = attachment.file.name
        AttachmentService.delete_attachment(attachment)
        
        # Step 4: Verify attachment was removed
        # Verify attachment record is deleted
        self.assertFalse(Attachment.objects.filter(id=attachment.id).exists())
        
        # Verify attachment is no longer associated with asset
        asset_attachments = AttachmentService.get_asset_attachments(self.asset)
        self.assertEqual(asset_attachments.count(), 0)
        
        # Verify file is removed from storage
        from django.core.files.storage import default_storage
        self.assertFalse(default_storage.exists(file_path))
    
    def test_multiple_attachments_workflow(self):
        """Test uploading and managing multiple attachments."""
        # Upload multiple attachments
        file1 = SimpleUploadedFile("doc1.txt", b'Content 1', content_type="text/plain")
        file2 = SimpleUploadedFile("doc2.txt", b'Content 2', content_type="text/plain")
        file3 = SimpleUploadedFile("doc3.txt", b'Content 3', content_type="text/plain")
        
        attachment1 = AttachmentService.upload_attachment(self.asset, file1)
        attachment2 = AttachmentService.upload_attachment(self.asset, file2)
        attachment3 = AttachmentService.upload_attachment(self.asset, file3)
        
        # Verify all attachments are stored
        asset_attachments = AttachmentService.get_asset_attachments(self.asset)
        self.assertEqual(asset_attachments.count(), 3)
        self.assertIn(attachment1, asset_attachments)
        self.assertIn(attachment2, asset_attachments)
        self.assertIn(attachment3, asset_attachments)
        
        # Delete one attachment
        AttachmentService.delete_attachment(attachment2)
        
        # Verify only the deleted attachment is removed
        asset_attachments = AttachmentService.get_asset_attachments(self.asset)
        self.assertEqual(asset_attachments.count(), 2)
        self.assertIn(attachment1, asset_attachments)
        self.assertNotIn(attachment2, asset_attachments)
        self.assertIn(attachment3, asset_attachments)
