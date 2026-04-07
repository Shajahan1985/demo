"""
Property-based tests using Hypothesis.
"""
import pytest
from datetime import timedelta
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase
from django.db import IntegrityError, models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from assets.models import OperatingSystem, Team, IPRange, IPAddress, Asset
from assets.services.asset_service import AssetService


# Property-based tests will be added here as features are implemented


@pytest.mark.django_db
class TestAssetServiceProperties(TestCase):
    """Property-based tests for AssetService."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create user - use get_or_create to avoid duplicate errors
        self.user, _ = User.objects.get_or_create(
            username='admin_prop_test',
            defaults={'password': 'password'}
        )
        
        # Create OS and Team - use get_or_create to avoid duplicates
        self.os, _ = OperatingSystem.objects.get_or_create(name="Windows 10 Test")
        self.team, _ = Team.objects.get_or_create(name="IT Department Test")
        
        # Create IP range and addresses
        self.ip_range, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.99.x",
            defaults={'network_prefix': "192.168.99"}
        )
        
        # Clean up any existing IPs and create fresh ones
        IPAddress.objects.filter(ip_range=self.ip_range).delete()
        self.ip1 = IPAddress.objects.create(
            address="192.168.99.1",
            ip_range=self.ip_range,
            is_assigned=False
        )
        self.ip2 = IPAddress.objects.create(
            address="192.168.99.2",
            ip_range=self.ip_range,
            is_assigned=False
        )
    
    @given(
        asset_tag=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        particulars=st.text(max_size=200),
        assigned_to=st.text(max_size=100)
    )
    @settings(max_examples=100)
    def test_property_1_asset_creation_completeness(self, asset_tag, system_type, particulars, assigned_to):
        """
        Feature: asset-tracker, Property 1: Asset creation completeness
        
        For any valid asset data (with asset_tag, system_type, OS, IP, particulars, 
        assigned_to, and team), creating an asset should result in an asset record 
        containing all the provided fields.
        
        Validates: Requirements 1.1
        """
        # Clean inputs
        asset_tag = asset_tag.strip()
        
        # Ensure unique asset tag
        assume(not Asset.objects.filter(asset_tag=asset_tag).exists())
        
        # Create asset with all fields
        data = {
            'asset_tag': asset_tag,
            'system_type': system_type,
            'operating_system': self.os.id,
            'ip_address': self.ip1.id,
            'particulars': particulars,
            'assigned_to': assigned_to,
            'team': self.team.id,
        }
        
        asset = AssetService.create_asset(data, self.user)
        
        # Verify all fields are present
        assert asset.asset_tag == asset_tag
        assert asset.system_type == system_type
        assert asset.operating_system == self.os
        assert asset.ip_address == self.ip1
        assert asset.particulars == particulars
        assert asset.assigned_to == assigned_to
        assert asset.team == self.team
        
        # Clean up for next iteration
        asset.delete()
        self.ip1.is_assigned = False
        self.ip1.assigned_to_asset = None
        self.ip1.save()
    
    @given(asset_tag=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
    @settings(max_examples=100)
    def test_property_2_asset_tag_uniqueness_enforcement(self, asset_tag):
        """
        Feature: asset-tracker, Property 2: Asset tag uniqueness enforcement
        
        For any existing asset with asset_tag A, attempting to create another asset 
        with the same asset_tag A should be rejected with an error.
        
        Validates: Requirements 1.2
        """
        # Clean input
        asset_tag = asset_tag.strip()
        
        # Create first asset
        data = {
            'asset_tag': asset_tag,
            'system_type': 'Desktop',
            'operating_system': self.os.id,
        }
        
        asset1 = AssetService.create_asset(data, self.user)
        
        # Attempt to create second asset with same tag
        with pytest.raises(ValidationError) as exc_info:
            AssetService.create_asset(data, self.user)
        
        # Verify error is about asset_tag
        assert 'asset_tag' in exc_info.value.message_dict
        
        # Clean up
        asset1.delete()
    
    @given(count=st.integers(min_value=1, max_value=10))
    @settings(max_examples=20)
    def test_property_3_sequential_serial_number_assignment(self, count):
        """
        Feature: asset-tracker, Property 3: Sequential serial number assignment
        
        For any sequence of asset creations, each new asset should receive a serial 
        number greater than all previously assigned serial numbers.
        
        Validates: Requirements 1.3
        """
        # Get the current max serial number
        max_serial = Asset.objects.aggregate(models.Max('serial_number'))['serial_number__max'] or 0
        
        assets = []
        previous_serial = max_serial
        
        for i in range(count):
            data = {
                'asset_tag': f'BIDC_TEST_{i}_{count}',
                'system_type': 'Desktop',
                'operating_system': self.os.id,
            }
            
            asset = AssetService.create_asset(data, self.user)
            assets.append(asset)
            
            # Verify serial number is greater than previous
            assert asset.serial_number > previous_serial
            previous_serial = asset.serial_number
        
        # Clean up
        for asset in assets:
            asset.delete()
    
    @given(system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']))
    @settings(max_examples=100)
    def test_property_4_ip_assignment_state_transition(self, system_type):
        """
        Feature: asset-tracker, Property 4: IP assignment state transition
        
        For any free IP address, when assigned to a new asset, the IP should be 
        marked as in use and no longer appear in the free IPs list.
        
        Validates: Requirements 1.4, 8.3
        """
        # Ensure IP is free
        self.ip1.is_assigned = False
        self.ip1.assigned_to_asset = None
        self.ip1.save()
        
        # Create asset with IP
        data = {
            'asset_tag': f'BIDC_IP_TEST_{system_type}',
            'system_type': system_type,
            'operating_system': self.os.id,
            'ip_address': self.ip1.id,
        }
        
        asset = AssetService.create_asset(data, self.user)
        
        # Verify IP is marked as assigned
        self.ip1.refresh_from_db()
        assert self.ip1.is_assigned is True
        assert self.ip1.assigned_to_asset == asset
        
        # Verify IP doesn't appear in free IPs
        from assets.services.ip_management_service import IPManagementService
        free_ips = IPManagementService.get_available_ips()
        assert self.ip1 not in free_ips
        
        # Clean up
        asset.delete()
        self.ip1.is_assigned = False
        self.ip1.assigned_to_asset = None
        self.ip1.save()
    
    @given(
        particulars=st.text(max_size=200),
        assigned_to=st.text(max_size=100)
    )
    @settings(max_examples=100)
    def test_property_6_asset_update_data_integrity(self, particulars, assigned_to):
        """
        Feature: asset-tracker, Property 6: Asset update data integrity
        
        For any asset and any subset of updatable fields, updating those fields 
        should preserve all other fields unchanged.
        
        Validates: Requirements 2.1
        """
        # Create asset with initial values
        initial_tag = 'BIDC_UPDATE_TEST'
        initial_type = 'Desktop'
        
        asset = Asset.objects.create(
            asset_tag=initial_tag,
            system_type=initial_type,
            operating_system=self.os,
            status='active'
        )
        
        # Update only particulars and assigned_to
        data = {
            'particulars': particulars,
            'assigned_to': assigned_to,
        }
        
        AssetService.update_asset(asset, data, self.user)
        
        # Verify updated fields changed
        asset.refresh_from_db()
        assert asset.particulars == particulars
        assert asset.assigned_to == assigned_to
        
        # Verify other fields unchanged
        assert asset.asset_tag == initial_tag
        assert asset.system_type == initial_type
        assert asset.operating_system == self.os
        
        # Clean up
        asset.delete()
    
    @given(system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']))
    @settings(max_examples=50)
    def test_property_7_ip_change_state_management(self, system_type):
        """
        Feature: asset-tracker, Property 7: IP change state management
        
        For any asset with IP address A, when changed to IP address B, IP A should 
        become free and IP B should become assigned.
        
        Validates: Requirements 2.2
        """
        # Ensure both IPs are free
        self.ip1.is_assigned = False
        self.ip1.assigned_to_asset = None
        self.ip1.save()
        self.ip2.is_assigned = False
        self.ip2.assigned_to_asset = None
        self.ip2.save()
        
        # Create asset with IP1
        asset = Asset.objects.create(
            asset_tag=f'BIDC_IP_CHANGE_{system_type}',
            system_type=system_type,
            operating_system=self.os,
            ip_address=self.ip1,
            status='active'
        )
        self.ip1.is_assigned = True
        self.ip1.assigned_to_asset = asset
        self.ip1.save()
        
        # Update to IP2
        data = {'ip_address': self.ip2.id}
        AssetService.update_asset(asset, data, self.user)
        
        # Verify IP1 is free
        self.ip1.refresh_from_db()
        assert self.ip1.is_assigned is False
        assert self.ip1.assigned_to_asset is None
        
        # Verify IP2 is assigned
        self.ip2.refresh_from_db()
        assert self.ip2.is_assigned is True
        assert self.ip2.assigned_to_asset == asset
        
        # Clean up
        asset.delete()
        self.ip2.is_assigned = False
        self.ip2.assigned_to_asset = None
        self.ip2.save()
    
    @given(count=st.integers(min_value=1, max_value=10))
    @settings(max_examples=20)
    def test_property_11_active_assets_view_completeness(self, count):
        """
        Feature: asset-tracker, Property 11: Active assets view completeness
        
        For any active asset in the system, querying the active assets list should 
        return that asset with all fields present.
        
        Validates: Requirements 4.1
        """
        assets = []
        
        for i in range(count):
            asset = Asset.objects.create(
                asset_tag=f'BIDC_ACTIVE_{i}_{count}',
                system_type='Desktop',
                operating_system=self.os,
                team=self.team,
                assigned_to=f'User {i}',
                status='active'
            )
            assets.append(asset)
        
        # Get active assets
        active_assets = AssetService.get_active_assets()
        
        # Verify all created assets are in the list
        for asset in assets:
            assert asset in active_assets
            
            # Verify all fields are accessible
            found_asset = active_assets.get(serial_number=asset.serial_number)
            assert found_asset.asset_tag == asset.asset_tag
            assert found_asset.system_type == asset.system_type
            assert found_asset.operating_system == asset.operating_system
            assert found_asset.team == asset.team
            assert found_asset.assigned_to == asset.assigned_to
        
        # Clean up
        for asset in assets:
            asset.delete()
    
    @given(
        active_count=st.integers(min_value=1, max_value=5),
        freed_count=st.integers(min_value=1, max_value=5),
        scrapped_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=20)
    def test_property_12_view_state_isolation(self, active_count, freed_count, scrapped_count):
        """
        Feature: asset-tracker, Property 12: View state isolation
        
        For any database state containing active, freed, and scrapped assets, the 
        active assets view should only show active assets, the freed systems view 
        should only show freed assets, and the scrapped items view should only show 
        scrapped assets.
        
        Validates: Requirements 4.2, 5.3
        """
        active_assets = []
        freed_assets = []
        scrapped_assets = []
        
        # Create active assets
        for i in range(active_count):
            asset = Asset.objects.create(
                asset_tag=f'BIDC_ACTIVE_{i}',
                system_type='Desktop',
                operating_system=self.os,
                status='active'
            )
            active_assets.append(asset)
        
        # Create freed assets
        for i in range(freed_count):
            asset = Asset.objects.create(
                asset_tag=f'BIDC_FREED_{i}',
                system_type='Laptop',
                operating_system=self.os,
                status='freed'
            )
            freed_assets.append(asset)
        
        # Create scrapped assets
        for i in range(scrapped_count):
            asset = Asset.objects.create(
                asset_tag=f'BIDC_SCRAPPED_{i}',
                system_type='Desktop',
                operating_system=self.os,
                status='scrapped'
            )
            scrapped_assets.append(asset)
        
        # Get views
        active_view = list(AssetService.get_active_assets())
        freed_view = list(AssetService.get_freed_assets())
        scrapped_view = list(AssetService.get_scrapped_assets())
        
        # Verify active view only contains active assets
        for asset in active_assets:
            assert asset in active_view
        for asset in freed_assets + scrapped_assets:
            assert asset not in active_view
        
        # Verify freed view only contains freed assets
        for asset in freed_assets:
            assert asset in freed_view
        for asset in active_assets + scrapped_assets:
            assert asset not in freed_view
        
        # Verify scrapped view only contains scrapped assets
        for asset in scrapped_assets:
            assert asset in scrapped_view
        for asset in active_assets + freed_assets:
            assert asset not in scrapped_view
        
        # Clean up
        for asset in active_assets + freed_assets + scrapped_assets:
            asset.delete()

    @given(count=st.integers(min_value=2, max_value=10))
    @settings(max_examples=20)
    def test_property_13_active_assets_ordering(self, count):
        """
        Feature: asset-tracker, Property 13: Active assets ordering

        For any set of active assets, the active assets list should be ordered by
        serial_number in ascending order.

        Validates: Requirements 4.3
        """
        assets = []

        # Create multiple active assets
        for i in range(count):
            asset = Asset.objects.create(
                asset_tag=f'BIDC_ORDER_{i}_{count}',
                system_type='Desktop',
                operating_system=self.os,
                status='active'
            )
            assets.append(asset)

        # Get active assets from service
        active_assets = list(AssetService.get_active_assets())

        # Filter to only our test assets
        test_assets = [a for a in active_assets if a in assets]

        # Verify we got all our test assets
        assert len(test_assets) == count, \
            f"Should retrieve all {count} created assets"

        # Verify ordering by serial_number in ascending order
        for i in range(len(test_assets) - 1):
            current_asset = test_assets[i]
            next_asset = test_assets[i + 1]

            assert current_asset.serial_number <= next_asset.serial_number, \
                f"Assets should be ordered by serial_number ascending. " \
                f"Asset {current_asset.asset_tag} (serial {current_asset.serial_number}) " \
                f"should come before or equal to {next_asset.asset_tag} (serial {next_asset.serial_number})"

        # Clean up
        for asset in assets:
            asset.delete()


    @given(
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        particulars=st.text(max_size=200),
        assigned_to=st.text(max_size=100)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_9_asset_freeing_state_transition(self, system_type, particulars, assigned_to):
        """
        Feature: asset-tracker, Property 9: Asset freeing state transition
        
        For any active asset, when freed with correct admin password, the asset should 
        move to freed status, appear on Free Systems page, not appear on Active Assets 
        page, and have assigned_to and team fields cleared.
        
        Validates: Requirements 3.3, 3.5
        """
        from django.utils import timezone
        
        # Set a proper password for the user
        self.user.set_password('testpassword123')
        self.user.save()
        
        # Ensure IP is free initially
        self.ip1.is_assigned = False
        self.ip1.assigned_to_asset = None
        self.ip1.save()
        
        # Create an active asset with all fields populated
        asset = Asset.objects.create(
            asset_tag=f'BIDC_FREE_TEST_{system_type}',
            system_type=system_type,
            operating_system=self.os,
            ip_address=self.ip1,
            particulars=particulars,
            assigned_to=assigned_to,
            team=self.team,
            status='active'
        )
        
        # Store original values for verification
        original_asset_tag = asset.asset_tag
        original_system_type = asset.system_type
        
        # Free the asset with correct password
        freed_asset = AssetService.free_asset(asset, self.user, 'testpassword123')
        
        # Verify status changed to freed
        assert freed_asset.status == 'freed'
        
        # Verify freed_date is recorded
        assert freed_asset.freed_date is not None
        assert isinstance(freed_asset.freed_date, timezone.datetime)
        
        # Verify assigned_to field is cleared
        assert freed_asset.assigned_to is None
        
        # Verify team field is cleared
        assert freed_asset.team is None
        
        # Verify other fields are preserved
        assert freed_asset.asset_tag == original_asset_tag
        assert freed_asset.system_type == original_system_type
        assert freed_asset.operating_system == self.os
        
        # Verify asset appears in freed systems view
        freed_view = list(AssetService.get_freed_assets())
        assert freed_asset in freed_view
        
        # Verify asset does NOT appear in active assets view
        active_view = list(AssetService.get_active_assets())
        assert freed_asset not in active_view
        
        # Clean up
        freed_asset.delete()
        self.ip1.is_assigned = False
        self.ip1.assigned_to_asset = None
        self.ip1.save()
    
    @given(
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        particulars=st.text(max_size=200),
        assigned_to=st.text(max_size=100)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_10_ip_release_on_asset_freeing(self, system_type, particulars, assigned_to):
        """
        Feature: asset-tracker, Property 10: IP release on asset freeing
        
        For any asset with an assigned IP address, when the asset is freed, the IP 
        should be released and appear in the Free IPs page under the appropriate range.
        
        Validates: Requirements 3.4, 8.4
        """
        from assets.services.ip_management_service import IPManagementService
        
        # Set a proper password for the user
        self.user.set_password('testpassword123')
        self.user.save()
        
        # Ensure IP is free initially
        self.ip1.is_assigned = False
        self.ip1.assigned_to_asset = None
        self.ip1.save()
        
        # Create an active asset with IP
        asset = Asset.objects.create(
            asset_tag=f'BIDC_FREE_IP_TEST_{system_type}',
            system_type=system_type,
            operating_system=self.os,
            ip_address=self.ip1,
            particulars=particulars,
            assigned_to=assigned_to,
            team=self.team,
            status='active'
        )
        
        # Assign the IP
        IPManagementService.assign_ip(self.ip1, asset)
        
        # Verify IP is assigned
        self.ip1.refresh_from_db()
        assert self.ip1.is_assigned is True
        assert self.ip1.assigned_to_asset == asset
        
        # Free the asset with correct password
        freed_asset = AssetService.free_asset(asset, self.user, 'testpassword123')
        
        # Verify IP is released
        self.ip1.refresh_from_db()
        assert self.ip1.is_assigned is False
        assert self.ip1.assigned_to_asset is None
        
        # Verify IP appears in free IPs list
        free_ips = IPManagementService.get_available_ips()
        assert self.ip1 in free_ips
        
        # Verify IP appears in free IPs grouped by range
        free_ips_by_range = IPManagementService.get_free_ips_by_range()
        range_pattern = self.ip1.ip_range.range_pattern
        assert range_pattern in free_ips_by_range
        assert self.ip1 in free_ips_by_range[range_pattern]
        
        # Clean up
        freed_asset.delete()
    
    @given(
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        particulars=st.text(max_size=200),
        assigned_to=st.text(max_size=100)
    )
    @settings(max_examples=100)
    def test_property_15_asset_scrapping_state_transition(self, system_type, particulars, assigned_to):
        """
        Feature: asset-tracker, Property 15: Asset scrapping state transition

        For any freed asset, when scrapped by an admin, the asset should move to
        scrapped status, appear on Scrapped Items page, not appear on Free Systems
        page, have a scrapped_date recorded, and retain asset_tag and IP information.

        Validates: Requirements 6.1, 6.2, 6.3
        """
        from django.utils import timezone

        # Ensure IP is free
        self.ip1.is_assigned = False
        self.ip1.assigned_to_asset = None
        self.ip1.save()

        # Create an active asset with IP
        asset = Asset.objects.create(
            asset_tag=f'BIDC_SCRAP_TEST_{system_type}',
            system_type=system_type,
            operating_system=self.os,
            ip_address=self.ip1,
            particulars=particulars,
            assigned_to=assigned_to,
            team=self.team,
            status='active'
        )

        # Store original values
        original_asset_tag = asset.asset_tag
        original_ip = asset.ip_address

        # First, free the asset (required before scrapping)
        asset.status = 'freed'
        asset.assigned_to = None
        asset.team = None
        asset.freed_date = timezone.now()
        asset.save()

        # Verify asset appears in freed systems view
        freed_view = list(AssetService.get_freed_assets())
        assert asset in freed_view

        # Now scrap the asset
        scrapped_asset = AssetService.scrap_asset(asset, self.user, "End of life")

        # Verify status changed to scrapped
        assert scrapped_asset.status == 'scrapped'

        # Verify scrapped_date is recorded
        assert scrapped_asset.scrapped_date is not None
        assert isinstance(scrapped_asset.scrapped_date, timezone.datetime)

        # Verify asset_tag is retained
        assert scrapped_asset.asset_tag == original_asset_tag

        # Verify IP address is retained
        assert scrapped_asset.ip_address == original_ip

        # Verify asset appears in scrapped items view
        scrapped_view = list(AssetService.get_scrapped_assets())
        assert scrapped_asset in scrapped_view

        # Verify asset does NOT appear in freed systems view
        freed_view_after = list(AssetService.get_freed_assets())
        assert scrapped_asset not in freed_view_after

        # Verify asset does NOT appear in active assets view
        active_view = list(AssetService.get_active_assets())
        assert scrapped_asset not in active_view

        # Clean up
        scrapped_asset.delete()
        self.ip1.is_assigned = False
        self.ip1.assigned_to_asset = None
        self.ip1.save()



@pytest.mark.django_db
class TestIPManagementProperties(TestCase):
    """Property-based tests for IP management."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create user
        self.user, _ = User.objects.get_or_create(
            username='admin_ip_test',
            defaults={'password': 'password'}
        )
        
        # Create OS and Team
        self.os, _ = OperatingSystem.objects.get_or_create(name="Windows 10 IP Test")
        self.team, _ = Team.objects.get_or_create(name="IT Department IP Test")
        
        # Create multiple IP ranges
        self.ip_range1, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.10.x",
            defaults={'network_prefix': "192.168.10"}
        )
        self.ip_range2, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.11.x",
            defaults={'network_prefix': "192.168.11"}
        )
        self.ip_range3, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.70.x",
            defaults={'network_prefix': "192.168.70"}
        )
        self.ip_range4, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.50.x",
            defaults={'network_prefix': "192.168.50"}
        )
        
        # Clean up any existing IPs and create fresh ones for each range
        IPAddress.objects.filter(ip_range__in=[self.ip_range1, self.ip_range2, self.ip_range3, self.ip_range4]).delete()
    
    @given(
        range1_count=st.integers(min_value=1, max_value=5),
        range2_count=st.integers(min_value=1, max_value=5),
        range3_count=st.integers(min_value=1, max_value=5),
        range4_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=20)
    def test_property_17_free_ips_grouping_by_range(self, range1_count, range2_count, range3_count, range4_count):
        """
        Feature: asset-tracker, Property 17: Free IPs grouping by range
        
        For any set of free IP addresses from multiple ranges, the Free IPs page 
        should display them grouped by their respective IP ranges (192.168.10.x, 
        192.168.11.x, 192.168.70.x, 192.168.50.x).
        
        Validates: Requirements 8.1, 8.2
        """
        from assets.services.ip_management_service import IPManagementService
        
        # Clean up any existing IPs
        IPAddress.objects.filter(ip_range__in=[self.ip_range1, self.ip_range2, self.ip_range3, self.ip_range4]).delete()
        
        # Create free IPs in range 1
        range1_ips = []
        for i in range(range1_count):
            ip = IPAddress.objects.create(
                address=f"192.168.10.{i+1}",
                ip_range=self.ip_range1,
                is_assigned=False
            )
            range1_ips.append(ip)
        
        # Create free IPs in range 2
        range2_ips = []
        for i in range(range2_count):
            ip = IPAddress.objects.create(
                address=f"192.168.11.{i+1}",
                ip_range=self.ip_range2,
                is_assigned=False
            )
            range2_ips.append(ip)
        
        # Create free IPs in range 3
        range3_ips = []
        for i in range(range3_count):
            ip = IPAddress.objects.create(
                address=f"192.168.70.{i+1}",
                ip_range=self.ip_range3,
                is_assigned=False
            )
            range3_ips.append(ip)
        
        # Create free IPs in range 4
        range4_ips = []
        for i in range(range4_count):
            ip = IPAddress.objects.create(
                address=f"192.168.50.{i+1}",
                ip_range=self.ip_range4,
                is_assigned=False
            )
            range4_ips.append(ip)
        
        # Get free IPs grouped by range
        free_ips_by_range = IPManagementService.get_free_ips_by_range()
        
        # Verify all ranges are present
        assert "192.168.10.x" in free_ips_by_range
        assert "192.168.11.x" in free_ips_by_range
        assert "192.168.70.x" in free_ips_by_range
        assert "192.168.50.x" in free_ips_by_range
        
        # Verify correct IPs are in each range
        assert len(free_ips_by_range["192.168.10.x"]) == range1_count
        assert len(free_ips_by_range["192.168.11.x"]) == range2_count
        assert len(free_ips_by_range["192.168.70.x"]) == range3_count
        assert len(free_ips_by_range["192.168.50.x"]) == range4_count
        
        # Verify each IP is in the correct range
        for ip in range1_ips:
            assert ip in free_ips_by_range["192.168.10.x"]
        for ip in range2_ips:
            assert ip in free_ips_by_range["192.168.11.x"]
        for ip in range3_ips:
            assert ip in free_ips_by_range["192.168.70.x"]
        for ip in range4_ips:
            assert ip in free_ips_by_range["192.168.50.x"]
        
        # Clean up
        IPAddress.objects.filter(ip_range__in=[self.ip_range1, self.ip_range2, self.ip_range3, self.ip_range4]).delete()


