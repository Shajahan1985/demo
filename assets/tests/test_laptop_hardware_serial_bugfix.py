"""
Bug condition exploration test for laptop hardware serial number edit fix.

**Validates: Requirements 1.1, 1.2, 1.3**

This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.
This test encodes the expected behavior - it will validate the fix when it passes after implementation.
"""
import pytest
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from assets.models import OperatingSystem, Team, IPRange, IPAddress, Asset
from assets.views import AssetUpdateView
from assets.services.asset_service import AssetService


@pytest.mark.django_db
class TestLaptopHardwareSerialBugCondition(TestCase):
    """
    Bug condition exploration tests for hardware serial number loss on laptop/All-in-One PC edit.
    
    These tests are EXPECTED TO FAIL on unfixed code.
    """
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create user
        self.user, _ = User.objects.get_or_create(
            username='admin_bugfix_test',
            defaults={'password': 'password', 'is_staff': True, 'is_superuser': True}
        )
        
        # Create OS and Team
        self.os, _ = OperatingSystem.objects.get_or_create(name="Windows 10 Bugfix Test")
        self.team, _ = Team.objects.get_or_create(name="IT Bugfix Test")
        
        # Create IP range and addresses
        self.ip_range, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.88.x",
            defaults={'network_prefix': "192.168.88"}
        )
        
        # Clean up any existing IPs and create fresh ones
        IPAddress.objects.filter(ip_range=self.ip_range).delete()
        self.ip1 = IPAddress.objects.create(
            address="192.168.88.1",
            ip_range=self.ip_range,
            is_assigned=False
        )
    
    def test_bug_condition_laptop_serial_update(self):
        """
        Test that editing a laptop asset with hardware serial number "ABC123" 
        and changing it to "XYZ789" results in the hardware_serial_number field 
        being updated to "XYZ789".
        
        **EXPECTED OUTCOME**: Test FAILS on unfixed code (proves bug exists)
        
        **Validates: Requirements 1.1, 1.3**
        """
        # Create laptop with hardware serial "ABC123"
        laptop = Asset.objects.create(
            asset_tag="BIDC_LAPTOP_001",
            system_type="Laptop",
            hardware_serial_number="ABC123",
            operating_system=self.os,
            ip_address=self.ip1,
            team=self.team
        )
        
        # Prepare update data to change serial to "XYZ789"
        data = {
            'asset_tag': 'BIDC_LAPTOP_001',
            'system_type': 'Laptop',
            'hardware_serial_number': 'XYZ789',
            'manufacturer': 'Dell',
            'operating_system': self.os.id,
            'ip_address': self.ip1.id,
            'manual_ip': None,
            'particulars': '',
            'assigned_to': '',
            'team': self.team.id,
            'warranty_expiration': None,
        }
        
        # Verify hardware_serial_number is in the data dictionary
        assert 'hardware_serial_number' in data, \
            "Bug detected: hardware_serial_number not in data dictionary"
        
        # Update asset using service
        updated_laptop = AssetService.update_asset(laptop, data, self.user)
        
        # Refresh from database
        updated_laptop.refresh_from_db()
        
        # Assert hardware serial number was updated to "XYZ789"
        assert updated_laptop.hardware_serial_number == "XYZ789", \
            f"Bug detected: Expected hardware_serial_number='XYZ789', got '{updated_laptop.hardware_serial_number}'"
    
    def test_bug_condition_allinone_serial_preservation(self):
        """
        Test that editing an All-in-One PC asset with hardware serial number "DEF456" 
        while changing the manufacturer preserves the hardware serial number "DEF456".
        
        **EXPECTED OUTCOME**: Test FAILS on unfixed code (proves bug exists)
        
        **Validates: Requirements 1.2, 1.3**
        """
        # Create All-in-One PC with hardware serial "DEF456"
        allinone = Asset.objects.create(
            asset_tag="BIDC_AIO_001",
            system_type="All-in-One PC",
            hardware_serial_number="DEF456",
            manufacturer="HP",
            operating_system=self.os,
            ip_address=self.ip1,
            team=self.team
        )
        
        # Prepare update data to change manufacturer but keep serial
        data = {
            'asset_tag': 'BIDC_AIO_001',
            'system_type': 'All-in-One PC',
            'hardware_serial_number': 'DEF456',
            'manufacturer': 'Lenovo',  # Changed manufacturer
            'operating_system': self.os.id,
            'ip_address': self.ip1.id,
            'manual_ip': None,
            'particulars': '',
            'assigned_to': '',
            'team': self.team.id,
            'warranty_expiration': None,
        }
        
        # Verify hardware_serial_number is in the data dictionary
        assert 'hardware_serial_number' in data, \
            "Bug detected: hardware_serial_number not in data dictionary"
        
        # Update asset using service
        updated_allinone = AssetService.update_asset(allinone, data, self.user)
        
        # Refresh from database
        updated_allinone.refresh_from_db()
        
        # Assert hardware serial number was preserved as "DEF456"
        assert updated_allinone.hardware_serial_number == "DEF456", \
            f"Bug detected: Expected hardware_serial_number='DEF456', got '{updated_allinone.hardware_serial_number}'"
        
        # Assert manufacturer was updated
        assert updated_allinone.manufacturer == "Lenovo", \
            f"Expected manufacturer='Lenovo', got '{updated_allinone.manufacturer}'"
    
    @patch('assets.views.messages')
    @patch('assets.views.AssetService.update_asset')
    def test_bug_condition_data_dictionary_contains_hardware_serial(self, mock_update_asset, mock_messages):
        """
        Test that the data dictionary passed to AssetService.update_asset() 
        contains the 'hardware_serial_number' key when updating a laptop.
        
        This test intercepts the call to AssetService.update_asset() to inspect
        the data dictionary being passed.
        
        **EXPECTED OUTCOME**: Test FAILS on unfixed code (proves bug exists)
        
        **Validates: Requirements 1.3**
        """
        from django.test import RequestFactory
        from assets.forms import AssetForm
        
        # Create laptop with hardware serial
        laptop = Asset.objects.create(
            asset_tag="BIDC_LAPTOP_002",
            system_type="Laptop",
            hardware_serial_number="GHI789",
            operating_system=self.os,
            ip_address=self.ip1,
            team=self.team
        )
        
        # Mock the update_asset to return the laptop unchanged
        mock_update_asset.return_value = laptop
        
        # Create a request with form data
        factory = RequestFactory()
        post_data = {
            'asset_tag': 'BIDC_LAPTOP_002',
            'system_type': 'Laptop',
            'hardware_serial_number': 'GHI789',
            'manufacturer': 'Dell',
            'operating_system': self.os.id,
            'ip_address': self.ip1.id,
            'team': self.team.id,
        }
        request = factory.post('/assets/update/1/', data=post_data)
        request.user = self.user
        
        # Create view instance
        view = AssetUpdateView()
        view.request = request
        view.kwargs = {'pk': laptop.pk}
        
        # Create form with the data
        form = AssetForm(data=post_data, instance=laptop)
        assert form.is_valid(), f"Form validation failed: {form.errors}"
        
        # Call form_valid
        view.form_valid(form)
        
        # Verify update_asset was called
        assert mock_update_asset.called, "AssetService.update_asset was not called"
        
        # Get the data dictionary passed to update_asset
        call_args = mock_update_asset.call_args
        data_dict = call_args[0][1]  # Second positional argument is the data dictionary
        
        # Assert hardware_serial_number is in the data dictionary
        assert 'hardware_serial_number' in data_dict, \
            f"Bug detected: 'hardware_serial_number' not in data dictionary. Keys present: {list(data_dict.keys())}"
        
        # Assert the value is correct
        assert data_dict['hardware_serial_number'] == 'GHI789', \
            f"Bug detected: Expected hardware_serial_number='GHI789', got '{data_dict.get('hardware_serial_number')}'"
