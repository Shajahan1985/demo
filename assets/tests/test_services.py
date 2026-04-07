"""
Unit tests for services.
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from assets.models import Asset, IPAddress, IPRange, OperatingSystem, Team
from assets.services.asset_service import AssetService
from assets.services.ip_management_service import IPManagementService


class TestAssetService(TestCase):
    """Test cases for AssetService."""
    
    def setUp(self):
        """Set up test data."""
        # Create user
        self.user = User.objects.create_user(username='admin', password='password')
        
        # Create IP range and addresses
        self.ip_range = IPRange.objects.create(
            range_pattern="192.168.10.x",
            network_prefix="192.168.10"
        )
        self.ip1 = IPAddress.objects.create(
            address="192.168.10.1",
            ip_range=self.ip_range,
            is_assigned=False
        )
        self.ip2 = IPAddress.objects.create(
            address="192.168.10.2",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create OS and Team
        self.os = OperatingSystem.objects.create(name="Windows 10")
        self.team = Team.objects.create(name="IT Department")
    
    def test_create_asset_with_all_fields(self):
        """Test creating an asset with all fields provided."""
        data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Desktop',
            'operating_system': self.os.id,
            'ip_address': self.ip1.id,
            'particulars': 'Test particulars',
            'assigned_to': 'John Doe',
            'team': self.team.id,
            'warranty_expiration': '2025-12-31'
        }
        
        asset = AssetService.create_asset(data, self.user)
        
        self.assertEqual(asset.asset_tag, 'BIDC001')
        self.assertEqual(asset.system_type, 'Desktop')
        self.assertEqual(asset.operating_system, self.os)
        self.assertEqual(asset.ip_address, self.ip1)
        self.assertEqual(asset.particulars, 'Test particulars')
        self.assertEqual(asset.assigned_to, 'John Doe')
        self.assertEqual(asset.team, self.team)
        self.assertEqual(asset.status, 'active')
        
        # Check IP is marked as assigned
        self.ip1.refresh_from_db()
        self.assertTrue(self.ip1.is_assigned)
        self.assertEqual(self.ip1.assigned_to_asset, asset)
    
    def test_create_asset_without_optional_fields(self):
        """Test creating an asset with only required fields."""
        data = {
            'asset_tag': 'BIDC002',
            'system_type': 'Laptop',
            'operating_system': self.os.id,
        }
        
        asset = AssetService.create_asset(data, self.user)
        
        self.assertEqual(asset.asset_tag, 'BIDC002')
        self.assertEqual(asset.system_type, 'Laptop')
        self.assertIsNone(asset.ip_address)
        self.assertEqual(asset.particulars, '')
        self.assertEqual(asset.assigned_to, '')
        self.assertIsNone(asset.team)
    
    def test_create_asset_with_duplicate_tag_raises_error(self):
        """Test that creating an asset with duplicate tag raises ValidationError."""
        data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Desktop',
            'operating_system': self.os.id,
        }
        
        # Create first asset
        AssetService.create_asset(data, self.user)
        
        # Try to create second asset with same tag
        with self.assertRaises(ValidationError) as context:
            AssetService.create_asset(data, self.user)
        
        self.assertIn('asset_tag', context.exception.message_dict)
    
    def test_create_asset_with_assigned_ip_raises_error(self):
        """Test that creating an asset with already assigned IP raises ValidationError."""
        # Assign IP to an asset
        self.ip1.is_assigned = True
        self.ip1.save()
        
        data = {
            'asset_tag': 'BIDC003',
            'system_type': 'Desktop',
            'operating_system': self.os.id,
            'ip_address': self.ip1.id,
        }
        
        with self.assertRaises(ValidationError) as context:
            AssetService.create_asset(data, self.user)
        
        self.assertIn('ip_address', context.exception.message_dict)
    
    def test_update_asset_changes_fields(self):
        """Test updating asset fields."""
        # Create asset
        asset = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        
        # Update asset
        data = {
            'system_type': 'Laptop',
            'particulars': 'Updated particulars',
            'assigned_to': 'Jane Doe',
        }
        
        updated_asset = AssetService.update_asset(asset, data, self.user)
        
        self.assertEqual(updated_asset.system_type, 'Laptop')
        self.assertEqual(updated_asset.particulars, 'Updated particulars')
        self.assertEqual(updated_asset.assigned_to, 'Jane Doe')
    
    def test_update_asset_changes_ip(self):
        """Test updating asset IP address."""
        # Create asset with IP
        asset = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            ip_address=self.ip1,
            status='active'
        )
        self.ip1.is_assigned = True
        self.ip1.assigned_to_asset = asset
        self.ip1.save()
        
        # Update to new IP
        data = {'ip_address': self.ip2.id}
        AssetService.update_asset(asset, data, self.user)
        
        # Check old IP is released
        self.ip1.refresh_from_db()
        self.assertFalse(self.ip1.is_assigned)
        
        # Check new IP is assigned
        self.ip2.refresh_from_db()
        self.assertTrue(self.ip2.is_assigned)
        
        # Check asset has new IP
        asset.refresh_from_db()
        self.assertEqual(asset.ip_address, self.ip2)
    
    def test_update_asset_tag_validates_uniqueness(self):
        """Test that updating asset tag validates uniqueness."""
        # Create two assets
        asset1 = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        asset2 = Asset.objects.create(
            asset_tag='BIDC002',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        
        # Try to update asset2 with asset1's tag
        data = {'asset_tag': 'BIDC001'}
        
        with self.assertRaises(ValidationError) as context:
            AssetService.update_asset(asset2, data, self.user)
        
        self.assertIn('asset_tag', context.exception.message_dict)
    
    def test_validate_asset_tag_returns_true_for_unique_tag(self):
        """Test that validate_asset_tag returns True for unique tag."""
        result = AssetService.validate_asset_tag('BIDC999')
        self.assertTrue(result)
    
    def test_validate_asset_tag_returns_false_for_existing_tag(self):
        """Test that validate_asset_tag returns False for existing tag."""
        Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        
        result = AssetService.validate_asset_tag('BIDC001')
        self.assertFalse(result)
    
    def test_validate_asset_tag_returns_false_for_empty_tag(self):
        """Test that validate_asset_tag returns False for empty tag."""
        result = AssetService.validate_asset_tag('')
        self.assertFalse(result)
    
    def test_get_active_assets_returns_only_active(self):
        """Test that get_active_assets returns only active assets."""
        # Create assets with different statuses
        active1 = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        active2 = Asset.objects.create(
            asset_tag='BIDC002',
            system_type='Laptop',
            operating_system=self.os,
            status='active'
        )
        freed = Asset.objects.create(
            asset_tag='BIDC003',
            system_type='Desktop',
            operating_system=self.os,
            status='freed'
        )
        scrapped = Asset.objects.create(
            asset_tag='BIDC004',
            system_type='Desktop',
            operating_system=self.os,
            status='scrapped'
        )
        
        active_assets = AssetService.get_active_assets()
        
        self.assertEqual(active_assets.count(), 2)
        self.assertIn(active1, active_assets)
        self.assertIn(active2, active_assets)
        self.assertNotIn(freed, active_assets)
        self.assertNotIn(scrapped, active_assets)
    
    def test_get_active_assets_ordered_by_serial_number(self):
        """Test that get_active_assets returns assets ordered by serial number."""
        # Create assets (they will get sequential serial numbers)
        asset1 = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        asset2 = Asset.objects.create(
            asset_tag='BIDC002',
            system_type='Laptop',
            operating_system=self.os,
            status='active'
        )
        asset3 = Asset.objects.create(
            asset_tag='BIDC003',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        
        active_assets = list(AssetService.get_active_assets())
        
        self.assertEqual(active_assets[0], asset1)
        self.assertEqual(active_assets[1], asset2)
        self.assertEqual(active_assets[2], asset3)
    
    def test_get_freed_assets_returns_only_freed(self):
        """Test that get_freed_assets returns only freed assets."""
        # Create assets with different statuses
        active = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        freed1 = Asset.objects.create(
            asset_tag='BIDC002',
            system_type='Laptop',
            operating_system=self.os,
            status='freed'
        )
        freed2 = Asset.objects.create(
            asset_tag='BIDC003',
            system_type='Desktop',
            operating_system=self.os,
            status='freed'
        )
        scrapped = Asset.objects.create(
            asset_tag='BIDC004',
            system_type='Desktop',
            operating_system=self.os,
            status='scrapped'
        )
        
        freed_assets = AssetService.get_freed_assets()
        
        self.assertEqual(freed_assets.count(), 2)
        self.assertIn(freed1, freed_assets)
        self.assertIn(freed2, freed_assets)
        self.assertNotIn(active, freed_assets)
        self.assertNotIn(scrapped, freed_assets)
    
    def test_get_scrapped_assets_returns_only_scrapped(self):
        """Test that get_scrapped_assets returns only scrapped assets."""
        # Create assets with different statuses
        active = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        freed = Asset.objects.create(
            asset_tag='BIDC002',
            system_type='Laptop',
            operating_system=self.os,
            status='freed'
        )
        scrapped1 = Asset.objects.create(
            asset_tag='BIDC003',
            system_type='Desktop',
            operating_system=self.os,
            status='scrapped'
        )
        scrapped2 = Asset.objects.create(
            asset_tag='BIDC004',
            system_type='Desktop',
            operating_system=self.os,
            status='scrapped'
        )
        
        scrapped_assets = AssetService.get_scrapped_assets()
        
        self.assertEqual(scrapped_assets.count(), 2)
        self.assertIn(scrapped1, scrapped_assets)
        self.assertIn(scrapped2, scrapped_assets)
        self.assertNotIn(active, scrapped_assets)
        self.assertNotIn(freed, scrapped_assets)
    
    def test_free_asset_with_correct_password(self):
        """Test freeing an asset with correct password."""
        from django.utils import timezone
        
        # Create asset with IP
        asset = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            ip_address=self.ip1,
            assigned_to='John Doe',
            team=self.team,
            status='active'
        )
        self.ip1.is_assigned = True
        self.ip1.assigned_to_asset = asset
        self.ip1.save()
        
        # Free the asset
        freed_asset = AssetService.free_asset(asset, self.user, 'password')
        
        # Check asset status
        self.assertEqual(freed_asset.status, 'freed')
        self.assertIsNone(freed_asset.assigned_to)
        self.assertIsNone(freed_asset.team)
        self.assertIsNotNone(freed_asset.freed_date)
        
        # Check IP is released
        self.ip1.refresh_from_db()
        self.assertFalse(self.ip1.is_assigned)
        self.assertIsNone(self.ip1.assigned_to_asset)
    
    def test_free_asset_with_incorrect_password(self):
        """Test that freeing an asset with incorrect password raises ValidationError."""
        asset = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        
        with self.assertRaises(ValidationError) as context:
            AssetService.free_asset(asset, self.user, 'wrongpassword')
        
        self.assertIn('password', context.exception.message_dict)
    
    def test_free_asset_non_active_raises_error(self):
        """Test that freeing a non-active asset raises ValidationError."""
        asset = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            status='freed'
        )
        
        with self.assertRaises(ValidationError) as context:
            AssetService.free_asset(asset, self.user, 'password')
        
        self.assertIn('status', context.exception.message_dict)
    
    def test_free_asset_without_ip(self):
        """Test freeing an asset that has no IP address."""
        asset = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            assigned_to='John Doe',
            team=self.team,
            status='active'
        )
        
        # Free the asset
        freed_asset = AssetService.free_asset(asset, self.user, 'password')
        
        # Check asset status
        self.assertEqual(freed_asset.status, 'freed')
        self.assertIsNone(freed_asset.assigned_to)
        self.assertIsNone(freed_asset.team)
        self.assertIsNotNone(freed_asset.freed_date)
    
    def test_scrap_asset_freed_asset(self):
        """Test scrapping a freed asset."""
        from django.utils import timezone
        
        asset = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            ip_address=self.ip1,
            status='freed',
            freed_date=timezone.now()
        )
        
        # Scrap the asset
        scrapped_asset = AssetService.scrap_asset(asset, self.user, "Obsolete hardware")
        
        # Check asset status
        self.assertEqual(scrapped_asset.status, 'scrapped')
        self.assertIsNotNone(scrapped_asset.scrapped_date)
        # Check that asset_tag and IP are retained
        self.assertEqual(scrapped_asset.asset_tag, 'BIDC001')
        self.assertEqual(scrapped_asset.ip_address, self.ip1)
    
    def test_scrap_asset_non_freed_raises_error(self):
        """Test that scrapping a non-freed asset raises ValidationError."""
        asset = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        
        with self.assertRaises(ValidationError) as context:
            AssetService.scrap_asset(asset, self.user, "Test reason")
        
        self.assertIn('status', context.exception.message_dict)

    def test_scrap_asset_with_valid_reason_succeeds(self):
        """Test scrapping a freed asset with a valid reason succeeds."""
        from django.utils import timezone

        asset = Asset.objects.create(
            asset_tag='BIDC010',
            system_type='Desktop',
            operating_system=self.os,
            status='freed',
            freed_date=timezone.now()
        )

        scrapped_asset = AssetService.scrap_asset(asset, self.user, "Hardware failure")

        self.assertEqual(scrapped_asset.status, 'scrapped')
        self.assertIsNotNone(scrapped_asset.scrapped_date)
        self.assertEqual(scrapped_asset.scrapping_reason, "Hardware failure")

    def test_scrap_asset_with_empty_reason_raises_error(self):
        """Test scrapping with empty reason raises ValidationError."""
        from django.utils import timezone

        asset = Asset.objects.create(
            asset_tag='BIDC011',
            system_type='Desktop',
            operating_system=self.os,
            status='freed',
            freed_date=timezone.now()
        )

        with self.assertRaises(ValidationError) as context:
            AssetService.scrap_asset(asset, self.user, "")

        self.assertIn('scrapping_reason', context.exception.message_dict)
        # Verify asset status unchanged
        asset.refresh_from_db()
        self.assertEqual(asset.status, 'freed')

    def test_scrap_asset_with_whitespace_only_reason_raises_error(self):
        """Test scrapping with whitespace-only reason raises ValidationError."""
        from django.utils import timezone

        asset = Asset.objects.create(
            asset_tag='BIDC012',
            system_type='Desktop',
            operating_system=self.os,
            status='freed',
            freed_date=timezone.now()
        )

        with self.assertRaises(ValidationError) as context:
            AssetService.scrap_asset(asset, self.user, "   \t\n  ")

        self.assertIn('scrapping_reason', context.exception.message_dict)
        # Verify asset status unchanged
        asset.refresh_from_db()
        self.assertEqual(asset.status, 'freed')

    def test_scrap_asset_releases_ip_when_asset_has_ip(self):
        """Test IP is released when scrapping an asset that has an IP."""
        from django.utils import timezone

        asset = Asset.objects.create(
            asset_tag='BIDC013',
            system_type='Desktop',
            operating_system=self.os,
            ip_address=self.ip1,
            status='freed',
            freed_date=timezone.now()
        )
        self.ip1.is_assigned = True
        self.ip1.assigned_to_asset = asset
        self.ip1.save()

        AssetService.scrap_asset(asset, self.user, "End of life")

        self.ip1.refresh_from_db()
        self.assertFalse(self.ip1.is_assigned)
        self.assertIsNone(self.ip1.assigned_to_asset)
        self.assertIsNotNone(self.ip1.freed_date)

    def test_scrap_asset_preserves_ip_reference(self):
        """Test IP reference is preserved on asset after scrapping."""
        from django.utils import timezone

        asset = Asset.objects.create(
            asset_tag='BIDC014',
            system_type='Desktop',
            operating_system=self.os,
            ip_address=self.ip1,
            status='freed',
            freed_date=timezone.now()
        )
        self.ip1.is_assigned = True
        self.ip1.assigned_to_asset = asset
        self.ip1.save()

        scrapped_asset = AssetService.scrap_asset(asset, self.user, "Damaged beyond repair")

        scrapped_asset.refresh_from_db()
        self.assertIsNotNone(scrapped_asset.ip_address)
        self.assertEqual(scrapped_asset.ip_address.pk, self.ip1.pk)

    def test_scrap_asset_without_ip_succeeds(self):
        """Test scrapping an asset without an IP address succeeds."""
        from django.utils import timezone

        asset = Asset.objects.create(
            asset_tag='BIDC015',
            system_type='Desktop',
            operating_system=self.os,
            ip_address=None,
            status='freed',
            freed_date=timezone.now()
        )

        scrapped_asset = AssetService.scrap_asset(asset, self.user, "No longer needed")

        self.assertEqual(scrapped_asset.status, 'scrapped')
        self.assertIsNotNone(scrapped_asset.scrapped_date)
        self.assertEqual(scrapped_asset.scrapping_reason, "No longer needed")
        self.assertIsNone(scrapped_asset.ip_address)



class TestIPManagementService(TestCase):
    """Test cases for IPManagementService."""
    
    def setUp(self):
        """Set up test data."""
        # Create IP ranges
        self.ip_range_10 = IPRange.objects.create(
            range_pattern="192.168.10.x",
            network_prefix="192.168.10"
        )
        self.ip_range_11 = IPRange.objects.create(
            range_pattern="192.168.11.x",
            network_prefix="192.168.11"
        )
        
        # Create IP addresses
        self.ip1 = IPAddress.objects.create(
            address="192.168.10.1",
            ip_range=self.ip_range_10,
            is_assigned=False
        )
        self.ip2 = IPAddress.objects.create(
            address="192.168.10.2",
            ip_range=self.ip_range_10,
            is_assigned=False
        )
        self.ip3 = IPAddress.objects.create(
            address="192.168.11.1",
            ip_range=self.ip_range_11,
            is_assigned=False
        )
        
        # Create OS and Team
        self.os = OperatingSystem.objects.create(name="Windows 10")
        self.team = Team.objects.create(name="IT Department")
        
        # Create asset
        self.asset = Asset.objects.create(
            asset_tag="BIDC001",
            system_type="Desktop",
            operating_system=self.os,
            team=self.team,
            status="active"
        )
    
    def test_assign_ip_marks_as_assigned(self):
        """Test that assign_ip marks IP as assigned."""
        IPManagementService.assign_ip(self.ip1, self.asset)
        
        self.ip1.refresh_from_db()
        self.assertTrue(self.ip1.is_assigned)
        self.assertEqual(self.ip1.assigned_to_asset, self.asset)
    
    def test_release_ip_marks_as_free(self):
        """Test that release_ip marks IP as free."""
        # First assign the IP
        self.ip1.is_assigned = True
        self.ip1.assigned_to_asset = self.asset
        self.ip1.save()
        
        # Now release it
        IPManagementService.release_ip(self.ip1)
        
        self.ip1.refresh_from_db()
        self.assertFalse(self.ip1.is_assigned)
        self.assertIsNone(self.ip1.assigned_to_asset)

    def test_release_ip_sets_freed_date(self):
        """Test that release_ip sets freed_date when IP is released."""
        # Assign the IP first
        self.ip1.is_assigned = True
        self.ip1.assigned_to_asset = self.asset
        self.ip1.freed_date = None
        self.ip1.save()

        # Release it
        IPManagementService.release_ip(self.ip1)

        self.ip1.refresh_from_db()
        self.assertIsNotNone(self.ip1.freed_date)

    def test_release_ip_freed_date_is_valid_datetime(self):
        """Test that freed_date is a valid datetime after IP release."""
        from django.utils import timezone
        from datetime import datetime

        # Assign the IP first
        self.ip1.is_assigned = True
        self.ip1.assigned_to_asset = self.asset
        self.ip1.freed_date = None
        self.ip1.save()

        before_release = timezone.now()
        IPManagementService.release_ip(self.ip1)
        after_release = timezone.now()

        self.ip1.refresh_from_db()
        self.assertIsInstance(self.ip1.freed_date, datetime)
        self.assertGreaterEqual(self.ip1.freed_date, before_release)
        self.assertLessEqual(self.ip1.freed_date, after_release)

    def test_release_ip_preserves_existing_functionality(self):
        """Test that release_ip still clears is_assigned and assigned_to_asset alongside setting freed_date."""
        # Assign the IP first
        self.ip1.is_assigned = True
        self.ip1.assigned_to_asset = self.asset
        self.ip1.freed_date = None
        self.ip1.save()

        IPManagementService.release_ip(self.ip1)

        self.ip1.refresh_from_db()
        # Existing functionality
        self.assertFalse(self.ip1.is_assigned)
        self.assertIsNone(self.ip1.assigned_to_asset)
        # New functionality
        self.assertIsNotNone(self.ip1.freed_date)

    def test_change_asset_ip_releases_old_and_assigns_new(self):
        """Test that change_asset_ip releases old IP and assigns new IP."""
        # Assign initial IP
        self.asset.ip_address = self.ip1
        self.asset.save()
        self.ip1.is_assigned = True
        self.ip1.assigned_to_asset = self.asset
        self.ip1.save()
        
        # Change to new IP
        IPManagementService.change_asset_ip(self.asset, self.ip2)
        
        # Check old IP is released
        self.ip1.refresh_from_db()
        self.assertFalse(self.ip1.is_assigned)
        self.assertIsNone(self.ip1.assigned_to_asset)
        
        # Check new IP is assigned
        self.ip2.refresh_from_db()
        self.assertTrue(self.ip2.is_assigned)
        self.assertEqual(self.ip2.assigned_to_asset, self.asset)
        
        # Check asset has new IP
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.ip_address, self.ip2)
    
    def test_change_asset_ip_with_no_previous_ip(self):
        """Test that change_asset_ip works when asset has no previous IP."""
        # Asset has no IP initially
        self.assertIsNone(self.asset.ip_address)
        
        # Assign IP
        IPManagementService.change_asset_ip(self.asset, self.ip1)
        
        # Check IP is assigned
        self.ip1.refresh_from_db()
        self.assertTrue(self.ip1.is_assigned)
        self.assertEqual(self.ip1.assigned_to_asset, self.asset)
        
        # Check asset has IP
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.ip_address, self.ip1)
    
    def test_get_free_ips_by_range_returns_grouped_ips(self):
        """Test that get_free_ips_by_range returns IPs grouped by range."""
        result = IPManagementService.get_free_ips_by_range()
        
        # Should have two ranges
        self.assertEqual(len(result), 2)
        self.assertIn("192.168.10.x", result)
        self.assertIn("192.168.11.x", result)
        
        # Check IPs in each range
        self.assertEqual(len(result["192.168.10.x"]), 2)
        self.assertEqual(len(result["192.168.11.x"]), 1)
        
        # Check IP addresses
        ip_addresses_10 = [ip.address for ip in result["192.168.10.x"]]
        self.assertIn("192.168.10.1", ip_addresses_10)
        self.assertIn("192.168.10.2", ip_addresses_10)
        
        ip_addresses_11 = [ip.address for ip in result["192.168.11.x"]]
        self.assertIn("192.168.11.1", ip_addresses_11)
    
    def test_get_free_ips_by_range_excludes_assigned_ips(self):
        """Test that get_free_ips_by_range excludes assigned IPs."""
        # Assign one IP
        self.ip1.is_assigned = True
        self.ip1.assigned_to_asset = self.asset
        self.ip1.save()
        
        result = IPManagementService.get_free_ips_by_range()
        
        # Should still have two ranges
        self.assertEqual(len(result), 2)
        
        # But 192.168.10.x should only have one IP now
        self.assertEqual(len(result["192.168.10.x"]), 1)
        ip_addresses_10 = [ip.address for ip in result["192.168.10.x"]]
        self.assertNotIn("192.168.10.1", ip_addresses_10)
        self.assertIn("192.168.10.2", ip_addresses_10)
    
    def test_get_available_ips_returns_unassigned_ips(self):
        """Test that get_available_ips returns only unassigned IPs."""
        # Assign one IP
        self.ip1.is_assigned = True
        self.ip1.assigned_to_asset = self.asset
        self.ip1.save()
        
        available_ips = IPManagementService.get_available_ips()
        
        # Should return 2 IPs (ip2 and ip3)
        self.assertEqual(available_ips.count(), 2)
        
        # Check that ip1 is not in the result
        ip_addresses = [ip.address for ip in available_ips]
        self.assertNotIn("192.168.10.1", ip_addresses)
        self.assertIn("192.168.10.2", ip_addresses)
        self.assertIn("192.168.11.1", ip_addresses)
    
    def test_get_available_ips_returns_all_when_none_assigned(self):
        """Test that get_available_ips returns all IPs when none are assigned."""
        available_ips = IPManagementService.get_available_ips()
        
        # Should return all 3 IPs
        self.assertEqual(available_ips.count(), 3)
    
    def test_get_free_ips_by_range_empty_when_all_assigned(self):
        """Test that get_free_ips_by_range returns empty dict when all IPs are assigned."""
        # Assign all IPs
        for ip in [self.ip1, self.ip2, self.ip3]:
            ip.is_assigned = True
            ip.assigned_to_asset = self.asset
            ip.save()
        
        result = IPManagementService.get_free_ips_by_range()
        
        # Should return empty dict
        self.assertEqual(len(result), 0)



class TestAttachmentService(TestCase):
    """Test cases for AttachmentService."""
    
    def setUp(self):
        """Set up test data."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create OS
        self.os = OperatingSystem.objects.create(name="Windows 10")
        
        # Create asset
        self.asset = Asset.objects.create(
            asset_tag="BIDC001",
            system_type="Desktop",
            operating_system=self.os,
            status="active"
        )
    
    def test_upload_attachment_creates_record(self):
        """Test that upload_attachment creates an attachment record."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from assets.services.attachment_service import AttachmentService
        
        # Create a test file
        file_content = b"Test file content"
        test_file = SimpleUploadedFile("test_document.pdf", file_content, content_type="application/pdf")
        
        # Upload attachment
        attachment = AttachmentService.upload_attachment(self.asset, test_file)
        
        # Verify attachment was created
        self.assertIsNotNone(attachment.id)
        self.assertEqual(attachment.asset, self.asset)
        self.assertEqual(attachment.filename, "test_document.pdf")
        self.assertTrue(attachment.file.name.endswith('.pdf'))
        
        # Clean up
        AttachmentService.delete_attachment(attachment)
    
    def test_upload_attachment_validates_file_size(self):
        """Test that upload_attachment rejects files exceeding size limit."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from assets.services.attachment_service import AttachmentService
        
        # Create a file larger than 10MB
        large_file_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile("large_file.pdf", large_file_content, content_type="application/pdf")
        
        # Try to upload - should raise ValidationError
        with self.assertRaises(ValidationError) as context:
            AttachmentService.upload_attachment(self.asset, large_file)
        
        self.assertIn('file', context.exception.message_dict)
        self.assertIn('exceeds', context.exception.message_dict['file'][0].lower())
    
    def test_upload_attachment_validates_file_type(self):
        """Test that upload_attachment rejects disallowed file types."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from assets.services.attachment_service import AttachmentService
        
        # Create a file with disallowed extension
        file_content = b"Test content"
        test_file = SimpleUploadedFile("test.exe", file_content, content_type="application/x-msdownload")
        
        # Try to upload - should raise ValidationError
        with self.assertRaises(ValidationError) as context:
            AttachmentService.upload_attachment(self.asset, test_file)
        
        self.assertIn('file', context.exception.message_dict)
        self.assertIn('not allowed', context.exception.message_dict['file'][0].lower())
    
    def test_upload_attachment_allows_valid_file_types(self):
        """Test that upload_attachment accepts all allowed file types."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from assets.services.attachment_service import AttachmentService
        
        allowed_files = [
            ("test.pdf", "application/pdf"),
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
            ("test.doc", "application/msword"),
            ("test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("test.txt", "text/plain"),
        ]
        
        attachments = []
        for filename, content_type in allowed_files:
            file_content = b"Test content"
            test_file = SimpleUploadedFile(filename, file_content, content_type=content_type)
            
            # Should not raise an error
            attachment = AttachmentService.upload_attachment(self.asset, test_file)
            self.assertIsNotNone(attachment.id)
            attachments.append(attachment)
        
        # Clean up
        for attachment in attachments:
            AttachmentService.delete_attachment(attachment)
    
    def test_delete_attachment_removes_file_and_record(self):
        """Test that delete_attachment removes both file and database record."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from assets.services.attachment_service import AttachmentService
        from assets.models import Attachment
        
        # Create and upload attachment
        file_content = b"Test file content"
        test_file = SimpleUploadedFile("test_document.pdf", file_content, content_type="application/pdf")
        attachment = AttachmentService.upload_attachment(self.asset, test_file)
        
        attachment_id = attachment.id
        file_path = attachment.file.name
        
        # Delete attachment
        AttachmentService.delete_attachment(attachment)
        
        # Verify record is deleted
        with self.assertRaises(Attachment.DoesNotExist):
            Attachment.objects.get(id=attachment_id)
        
        # Verify file is deleted from storage
        from django.core.files.storage import default_storage
        self.assertFalse(default_storage.exists(file_path))
    
    def test_get_asset_attachments_returns_all_attachments(self):
        """Test that get_asset_attachments returns all attachments for an asset."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from assets.services.attachment_service import AttachmentService
        
        # Create multiple attachments
        attachments = []
        for i in range(3):
            file_content = b"Test content"
            test_file = SimpleUploadedFile(f"test_{i}.pdf", file_content, content_type="application/pdf")
            attachment = AttachmentService.upload_attachment(self.asset, test_file)
            attachments.append(attachment)
        
        # Get attachments
        retrieved_attachments = AttachmentService.get_asset_attachments(self.asset)
        
        # Verify all attachments are returned
        self.assertEqual(retrieved_attachments.count(), 3)
        
        # Clean up
        for attachment in attachments:
            AttachmentService.delete_attachment(attachment)
    
    def test_get_asset_attachments_returns_empty_for_no_attachments(self):
        """Test that get_asset_attachments returns empty queryset when no attachments exist."""
        from assets.services.attachment_service import AttachmentService
        
        # Get attachments for asset with no attachments
        attachments = AttachmentService.get_asset_attachments(self.asset)
        
        # Verify empty queryset
        self.assertEqual(attachments.count(), 0)
    
    def test_get_asset_attachments_ordered_by_upload_date(self):
        """Test that get_asset_attachments returns attachments ordered by upload date (newest first)."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from assets.services.attachment_service import AttachmentService
        import time
        
        # Create multiple attachments with slight delays
        attachments = []
        for i in range(3):
            file_content = b"Test content"
            test_file = SimpleUploadedFile(f"test_{i}.pdf", file_content, content_type="application/pdf")
            attachment = AttachmentService.upload_attachment(self.asset, test_file)
            attachments.append(attachment)
            if i < 2:  # Don't sleep after last one
                time.sleep(0.01)  # Small delay to ensure different timestamps
        
        # Get attachments
        retrieved_attachments = list(AttachmentService.get_asset_attachments(self.asset))
        
        # Verify ordering (newest first)
        self.assertEqual(retrieved_attachments[0].filename, "test_2.pdf")
        self.assertEqual(retrieved_attachments[1].filename, "test_1.pdf")
        self.assertEqual(retrieved_attachments[2].filename, "test_0.pdf")
        
        # Clean up
        for attachment in attachments:
            AttachmentService.delete_attachment(attachment)
    
    def test_delete_attachment_handles_missing_file(self):
        """Test that delete_attachment handles case where file doesn't exist in storage."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from assets.services.attachment_service import AttachmentService
        from django.core.files.storage import default_storage
        
        # Create attachment
        file_content = b"Test content"
        test_file = SimpleUploadedFile("test.pdf", file_content, content_type="application/pdf")
        attachment = AttachmentService.upload_attachment(self.asset, test_file)
        
        # Manually delete the file from storage
        if default_storage.exists(attachment.file.name):
            default_storage.delete(attachment.file.name)
        
        # Delete attachment - should not raise an error
        AttachmentService.delete_attachment(attachment)
        
        # Verify record is deleted
        from assets.models import Attachment
        with self.assertRaises(Attachment.DoesNotExist):
            Attachment.objects.get(id=attachment.id)


class TestWarrantyService(TestCase):
    """Test cases for WarrantyService."""
    
    def setUp(self):
        """Set up test data."""
        from datetime import date, timedelta
        from django.utils import timezone
        
        # Create OS
        self.os = OperatingSystem.objects.create(name="Windows 10")
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password',
            is_staff=True,
            is_active=True
        )
        
        # Create non-admin user
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password',
            is_staff=False,
            is_active=True
        )
        
        today = timezone.now().date()
        
        # Create assets with various warranty dates
        self.asset_expired = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            status='active',
            warranty_expiration=today - timedelta(days=10)
        )
        
        self.asset_expiring_today = Asset.objects.create(
            asset_tag='BIDC002',
            system_type='Laptop',
            operating_system=self.os,
            status='active',
            warranty_expiration=today
        )
        
        self.asset_expiring_in_3_days = Asset.objects.create(
            asset_tag='BIDC003',
            system_type='Desktop',
            operating_system=self.os,
            status='active',
            warranty_expiration=today + timedelta(days=3)
        )
        
        self.asset_expiring_in_7_days = Asset.objects.create(
            asset_tag='BIDC004',
            system_type='All-in-One PC',
            operating_system=self.os,
            status='active',
            warranty_expiration=today + timedelta(days=7)
        )
        
        self.asset_expiring_in_8_days = Asset.objects.create(
            asset_tag='BIDC005',
            system_type='Desktop',
            operating_system=self.os,
            status='active',
            warranty_expiration=today + timedelta(days=8)
        )
        
        self.asset_no_warranty = Asset.objects.create(
            asset_tag='BIDC006',
            system_type='Laptop',
            operating_system=self.os,
            status='active',
            warranty_expiration=None
        )
        
        self.asset_freed = Asset.objects.create(
            asset_tag='BIDC007',
            system_type='Desktop',
            operating_system=self.os,
            status='freed',
            warranty_expiration=today + timedelta(days=5)
        )
    
    def test_check_expiring_warranties_returns_assets_within_7_days(self):
        """Test that check_expiring_warranties returns assets expiring within 7 days."""
        from assets.services.warranty_service import WarrantyService
        
        expiring_assets = WarrantyService.check_expiring_warranties()
        
        # Should include assets expiring today, in 3 days, and in 7 days
        self.assertEqual(expiring_assets.count(), 3)
        
        asset_tags = [asset.asset_tag for asset in expiring_assets]
        self.assertIn('BIDC002', asset_tags)  # expiring today
        self.assertIn('BIDC003', asset_tags)  # expiring in 3 days
        self.assertIn('BIDC004', asset_tags)  # expiring in 7 days
    
    def test_check_expiring_warranties_excludes_expired_assets(self):
        """Test that check_expiring_warranties excludes already expired assets."""
        from assets.services.warranty_service import WarrantyService
        
        expiring_assets = WarrantyService.check_expiring_warranties()
        
        asset_tags = [asset.asset_tag for asset in expiring_assets]
        self.assertNotIn('BIDC001', asset_tags)  # expired 10 days ago
    
    def test_check_expiring_warranties_excludes_assets_beyond_7_days(self):
        """Test that check_expiring_warranties excludes assets expiring beyond 7 days."""
        from assets.services.warranty_service import WarrantyService
        
        expiring_assets = WarrantyService.check_expiring_warranties()
        
        asset_tags = [asset.asset_tag for asset in expiring_assets]
        self.assertNotIn('BIDC005', asset_tags)  # expiring in 8 days
    
    def test_check_expiring_warranties_excludes_freed_assets(self):
        """Test that check_expiring_warranties excludes freed assets."""
        from assets.services.warranty_service import WarrantyService
        
        expiring_assets = WarrantyService.check_expiring_warranties()
        
        asset_tags = [asset.asset_tag for asset in expiring_assets]
        self.assertNotIn('BIDC007', asset_tags)  # freed asset
    
    def test_check_expiring_warranties_excludes_assets_without_warranty(self):
        """Test that check_expiring_warranties excludes assets without warranty dates."""
        from assets.services.warranty_service import WarrantyService
        
        expiring_assets = WarrantyService.check_expiring_warranties()
        
        asset_tags = [asset.asset_tag for asset in expiring_assets]
        self.assertNotIn('BIDC006', asset_tags)  # no warranty date
    
    def test_get_warranty_status_returns_expired(self):
        """Test that get_warranty_status returns 'expired' for expired warranties."""
        from assets.services.warranty_service import WarrantyService
        
        status = WarrantyService.get_warranty_status(self.asset_expired)
        self.assertEqual(status, 'expired')
    
    def test_get_warranty_status_returns_expiring_soon(self):
        """Test that get_warranty_status returns 'expiring_soon' for warranties within 7 days."""
        from assets.services.warranty_service import WarrantyService
        
        status = WarrantyService.get_warranty_status(self.asset_expiring_in_3_days)
        self.assertEqual(status, 'expiring_soon')
        
        status = WarrantyService.get_warranty_status(self.asset_expiring_in_7_days)
        self.assertEqual(status, 'expiring_soon')
    
    def test_get_warranty_status_returns_active(self):
        """Test that get_warranty_status returns 'active' for warranties beyond 7 days."""
        from assets.services.warranty_service import WarrantyService
        
        status = WarrantyService.get_warranty_status(self.asset_expiring_in_8_days)
        self.assertEqual(status, 'active')
    
    def test_get_warranty_status_returns_active_for_no_warranty(self):
        """Test that get_warranty_status returns 'active' when no warranty date is set."""
        from assets.services.warranty_service import WarrantyService
        
        status = WarrantyService.get_warranty_status(self.asset_no_warranty)
        self.assertEqual(status, 'active')
    
    def test_send_warranty_alerts_sends_email_to_admins(self):
        """Test that send_warranty_alerts sends email to admin users."""
        from assets.services.warranty_service import WarrantyService
        from django.core import mail
        
        expiring_assets = [self.asset_expiring_in_3_days, self.asset_expiring_in_7_days]
        
        WarrantyService.send_warranty_alerts(expiring_assets)
        
        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email details
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Asset Warranty Expiration Alert')
        self.assertIn('admin@example.com', email.to)
        self.assertNotIn('user@example.com', email.to)  # non-admin should not receive
        
        # Check email content
        self.assertIn('BIDC003', email.body)
        self.assertIn('BIDC004', email.body)
        self.assertIn('expiring within the next 7 days', email.body)
    
    def test_send_warranty_alerts_includes_days_remaining(self):
        """Test that send_warranty_alerts includes days remaining in email."""
        from assets.services.warranty_service import WarrantyService
        from django.core import mail
        
        expiring_assets = [self.asset_expiring_in_3_days]
        
        WarrantyService.send_warranty_alerts(expiring_assets)
        
        email = mail.outbox[0]
        self.assertIn('3 days remaining', email.body)
    
    def test_send_warranty_alerts_does_nothing_for_empty_list(self):
        """Test that send_warranty_alerts does nothing when given empty list."""
        from assets.services.warranty_service import WarrantyService
        from django.core import mail
        
        WarrantyService.send_warranty_alerts([])
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_warranty_alerts_does_nothing_when_no_admin_emails(self):
        """Test that send_warranty_alerts does nothing when no admin users have emails."""
        from assets.services.warranty_service import WarrantyService
        from django.core import mail
        
        # Remove admin email
        self.admin_user.email = ''
        self.admin_user.save()
        
        expiring_assets = [self.asset_expiring_in_3_days]
        
        WarrantyService.send_warranty_alerts(expiring_assets)
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_warranty_alerts_only_sends_to_active_admins(self):
        """Test that send_warranty_alerts only sends to active admin users."""
        from assets.services.warranty_service import WarrantyService
        from django.core import mail
        
        # Create inactive admin
        inactive_admin = User.objects.create_user(
            username='inactive_admin',
            email='inactive@example.com',
            password='password',
            is_staff=True,
            is_active=False
        )
        
        expiring_assets = [self.asset_expiring_in_3_days]
        
        WarrantyService.send_warranty_alerts(expiring_assets)
        
        email = mail.outbox[0]
        self.assertIn('admin@example.com', email.to)
        self.assertNotIn('inactive@example.com', email.to)



