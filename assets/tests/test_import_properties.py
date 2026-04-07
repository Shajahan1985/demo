"""
Property-based tests for ImportService using Hypothesis.

These tests validate the correctness properties of the ImportService
for bulk asset import functionality.
"""
import pytest
import io
import openpyxl
from datetime import datetime, date
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase
from django.contrib.auth.models import User
from assets.models import OperatingSystem, Team, IPRange, IPAddress, Asset
from assets.services.import_service import ImportService


@pytest.mark.django_db
class TestImportServiceProperties(TestCase):
    """Property-based tests for ImportService."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create user
        self.user, _ = User.objects.get_or_create(
            username='admin_import_test',
            defaults={'password': 'password'}
        )
        
        # Create OS and Team
        self.os1, _ = OperatingSystem.objects.get_or_create(name="Windows 10 Import")
        self.os2, _ = OperatingSystem.objects.get_or_create(name="Windows 11 Import")
        self.team1, _ = Team.objects.get_or_create(name="Engineering Import")
        self.team2, _ = Team.objects.get_or_create(name="IT Import")
        
        # Create IP range and addresses
        self.ip_range, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.100.x",
            defaults={'network_prefix': "192.168.100"}
        )
        
        # Clean up any existing IPs and create fresh ones
        IPAddress.objects.filter(ip_range=self.ip_range).delete()
        self.free_ips = []
        for i in range(1, 21):  # Create 20 free IPs for testing
            ip = IPAddress.objects.create(
                address=f"192.168.100.{i}",
                ip_range=self.ip_range,
                is_assigned=False
            )
            self.free_ips.append(ip)
    
    def _create_excel_file(self, rows):
        """
        Helper method to create an Excel file from row data.
        
        Args:
            rows: List of dictionaries containing row data
            
        Returns:
            BytesIO object containing Excel file
        """
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        
        # Write headers
        if rows:
            headers = list(rows[0].keys())
            sheet.append(headers)
            
            # Write data rows
            for row in rows:
                sheet.append([row.get(header) for header in headers])
        
        # Save to BytesIO
        file_stream = io.BytesIO()
        workbook.save(file_stream)
        file_stream.seek(0)
        
        return file_stream
    
    @given(
        count=st.integers(min_value=1, max_value=10),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC'])
    )
    @settings(max_examples=50, deadline=None)
    def test_property_1_import_validation_completeness(self, count, system_type):
        """
        **Validates: Requirements 2.3, 2.4, 3.1, 3.2, 3.3**
        
        Property 1: Import validation completeness
        
        For any set of valid asset rows imported from Excel, all successfully 
        imported assets should pass all validation rules (unique asset_tag, 
        valid system_type, existing OS, available IP).
        
        This property ensures that the import process only creates assets that 
        meet all validation criteria, maintaining data integrity.
        """
        # Ensure we have enough free IPs
        assume(count <= len(self.free_ips))
        
        # Create valid rows
        rows = []
        used_tags = set()
        
        for i in range(count):
            asset_tag = f'BIDC_IMPORT_VAL_{i}_{count}'
            # Ensure tag doesn't exist in database
            assume(not Asset.objects.filter(asset_tag=asset_tag).exists())
            used_tags.add(asset_tag)
            
            row = {
                'asset_tag': asset_tag,
                'system_type': system_type,
                'operating_system': self.os1.name,
                'ip_address': self.free_ips[i].address,
                'particulars': f'Test particulars {i}',
                'assigned_to': f'User {i}',
                'team': self.team1.name,
                'warranty_expiration': '2025-12-31'
            }
            rows.append(row)
        
        # Create Excel file
        excel_file = self._create_excel_file(rows)
        
        # Import assets
        import_service = ImportService()
        result = import_service.import_assets(excel_file, self.user)
        
        # Verify all rows were imported successfully
        assert result['created_count'] == count, \
            f"Expected {count} successful imports, got {result['created_count']}"
        assert result['error_count'] == 0, \
            f"Expected 0 errors, got {result['error_count']}: {result['errors']}"
        
        # Verify all imported assets exist and pass validation
        for row in rows:
            asset = Asset.objects.get(asset_tag=row['asset_tag'])
            
            # Verify asset_tag is unique
            assert Asset.objects.filter(asset_tag=asset.asset_tag).count() == 1
            
            # Verify system_type is valid
            assert asset.system_type in ['Desktop', 'Laptop', 'All-in-One PC']
            
            # Verify operating_system exists
            assert asset.operating_system is not None
            assert OperatingSystem.objects.filter(id=asset.operating_system.id).exists()
            
            # Verify IP is assigned
            if asset.ip_address:
                ip_obj = IPAddress.objects.get(id=asset.ip_address.id)
                assert ip_obj.is_assigned is True
                assert ip_obj.assigned_to_asset == asset
            
            # Verify team exists if provided
            if asset.team:
                assert Team.objects.filter(id=asset.team.id).exists()
            
            # Clean up
            asset.delete()
        
        # Reset IPs
        for ip in self.free_ips:
            ip.is_assigned = False
            ip.assigned_to_asset = None
            ip.save()
    
    @given(
        count=st.integers(min_value=2, max_value=10),
        duplicate_index=st.integers(min_value=0, max_value=9)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_2_import_uniqueness(self, count, duplicate_index):
        """
        **Validates: Requirements 2.3, 2.4, 3.1, 3.2, 3.3**
        
        Property 2: Import uniqueness (upsert behavior)
        
        For any import operation, no two assets should be created with the same 
        asset_tag. If duplicate asset_tags are present in the Excel file, the 
        first occurrence creates the asset and subsequent occurrences update it.
        The database should always have exactly one asset per asset_tag.
        
        This property ensures asset_tag uniqueness is maintained via upsert during bulk imports.
        """
        # Ensure duplicate_index is within bounds
        assume(duplicate_index < count)
        assume(count < len(self.free_ips))
        
        # Create rows with one duplicate
        rows = []
        duplicate_tag = f'BIDC_IMPORT_DUP_{count}'
        
        for i in range(count):
            if i == duplicate_index:
                # Use the duplicate tag
                asset_tag = duplicate_tag
            else:
                asset_tag = f'BIDC_IMPORT_UNIQ_{i}_{count}'
            
            # Ensure tag doesn't exist in database
            assume(not Asset.objects.filter(asset_tag=asset_tag).exists())
            
            row = {
                'asset_tag': asset_tag,
                'system_type': 'Desktop',
                'operating_system': self.os1.name,
                'ip_address': self.free_ips[i].address,
                'particulars': f'Test particulars {i}',
                'assigned_to': f'User {i}',
                'team': self.team1.name,
                'warranty_expiration': '2025-12-31'
            }
            rows.append(row)
        
        # Add another row with the duplicate tag and a different free IP
        rows.append({
            'asset_tag': duplicate_tag,
            'system_type': 'Laptop',
            'operating_system': self.os2.name,
            'ip_address': self.free_ips[count].address,
            'particulars': 'Updated row',
            'assigned_to': 'Updated User',
            'team': self.team2.name,
            'warranty_expiration': '2026-12-31'
        })
        
        # Create Excel file
        excel_file = self._create_excel_file(rows)
        
        # Import assets
        import_service = ImportService()
        result = import_service.import_assets(excel_file, self.user)
        
        # With upsert, the first occurrence creates and the second updates
        # So we expect created_count = count (unique tags), updated_count = 1 (the duplicate)
        assert result['created_count'] == count, \
            f"Expected {count} created, got {result['created_count']}"
        assert result['updated_count'] == 1, \
            f"Expected 1 updated (duplicate tag), got {result['updated_count']}"
        assert result['error_count'] == 0, \
            f"Expected 0 errors, got {result['error_count']}: {result['errors']}"
        
        # Verify no duplicate asset_tags exist in database
        all_imported_assets = Asset.objects.filter(
            asset_tag__startswith=f'BIDC_IMPORT_'
        ).filter(
            asset_tag__contains=str(count)
        )
        
        asset_tags = [asset.asset_tag for asset in all_imported_assets]
        unique_tags = set(asset_tags)
        
        assert len(asset_tags) == len(unique_tags), \
            f"Found duplicate asset_tags in database: {asset_tags}"
        
        # Verify only one asset with duplicate_tag exists
        duplicate_count = Asset.objects.filter(asset_tag=duplicate_tag).count()
        assert duplicate_count == 1, \
            f"Expected exactly 1 asset with tag {duplicate_tag}, found {duplicate_count}"
        
        # Verify the duplicate tag asset was updated with the second row's data
        updated_asset = Asset.objects.get(asset_tag=duplicate_tag)
        assert updated_asset.system_type == 'Laptop', \
            f"Expected system_type 'Laptop' after update, got '{updated_asset.system_type}'"
        
        # Clean up
        for asset in all_imported_assets:
            asset.delete()
        
        # Reset IPs
        for ip in self.free_ips:
            ip.is_assigned = False
            ip.assigned_to_asset = None
            ip.save()
    
    @given(
        count=st.integers(min_value=1, max_value=10),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC'])
    )
    @settings(max_examples=50, deadline=None)
    def test_property_3_import_ip_assignment(self, count, system_type):
        """
        **Validates: Requirements 2.3, 2.4, 3.1, 3.2, 3.3**
        
        Property 3: Import IP assignment
        
        For any asset imported with an IP address, the IP should be marked as 
        assigned and linked to the asset. The IP should no longer appear in the 
        free IPs list.
        
        This property ensures IP assignment state is correctly managed during 
        bulk imports.
        """
        # Ensure we have enough free IPs
        assume(count <= len(self.free_ips))
        
        # Create valid rows with IPs
        rows = []
        ip_addresses = []
        
        for i in range(count):
            asset_tag = f'BIDC_IMPORT_IP_{i}_{count}'
            # Ensure tag doesn't exist in database
            assume(not Asset.objects.filter(asset_tag=asset_tag).exists())
            
            ip_address = self.free_ips[i].address
            ip_addresses.append(ip_address)
            
            row = {
                'asset_tag': asset_tag,
                'system_type': system_type,
                'operating_system': self.os1.name,
                'ip_address': ip_address,
                'particulars': f'Test particulars {i}',
                'assigned_to': f'User {i}',
                'team': self.team1.name,
                'warranty_expiration': '2025-12-31'
            }
            rows.append(row)
        
        # Create Excel file
        excel_file = self._create_excel_file(rows)
        
        # Import assets
        import_service = ImportService()
        result = import_service.import_assets(excel_file, self.user)
        
        # Verify all rows were imported successfully
        assert result['created_count'] == count, \
            f"Expected {count} successful imports, got {result['created_count']}"
        assert result['error_count'] == 0, \
            f"Expected 0 errors, got {result['error_count']}: {result['errors']}"
        
        # Verify all IPs are assigned
        for i, row in enumerate(rows):
            asset = Asset.objects.get(asset_tag=row['asset_tag'])
            
            # Verify asset has an IP address
            assert asset.ip_address is not None, \
                f"Asset {asset.asset_tag} should have an IP address"
            
            # Verify IP is marked as assigned
            ip_obj = IPAddress.objects.get(address=ip_addresses[i])
            assert ip_obj.is_assigned is True, \
                f"IP {ip_obj.address} should be marked as assigned"
            assert ip_obj.assigned_to_asset == asset, \
                f"IP {ip_obj.address} should be linked to asset {asset.asset_tag}"
            
            # Verify IP doesn't appear in free IPs
            from assets.services.ip_management_service import IPManagementService
            free_ips = IPManagementService.get_available_ips()
            assert ip_obj not in free_ips, \
                f"IP {ip_obj.address} should not appear in free IPs list"
            
            # Clean up
            asset.delete()
        
        # Reset IPs
        for ip in self.free_ips:
            ip.is_assigned = False
            ip.assigned_to_asset = None
            ip.save()
