"""
Preservation Property Tests for Laptop Hardware Serial Number Edit Fix

**Property 2: Preservation** - Non-Hardware-Serial-Number Updates

These tests verify that asset update operations that do NOT involve laptop/All-in-One PC
hardware serial numbers continue to work correctly after the fix is implemented.

**IMPORTANT**: These tests follow observation-first methodology:
1. Run tests on UNFIXED code to observe baseline behavior
2. Tests should PASS on unfixed code (confirms baseline)
3. After implementing fix, re-run tests to ensure no regressions

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase as HypothesisTestCase
from django.test import TestCase
from django.contrib.auth.models import User
from assets.models import OperatingSystem, Team, IPRange, IPAddress, Asset
from assets.services.asset_service import AssetService


class TestLaptopHardwareSerialPreservation(TestCase):
    """
    **Property 2: Preservation** - Non-Hardware-Serial-Number Updates
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
    
    These tests verify that asset update operations unrelated to laptop/All-in-One PC
    hardware serial numbers work correctly and must continue to work after the fix.
    
    **EXPECTED OUTCOME**: All tests PASS on unfixed code (confirms baseline behavior)
    """
    
    def setUp(self):
        """Set up test data for preservation tests."""
        # Create user
        self.user = User.objects.create_user(
            username='admin_preservation',
            password='password',
            is_staff=True,
            is_superuser=True
        )
        
        # Create operating systems
        self.os1 = OperatingSystem.objects.create(name="Windows 10 Preservation")
        self.os2 = OperatingSystem.objects.create(name="Windows 11 Preservation")
        self.os3 = OperatingSystem.objects.create(name="Ubuntu 22.04 Preservation")
        
        # Create teams
        self.team1 = Team.objects.create(name="IT Preservation")
        self.team2 = Team.objects.create(name="HR Preservation")
        
        # Create IP range and addresses
        self.ip_range = IPRange.objects.create(
            range_pattern="192.168.99.x",
            network_prefix="192.168.99"
        )
        
        # Clean up any existing IPs and create fresh ones
        IPAddress.objects.filter(ip_range=self.ip_range).delete()
        self.ip1 = IPAddress.objects.create(
            address="192.168.99.10",
            ip_range=self.ip_range,
            is_assigned=False
        )
        self.ip2 = IPAddress.objects.create(
            address="192.168.99.11",
            ip_range=self.ip_range,
            is_assigned=False
        )
        self.ip3 = IPAddress.objects.create(
            address="192.168.99.12",
            ip_range=self.ip_range,
            is_assigned=False
        )
    
    def test_preservation_desktop_asset_update_manufacturer(self):
        """
        **Property 2: Preservation** - Desktop Asset Update with Manufacturer Change
        
        **Validates: Requirements 3.1, 3.4**
        
        Test that updating a desktop asset's manufacturer works correctly.
        Desktop assets do not have hardware serial numbers, so this operation
        should be completely unaffected by the fix.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Create desktop asset (no hardware serial number)
        desktop = Asset.objects.create(
            asset_tag="BIDC_DESKTOP_001",
            system_type="Desktop",
            manufacturer="Dell",
            operating_system=self.os1,
            ip_address=self.ip1,
            team=self.team1
        )
        
        # Prepare update data to change manufacturer
        data = {
            'asset_tag': 'BIDC_DESKTOP_001',
            'system_type': 'Desktop',
            'manufacturer': 'HP',  # Changed manufacturer
            'operating_system': self.os1.id,
            'ip_address': self.ip1.id,
            'manual_ip': None,
            'particulars': '',
            'assigned_to': '',
            'team': self.team1.id,
            'warranty_expiration': None,
        }
        
        # Update asset using service
        updated_desktop = AssetService.update_asset(desktop, data, self.user)
        
        # Refresh from database
        updated_desktop.refresh_from_db()
        
        # Assert manufacturer was updated
        self.assertEqual(
            updated_desktop.manufacturer,
            "HP",
            "Desktop asset manufacturer should update correctly"
        )
        
        # Assert other fields remain unchanged
        self.assertEqual(updated_desktop.asset_tag, "BIDC_DESKTOP_001")
        self.assertEqual(updated_desktop.system_type, "Desktop")
        self.assertEqual(updated_desktop.operating_system, self.os1)
        self.assertEqual(updated_desktop.team, self.team1)
    
    def test_preservation_desktop_asset_update_operating_system(self):
        """
        **Property 2: Preservation** - Desktop Asset Update with OS Change
        
        **Validates: Requirements 3.1, 3.4**
        
        Test that updating a desktop asset's operating system works correctly.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Create desktop asset
        desktop = Asset.objects.create(
            asset_tag="BIDC_DESKTOP_002",
            system_type="Desktop",
            manufacturer="Lenovo",
            operating_system=self.os1,
            ip_address=self.ip1,
            team=self.team1
        )
        
        # Prepare update data to change OS
        data = {
            'asset_tag': 'BIDC_DESKTOP_002',
            'system_type': 'Desktop',
            'manufacturer': 'Lenovo',
            'operating_system': self.os2.id,  # Changed OS
            'ip_address': self.ip1.id,
            'manual_ip': None,
            'particulars': '',
            'assigned_to': '',
            'team': self.team1.id,
            'warranty_expiration': None,
        }
        
        # Update asset using service
        updated_desktop = AssetService.update_asset(desktop, data, self.user)
        
        # Refresh from database
        updated_desktop.refresh_from_db()
        
        # Assert OS was updated
        self.assertEqual(
            updated_desktop.operating_system,
            self.os2,
            "Desktop asset operating system should update correctly"
        )
        
        # Assert other fields remain unchanged
        self.assertEqual(updated_desktop.manufacturer, "Lenovo")
        self.assertEqual(updated_desktop.system_type, "Desktop")
    
    def test_preservation_server_asset_update_team(self):
        """
        **Property 2: Preservation** - Server Asset Update with Team Change
        
        **Validates: Requirements 3.2, 3.4**
        
        Test that updating a server asset's team assignment works correctly.
        Server assets do not have hardware serial numbers in this system.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Create server asset (system_type would be Desktop in this system)
        # Note: The system only has Desktop, Laptop, All-in-One PC types
        # So we test with Desktop as a non-laptop type
        server = Asset.objects.create(
            asset_tag="BIDC_SERVER_001",
            system_type="Desktop",  # Using Desktop as server equivalent
            manufacturer="Dell",
            operating_system=self.os3,
            ip_address=self.ip2,
            team=self.team1
        )
        
        # Prepare update data to change team
        data = {
            'asset_tag': 'BIDC_SERVER_001',
            'system_type': 'Desktop',
            'manufacturer': 'Dell',
            'operating_system': self.os3.id,
            'ip_address': self.ip2.id,
            'manual_ip': None,
            'particulars': '',
            'assigned_to': '',
            'team': self.team2.id,  # Changed team
            'warranty_expiration': None,
        }
        
        # Update asset using service
        updated_server = AssetService.update_asset(server, data, self.user)
        
        # Refresh from database
        updated_server.refresh_from_db()
        
        # Assert team was updated
        self.assertEqual(
            updated_server.team,
            self.team2,
            "Server asset team should update correctly"
        )
        
        # Assert other fields remain unchanged
        self.assertEqual(updated_server.manufacturer, "Dell")
        self.assertEqual(updated_server.operating_system, self.os3)
    
    def test_preservation_laptop_asset_creation_with_hardware_serial(self):
        """
        **Property 2: Preservation** - Laptop Asset Creation with Hardware Serial
        
        **Validates: Requirements 3.3**
        
        Test that creating a new laptop asset with a hardware serial number works correctly.
        This functionality should already work and must continue to work after the fix.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Prepare creation data for laptop with hardware serial
        data = {
            'asset_tag': 'BIDC_LAPTOP_CREATE_001',
            'system_type': 'Laptop',
            'hardware_serial_number': 'NEW_SERIAL_123',
            'manufacturer': 'Dell',
            'operating_system': self.os1.id,
            'ip_address': self.ip3.id,
            'manual_ip': None,
            'particulars': 'New laptop for testing',
            'assigned_to': 'John Doe',
            'team': self.team1.id,
            'warranty_expiration': None,
        }
        
        # Create asset using service
        new_laptop = AssetService.create_asset(data, self.user)
        
        # Refresh from database
        new_laptop.refresh_from_db()
        
        # Assert hardware serial number was saved
        self.assertEqual(
            new_laptop.hardware_serial_number,
            "NEW_SERIAL_123",
            "Laptop creation should save hardware serial number correctly"
        )
        
        # Assert other fields were saved correctly
        self.assertEqual(new_laptop.asset_tag, "BIDC_LAPTOP_CREATE_001")
        self.assertEqual(new_laptop.system_type, "Laptop")
        self.assertEqual(new_laptop.manufacturer, "Dell")
        self.assertEqual(new_laptop.operating_system, self.os1)
        self.assertEqual(new_laptop.team, self.team1)
        self.assertEqual(new_laptop.assigned_to, "John Doe")
    
    def test_preservation_manual_ip_entry_handling(self):
        """
        **Property 2: Preservation** - Manual IP Entry Handling
        
        **Validates: Requirements 3.5**
        
        Test that updating an asset with manual IP address entry works correctly.
        Manual IP addresses are not tracked in the IP management system.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Create desktop asset with managed IP
        desktop = Asset.objects.create(
            asset_tag="BIDC_DESKTOP_MANUAL_IP",
            system_type="Desktop",
            manufacturer="HP",
            operating_system=self.os1,
            ip_address=self.ip1,
            team=self.team1
        )
        
        # Prepare update data to switch to manual IP
        data = {
            'asset_tag': 'BIDC_DESKTOP_MANUAL_IP',
            'system_type': 'Desktop',
            'manufacturer': 'HP',
            'operating_system': self.os1.id,
            'ip_address': None,  # Clear managed IP
            'manual_ip': '10.0.0.50',  # Set manual IP
            'particulars': '',
            'assigned_to': '',
            'team': self.team1.id,
            'warranty_expiration': None,
        }
        
        # Update asset using service
        updated_desktop = AssetService.update_asset(desktop, data, self.user)
        
        # Refresh from database
        updated_desktop.refresh_from_db()
        
        # Assert manual IP was set
        self.assertEqual(
            updated_desktop.manual_ip,
            "10.0.0.50",
            "Manual IP should be set correctly"
        )
        
        # Assert managed IP was cleared
        self.assertIsNone(
            updated_desktop.ip_address,
            "Managed IP should be cleared when switching to manual IP"
        )
    
    def test_preservation_manual_os_entry_handling(self):
        """
        **Property 2: Preservation** - Manual OS Entry Handling
        
        **Validates: Requirements 3.6**
        
        Test that updating an asset's operating system selection works correctly.
        The OS field uses a foreign key to OperatingSystem model.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Create desktop asset with OS1
        desktop = Asset.objects.create(
            asset_tag="BIDC_DESKTOP_OS_CHANGE",
            system_type="Desktop",
            manufacturer="Lenovo",
            operating_system=self.os1,
            ip_address=self.ip1,
            team=self.team1
        )
        
        # Prepare update data to change OS
        data = {
            'asset_tag': 'BIDC_DESKTOP_OS_CHANGE',
            'system_type': 'Desktop',
            'manufacturer': 'Lenovo',
            'operating_system': self.os3.id,  # Change to Ubuntu
            'ip_address': self.ip1.id,
            'manual_ip': None,
            'particulars': '',
            'assigned_to': '',
            'team': self.team1.id,
            'warranty_expiration': None,
        }
        
        # Update asset using service
        updated_desktop = AssetService.update_asset(desktop, data, self.user)
        
        # Refresh from database
        updated_desktop.refresh_from_db()
        
        # Assert OS was updated
        self.assertEqual(
            updated_desktop.operating_system,
            self.os3,
            "Operating system should update correctly"
        )
        
        # Assert other fields remain unchanged
        self.assertEqual(updated_desktop.manufacturer, "Lenovo")
        self.assertEqual(updated_desktop.system_type, "Desktop")
    
    def test_preservation_multiple_field_updates_desktop(self):
        """
        **Property 2: Preservation** - Multiple Field Updates on Desktop
        
        **Validates: Requirements 3.1, 3.4**
        
        Test that updating multiple fields simultaneously on a desktop asset works correctly.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Create desktop asset
        desktop = Asset.objects.create(
            asset_tag="BIDC_DESKTOP_MULTI",
            system_type="Desktop",
            manufacturer="Dell",
            operating_system=self.os1,
            ip_address=self.ip1,
            team=self.team1,
            assigned_to="Alice"
        )
        
        # Prepare update data to change multiple fields
        data = {
            'asset_tag': 'BIDC_DESKTOP_MULTI',
            'system_type': 'Desktop',
            'manufacturer': 'HP',  # Changed
            'operating_system': self.os2.id,  # Changed
            'ip_address': self.ip2.id,  # Changed
            'manual_ip': None,
            'particulars': 'Updated desktop',  # Changed
            'assigned_to': 'Bob',  # Changed
            'team': self.team2.id,  # Changed
            'warranty_expiration': None,
        }
        
        # Update asset using service
        updated_desktop = AssetService.update_asset(desktop, data, self.user)
        
        # Refresh from database
        updated_desktop.refresh_from_db()
        
        # Assert all fields were updated correctly
        self.assertEqual(updated_desktop.manufacturer, "HP")
        self.assertEqual(updated_desktop.operating_system, self.os2)
        self.assertEqual(updated_desktop.ip_address, self.ip2)
        self.assertEqual(updated_desktop.particulars, "Updated desktop")
        self.assertEqual(updated_desktop.assigned_to, "Bob")
        self.assertEqual(updated_desktop.team, self.team2)
        
        # Assert asset_tag and system_type remain unchanged
        self.assertEqual(updated_desktop.asset_tag, "BIDC_DESKTOP_MULTI")
        self.assertEqual(updated_desktop.system_type, "Desktop")