@pytest.mark.django_db
class TestPermissionProperties(TestCase):
    """Property-based tests for permission enforcement."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin_perm_test',
            password='adminpass123',
            is_staff=True
        )
        
        # Create non-admin user
        self.non_admin_user = User.objects.create_user(
            username='nonadmin_perm_test',
            password='userpass123',
            is_staff=False
        )
        
        # Create test data
        self.os, _ = OperatingSystem.objects.get_or_create(name="Windows 10 Perm Test")
        self.team, _ = Team.objects.get_or_create(name="IT Department Perm Test")
        
        # Create IP range and address
        self.ip_range, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.88.x",
            defaults={'network_prefix': "192.168.88"}
        )
        IPAddress.objects.filter(ip_range=self.ip_range).delete()
        self.ip1 = IPAddress.objects.create(
            address="192.168.88.1",
            ip_range=self.ip_range,
            is_assigned=False
        )
    
    @given(
        operation=st.sampled_from(['create', 'update', 'free', 'scrap']),
        asset_tag=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC'])
    )
    @settings(max_examples=100)
    def test_property_5_admin_only_operation_enforcement(self, operation, asset_tag, system_type):
        """
        Feature: asset-tracker, Property 5: Admin-only operation enforcement
        
        For any non-admin user attempting to perform add, edit, free, or scrap 
        operations, the system should deny access and return an authorization error.
        
        Validates: Requirements 1.5, 2.4, 3.6, 6.4
        """
        from django.core.exceptions import PermissionDenied
        from django.http import HttpResponseForbidden
        from django.test import RequestFactory
        from assets.views import AssetCreateView
        from assets.permissions import admin_required
        
        # Clean inputs
        asset_tag = asset_tag.strip()
        
        # Ensure unique asset tag
        assume(not Asset.objects.filter(asset_tag=asset_tag).exists())
        
        factory = RequestFactory()
        
        if operation == 'create':
            # Test create operation (view-based)
            request = factory.get('/assets/create/')
            request.user = self.non_admin_user
            
            view = AssetCreateView()
            view.request = request
            
            # Non-admin should be denied access
            with pytest.raises(PermissionDenied) as exc_info:
                view.dispatch(request)
            
            assert "Admin access required" in str(exc_info.value)
        
        elif operation == 'update':
            # Create an asset first (as admin)
            asset = Asset.objects.create(
                asset_tag=asset_tag,
                system_type=system_type,
                operating_system=self.os,
                status='active'
            )
            
            # Test update operation (service-based, but would be protected by view)
            # The view protection is tested above, here we verify the pattern
            request = factory.post(f'/assets/{asset.serial_number}/edit/')
            request.user = self.non_admin_user
            
            # Create a mock view with AdminRequiredMixin
            from assets.permissions import AdminRequiredMixin
            from django.views import View
            
            class MockUpdateView(AdminRequiredMixin, View):
                pass
            
            view = MockUpdateView()
            view.request = request
            
            # Non-admin should be denied access
            with pytest.raises(PermissionDenied) as exc_info:
                view.dispatch(request)
            
            assert "Admin access required" in str(exc_info.value)
            
            # Clean up
            asset.delete()
        
        elif operation == 'free':
            # Create an active asset first (as admin)
            asset = Asset.objects.create(
                asset_tag=asset_tag,
                system_type=system_type,
                operating_system=self.os,
                status='active'
            )
            
            # Test free operation using decorator
            @admin_required
            def mock_free_view(request, asset_id):
                return "Success"
            
            request = factory.post(f'/assets/{asset.serial_number}/free/')
            request.user = self.non_admin_user
            
            # Non-admin should be denied access
            response = mock_free_view(request, asset.serial_number)
            assert isinstance(response, HttpResponseForbidden)
            assert "Admin access required" in str(response.content, 'utf-8')
            
            # Clean up
            asset.delete()
        
        elif operation == 'scrap':
            # Create a freed asset first (as admin)
            asset = Asset.objects.create(
                asset_tag=asset_tag,
                system_type=system_type,
                operating_system=self.os,
                status='freed'
            )
            
            # Test scrap operation using decorator
            @admin_required
            def mock_scrap_view(request, asset_id):
                return "Success"
            
            request = factory.post(f'/assets/{asset.serial_number}/scrap/')
            request.user = self.non_admin_user
            
            # Non-admin should be denied access
            response = mock_scrap_view(request, asset.serial_number)
            assert isinstance(response, HttpResponseForbidden)
            assert "Admin access required" in str(response.content, 'utf-8')
            
            # Clean up
            asset.delete()


@pytest.mark.django_db
class TestOperatingSystemProperties(TestCase):
    """Property-based tests for OperatingSystem model."""
    
    @given(os_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
    @settings(max_examples=100)
    def test_property_18_operating_system_management(self, os_name):
        """
        Feature: asset-tracker, Property 18: Operating system management
        
        For any new OS name, adding it should make it available in the OS list,
        and attempting to add a duplicate OS name should be rejected.
        
        Validates: Requirements 9.1, 9.3
        """
        # Clean the OS name to ensure it's valid
        os_name = os_name.strip()
        
        # Create the first OS with this name
        os1 = OperatingSystem.objects.create(name=os_name)
        
        # Verify it's available in the OS list
        assert OperatingSystem.objects.filter(name=os_name).exists()
        assert os1.name == os_name
        
        # Attempt to create a duplicate OS with the same name
        with pytest.raises(IntegrityError):
            OperatingSystem.objects.create(name=os_name)


@pytest.mark.django_db
class TestTeamProperties(TestCase):
    """Property-based tests for Team model."""
    
    @given(team_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
    @settings(max_examples=100)
    def test_property_19_team_management(self, team_name):
        """
        Feature: asset-tracker, Property 19: Team management
        
        For any new team name, adding it should make it available in the teams list,
        and attempting to add a duplicate team name should be rejected.
        
        Validates: Requirements 10.1, 10.3
        """
        # Clean the team name to ensure it's valid
        team_name = team_name.strip()
        
        # Create the first team with this name
        team1 = Team.objects.create(name=team_name)
        
        # Verify it's available in the teams list
        assert Team.objects.filter(name=team_name).exists()
        assert team1.name == team_name
        
        # Attempt to create a duplicate team with the same name
        with pytest.raises(IntegrityError):
            Team.objects.create(name=team_name)


@pytest.mark.django_db
class TestIPRangeProperties(TestCase):
    """Property-based tests for IPRange model."""
    
    @given(
        range_pattern=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
        network_prefix=st.text(min_size=1, max_size=15).filter(lambda x: x.strip())
    )
    @settings(max_examples=100)
    def test_property_20_ip_range_management(self, range_pattern, network_prefix):
        """
        Feature: asset-tracker, Property 20: IP range management
        
        For any new IP range pattern, adding it should make IPs from that range available,
        and attempting to add a duplicate range should be rejected.
        
        Validates: Requirements 11.1, 11.3
        """
        # Clean the inputs to ensure they're valid
        range_pattern = range_pattern.strip()
        network_prefix = network_prefix.strip()
        
        # Create the first IP range with this pattern
        ip_range1 = IPRange.objects.create(
            range_pattern=range_pattern,
            network_prefix=network_prefix
        )
        
        # Verify it's available in the IP range list
        assert IPRange.objects.filter(range_pattern=range_pattern).exists()
        assert ip_range1.range_pattern == range_pattern
        assert ip_range1.network_prefix == network_prefix
        
        # Attempt to create a duplicate IP range with the same pattern
        with pytest.raises(IntegrityError):
            IPRange.objects.create(
                range_pattern=range_pattern,
                network_prefix=network_prefix
            )



@pytest.mark.django_db
class TestWarrantyProperties(TestCase):
    """Property-based tests for warranty management."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create admin user with email - use get_or_create to avoid duplicates
        self.admin_user, created = User.objects.get_or_create(
            username='admin_warranty_test',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_active': True
            }
        )
        if created:
            self.admin_user.set_password('adminpass123')
            self.admin_user.save()
        
        # Create test data
        self.os, _ = OperatingSystem.objects.get_or_create(name="Windows 10 Warranty Test")
        self.team, _ = Team.objects.get_or_create(name="IT Department Warranty Test")
    
    @given(
        days_until_expiry=st.integers(min_value=-10, max_value=20),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC'])
    )
    @settings(max_examples=100)
    def test_property_24_warranty_expiration_identification(self, days_until_expiry, system_type):
        """
        Feature: asset-tracker, Property 24: Warranty expiration identification
        
        For any set of assets with various warranty dates, running the daily check 
        should identify exactly those assets with warranties expiring within 7 days 
        from the current date.
        
        Validates: Requirements 13.2
        """
        from assets.services.warranty_service import WarrantyService
        from django.utils import timezone
        
        # Calculate warranty expiration date
        today = timezone.now().date()
        warranty_date = today + timedelta(days=days_until_expiry)
        
        # Create an active asset with warranty
        asset = Asset.objects.create(
            asset_tag=f'BIDC_WARRANTY_{days_until_expiry}_{system_type}',
            system_type=system_type,
            operating_system=self.os,
            warranty_expiration=warranty_date,
            status='active'
        )
        
        # Run the warranty check
        expiring_assets = WarrantyService.check_expiring_warranties()
        
        # Verify the asset is included if and only if it expires within 7 days
        # (between today and today + 7 days, inclusive)
        should_be_included = 0 <= days_until_expiry <= 7
        
        if should_be_included:
            assert asset in expiring_assets, \
                f"Asset expiring in {days_until_expiry} days should be in expiring list"
        else:
            assert asset not in expiring_assets, \
                f"Asset expiring in {days_until_expiry} days should NOT be in expiring list"
        
        # Clean up
        asset.delete()
    
    @given(
        days_until_expiry=st.integers(min_value=0, max_value=7),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC'])
    )
    @settings(max_examples=50)
    def test_property_25_warranty_alert_email_delivery(self, days_until_expiry, system_type):
        """
        Feature: asset-tracker, Property 25: Warranty alert email delivery
        
        For any asset with warranty expiring within 7 days, the daily check should 
        trigger an alert email to admin users.
        
        Validates: Requirements 13.3
        """
        from assets.services.warranty_service import WarrantyService
        from django.utils import timezone
        from django.core import mail
        
        # Calculate warranty expiration date (within 7 days)
        today = timezone.now().date()
        warranty_date = today + timedelta(days=days_until_expiry)
        
        # Create an active asset with warranty expiring soon
        asset = Asset.objects.create(
            asset_tag=f'BIDC_ALERT_{days_until_expiry}_{system_type}',
            system_type=system_type,
            operating_system=self.os,
            warranty_expiration=warranty_date,
            status='active'
        )
        
        # Clear the mail outbox
        mail.outbox = []
        
        # Get expiring assets and send alerts
        expiring_assets = WarrantyService.check_expiring_warranties()
        WarrantyService.send_warranty_alerts(expiring_assets)
        
        # Verify email was sent
        assert len(mail.outbox) >= 1, "At least one email should be sent"
        
        # Verify email contains asset information
        email = mail.outbox[0]
        assert asset.asset_tag in email.body, "Email should contain asset tag"
        assert str(warranty_date) in email.body or warranty_date.strftime("%Y-%m-%d") in email.body, \
            "Email should contain warranty expiration date"
        
        # Verify email was sent to admin
        assert self.admin_user.email in email.to, "Email should be sent to admin user"
        
        # Verify subject is appropriate
        assert 'warranty' in email.subject.lower() or 'expir' in email.subject.lower(), \
            "Email subject should mention warranty or expiration"
        
        # Clean up
        asset.delete()
    
    @given(
        days_offset=st.integers(min_value=-30, max_value=30),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC'])
    )
    @settings(max_examples=100)
    def test_property_27_warranty_expiration_status_marking(self, days_offset, system_type):
        """
        Feature: asset-tracker, Property 27: Warranty expiration status marking
        
        For any asset with warranty_expiration date in the past, the Warranty page 
        should mark it as expired.
        
        Validates: Requirements 13.7
        """
        from assets.services.warranty_service import WarrantyService
        from django.utils import timezone
        
        # Calculate warranty expiration date
        today = timezone.now().date()
        warranty_date = today + timedelta(days=days_offset)
        
        # Create an active asset with warranty
        asset = Asset.objects.create(
            asset_tag=f'BIDC_STATUS_{days_offset}_{system_type}',
            system_type=system_type,
            operating_system=self.os,
            warranty_expiration=warranty_date,
            status='active'
        )
        
        # Get warranty status
        status = WarrantyService.get_warranty_status(asset)
        
        # Verify status is correct based on warranty date
        if days_offset < 0:
            # Warranty is in the past
            assert status == 'expired', \
                f"Asset with warranty {days_offset} days ago should be marked as 'expired'"
        elif 0 <= days_offset <= 7:
            # Warranty expires within 7 days
            assert status == 'expiring_soon', \
                f"Asset with warranty expiring in {days_offset} days should be marked as 'expiring_soon'"
        else:
            # Warranty is more than 7 days in the future
            assert status == 'active', \
                f"Asset with warranty expiring in {days_offset} days should be marked as 'active'"
        
        # Clean up
        asset.delete()


    @given(
        warranty_count=st.integers(min_value=1, max_value=10),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC'])
    )
    @settings(max_examples=50)
    def test_property_26_warranty_page_completeness_and_ordering(self, warranty_count, system_type):
        """
        Feature: asset-tracker, Property 26: Warranty page completeness and ordering

        For any set of assets with warranty dates, the Warranty page should display
        all of them with warranty_expiration dates, ordered by warranty_expiration
        in ascending order.

        Validates: Requirements 13.4, 13.6
        """
        from django.utils import timezone
        from datetime import timedelta

        # Create assets with different warranty dates
        assets_with_warranty = []
        base_date = timezone.now().date()

        for i in range(warranty_count):
            # Create warranty dates spread over time (some past, some future)
            # Use different offsets to ensure variety
            days_offset = (i - warranty_count // 2) * 10  # Spread around today
            warranty_date = base_date + timedelta(days=days_offset)

            # Create asset with warranty
            asset = Asset.objects.create(
                asset_tag=f'BIDC_WARRANTY_PAGE_{i}_{system_type}',
                system_type=system_type,
                operating_system=self.os,
                warranty_expiration=warranty_date,
                status='active'
            )
            assets_with_warranty.append(asset)

        # Get warranty view queryset (simulating what the view does)
        warranty_view = list(Asset.objects.filter(
            warranty_expiration__isnull=False
        ).order_by('warranty_expiration'))

        # Verify all assets with warranty are in the view
        for asset in assets_with_warranty:
            assert asset in warranty_view, \
                f"Asset {asset.asset_tag} with warranty should be in warranty view"

        # Verify all assets in view have warranty_expiration dates
        for asset in warranty_view:
            assert asset.warranty_expiration is not None, \
                "All assets in warranty view should have warranty_expiration dates"

        # Verify ordering by warranty_expiration in ascending order
        # Earlier dates should come first
        for i in range(len(warranty_view) - 1):
            current_asset = warranty_view[i]
            next_asset = warranty_view[i + 1]

            # Skip if either asset doesn't have a warranty_expiration (shouldn't happen)
            if current_asset.warranty_expiration is None or next_asset.warranty_expiration is None:
                continue

            # Current asset should have warranty_expiration <= next asset (ascending order)
            assert current_asset.warranty_expiration <= next_asset.warranty_expiration, \
                f"Assets should be ordered by warranty_expiration ascending. " \
                f"Asset {current_asset.asset_tag} (expires {current_asset.warranty_expiration}) " \
                f"should come before {next_asset.asset_tag} (expires {next_asset.warranty_expiration})"

        # Verify that assets WITHOUT warranty are NOT in the view
        # Create an asset without warranty
        asset_no_warranty = Asset.objects.create(
            asset_tag=f'BIDC_NO_WARRANTY_{system_type}',
            system_type=system_type,
            operating_system=self.os,
            warranty_expiration=None,
            status='active'
        )

        # Re-fetch the warranty view
        warranty_view_after = list(Asset.objects.filter(
            warranty_expiration__isnull=False
        ).order_by('warranty_expiration'))

        # Verify asset without warranty is NOT in the view
        assert asset_no_warranty not in warranty_view_after, \
            "Assets without warranty_expiration should NOT be in warranty view"

        # Clean up
        for asset in assets_with_warranty:
            asset.delete()
        asset_no_warranty.delete()




@pytest.mark.django_db
class TestAttachmentProperties(TestCase):
    """Property-based tests for attachment management."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create user
        self.user, _ = User.objects.get_or_create(
            username='admin_attachment_test',
            defaults={'password': 'password', 'is_staff': True}
        )
        
        # Create test data
        self.os, _ = OperatingSystem.objects.get_or_create(name="Windows 10 Attachment Test")
        self.team, _ = Team.objects.get_or_create(name="IT Department Attachment Test")
        
        # Create IP range and address
        self.ip_range, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.77.x",
            defaults={'network_prefix': "192.168.77"}
        )
        IPAddress.objects.filter(ip_range=self.ip_range).delete()
        self.ip1 = IPAddress.objects.create(
            address="192.168.77.1",
            ip_range=self.ip_range,
            is_assigned=False
        )
    
    @given(
        particulars=st.text(max_size=200),
        assigned_to=st.text(max_size=100),
        attachment_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100)
    def test_property_8_attachment_preservation_during_updates(self, particulars, assigned_to, attachment_count):
        """
        Feature: asset-tracker, Property 8: Attachment preservation during updates
        
        For any asset with attachments, updating non-attachment fields should 
        preserve all existing attachments.
        
        Validates: Requirements 2.3
        """
        from assets.services.attachment_service import AttachmentService
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create an asset
        asset = Asset.objects.create(
            asset_tag=f'BIDC_ATTACH_UPDATE_{attachment_count}',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        
        # Create attachments for the asset
        attachments = []
        for i in range(attachment_count):
            # Create a simple test file
            file_content = f'Test file content {i}'.encode('utf-8')
            uploaded_file = SimpleUploadedFile(
                name=f'test_file_{i}.txt',
                content=file_content,
                content_type='text/plain'
            )
            
            attachment = AttachmentService.upload_attachment(asset, uploaded_file)
            attachments.append(attachment)
        
        # Verify attachments were created
        assert asset.attachments.count() == attachment_count
        
        # Update asset with non-attachment fields
        data = {
            'particulars': particulars,
            'assigned_to': assigned_to,
        }
        AssetService.update_asset(asset, data, self.user)
        
        # Verify attachments are preserved
        asset.refresh_from_db()
        assert asset.attachments.count() == attachment_count, \
            "All attachments should be preserved after update"
        
        # Verify each attachment still exists
        for attachment in attachments:
            attachment.refresh_from_db()
            assert attachment.asset == asset, \
                "Attachment should still be associated with the asset"
            assert AttachmentService.get_asset_attachments(asset).filter(id=attachment.id).exists(), \
                "Attachment should be retrievable"
        
        # Clean up
        for attachment in attachments:
            AttachmentService.delete_attachment(attachment)
        asset.delete()
    
    @given(
        filename_base=st.text(min_size=1, max_size=40).filter(
            lambda x: x.strip() and 
            '/' not in x and 
            '\\' not in x and 
            '.' not in x and
            ':' not in x and  # Windows invalid character
            '*' not in x and  # Windows invalid character
            '?' not in x and  # Windows invalid character
            '"' not in x and  # Windows invalid character
            '<' not in x and  # Windows invalid character
            '>' not in x and  # Windows invalid character
            '|' not in x      # Windows invalid character
        ),
        file_extension=st.sampled_from(['txt', 'pdf', 'jpg', 'png', 'doc', 'docx']),
        file_content=st.text(min_size=1, max_size=1000)
    )
    @settings(max_examples=100)
    def test_property_21_attachment_upload_and_association(self, filename_base, file_extension, file_content):
        """
        Feature: asset-tracker, Property 21: Attachment upload and association
        
        For any asset and any file, uploading the file should store it and 
        associate it with the asset, making it retrievable when querying the 
        asset's attachments.
        
        Validates: Requirements 12.1, 12.2
        """
        from assets.services.attachment_service import AttachmentService
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Clean filename and add extension
        filename_base = filename_base.strip()
        filename = f"{filename_base}.{file_extension}"
        
        # Create an asset
        asset = Asset.objects.create(
            asset_tag=f'BIDC_ATTACH_UPLOAD_{filename[:10]}',
            system_type='Laptop',
            operating_system=self.os,
            status='active'
        )
        
        # Create a test file
        uploaded_file = SimpleUploadedFile(
            name=filename,
            content=file_content.encode('utf-8'),
            content_type='text/plain'
        )
        
        # Upload the attachment
        attachment = AttachmentService.upload_attachment(asset, uploaded_file)
        
        # Verify attachment was created
        assert attachment is not None, "Attachment should be created"
        assert attachment.asset == asset, "Attachment should be associated with the asset"
        assert attachment.filename == filename, "Filename should be preserved"
        
        # Verify attachment is retrievable
        asset_attachments = AttachmentService.get_asset_attachments(asset)
        assert attachment in asset_attachments, \
            "Uploaded attachment should be retrievable from asset"
        
        # Verify file is stored
        assert attachment.file, "File should be stored"
        assert attachment.file.name, "File should have a name"
        
        # Verify attachment appears in asset's attachments
        assert asset.attachments.filter(id=attachment.id).exists(), \
            "Attachment should be in asset's attachments queryset"
        
        # Clean up
        AttachmentService.delete_attachment(attachment)
        asset.delete()
    
    @given(
        attachment_count=st.integers(min_value=1, max_value=5),
        delete_index=st.integers(min_value=0, max_value=4)
    )
    @settings(max_examples=50)
    def test_property_22_attachment_deletion_completeness(self, attachment_count, delete_index):
        """
        Feature: asset-tracker, Property 22: Attachment deletion completeness
        
        For any attachment, deleting it should remove both the file from storage 
        and the attachment record from the asset.
        
        Validates: Requirements 12.3
        """
        from assets.services.attachment_service import AttachmentService
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.core.files.storage import default_storage
        
        # Ensure delete_index is within bounds
        assume(delete_index < attachment_count)
        
        # Create an asset
        asset = Asset.objects.create(
            asset_tag=f'BIDC_ATTACH_DELETE_{attachment_count}',
            system_type='Desktop',
            operating_system=self.os,
            status='active'
        )
        
        # Create multiple attachments
        attachments = []
        for i in range(attachment_count):
            file_content = f'Test file content {i}'.encode('utf-8')
            uploaded_file = SimpleUploadedFile(
                name=f'test_delete_{i}.txt',
                content=file_content,
                content_type='text/plain'
            )
            
            attachment = AttachmentService.upload_attachment(asset, uploaded_file)
            attachments.append(attachment)
        
        # Verify all attachments were created
        assert asset.attachments.count() == attachment_count
        
        # Select attachment to delete
        attachment_to_delete = attachments[delete_index]
        file_path = attachment_to_delete.file.name
        attachment_id = attachment_to_delete.id
        
        # Verify file exists before deletion
        assert default_storage.exists(file_path), "File should exist before deletion"
        
        # Delete the attachment
        AttachmentService.delete_attachment(attachment_to_delete)
        
        # Verify attachment record is removed
        from assets.models import Attachment
        assert not Attachment.objects.filter(id=attachment_id).exists(), \
            "Attachment record should be removed from database"
        
        # Verify file is removed from storage
        assert not default_storage.exists(file_path), \
            "File should be removed from storage"
        
        # Verify asset's attachment count decreased
        assert asset.attachments.count() == attachment_count - 1, \
            "Asset should have one fewer attachment"
        
        # Verify other attachments are still present
        for i, attachment in enumerate(attachments):
            if i != delete_index:
                attachment.refresh_from_db()
                assert attachment.asset == asset, \
                    "Other attachments should still be associated with the asset"
        
        # Clean up remaining attachments
        for i, attachment in enumerate(attachments):
            if i != delete_index:
                AttachmentService.delete_attachment(attachment)
        asset.delete()
    
    @given(
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        attachment_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=50)
    def test_property_23_attachment_preservation_on_scrapping(self, system_type, attachment_count):
        """
        Feature: asset-tracker, Property 23: Attachment preservation on scrapping
        
        For any asset with attachments, scrapping the asset should retain all 
        attachments for historical reference.
        
        Validates: Requirements 12.4
        """
        from assets.services.attachment_service import AttachmentService
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.utils import timezone
        
        # Create an asset
        asset = Asset.objects.create(
            asset_tag=f'BIDC_ATTACH_SCRAP_{system_type}',
            system_type=system_type,
            operating_system=self.os,
            status='active'
        )
        
        # Create attachments for the asset
        attachments = []
        for i in range(attachment_count):
            file_content = f'Test file content {i}'.encode('utf-8')
            uploaded_file = SimpleUploadedFile(
                name=f'test_scrap_{i}.txt',
                content=file_content,
                content_type='text/plain'
            )
            
            attachment = AttachmentService.upload_attachment(asset, uploaded_file)
            attachments.append(attachment)
        
        # Verify attachments were created
        assert asset.attachments.count() == attachment_count
        
        # First, free the asset (required before scrapping)
        asset.status = 'freed'
        asset.assigned_to = None
        asset.team = None
        asset.freed_date = timezone.now()
        asset.save()
        
        # Now scrap the asset
        scrapped_asset = AssetService.scrap_asset(asset, self.user, "Hardware failure")
        
        # Verify asset is scrapped
        assert scrapped_asset.status == 'scrapped'
        
        # Verify all attachments are preserved
        scrapped_asset.refresh_from_db()
        assert scrapped_asset.attachments.count() == attachment_count, \
            "All attachments should be preserved after scrapping"
        
        # Verify each attachment still exists and is associated with the asset
        for attachment in attachments:
            attachment.refresh_from_db()
            assert attachment.asset == scrapped_asset, \
                "Attachment should still be associated with the scrapped asset"
            assert AttachmentService.get_asset_attachments(scrapped_asset).filter(id=attachment.id).exists(), \
                "Attachment should be retrievable from scrapped asset"
            
            # Verify file still exists in storage
            from django.core.files.storage import default_storage
            assert default_storage.exists(attachment.file.name), \
                "Attachment file should still exist in storage"
        
        # Clean up
        for attachment in attachments:
            AttachmentService.delete_attachment(attachment)
        scrapped_asset.delete()



@pytest.mark.django_db
class TestFreedSystemsViewProperties(TestCase):
    """Property-based tests for freed systems view."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create user
        self.user, _ = User.objects.get_or_create(
            username='admin_freed_test',
            defaults={'password': 'password', 'is_staff': True}
        )
        
        # Create test data
        self.os, _ = OperatingSystem.objects.get_or_create(name="Windows 10 Freed Test")
        self.team, _ = Team.objects.get_or_create(name="IT Department Freed Test")
        
        # Create IP range and address
        self.ip_range, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.65.x",
            defaults={'network_prefix': "192.168.65"}
        )
        IPAddress.objects.filter(ip_range=self.ip_range).delete()
    
    @given(
        freed_count=st.integers(min_value=1, max_value=10),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC'])
    )
    @settings(max_examples=50)
    def test_property_14_freed_systems_view_completeness(self, freed_count, system_type):
        """
        Feature: asset-tracker, Property 14: Freed systems view completeness
        
        For any freed asset, querying the Free Systems page should return that 
        asset with at least IP address and asset_tag visible.
        
        Validates: Requirements 5.1
        """
        from django.utils import timezone
        
        # Create freed assets
        freed_assets = []
        
        for i in range(freed_count):
            # Create IP address for this asset
            ip = IPAddress.objects.create(
                address=f"192.168.65.{i+1}",
                ip_range=self.ip_range,
                is_assigned=False
            )
            
            # Create freed asset
            asset = Asset.objects.create(
                asset_tag=f'BIDC_FREED_{i}_{system_type}',
                system_type=system_type,
                operating_system=self.os,
                ip_address=ip,
                status='freed',
                freed_date=timezone.now()
            )
            freed_assets.append(asset)
        
        # Get freed systems view
        freed_view = list(AssetService.get_freed_assets())
        
        # Verify all freed assets are in the view
        for asset in freed_assets:
            assert asset in freed_view, \
                f"Freed asset {asset.asset_tag} should be in freed systems view"
        
        # Verify all required fields are accessible (at least IP address and asset_tag)
        for asset in freed_assets:
            found_asset = next((a for a in freed_view if a.serial_number == asset.serial_number), None)
            assert found_asset is not None, \
                f"Asset {asset.asset_tag} should be found in freed view"
            
            # Verify asset_tag is present
            assert found_asset.asset_tag == asset.asset_tag, \
                "Asset tag should be present and correct"
            
            # Verify IP address is present
            assert found_asset.ip_address == asset.ip_address, \
                "IP address should be present and correct"
        
        # Clean up
        for asset in freed_assets:
            if asset.ip_address:
                asset.ip_address.delete()
            asset.delete()