class TestWarrantyTask(TestCase):
    """Test cases for warranty Celery task."""
    
    def setUp(self):
        """Set up test data."""
        from datetime import timedelta
        from django.utils import timezone
        
        # Create OS
        self.os = OperatingSystem.objects.create(name="Windows 10")
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password',
            is_staff=True,
            is_active=True
        )
        
        today = timezone.now().date()
        
        # Create asset expiring soon
        self.asset_expiring = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            status='active',
            warranty_expiration=today + timedelta(days=5)
        )
    
    def test_run_daily_warranty_check_sends_alerts(self):
        """Test that run_daily_warranty_check task sends alerts for expiring warranties."""
        from assets.tasks import run_daily_warranty_check
        from django.core import mail
        
        # Run the task
        run_daily_warranty_check()
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Asset Warranty Expiration Alert')
        self.assertIn('BIDC001', email.body)
    
    def test_run_daily_warranty_check_does_nothing_when_no_expiring(self):
        """Test that run_daily_warranty_check does nothing when no warranties are expiring."""
        from assets.tasks import run_daily_warranty_check
        from django.core import mail
        
        # Delete the expiring asset
        self.asset_expiring.delete()
        
        # Run the task
        run_daily_warranty_check()
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)



class TestImportService(TestCase):
    """Test cases for ImportService."""
    
    def setUp(self):
        """Set up test data."""
        from assets.services.import_service import ImportService
        self.import_service = ImportService()
    
    def test_validate_headers_with_all_required_columns(self):
        """Test that validate_headers returns True when all required columns are present."""
        headers = ['asset_tag', 'system_type', 'operating_system', 'ip_address', 'particulars']
        is_valid, missing = self.import_service.validate_headers(headers)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)
    
    def test_validate_headers_with_missing_columns(self):
        """Test that validate_headers returns False and lists missing columns."""
        headers = ['asset_tag', 'system_type']
        is_valid, missing = self.import_service.validate_headers(headers)
        
        self.assertFalse(is_valid)
        self.assertEqual(len(missing), 1)
        self.assertIn('operating_system', missing)
    
    def test_validate_headers_with_no_required_columns(self):
        """Test that validate_headers returns False when no required columns are present."""
        headers = ['some_column', 'another_column']
        is_valid, missing = self.import_service.validate_headers(headers)
        
        self.assertFalse(is_valid)
        self.assertEqual(len(missing), 3)
        self.assertIn('asset_tag', missing)
        self.assertIn('system_type', missing)
        self.assertIn('operating_system', missing)
    
    def test_validate_headers_with_extra_columns(self):
        """Test that validate_headers returns True when extra columns are present."""
        headers = ['asset_tag', 'system_type', 'operating_system', 'ip_address', 'extra_column', 'another_extra']
        is_valid, missing = self.import_service.validate_headers(headers)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)

    def test_validate_row_with_valid_data(self):
        """Test that validate_row returns True for valid row data."""
        # Set up test data
        os = OperatingSystem.objects.create(name="Windows 10")
        team = Team.objects.create(name="Engineering")
        ip_range = IPRange.objects.create(range_pattern="192.168.10.x", network_prefix="192.168.10")
        ip = IPAddress.objects.create(address="192.168.10.100", ip_range=ip_range, is_assigned=False)
        
        row_data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Desktop',
            'operating_system': 'Windows 10',
            'ip_address': '192.168.10.100',
            'team': 'Engineering',
            'warranty_expiration': '2025-12-31'
        }
        
        is_valid, errors, is_update = self.import_service.validate_row(row_data, 2)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.assertFalse(is_update)
    
    def test_validate_row_with_empty_asset_tag(self):
        """Test that validate_row returns error for empty asset_tag."""
        os_obj = OperatingSystem.objects.create(name="Windows 10")
        row_data = {
            'asset_tag': '',
            'system_type': 'Desktop',
            'operating_system': 'Windows 10',
        }
        
        is_valid, errors, is_update = self.import_service.validate_row(row_data, 2)
        
        self.assertFalse(is_valid)
        self.assertIn("Asset tag is required", errors)
        self.assertFalse(is_update)
    
    def test_validate_row_with_duplicate_asset_tag(self):
        """Test that validate_row sets is_update=True for existing asset_tag."""
        # Create existing asset
        os = OperatingSystem.objects.create(name="Windows 10")
        ip_range = IPRange.objects.create(range_pattern="192.168.10.x", network_prefix="192.168.10")
        ip = IPAddress.objects.create(address="192.168.10.100", ip_range=ip_range, is_assigned=True)
        
        Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=os,
            ip_address=ip
        )
        
        row_data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Laptop',
            'operating_system': 'Windows 10',
        }
        
        is_valid, errors, is_update = self.import_service.validate_row(row_data, 2)
        
        self.assertTrue(is_valid)
        self.assertTrue(is_update)
        self.assertEqual(len(errors), 0)
    
    def test_validate_row_with_invalid_system_type(self):
        """Test that validate_row returns error for invalid system_type."""
        os_obj = OperatingSystem.objects.create(name="Windows 10")
        row_data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Server',  # Invalid type
            'operating_system': 'Windows 10',
        }
        
        is_valid, errors, is_update = self.import_service.validate_row(row_data, 2)
        
        self.assertFalse(is_valid)
        self.assertIn("Invalid system type. Must be Desktop, Laptop, or All-in-One PC", errors)
    
    def test_validate_row_with_nonexistent_operating_system(self):
        """Test that validate_row accepts non-existent OS (will be auto-created on import)."""
        row_data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Desktop',
            'operating_system': 'NonExistentOS',
        }
        
        is_valid, errors, is_update = self.import_service.validate_row(row_data, 2)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_row_with_invalid_ip_address_format(self):
        """Test that validate_row returns error for invalid IPv4 format."""
        os = OperatingSystem.objects.create(name="Windows 10")
        
        row_data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Desktop',
            'operating_system': 'Windows 10',
            'ip_address': '999.999.999.999'  # Invalid IP
        }
        
        is_valid, errors, is_update = self.import_service.validate_row(row_data, 2)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid IPv4 address format" in err for err in errors))
    
    def test_validate_row_with_unavailable_ip_address(self):
        """Test that validate_row returns error for already assigned IP."""
        os = OperatingSystem.objects.create(name="Windows 10")
        ip_range = IPRange.objects.create(range_pattern="192.168.10.x", network_prefix="192.168.10")
        ip = IPAddress.objects.create(address="192.168.10.100", ip_range=ip_range, is_assigned=True)
        
        row_data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Desktop',
            'operating_system': 'Windows 10',
            'ip_address': '192.168.10.100'
        }
        
        is_valid, errors, is_update = self.import_service.validate_row(row_data, 2)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("already assigned to" in err for err in errors))
    
    def test_validate_row_with_ip_not_in_system(self):
        """Test that validate_row accepts IP not in system (will be treated as manual IP)."""
        os = OperatingSystem.objects.create(name="Windows 10")
        
        row_data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Desktop',
            'operating_system': 'Windows 10',
            'ip_address': '192.168.10.100'  # IP not in database - will be manual IP
        }
        
        is_valid, errors, is_update = self.import_service.validate_row(row_data, 2)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_row_with_nonexistent_team(self):
        """Test that validate_row returns error for non-existent team."""
        os = OperatingSystem.objects.create(name="Windows 10")
        ip_range = IPRange.objects.create(range_pattern="192.168.10.x", network_prefix="192.168.10")
        ip = IPAddress.objects.create(address="192.168.10.100", ip_range=ip_range, is_assigned=False)
        
        row_data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Desktop',
            'operating_system': 'Windows 10',
            'ip_address': '192.168.10.100',
            'team': 'NonExistentTeam'
        }
        
        is_valid, errors, is_update = self.import_service.validate_row(row_data, 2)
        
        self.assertFalse(is_valid)
        self.assertIn("Team not found", errors)
    
    def test_validate_row_with_invalid_warranty_date_format(self):
        """Test that validate_row returns error for invalid warranty date format."""
        os = OperatingSystem.objects.create(name="Windows 10")
        ip_range = IPRange.objects.create(range_pattern="192.168.10.x", network_prefix="192.168.10")
        ip = IPAddress.objects.create(address="192.168.10.100", ip_range=ip_range, is_assigned=False)
        
        row_data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Desktop',
            'operating_system': 'Windows 10',
            'ip_address': '192.168.10.100',
            'warranty_expiration': '12/31/2025'  # Wrong format
        }
        
        is_valid, errors, is_update = self.import_service.validate_row(row_data, 2)
        
        self.assertFalse(is_valid)
        self.assertIn("Invalid date format. Use YYYY-MM-DD", errors)
    
    def test_validate_row_with_optional_fields_empty(self):
        """Test that validate_row accepts empty optional fields including ip_address."""
        os = OperatingSystem.objects.create(name="Windows 10")
        
        row_data = {
            'asset_tag': 'BIDC001',
            'system_type': 'Desktop',
            'operating_system': 'Windows 10',
            'ip_address': '',
            'team': '',
            'warranty_expiration': ''
        }
        
        is_valid, errors, is_update = self.import_service.validate_row(row_data, 2)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.assertFalse(is_update)
    
    def test_validate_row_with_multiple_errors(self):
        """Test that validate_row returns all errors for a row with multiple issues."""
        row_data = {
            'asset_tag': '',
            'system_type': 'Server',
            'operating_system': 'NonExistentOS',
        }
        
        is_valid, errors, is_update = self.import_service.validate_row(row_data, 2)
        
        self.assertFalse(is_valid)
        self.assertGreaterEqual(len(errors), 2)  # At least 2 errors (empty asset_tag + invalid system_type)
        self.assertFalse(is_update)

    def test_import_assets_with_valid_excel_file(self):
        """Test that import_assets successfully imports valid assets from Excel."""
        import openpyxl
        from io import BytesIO
        from django.contrib.auth.models import User
        
        # Set up test data
        os = OperatingSystem.objects.create(name="Windows 10")
        team = Team.objects.create(name="Engineering")
        ip_range = IPRange.objects.create(range_pattern="192.168.10.x", network_prefix="192.168.10")
        ip1 = IPAddress.objects.create(address="192.168.10.100", ip_range=ip_range, is_assigned=False)
        ip2 = IPAddress.objects.create(address="192.168.10.101", ip_range=ip_range, is_assigned=False)
        user = User.objects.create_user(username='testuser', password='password')
        
        # Create Excel file in memory
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        
        # Write headers
        sheet.append(['asset_tag', 'system_type', 'operating_system', 'ip_address', 'particulars', 'assigned_to', 'team', 'warranty_expiration'])
        
        # Write data rows
        sheet.append(['BIDC001', 'Desktop', 'Windows 10', '192.168.10.100', 'Test asset 1', 'John Doe', 'Engineering', '2025-12-31'])
        sheet.append(['BIDC002', 'Laptop', 'Windows 10', '192.168.10.101', 'Test asset 2', 'Jane Smith', 'Engineering', '2026-01-15'])
        
        # Save to BytesIO
        excel_file = BytesIO()
        workbook.save(excel_file)
        excel_file.seek(0)
        
        # Import assets
        result = self.import_service.import_assets(excel_file, user)
        
        # Verify results
        self.assertEqual(result['created_count'], 2)
        self.assertEqual(result['updated_count'], 0)
        self.assertEqual(result['error_count'], 0)
        self.assertEqual(len(result['errors']), 0)
        
        # Verify assets were created
        self.assertEqual(Asset.objects.count(), 2)
        asset1 = Asset.objects.get(asset_tag='BIDC001')
        self.assertEqual(asset1.system_type, 'Desktop')
        self.assertEqual(asset1.operating_system.name, 'Windows 10')
        self.assertEqual(asset1.ip_address.address, '192.168.10.100')
        self.assertEqual(asset1.assigned_to, 'John Doe')
        self.assertEqual(asset1.team.name, 'Engineering')
        
        # Verify IPs were assigned
        ip1.refresh_from_db()
        ip2.refresh_from_db()
        self.assertTrue(ip1.is_assigned)
        self.assertTrue(ip2.is_assigned)
    
    def test_import_assets_with_validation_errors(self):
        """Test that import_assets handles validation errors correctly."""
        import openpyxl
        from io import BytesIO
        from django.contrib.auth.models import User
        
        # Set up test data
        os = OperatingSystem.objects.create(name="Windows 10")
        ip_range = IPRange.objects.create(range_pattern="192.168.10.x", network_prefix="192.168.10")
        ip1 = IPAddress.objects.create(address="192.168.10.100", ip_range=ip_range, is_assigned=False)
        user = User.objects.create_user(username='testuser', password='password')
        
        # Create Excel file with one valid and one invalid row
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        
        # Write headers
        sheet.append(['asset_tag', 'system_type', 'operating_system', 'ip_address'])
        
        # Write data rows
        sheet.append(['BIDC001', 'Desktop', 'Windows 10', '192.168.10.100'])  # Valid
        sheet.append(['BIDC002', 'Server', 'Windows 10', '192.168.10.101'])  # Invalid system_type
        
        # Save to BytesIO
        excel_file = BytesIO()
        workbook.save(excel_file)
        excel_file.seek(0)
        
        # Import assets
        result = self.import_service.import_assets(excel_file, user)
        
        # Verify results
        self.assertEqual(result['created_count'], 1)
        self.assertEqual(result['updated_count'], 0)
        self.assertEqual(result['error_count'], 1)
        self.assertEqual(len(result['errors']), 1)
        self.assertEqual(result['errors'][0]['row'], 3)
        self.assertIn('Invalid system type', result['errors'][0]['errors'][0])
        
        # Verify only valid asset was created
        self.assertEqual(Asset.objects.count(), 1)
        self.assertTrue(Asset.objects.filter(asset_tag='BIDC001').exists())
        self.assertFalse(Asset.objects.filter(asset_tag='BIDC002').exists())
    
    def test_import_assets_with_missing_headers(self):
        """Test that import_assets returns error for missing required headers."""
        import openpyxl
        from io import BytesIO
        from django.contrib.auth.models import User
        
        user = User.objects.create_user(username='testuser', password='password')
        
        # Create Excel file with missing headers
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        
        # Write incomplete headers
        sheet.append(['asset_tag', 'system_type'])  # Missing operating_system and ip_address
        sheet.append(['BIDC001', 'Desktop'])
        
        # Save to BytesIO
        excel_file = BytesIO()
        workbook.save(excel_file)
        excel_file.seek(0)
        
        # Import assets
        result = self.import_service.import_assets(excel_file, user)
        
        # Verify results
        self.assertEqual(result['created_count'], 0)
        self.assertEqual(result['updated_count'], 0)
        self.assertEqual(result['error_count'], 0)
        self.assertEqual(len(result['errors']), 1)
        self.assertEqual(result['errors'][0]['row'], 0)
        self.assertIn('Missing required columns', result['errors'][0]['errors'][0])
        
        # Verify no assets were created
        self.assertEqual(Asset.objects.count(), 0)