class TestLaptopHardwareSerialPreservationPropertyBased(HypothesisTestCase):
    """
    Property-Based Tests for Preservation
    
    **Property 2: Preservation** - Non-Hardware-Serial-Number Updates
    
    **Validates: Requirements 3.1, 3.2, 3.4**
    
    These property-based tests generate many test cases to verify that
    asset updates unrelated to laptop/All-in-One PC hardware serial numbers
    work correctly across a wide range of inputs.
    
    **EXPECTED OUTCOME**: All tests PASS on unfixed code (confirms baseline behavior)
    """
    
    def setUp(self):
        """Set up test data for property-based tests."""
        # Create user (use get_or_create to avoid conflicts)
        self.user, _ = User.objects.get_or_create(
            username='admin_pbt_preservation',
            defaults={
                'password': 'password',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        # Create operating systems (use get_or_create to avoid conflicts)
        self.os1, _ = OperatingSystem.objects.get_or_create(name="Windows 10 PBT")
        self.os2, _ = OperatingSystem.objects.get_or_create(name="Windows 11 PBT")
        
        # Create teams (use get_or_create to avoid conflicts)
        self.team1, _ = Team.objects.get_or_create(name="IT PBT")
        self.team2, _ = Team.objects.get_or_create(name="HR PBT")
        
        # Create IP range (use get_or_create to avoid conflicts)
        self.ip_range, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.100.x",
            defaults={'network_prefix': "192.168.100"}
        )
    
    @given(
        manufacturer=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        particulars=st.text(min_size=0, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N', 'P'))),
        assigned_to=st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=('L',)))
    )
    @settings(max_examples=30, deadline=None)
    def test_property_preservation_desktop_updates_work(self, manufacturer, particulars, assigned_to):
        """
        **Property 2: Preservation** - Desktop Asset Updates Always Work
        
        **Validates: Requirements 3.1, 3.4**
        
        Property: For any desktop asset update (no hardware serial number involved),
        all fields should update correctly.
        
        This property-based test generates many test cases with different
        manufacturers, particulars, and assigned_to values to ensure the fix
        doesn't break desktop asset updates.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Assume non-empty manufacturer
        assume(len(manufacturer.strip()) > 0)
        
        # Clean up any previous test data
        Asset.objects.filter(asset_tag__startswith='PBTD').delete()
        IPAddress.objects.filter(address__startswith='192.168.100.').delete()
        
        # Create IP address for this test
        ip_suffix = (hash(manufacturer + particulars + assigned_to) % 200) + 10
        ip = IPAddress.objects.create(
            address=f"192.168.100.{ip_suffix}",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create desktop asset
        asset_tag = f"PBTD{hash(manufacturer + particulars) % 10000:04d}"
        desktop = Asset.objects.create(
            asset_tag=asset_tag,
            system_type="Desktop",
            manufacturer="Original Manufacturer",
            operating_system=self.os1,
            ip_address=ip,
            team=self.team1
        )
        
        # Prepare update data
        data = {
            'asset_tag': asset_tag,
            'system_type': 'Desktop',
            'manufacturer': manufacturer.strip(),
            'operating_system': self.os2.id,  # Change OS
            'ip_address': ip.id,
            'manual_ip': None,
            'particulars': particulars.strip(),
            'assigned_to': assigned_to.strip(),
            'team': self.team2.id,  # Change team
            'warranty_expiration': None,
        }
        
        # Update asset using service
        updated_desktop = AssetService.update_asset(desktop, data, self.user)
        
        # Refresh from database
        updated_desktop.refresh_from_db()
        
        # Property: All fields should update correctly
        self.assertEqual(
            updated_desktop.manufacturer,
            manufacturer.strip(),
            f"Desktop manufacturer should update to: {manufacturer[:30]}"
        )
        self.assertEqual(
            updated_desktop.operating_system,
            self.os2,
            "Desktop OS should update correctly"
        )
        self.assertEqual(
            updated_desktop.particulars,
            particulars.strip(),
            f"Desktop particulars should update to: {particulars[:30]}"
        )
        self.assertEqual(
            updated_desktop.assigned_to,
            assigned_to.strip(),
            f"Desktop assigned_to should update to: {assigned_to[:30]}"
        )
        self.assertEqual(
            updated_desktop.team,
            self.team2,
            "Desktop team should update correctly"
        )
    
    @given(
        manual_ip_octets=st.tuples(
            st.integers(min_value=1, max_value=255),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=1, max_value=254)
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_property_preservation_manual_ip_handling_works(self, manual_ip_octets):
        """
        **Property 2: Preservation** - Manual IP Handling Always Works
        
        **Validates: Requirements 3.5**
        
        Property: For any asset update with manual IP entry, the manual IP
        should be set correctly and the managed IP should be cleared.
        
        This property-based test generates many test cases with different
        manual IP addresses to ensure the fix doesn't break manual IP handling.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Clean up any previous test data
        Asset.objects.filter(asset_tag__startswith='PBTM').delete()
        IPAddress.objects.filter(address__startswith='192.168.100.').delete()
        
        # Create IP address for this test
        ip = IPAddress.objects.create(
            address=f"192.168.100.{manual_ip_octets[3]}",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create desktop asset with managed IP
        asset_tag = f"PBTM{hash(str(manual_ip_octets)) % 10000:04d}"
        desktop = Asset.objects.create(
            asset_tag=asset_tag,
            system_type="Desktop",
            manufacturer="Dell",
            operating_system=self.os1,
            ip_address=ip,
            team=self.team1
        )
        
        # Prepare manual IP address
        manual_ip = f"{manual_ip_octets[0]}.{manual_ip_octets[1]}.{manual_ip_octets[2]}.{manual_ip_octets[3]}"
        
        # Prepare update data to switch to manual IP
        data = {
            'asset_tag': asset_tag,
            'system_type': 'Desktop',
            'manufacturer': 'Dell',
            'operating_system': self.os1.id,
            'ip_address': None,  # Clear managed IP
            'manual_ip': manual_ip,  # Set manual IP
            'particulars': '',
            'assigned_to': '',
            'team': self.team1.id,
            'warranty_expiration': None,
        }
        
        # Update asset using service
        updated_desktop = AssetService.update_asset(desktop, data, self.user)
        
        # Refresh from database
        updated_desktop.refresh_from_db()
        
        # Property: Manual IP should be set correctly
        self.assertEqual(
            updated_desktop.manual_ip,
            manual_ip,
            f"Manual IP should be set to: {manual_ip}"
        )
        
        # Property: Managed IP should be cleared
        self.assertIsNone(
            updated_desktop.ip_address,
            "Managed IP should be cleared when switching to manual IP"
        )
    
    @given(
        os_choice=st.sampled_from([1, 2])
    )
    @settings(max_examples=10, deadline=None)
    def test_property_preservation_os_updates_work(self, os_choice):
        """
        **Property 2: Preservation** - OS Updates Always Work
        
        **Validates: Requirements 3.6**
        
        Property: For any asset update with OS change, the operating system
        should update correctly.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Clean up any previous test data
        Asset.objects.filter(asset_tag__startswith='PBTO').delete()
        IPAddress.objects.filter(address__startswith='192.168.100.').delete()
        
        # Create IP address for this test
        ip = IPAddress.objects.create(
            address=f"192.168.100.{50 + os_choice}",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create desktop asset
        asset_tag = f"PBTO{os_choice:04d}"
        desktop = Asset.objects.create(
            asset_tag=asset_tag,
            system_type="Desktop",
            manufacturer="HP",
            operating_system=self.os1,
            ip_address=ip,
            team=self.team1
        )
        
        # Select target OS
        target_os = self.os2 if os_choice == 1 else self.os1
        
        # Prepare update data to change OS
        data = {
            'asset_tag': asset_tag,
            'system_type': 'Desktop',
            'manufacturer': 'HP',
            'operating_system': target_os.id,
            'ip_address': ip.id,
            'manual_ip': None,
            'particulars': '',
            'assigned_to': '',
            'team': self.team1.id,
            'warranty_expiration': None,
        }
        
        # Update asset using service
        updated_desktop = AssetService.update_asset(desktop, data, self.user)
        
        # Refresh from database
        updated_desktop.refresh_from_db()
        
        # Property: OS should update correctly
        self.assertEqual(
            updated_desktop.operating_system,
            target_os,
            f"Operating system should update to: {target_os.name}"
        )