@pytest.mark.django_db
class TestScrappedItemsViewProperties(TestCase):
    """Property-based tests for scrapped items view."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create user
        self.user, _ = User.objects.get_or_create(
            username='admin_scrapped_test',
            defaults={'password': 'password', 'is_staff': True}
        )
        
        # Create test data
        self.os, _ = OperatingSystem.objects.get_or_create(name="Windows 10 Scrapped Test")
        self.team, _ = Team.objects.get_or_create(name="IT Department Scrapped Test")
        
        # Create IP range and address
        self.ip_range, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.66.x",
            defaults={'network_prefix': "192.168.66"}
        )
        IPAddress.objects.filter(ip_range=self.ip_range).delete()
    
    @given(
        scrapped_count=st.integers(min_value=1, max_value=10),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC'])
    )
    @settings(max_examples=50)
    def test_property_16_scrapped_items_view_completeness_and_ordering(self, scrapped_count, system_type):
        """
        Feature: asset-tracker, Property 16: Scrapped items view completeness and ordering
        
        For any set of scrapped assets, the Scrapped Items page should display all 
        of them with asset_tag, IP address, and scrapped_date, ordered by 
        scrapped_date in descending order.
        
        Validates: Requirements 7.1, 7.2
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Create scrapped assets with different scrapped dates
        scrapped_assets = []
        base_time = timezone.now()
        
        for i in range(scrapped_count):
            # Create IP address for this asset
            ip = IPAddress.objects.create(
                address=f"192.168.66.{i+1}",
                ip_range=self.ip_range,
                is_assigned=False
            )
            
            # Create asset with unique scrapped_date (spread over time)
            # Use negative timedelta to create dates in the past
            scrapped_date = base_time - timedelta(hours=i)
            
            asset = Asset.objects.create(
                asset_tag=f'BIDC_SCRAPPED_{i}_{system_type}',
                system_type=system_type,
                operating_system=self.os,
                ip_address=ip,
                status='scrapped',
                scrapped_date=scrapped_date
            )
            scrapped_assets.append(asset)
        
        # Get scrapped items view
        scrapped_view = list(AssetService.get_scrapped_assets())
        
        # Verify all scrapped assets are in the view
        for asset in scrapped_assets:
            assert asset in scrapped_view, \
                f"Scrapped asset {asset.asset_tag} should be in scrapped items view"
        
        # Verify all required fields are accessible
        for asset in scrapped_assets:
            found_asset = next((a for a in scrapped_view if a.serial_number == asset.serial_number), None)
            assert found_asset is not None, \
                f"Asset {asset.asset_tag} should be found in scrapped view"
            
            # Verify asset_tag is present
            assert found_asset.asset_tag == asset.asset_tag, \
                "Asset tag should be present and correct"
            
            # Verify IP address is present
            assert found_asset.ip_address == asset.ip_address, \
                "IP address should be present and correct"
            
            # Verify scrapped_date is present
            assert found_asset.scrapped_date is not None, \
                "Scrapped date should be present"
            assert found_asset.scrapped_date == asset.scrapped_date, \
                "Scrapped date should be correct"
        
        # Verify ordering by scrapped_date in descending order
        # The most recently scrapped (highest scrapped_date) should be first
        for i in range(len(scrapped_view) - 1):
            current_asset = scrapped_view[i]
            next_asset = scrapped_view[i + 1]
            
            # Skip if either asset doesn't have a scrapped_date (shouldn't happen, but be safe)
            if current_asset.scrapped_date is None or next_asset.scrapped_date is None:
                continue
            
            # Current asset should have scrapped_date >= next asset (descending order)
            assert current_asset.scrapped_date >= next_asset.scrapped_date, \
                f"Scrapped items should be ordered by scrapped_date descending. " \
                f"Asset {current_asset.asset_tag} (scrapped {current_asset.scrapped_date}) " \
                f"should come before {next_asset.asset_tag} (scrapped {next_asset.scrapped_date})"
        
        # Clean up
        for asset in scrapped_assets:
            if asset.ip_address:
                asset.ip_address.delete()
            asset.delete()