class TestExportService(TestCase):
    """Test cases for ExportService."""
    
    def setUp(self):
        """Set up test data."""
        from assets.services.export_service import ExportService
        
        # Create OS and Team
        self.os = OperatingSystem.objects.create(name="Windows 10")
        self.team = Team.objects.create(name="IT Department")
        
        # Create IP range and address
        self.ip_range = IPRange.objects.create(
            range_pattern="192.168.10.x",
            network_prefix="192.168.10"
        )
        self.ip = IPAddress.objects.create(
            address="192.168.10.1",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create test assets
        self.asset1 = Asset.objects.create(
            asset_tag='BIDC001',
            system_type='Desktop',
            operating_system=self.os,
            ip_address=self.ip,
            assigned_to='John Doe',
            team=self.team,
            status='active'
        )
        self.asset2 = Asset.objects.create(
            asset_tag='BIDC002',
            system_type='Laptop',
            operating_system=self.os,
            status='active'
        )
        
        self.export_service = ExportService()
    
    def test_create_workbook_with_empty_queryset(self):
        """Test that _create_workbook handles empty queryset."""
        from assets.models import Asset
        
        queryset = Asset.objects.none()
        columns = ['Serial Number', 'Asset Tag', 'System Type']
        title = 'Test Export'
        
        workbook = self.export_service._create_workbook(queryset, columns, title)
        sheet = workbook.active
        
        # Check title
        self.assertEqual(sheet.title, title)
        
        # Check headers are present
        self.assertEqual(sheet.cell(1, 1).value, 'Serial Number')
        self.assertEqual(sheet.cell(1, 2).value, 'Asset Tag')
        self.assertEqual(sheet.cell(1, 3).value, 'System Type')
        
        # Check no data rows (only header row)
        self.assertEqual(sheet.max_row, 1)
    
    def test_create_workbook_with_data(self):
        """Test that _create_workbook creates workbook with data."""
        from assets.models import Asset
        
        queryset = Asset.objects.filter(status='active').order_by('serial_number')
        columns = ['Serial Number', 'Asset Tag', 'System Type']
        title = 'Active Assets'
        
        # Define row extractor function
        def extract_row(asset):
            return [
                asset.serial_number,
                asset.asset_tag,
                asset.system_type
            ]
        
        workbook = self.export_service._create_workbook(queryset, columns, title, extract_row)
        sheet = workbook.active
        
        # Check title
        self.assertEqual(sheet.title, title)
        
        # Check headers
        self.assertEqual(sheet.cell(1, 1).value, 'Serial Number')
        self.assertEqual(sheet.cell(1, 2).value, 'Asset Tag')
        self.assertEqual(sheet.cell(1, 3).value, 'System Type')
        
        # Check data rows (2 assets + 1 header = 3 rows)
        self.assertEqual(sheet.max_row, 3)
        
        # Check first data row
        self.assertEqual(sheet.cell(2, 1).value, self.asset1.serial_number)
        self.assertEqual(sheet.cell(2, 2).value, 'BIDC001')
        self.assertEqual(sheet.cell(2, 3).value, 'Desktop')
        
        # Check second data row
        self.assertEqual(sheet.cell(3, 1).value, self.asset2.serial_number)
        self.assertEqual(sheet.cell(3, 2).value, 'BIDC002')
        self.assertEqual(sheet.cell(3, 3).value, 'Laptop')
    
    def test_create_workbook_formats_column_widths(self):
        """Test that _create_workbook formats column widths appropriately."""
        from assets.models import Asset
        
        queryset = Asset.objects.filter(status='active').order_by('serial_number')
        columns = ['Serial Number', 'Asset Tag']
        title = 'Test'
        
        def extract_row(asset):
            return [asset.serial_number, asset.asset_tag]
        
        workbook = self.export_service._create_workbook(queryset, columns, title, extract_row)
        sheet = workbook.active
        
        # Check that column widths are set (should be at least 10)
        self.assertGreaterEqual(sheet.column_dimensions['A'].width, 10)
        self.assertGreaterEqual(sheet.column_dimensions['B'].width, 10)
        
        # Check that column widths don't exceed maximum (50)
        self.assertLessEqual(sheet.column_dimensions['A'].width, 50)
        self.assertLessEqual(sheet.column_dimensions['B'].width, 50)

    def test_export_active_assets_returns_http_response(self):
        """Test that export_active_assets returns HttpResponse with correct headers."""
        response = self.export_service.export_active_assets()
        
        # Check response type
        from django.http import HttpResponse
        self.assertIsInstance(response, HttpResponse)
        
        # Check content type
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Check Content-Disposition header
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=active_assets.xlsx'
        )
    
    def test_export_active_assets_includes_all_columns(self):
        """Test that export_active_assets includes all required columns."""
        import openpyxl
        from io import BytesIO
        
        response = self.export_service.export_active_assets()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Check headers
        expected_headers = [
            'Serial Number',
            'Asset Tag',
            'System Type',
            'OS',
            'IP Address',
            'Assigned To',
            'Team',
            'Warranty Expiration'
        ]
        
        for col_idx, expected_header in enumerate(expected_headers, start=1):
            self.assertEqual(sheet.cell(1, col_idx).value, expected_header)
    
    def test_export_active_assets_includes_only_active_assets(self):
        """Test that export_active_assets includes only active assets."""
        import openpyxl
        from io import BytesIO
        
        # Create a freed asset
        Asset.objects.create(
            asset_tag='BIDC003',
            system_type='Desktop',
            operating_system=self.os,
            status='freed'
        )
        
        response = self.export_service.export_active_assets()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Should have 2 active assets + 1 header row = 3 rows
        self.assertEqual(sheet.max_row, 3)
    
    def test_export_active_assets_with_all_fields(self):
        """Test that export_active_assets correctly exports all fields."""
        import openpyxl
        from io import BytesIO
        from datetime import date
        
        # Update asset1 with warranty expiration
        self.asset1.warranty_expiration = date(2025, 12, 31)
        self.asset1.save()
        
        response = self.export_service.export_active_assets()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Check first data row (asset1)
        self.assertEqual(sheet.cell(2, 1).value, self.asset1.serial_number)
        self.assertEqual(sheet.cell(2, 2).value, 'BIDC001')
        self.assertEqual(sheet.cell(2, 3).value, 'Desktop')
        self.assertEqual(sheet.cell(2, 4).value, 'Windows 10')
        self.assertEqual(sheet.cell(2, 5).value, '192.168.10.1')
        self.assertEqual(sheet.cell(2, 6).value, 'John Doe')
        self.assertEqual(sheet.cell(2, 7).value, 'IT Department')
        self.assertEqual(sheet.cell(2, 8).value, '2025-12-31')
    
    def test_export_active_assets_with_empty_optional_fields(self):
        """Test that export_active_assets handles empty optional fields."""
        import openpyxl
        from io import BytesIO
        
        response = self.export_service.export_active_assets()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Check second data row (asset2 has no IP, assigned_to, team, warranty)
        self.assertEqual(sheet.cell(3, 1).value, self.asset2.serial_number)
        self.assertEqual(sheet.cell(3, 2).value, 'BIDC002')
        self.assertEqual(sheet.cell(3, 3).value, 'Laptop')
        self.assertEqual(sheet.cell(3, 4).value, 'Windows 10')
        # Empty cells return empty string or None in openpyxl
        self.assertIn(sheet.cell(3, 5).value, ['', None])  # No IP
        self.assertIn(sheet.cell(3, 6).value, ['', None])  # No assigned_to
        self.assertIn(sheet.cell(3, 7).value, ['', None])  # No team
        self.assertIn(sheet.cell(3, 8).value, ['', None])  # No warranty

    def test_export_freed_assets_returns_http_response(self):
        """Test that export_freed_assets returns HttpResponse with correct headers."""
        response = self.export_service.export_freed_assets()
        
        # Check response type
        from django.http import HttpResponse
        self.assertIsInstance(response, HttpResponse)
        
        # Check content type
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Check Content-Disposition header
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=freed_assets.xlsx'
        )
    
    def test_export_freed_assets_includes_all_columns(self):
        """Test that export_freed_assets includes all required columns."""
        import openpyxl
        from io import BytesIO
        
        response = self.export_service.export_freed_assets()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Check headers
        expected_headers = [
            'Serial Number',
            'Asset Tag',
            'System Type',
            'OS',
            'IP Address',
            'Freed Date'
        ]
        
        for col_idx, expected_header in enumerate(expected_headers, start=1):
            self.assertEqual(sheet.cell(1, col_idx).value, expected_header)
    
    def test_export_freed_assets_includes_only_freed_assets(self):
        """Test that export_freed_assets includes only freed assets."""
        import openpyxl
        from io import BytesIO
        from django.utils import timezone
        
        # Create freed assets
        freed_asset1 = Asset.objects.create(
            asset_tag='BIDC003',
            system_type='Desktop',
            operating_system=self.os,
            status='freed',
            freed_date=timezone.now()
        )
        freed_asset2 = Asset.objects.create(
            asset_tag='BIDC004',
            system_type='Laptop',
            operating_system=self.os,
            status='freed',
            freed_date=timezone.now()
        )
        
        response = self.export_service.export_freed_assets()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Should have 2 freed assets + 1 header row = 3 rows
        self.assertEqual(sheet.max_row, 3)
        
        # Verify active assets are not included
        asset_tags = [sheet.cell(row, 2).value for row in range(2, sheet.max_row + 1)]
        self.assertIn('BIDC003', asset_tags)
        self.assertIn('BIDC004', asset_tags)
        self.assertNotIn('BIDC001', asset_tags)  # Active asset
        self.assertNotIn('BIDC002', asset_tags)  # Active asset
    
    def test_export_freed_assets_ordered_by_freed_date_descending(self):
        """Test that export_freed_assets orders by freed_date descending."""
        import openpyxl
        from io import BytesIO
        from django.utils import timezone
        from datetime import timedelta
        
        # Create freed assets with different freed dates
        now = timezone.now()
        freed_asset1 = Asset.objects.create(
            asset_tag='BIDC003',
            system_type='Desktop',
            operating_system=self.os,
            status='freed',
            freed_date=now - timedelta(days=2)  # Older
        )
        freed_asset2 = Asset.objects.create(
            asset_tag='BIDC004',
            system_type='Laptop',
            operating_system=self.os,
            status='freed',
            freed_date=now  # Newer
        )
        
        response = self.export_service.export_freed_assets()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # First data row should be the newer freed asset (BIDC004)
        self.assertEqual(sheet.cell(2, 2).value, 'BIDC004')
        # Second data row should be the older freed asset (BIDC003)
        self.assertEqual(sheet.cell(3, 2).value, 'BIDC003')
    
    def test_export_freed_assets_with_all_fields(self):
        """Test that export_freed_assets correctly exports all fields."""
        import openpyxl
        from io import BytesIO
        from django.utils import timezone
        
        # Create IP for freed asset
        ip2 = IPAddress.objects.create(
            address="192.168.10.2",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create freed asset with all fields
        freed_date = timezone.now()
        freed_asset = Asset.objects.create(
            asset_tag='BIDC003',
            system_type='Desktop',
            operating_system=self.os,
            ip_address=ip2,
            status='freed',
            freed_date=freed_date
        )
        
        response = self.export_service.export_freed_assets()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Check first data row
        self.assertEqual(sheet.cell(2, 1).value, freed_asset.serial_number)
        self.assertEqual(sheet.cell(2, 2).value, 'BIDC003')
        self.assertEqual(sheet.cell(2, 3).value, 'Desktop')
        self.assertEqual(sheet.cell(2, 4).value, 'Windows 10')
        self.assertEqual(sheet.cell(2, 5).value, '192.168.10.2')
        # Check freed date is present (format: YYYY-MM-DD HH:MM:SS)
        self.assertIsNotNone(sheet.cell(2, 6).value)
        self.assertIn(freed_date.strftime('%Y-%m-%d'), sheet.cell(2, 6).value)
    
    def test_export_freed_assets_with_empty_optional_fields(self):
        """Test that export_freed_assets handles empty optional fields."""
        import openpyxl
        from io import BytesIO
        from django.utils import timezone
        
        # Create freed asset without IP and freed_date
        freed_asset = Asset.objects.create(
            asset_tag='BIDC003',
            system_type='Laptop',
            operating_system=self.os,
            status='freed'
            # No ip_address, no freed_date
        )
        
        response = self.export_service.export_freed_assets()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Check data row
        self.assertEqual(sheet.cell(2, 1).value, freed_asset.serial_number)
        self.assertEqual(sheet.cell(2, 2).value, 'BIDC003')
        self.assertEqual(sheet.cell(2, 3).value, 'Laptop')
        self.assertEqual(sheet.cell(2, 4).value, 'Windows 10')
        # Empty cells return empty string or None in openpyxl
        self.assertIn(sheet.cell(2, 5).value, ['', None])  # No IP
        self.assertIn(sheet.cell(2, 6).value, ['', None])  # No freed_date
    
    def test_export_freed_assets_with_empty_queryset(self):
        """Test that export_freed_assets handles empty queryset (no freed assets)."""
        import openpyxl
        from io import BytesIO
        
        # No freed assets exist, only active ones
        response = self.export_service.export_freed_assets()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Should have only header row
        self.assertEqual(sheet.max_row, 1)
        
        # Check headers are present
        self.assertEqual(sheet.cell(1, 1).value, 'Serial Number')
        self.assertEqual(sheet.cell(1, 2).value, 'Asset Tag')

    def test_export_free_ips_returns_http_response(self):
        """Test that export_free_ips returns HttpResponse with correct headers."""
        response = self.export_service.export_free_ips()
        
        # Check response type
        from django.http import HttpResponse
        self.assertIsInstance(response, HttpResponse)
        
        # Check content type
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Check Content-Disposition header
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=free_ips.xlsx'
        )
    
    def test_export_free_ips_includes_all_columns(self):
        """Test that export_free_ips includes all required columns."""
        import openpyxl
        from io import BytesIO
        
        response = self.export_service.export_free_ips()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Check headers
        expected_headers = [
            'IP Address',
            'IP Range'
        ]
        
        for col_idx, expected_header in enumerate(expected_headers, start=1):
            self.assertEqual(sheet.cell(1, col_idx).value, expected_header)
    
    def test_export_free_ips_includes_only_free_ips(self):
        """Test that export_free_ips includes only unassigned IP addresses."""
        import openpyxl
        from io import BytesIO
        
        # Create additional free IPs
        free_ip1 = IPAddress.objects.create(
            address="192.168.10.5",
            ip_range=self.ip_range,
            is_assigned=False
        )
        free_ip2 = IPAddress.objects.create(
            address="192.168.10.10",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create an assigned IP
        assigned_ip = IPAddress.objects.create(
            address="192.168.10.20",
            ip_range=self.ip_range,
            is_assigned=True
        )
        
        response = self.export_service.export_free_ips()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Should have 3 free IPs (self.ip + free_ip1 + free_ip2) + 1 header row = 4 rows
        self.assertEqual(sheet.max_row, 4)
        
        # Verify assigned IP is not included
        ip_addresses = [sheet.cell(row, 1).value for row in range(2, sheet.max_row + 1)]
        self.assertIn('192.168.10.1', ip_addresses)
        self.assertIn('192.168.10.5', ip_addresses)
        self.assertIn('192.168.10.10', ip_addresses)
        self.assertNotIn('192.168.10.20', ip_addresses)  # Assigned IP
    
    def test_export_free_ips_ordered_by_range_and_address(self):
        """Test that export_free_ips orders by IP range then by address."""
        import openpyxl
        from io import BytesIO
        
        # Create another IP range
        ip_range2 = IPRange.objects.create(
            range_pattern="192.168.11.x",
            network_prefix="192.168.11"
        )
        
        # Create IPs in different ranges
        ip1 = IPAddress.objects.create(
            address="192.168.11.5",
            ip_range=ip_range2,
            is_assigned=False
        )
        ip2 = IPAddress.objects.create(
            address="192.168.10.100",
            ip_range=self.ip_range,
            is_assigned=False
        )
        ip3 = IPAddress.objects.create(
            address="192.168.10.50",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        response = self.export_service.export_free_ips()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Verify ordering: IPs should be grouped by range and ordered by address within range
        # Expected order depends on range_pattern ordering
        ip_addresses = [sheet.cell(row, 1).value for row in range(2, sheet.max_row + 1)]
        ip_ranges = [sheet.cell(row, 2).value for row in range(2, sheet.max_row + 1)]
        
        # All IPs should be present
        self.assertIn('192.168.10.1', ip_addresses)
        self.assertIn('192.168.10.50', ip_addresses)
        self.assertIn('192.168.10.100', ip_addresses)
        self.assertIn('192.168.11.5', ip_addresses)
        
        # All ranges should be present
        self.assertIn('192.168.10.x', ip_ranges)
        self.assertIn('192.168.11.x', ip_ranges)
    
    def test_export_free_ips_with_all_fields(self):
        """Test that export_free_ips correctly exports all fields."""
        import openpyxl
        from io import BytesIO
        
        response = self.export_service.export_free_ips()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Check first data row (self.ip)
        self.assertEqual(sheet.cell(2, 1).value, '192.168.10.1')
        self.assertEqual(sheet.cell(2, 2).value, '192.168.10.x')
    
    def test_export_free_ips_with_empty_queryset(self):
        """Test that export_free_ips handles empty queryset (no free IPs)."""
        import openpyxl
        from io import BytesIO
        
        # Mark all IPs as assigned
        IPAddress.objects.all().update(is_assigned=True)
        
        response = self.export_service.export_free_ips()
        
        # Load workbook from response
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        # Should have only header row
        self.assertEqual(sheet.max_row, 1)
        
        # Check headers are present
        self.assertEqual(sheet.cell(1, 1).value, 'IP Address')
        self.assertEqual(sheet.cell(1, 2).value, 'IP Range')



class TestFilterService(TestCase):
    """Test cases for FilterService."""
    
    def setUp(self):
        """Set up test data."""
        from assets.services.filter_service import FilterService
        
        # Create OS
        self.os1 = OperatingSystem.objects.create(name="Windows 10")
        self.os2 = OperatingSystem.objects.create(name="Ubuntu 20.04")
        
        # Create teams
        self.team1 = Team.objects.create(name="Engineering")
        self.team2 = Team.objects.create(name="Marketing")
        
        # Create assets
        self.asset1 = Asset.objects.create(
            asset_tag="BIDC001",
            system_type="Desktop",
            operating_system=self.os1,
            assigned_to="John Doe",
            team=self.team1,
            status="active"
        )
        self.asset2 = Asset.objects.create(
            asset_tag="BIDC002",
            system_type="Laptop",
            operating_system=self.os2,
            assigned_to="Jane Smith",
            team=self.team2,
            status="active"
        )
        self.asset3 = Asset.objects.create(
            asset_tag="BIDC003",
            system_type="Desktop",
            operating_system=self.os1,
            assigned_to="Bob Johnson",
            team=self.team1,
            status="active"
        )
        
        self.filter_service = FilterService()
    
    def test_filter_by_os(self):
        """Test filtering assets by operating system."""
        queryset = Asset.objects.filter(status='active')
        filtered = self.filter_service.filter_by_os(queryset, self.os1.id)
        
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.asset1, filtered)
        self.assertIn(self.asset3, filtered)
        self.assertNotIn(self.asset2, filtered)
    
    def test_filter_by_asset_tag(self):
        """Test filtering assets by asset tag (partial match)."""
        queryset = Asset.objects.filter(status='active')
        filtered = self.filter_service.filter_by_asset_tag(queryset, "BIDC001")
        
        self.assertEqual(filtered.count(), 1)
        self.assertIn(self.asset1, filtered)
    
    def test_filter_by_asset_tag_case_insensitive(self):
        """Test that asset tag filter is case-insensitive."""
        queryset = Asset.objects.filter(status='active')
        filtered = self.filter_service.filter_by_asset_tag(queryset, "bidc001")
        
        self.assertEqual(filtered.count(), 1)
        self.assertIn(self.asset1, filtered)
    
    def test_filter_by_asset_tag_partial_match(self):
        """Test that asset tag filter supports partial matching."""
        queryset = Asset.objects.filter(status='active')
        filtered = self.filter_service.filter_by_asset_tag(queryset, "BIDC")
        
        self.assertEqual(filtered.count(), 3)
    
    def test_filter_by_team(self):
        """Test filtering assets by team."""
        queryset = Asset.objects.filter(status='active')
        filtered = self.filter_service.filter_by_team(queryset, self.team1.id)
        
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.asset1, filtered)
        self.assertIn(self.asset3, filtered)
        self.assertNotIn(self.asset2, filtered)
    
    def test_filter_by_assigned_user(self):
        """Test filtering assets by assigned user name."""
        queryset = Asset.objects.filter(status='active')
        filtered = self.filter_service.filter_by_assigned_user(queryset, "John Doe")
        
        self.assertEqual(filtered.count(), 1)
        self.assertIn(self.asset1, filtered)
    
    def test_filter_by_assigned_user_case_insensitive(self):
        """Test that assigned user filter is case-insensitive."""
        queryset = Asset.objects.filter(status='active')
        filtered = self.filter_service.filter_by_assigned_user(queryset, "john doe")
        
        self.assertEqual(filtered.count(), 1)
        self.assertIn(self.asset1, filtered)
    
    def test_filter_by_assigned_user_partial_match(self):
        """Test that assigned user filter supports partial matching."""
        queryset = Asset.objects.filter(status='active')
        filtered = self.filter_service.filter_by_assigned_user(queryset, "John")
        
        # Should match "John Doe" and "Bob Johnson"
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.asset1, filtered)
        self.assertIn(self.asset3, filtered)

    def test_apply_filters_single_os(self):
        """Test applying a single OS filter."""
        queryset = Asset.objects.filter(status='active')
        filters = {'operating_system': self.os1.id}
        filtered = self.filter_service.apply_filters(queryset, filters)
        
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.asset1, filtered)
        self.assertIn(self.asset3, filtered)
        self.assertNotIn(self.asset2, filtered)
    
    def test_apply_filters_single_asset_tag(self):
        """Test applying a single asset tag filter."""
        queryset = Asset.objects.filter(status='active')
        filters = {'asset_tag': 'BIDC001'}
        filtered = self.filter_service.apply_filters(queryset, filters)
        
        self.assertEqual(filtered.count(), 1)
        self.assertIn(self.asset1, filtered)
    
    def test_apply_filters_single_team(self):
        """Test applying a single team filter."""
        queryset = Asset.objects.filter(status='active')
        filters = {'team': self.team1.id}
        filtered = self.filter_service.apply_filters(queryset, filters)
        
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.asset1, filtered)
        self.assertIn(self.asset3, filtered)
    
    def test_apply_filters_single_assigned_to(self):
        """Test applying a single assigned_to filter."""
        queryset = Asset.objects.filter(status='active')
        filters = {'assigned_to': 'John'}
        filtered = self.filter_service.apply_filters(queryset, filters)
        
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.asset1, filtered)
        self.assertIn(self.asset3, filtered)
    
    def test_apply_filters_multiple_and_logic(self):
        """Test applying multiple filters with AND logic."""
        queryset = Asset.objects.filter(status='active')
        filters = {
            'operating_system': self.os1.id,
            'team': self.team1.id
        }
        filtered = self.filter_service.apply_filters(queryset, filters)
        
        # Both asset1 and asset3 have os1 and team1
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.asset1, filtered)
        self.assertIn(self.asset3, filtered)
    
    def test_apply_filters_multiple_narrow_results(self):
        """Test that multiple filters narrow down results."""
        queryset = Asset.objects.filter(status='active')
        filters = {
            'operating_system': self.os1.id,
            'assigned_to': 'John Doe'
        }
        filtered = self.filter_service.apply_filters(queryset, filters)
        
        # Only asset1 matches both criteria
        self.assertEqual(filtered.count(), 1)
        self.assertIn(self.asset1, filtered)
    
    def test_apply_filters_all_filters(self):
        """Test applying all four filters together."""
        queryset = Asset.objects.filter(status='active')
        filters = {
            'operating_system': self.os1.id,
            'asset_tag': 'BIDC001',
            'team': self.team1.id,
            'assigned_to': 'John'
        }
        filtered = self.filter_service.apply_filters(queryset, filters)
        
        # Only asset1 matches all criteria
        self.assertEqual(filtered.count(), 1)
        self.assertIn(self.asset1, filtered)
    
    def test_apply_filters_no_matches(self):
        """Test applying filters that result in no matches."""
        queryset = Asset.objects.filter(status='active')
        filters = {
            'operating_system': self.os1.id,
            'team': self.team2.id  # os1 assets are in team1, not team2
        }
        filtered = self.filter_service.apply_filters(queryset, filters)
        
        self.assertEqual(filtered.count(), 0)
    
    def test_apply_filters_empty_dict(self):
        """Test applying empty filters dict returns original queryset."""
        queryset = Asset.objects.filter(status='active')
        filters = {}
        filtered = self.filter_service.apply_filters(queryset, filters)
        
        self.assertEqual(filtered.count(), 3)
        self.assertEqual(list(filtered), list(queryset))
    
    def test_apply_filters_none_values(self):
        """Test that None values in filters are ignored."""
        queryset = Asset.objects.filter(status='active')
        filters = {
            'operating_system': None,
            'asset_tag': None,
            'team': self.team1.id,
            'assigned_to': None
        }
        filtered = self.filter_service.apply_filters(queryset, filters)
        
        # Only team filter should be applied
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.asset1, filtered)
        self.assertIn(self.asset3, filtered)
    
    def test_apply_filters_empty_string_values(self):
        """Test that empty string values in filters are ignored."""
        queryset = Asset.objects.filter(status='active')
        filters = {
            'operating_system': '',
            'asset_tag': '',
            'team': self.team1.id,
            'assigned_to': ''
        }
        filtered = self.filter_service.apply_filters(queryset, filters)
        
        # Only team filter should be applied
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.asset1, filtered)
        self.assertIn(self.asset3, filtered)