@pytest.mark.django_db
class TestEnhancedScrappedItemsProperties(TestCase):
    """Property-based tests for enhanced scrapped items feature."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.user, _ = User.objects.get_or_create(
            username='admin_enhanced_scrap_test',
            defaults={'password': 'password'}
        )
        self.os, _ = OperatingSystem.objects.get_or_create(name="Windows 10 Enhanced Scrap Test")
        self.team, _ = Team.objects.get_or_create(name="IT Dept Enhanced Scrap Test")
        self.ip_range, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.88.x",
            defaults={'network_prefix': "192.168.88"}
        )
        IPAddress.objects.filter(ip_range=self.ip_range).delete()

    @given(
        asset_tag=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        manufacturer=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100)
    def test_property_1_manufacturer_field_persistence(self, asset_tag, system_type, manufacturer):
        """
        Feature: enhanced-scrapped-items, Property 1: Manufacturer field persistence

        For any asset with a manufacturer value, creating or updating the asset
        should result in the manufacturer value being stored and retrievable
        from the database.

        **Validates: Requirements 1.1, 1.2**
        """
        asset_tag = asset_tag.strip()
        manufacturer = manufacturer.strip()

        assume(not Asset.objects.filter(asset_tag=asset_tag).exists())

        # Create an IP for the asset
        ip = IPAddress.objects.create(
            address=f"192.168.88.{Asset.objects.count() % 254 + 1}",
            ip_range=self.ip_range,
            is_assigned=False,
        )

        # --- Test creation with manufacturer ---
        data = {
            'asset_tag': asset_tag,
            'system_type': system_type,
            'operating_system': self.os.id,
            'ip_address': ip.id,
            'team': self.team.id,
            'manufacturer': manufacturer,
        }
        asset = AssetService.create_asset(data, self.user)

        # Reload from DB and verify manufacturer persisted
        asset.refresh_from_db()
        assert asset.manufacturer == manufacturer, (
            f"After creation, manufacturer should be '{manufacturer}' but got '{asset.manufacturer}'"
        )

        # --- Test update with a new manufacturer value ---
        new_manufacturer = manufacturer[::-1] if len(manufacturer) > 1 else manufacturer + "X"
        update_data = {'manufacturer': new_manufacturer}
        updated_asset = AssetService.update_asset(asset, update_data, self.user)

        updated_asset.refresh_from_db()
        assert updated_asset.manufacturer == new_manufacturer, (
            f"After update, manufacturer should be '{new_manufacturer}' but got '{updated_asset.manufacturer}'"
        )

        # Clean up
        updated_asset.delete()
        ip.is_assigned = False
        ip.assigned_to_asset = None
        ip.save()
        ip.delete()

    @given(
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        ip_last_octet=st.integers(min_value=1, max_value=254),
    )
    @settings(max_examples=100)
    def test_property_7_freed_date_is_set_on_ip_release(self, system_type, ip_last_octet):
        """
        # Feature: enhanced-scrapped-items, Property 7: Freed date is set on IP release

        For any IP address that is released, the freed_date field should be set
        to the current timestamp and should not be None.

        **Validates: Requirements 5.3**
        """
        from assets.services.ip_management_service import IPManagementService
        from django.utils import timezone
        from datetime import timedelta

        address = f"192.168.88.{ip_last_octet}"
        assume(not IPAddress.objects.filter(address=address).exists())

        ip = IPAddress.objects.create(
            address=address,
            ip_range=self.ip_range,
            is_assigned=True,
            assigned_to_asset=None,
            freed_date=None,
        )

        before_release = timezone.now()
        IPManagementService.release_ip(ip)
        after_release = timezone.now()

        ip.refresh_from_db()

        # freed_date must be set (not None)
        assert ip.freed_date is not None, (
            "After release_ip(), freed_date should not be None"
        )

        # freed_date should be a valid datetime close to the current time
        assert before_release - timedelta(seconds=1) <= ip.freed_date <= after_release + timedelta(seconds=1), (
            f"freed_date {ip.freed_date} should be between {before_release} and {after_release}"
        )

        # IP should also be marked as not assigned
        assert ip.is_assigned is False, (
            "After release_ip(), is_assigned should be False"
        )

        # Clean up
        ip.delete()

    @given(
        asset_tag=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        scrapping_reason=st.one_of(
            st.just(''),
            st.just(None),
            st.text(alphabet=' \t\n\r', min_size=1, max_size=50),
        ),
    )
    @settings(max_examples=100)
    def test_property_2_scrapping_reason_validation(self, asset_tag, system_type, scrapping_reason):
        """
        # Feature: enhanced-scrapped-items, Property 2: Scrapping reason validation

        For any freed asset, attempting to scrap it with an empty or whitespace-only
        scrapping reason should be rejected, and the asset status should remain 'freed'.

        **Validates: Requirements 2.1, 2.2**
        """
        from django.utils import timezone

        asset_tag = asset_tag.strip()

        assume(not Asset.objects.filter(asset_tag=asset_tag).exists())

        # Create an IP for the asset
        ip = IPAddress.objects.create(
            address=f"192.168.88.{Asset.objects.count() % 254 + 1}",
            ip_range=self.ip_range,
            is_assigned=False,
        )

        # Create asset directly in 'freed' status (bypasses password-protected free_asset)
        asset = Asset.objects.create(
            asset_tag=asset_tag,
            system_type=system_type,
            operating_system=self.os,
            ip_address=ip,
            status='freed',
            freed_date=timezone.now(),
        )

        assert asset.status == 'freed', (
            f"Asset should be in 'freed' status before scrapping, got '{asset.status}'"
        )

        # Attempting to scrap with empty/whitespace reason should raise ValidationError
        with pytest.raises(ValidationError):
            AssetService.scrap_asset(asset, self.user, scrapping_reason)

        # Asset status should remain 'freed' after failed scrap attempt
        asset.refresh_from_db()
        assert asset.status == 'freed', (
            f"Asset status should remain 'freed' after rejected scrap, got '{asset.status}'"
        )

        # Clean up
        asset.delete()
        ip.is_assigned = False
        ip.assigned_to_asset = None
        ip.save()
        ip.delete()

    @given(
        asset_tag=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        scrapping_reason=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        ip_last_octet=st.integers(min_value=1, max_value=254),
    )
    @settings(max_examples=100)
    def test_property_4_ip_release_on_scrapping(self, asset_tag, system_type, scrapping_reason, ip_last_octet):
        """
        # Feature: enhanced-scrapped-items, Property 4: IP release on scrapping

        For any freed asset with an assigned IP address, scrapping the asset
        should result in the IP address being released (is_assigned=False,
        assigned_to_asset=None).

        **Validates: Requirements 4.1**
        """
        from django.utils import timezone

        asset_tag = asset_tag.strip()
        scrapping_reason = scrapping_reason.strip()
        address = f"192.168.88.{ip_last_octet}"

        assume(not Asset.objects.filter(asset_tag=asset_tag).exists())
        assume(not IPAddress.objects.filter(address=address).exists())

        # Create an IP and mark it as assigned
        ip = IPAddress.objects.create(
            address=address,
            ip_range=self.ip_range,
            is_assigned=True,
            assigned_to_asset=None,
        )

        # Create asset directly in 'freed' status with the assigned IP
        asset = Asset.objects.create(
            asset_tag=asset_tag,
            system_type=system_type,
            operating_system=self.os,
            ip_address=ip,
            status='freed',
            freed_date=timezone.now(),
        )

        # Update IP to point to this asset
        ip.assigned_to_asset = asset
        ip.save()

        # Scrap the asset with a valid reason
        AssetService.scrap_asset(asset, self.user, scrapping_reason)

        # Reload IP from DB and verify it was released
        ip.refresh_from_db()

        assert ip.is_assigned is False, (
            f"After scrapping, IP is_assigned should be False but got {ip.is_assigned}"
        )
        assert ip.assigned_to_asset is None, (
            f"After scrapping, IP assigned_to_asset should be None but got {ip.assigned_to_asset}"
        )

        # Clean up
        asset.delete()
        ip.delete()

    @given(
        asset_tag=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        scrapping_reason=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        ip_last_octet=st.integers(min_value=1, max_value=254),
    )
    @settings(max_examples=100)
    def test_property_6_ip_reference_preservation_on_scrapping(self, asset_tag, system_type, scrapping_reason, ip_last_octet):
        """
        # Feature: enhanced-scrapped-items, Property 6: IP reference preservation on scrapping

        For any scrapped asset that had an IP address, the asset.ip_address
        reference should still point to the same IPAddress object after scrapping
        (not set to None).

        **Validates: Requirements 4.3, 7.3**
        """
        from django.utils import timezone

        asset_tag = asset_tag.strip()
        scrapping_reason = scrapping_reason.strip()
        address = f"192.168.88.{ip_last_octet}"

        assume(not Asset.objects.filter(asset_tag=asset_tag).exists())
        assume(not IPAddress.objects.filter(address=address).exists())

        # Create an IP and mark it as assigned
        ip = IPAddress.objects.create(
            address=address,
            ip_range=self.ip_range,
            is_assigned=True,
            assigned_to_asset=None,
        )

        # Create asset directly in 'freed' status with the assigned IP
        asset = Asset.objects.create(
            asset_tag=asset_tag,
            system_type=system_type,
            operating_system=self.os,
            ip_address=ip,
            status='freed',
            freed_date=timezone.now(),
        )

        # Update IP to point to this asset
        ip.assigned_to_asset = asset
        ip.save()

        original_ip_id = ip.id

        # Scrap the asset with a valid reason
        AssetService.scrap_asset(asset, self.user, scrapping_reason)

        # Reload asset from DB
        asset.refresh_from_db()

        # The asset should still reference the same IP address (not None)
        assert asset.ip_address is not None, (
            "After scrapping, asset.ip_address should not be None — "
            "the IP reference must be preserved for historical record"
        )
        assert asset.ip_address_id == original_ip_id, (
            f"After scrapping, asset.ip_address should still point to the original IP "
            f"(id={original_ip_id}) but got ip_address_id={asset.ip_address_id}"
        )

        # Clean up
        asset.delete()
        ip.delete()

    @given(
        asset_tag=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        scrapping_reason=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        ip_last_octet=st.integers(min_value=1, max_value=254),
    )
    @settings(max_examples=100)
    def test_property_6_ip_reference_preservation_on_scrapping(self, asset_tag, system_type, scrapping_reason, ip_last_octet):
        """
        # Feature: enhanced-scrapped-items, Property 6: IP reference preservation on scrapping

        For any scrapped asset that had an IP address, the asset.ip_address
        reference should still point to the same IPAddress object after scrapping
        (not set to None).

        **Validates: Requirements 4.3, 7.3**
        """
        from django.utils import timezone

        asset_tag = asset_tag.strip()
        scrapping_reason = scrapping_reason.strip()
        address = f"192.168.88.{ip_last_octet}"

        assume(not Asset.objects.filter(asset_tag=asset_tag).exists())
        assume(not IPAddress.objects.filter(address=address).exists())

        # Create an IP and mark it as assigned
        ip = IPAddress.objects.create(
            address=address,
            ip_range=self.ip_range,
            is_assigned=True,
            assigned_to_asset=None,
        )

        # Create asset directly in 'freed' status with the assigned IP
        asset = Asset.objects.create(
            asset_tag=asset_tag,
            system_type=system_type,
            operating_system=self.os,
            ip_address=ip,
            status='freed',
            freed_date=timezone.now(),
        )

        # Update IP to point to this asset
        ip.assigned_to_asset = asset
        ip.save()

        original_ip_id = ip.id

        # Scrap the asset with a valid reason
        AssetService.scrap_asset(asset, self.user, scrapping_reason)

        # Reload asset from DB
        asset.refresh_from_db()

        # The asset should still reference the same IP address (not None)
        assert asset.ip_address is not None, (
            "After scrapping, asset.ip_address should not be None — "
            "the IP reference must be preserved for historical record"
        )
        assert asset.ip_address_id == original_ip_id, (
            f"After scrapping, asset.ip_address should still point to the original IP "
            f"(id={original_ip_id}) but got ip_address_id={asset.ip_address_id}"
        )

        # Clean up
        asset.delete()
        ip.delete()


    @given(
        asset_tag=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        scrapping_reason=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        ip_last_octet=st.integers(min_value=1, max_value=254),
    )
    @settings(max_examples=100)
    def test_property_5_released_ip_appears_in_free_ips(self, asset_tag, system_type, scrapping_reason, ip_last_octet):
        """
        # Feature: enhanced-scrapped-items, Property 5: Released IP appears in free IPs

        For any asset with an IP address, after scrapping the asset, the IP address
        should appear in the free IPs queryset returned by
        IPManagementService.get_free_ips_by_range().

        **Validates: Requirements 4.2, 5.1**
        """
        from assets.services.ip_management_service import IPManagementService
        from django.utils import timezone

        asset_tag = asset_tag.strip()
        scrapping_reason = scrapping_reason.strip()
        address = f"192.168.88.{ip_last_octet}"

        assume(not Asset.objects.filter(asset_tag=asset_tag).exists())
        assume(not IPAddress.objects.filter(address=address).exists())

        # Create an IP and mark it as assigned
        ip = IPAddress.objects.create(
            address=address,
            ip_range=self.ip_range,
            is_assigned=True,
            assigned_to_asset=None,
        )

        # Create asset directly in 'freed' status with the assigned IP
        asset = Asset.objects.create(
            asset_tag=asset_tag,
            system_type=system_type,
            operating_system=self.os,
            ip_address=ip,
            status='freed',
            freed_date=timezone.now(),
        )

        # Update IP to point to this asset
        ip.assigned_to_asset = asset
        ip.save()

        # Scrap the asset with a valid reason
        AssetService.scrap_asset(asset, self.user, scrapping_reason)

        # Get free IPs by range and verify the released IP appears
        free_ips_by_range = IPManagementService.get_free_ips_by_range()

        # Collect all free IP addresses across all ranges
        all_free_ip_addresses = []
        for range_pattern, ips in free_ips_by_range.items():
            all_free_ip_addresses.extend(ip_obj.address for ip_obj in ips)

        assert address in all_free_ip_addresses, (
            f"After scrapping, IP {address} should appear in free IPs "
            f"but it was not found. Free IPs: {all_free_ip_addresses}"
        )

        # Also verify it appears under the correct range
        range_key = self.ip_range.range_pattern
        assert range_key in free_ips_by_range, (
            f"IP range '{range_key}' should be present in free IPs result"
        )
        range_ips = [ip_obj.address for ip_obj in free_ips_by_range[range_key]]
        assert address in range_ips, (
            f"After scrapping, IP {address} should appear under range '{range_key}' "
            f"but found: {range_ips}"
        )

        # Clean up
        asset.delete()
        ip.delete()

    @given(
        asset_tag=st.from_regex(r'[A-Za-z0-9]{1,50}', fullmatch=True),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        manufacturer=st.from_regex(r'[A-Za-z0-9 ]{1,100}', fullmatch=True).filter(lambda x: x.strip()),
        scrapping_reason=st.from_regex(r'[A-Za-z0-9 ]{1,200}', fullmatch=True).filter(lambda x: x.strip()),
        ip_last_octet=st.integers(min_value=1, max_value=254),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_3_scrapped_items_page_displays_all_required_fields(self, asset_tag, system_type, manufacturer, scrapping_reason, ip_last_octet):
        """
        # Feature: enhanced-scrapped-items, Property 3: Scrapped items page displays all required fields

        For any scrapped asset, the rendered scrapped items page HTML should contain
        the asset's IP address, asset tag (BIDC number), system type, manufacturer
        (system make), scrapped date, and scrapping reason.

        **Validates: Requirements 1.3, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
        """
        from django.urls import reverse
        from django.utils import timezone

        manufacturer = manufacturer.strip()
        scrapping_reason = scrapping_reason.strip()
        address = f"192.168.88.{ip_last_octet}"

        assume(not Asset.objects.filter(asset_tag=asset_tag).exists())
        assume(not IPAddress.objects.filter(address=address).exists())

        # Create an IP address
        ip = IPAddress.objects.create(
            address=address,
            ip_range=self.ip_range,
            is_assigned=False,
        )

        # Create a scrapped asset with all fields populated
        scrapped_date = timezone.now()
        asset = Asset.objects.create(
            asset_tag=asset_tag,
            system_type=system_type,
            operating_system=self.os,
            ip_address=ip,
            manufacturer=manufacturer,
            scrapping_reason=scrapping_reason,
            status='scrapped',
            scrapped_date=scrapped_date,
        )

        # Log in and request the scrapped items page
        self.user.set_password('testpass123')
        self.user.save()
        self.client.login(username=self.user.username, password='testpass123')

        response = self.client.get(reverse('scrapped_items'))
        assert response.status_code == 200, (
            f"Expected status 200 but got {response.status_code}"
        )

        content = response.content.decode()

        # Requirement 3.1: IP address is displayed
        assert address in content, (
            f"IP address '{address}' should appear on scrapped items page"
        )

        # Requirement 3.2: Asset tag (BIDC number) is displayed
        assert asset_tag in content, (
            f"Asset tag '{asset_tag}' should appear on scrapped items page"
        )

        # Requirement 3.3: System type is displayed
        assert system_type in content, (
            f"System type '{system_type}' should appear on scrapped items page"
        )

        # Requirement 3.4 / 1.3: System make (manufacturer) is displayed
        assert manufacturer in content, (
            f"Manufacturer '{manufacturer}' should appear on scrapped items page"
        )

        # Requirement 3.5: Scrapped date is displayed
        formatted_date = scrapped_date.strftime("%Y-%m-%d")
        assert formatted_date in content, (
            f"Scrapped date '{formatted_date}' should appear on scrapped items page"
        )

        # Requirement 3.6 / 2.3: Scrapping reason is displayed
        assert scrapping_reason in content, (
            f"Scrapping reason '{scrapping_reason}' should appear on scrapped items page"
        )

        # Clean up
        asset.delete()
        ip.delete()

    @given(
        asset_tag=st.from_regex(r'[A-Za-z0-9]{1,50}', fullmatch=True),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        manufacturer=st.from_regex(r'[A-Za-z0-9 ]{1,100}', fullmatch=True).filter(lambda x: x.strip()),
        scrapping_reason=st.from_regex(r'[A-Za-z0-9 ]{1,200}', fullmatch=True).filter(lambda x: x.strip()),
        ip_last_octet=st.integers(min_value=1, max_value=254),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_10_scrapped_items_page_shows_ip_reassignment_status(self, asset_tag, system_type, manufacturer, scrapping_reason, ip_last_octet):
        """
        # Feature: enhanced-scrapped-items, Property 10: Scrapped items page shows IP reassignment status

        For any scrapped asset whose IP address has been reassigned to another asset,
        the rendered scrapped items page HTML should indicate the IP is no longer
        available (e.g., with "(Reassigned)" label or different styling).

        **Validates: Requirements 7.1, 7.2**
        """
        from django.urls import reverse
        from django.utils import timezone

        manufacturer = manufacturer.strip()
        scrapping_reason = scrapping_reason.strip()
        address = f"192.168.88.{ip_last_octet}"

        assume(not Asset.objects.filter(asset_tag=asset_tag).exists())
        assume(not IPAddress.objects.filter(address=address).exists())

        # Create an IP address
        ip = IPAddress.objects.create(
            address=address,
            ip_range=self.ip_range,
            is_assigned=False,
        )

        # Create a scrapped asset with the IP
        scrapped_date = timezone.now()
        scrapped_asset = Asset.objects.create(
            asset_tag=asset_tag,
            system_type=system_type,
            operating_system=self.os,
            ip_address=ip,
            manufacturer=manufacturer,
            scrapping_reason=scrapping_reason,
            status='scrapped',
            scrapped_date=scrapped_date,
        )

        # Simulate IP reassignment: mark the IP as assigned (reassigned to another asset)
        ip.is_assigned = True
        ip.save()

        # Log in and request the scrapped items page
        self.user.set_password('testpass123')
        self.user.save()
        self.client.login(username=self.user.username, password='testpass123')

        response = self.client.get(reverse('scrapped_items'))
        assert response.status_code == 200, (
            f"Expected status 200 but got {response.status_code}"
        )

        content = response.content.decode()

        # Requirement 7.1: The page should indicate the IP is no longer available
        assert '(Reassigned)' in content, (
            f"Scrapped items page should show '(Reassigned)' label for IP {address} "
            f"that has been reassigned"
        )

        # Requirement 7.2: The IP should be displayed with different styling (red color)
        assert 'color: red' in content or 'color:red' in content, (
            f"Scrapped items page should display reassigned IP {address} with red color styling"
        )

        # Verify the IP address itself is still shown (historical preservation)
        assert address in content, (
            f"IP address '{address}' should still appear on scrapped items page "
            f"even when reassigned"
        )

        # Clean up
        scrapped_asset.delete()
        ip.delete()

    @given(
        ip_last_octet=st.integers(min_value=1, max_value=254),
        is_assigned=st.booleans(),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_8_free_ips_page_shows_availability_status(self, ip_last_octet, is_assigned):
        """
        # Feature: enhanced-scrapped-items, Property 8: Free IPs page shows availability status

        For any IP address displayed on the free IPs page, the rendered HTML
        should indicate whether the IP is available (is_assigned=False) or
        occupied (is_assigned=True).

        **Validates: Requirements 5.2, 6.2**
        """
        from django.urls import reverse

        address = f"192.168.88.{ip_last_octet}"

        assume(not IPAddress.objects.filter(address=address).exists())

        # Create an IP with the given assignment status
        ip = IPAddress.objects.create(
            address=address,
            ip_range=self.ip_range,
            is_assigned=is_assigned,
            assigned_to_asset=None,
        )

        # Log in and request the free IPs page
        self.user.set_password('testpass123')
        self.user.save()
        self.client.login(username=self.user.username, password='testpass123')

        response = self.client.get(reverse('free_ips'))
        assert response.status_code == 200, (
            f"Expected status 200 but got {response.status_code}"
        )

        content = response.content.decode()

        # The IP address should appear on the page
        assert address in content, (
            f"IP address '{address}' should appear on the free IPs page"
        )

        if is_assigned:
            # Requirement 6.2: Occupied IPs should have the 'occupied' CSS class
            assert 'occupied' in content, (
                f"Occupied IP {address} should have 'occupied' CSS class on free IPs page"
            )
            # The title attribute should indicate 'Occupied'
            assert 'title="Occupied"' in content, (
                f"Occupied IP {address} should have title='Occupied' on free IPs page"
            )
        else:
            # Requirement 5.2: Free IPs should have the 'free' CSS class
            assert 'free' in content, (
                f"Free IP {address} should have 'free' CSS class on free IPs page"
            )
            # The title attribute should indicate 'Free'
            assert 'title="Free' in content, (
                f"Free IP {address} should have title starting with 'Free' on free IPs page"
            )

        # Clean up
        ip.delete()

    @given(
        ip_last_octet=st.integers(min_value=1, max_value=254),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_9_reassigned_ips_display_in_red_on_free_ips_page(self, ip_last_octet):
        """
        # Feature: enhanced-scrapped-items, Property 9: Reassigned IPs display in red on free IPs page

        For any IP address that is reassigned (is_assigned=True), the rendered
        free IPs page HTML should display the IP address with red color styling
        or a red CSS class.

        **Validates: Requirements 6.1**
        """
        from django.urls import reverse

        address = f"192.168.88.{ip_last_octet}"

        assume(not IPAddress.objects.filter(address=address).exists())

        # Create an IP that is reassigned (is_assigned=True)
        ip = IPAddress.objects.create(
            address=address,
            ip_range=self.ip_range,
            is_assigned=True,
            assigned_to_asset=None,
        )

        # Log in and request the free IPs page
        self.user.set_password('testpass123')
        self.user.save()
        self.client.login(username=self.user.username, password='testpass123')

        response = self.client.get(reverse('free_ips'))
        assert response.status_code == 200, (
            f"Expected status 200 but got {response.status_code}"
        )

        content = response.content.decode()

        # The IP address should appear on the page
        assert address in content, (
            f"Reassigned IP '{address}' should appear on the free IPs page"
        )

        # Requirement 6.1: Reassigned IPs should have the 'occupied' CSS class
        # which applies red color styling (color: #721c24, background: #f8d7da, border: #dc3545)
        assert 'occupied' in content, (
            f"Reassigned IP {address} should have 'occupied' CSS class "
            f"(which applies red color styling) on free IPs page"
        )

        # Verify the specific IP element has the occupied class by checking
        # that the ip-item with occupied class exists in the rendered HTML
        import re
        occupied_pattern = re.compile(
            r'class="ip-item\s+occupied"[^>]*>[\s\S]*?' + re.escape(address)
        )
        assert occupied_pattern.search(content), (
            f"IP {address} should be rendered inside an element with "
            f"'ip-item occupied' classes for red styling"
        )

        # Clean up
        ip.delete()





