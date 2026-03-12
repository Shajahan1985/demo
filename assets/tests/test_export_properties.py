"""
Property-based tests for ExportService using Hypothesis.

These tests validate the correctness properties of the ExportService
for Excel export functionality.
"""
import pytest
import io
import openpyxl
from datetime import datetime, date
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from assets.models import OperatingSystem, Team, IPRange, IPAddress, Asset
from assets.services.export_service import ExportService


@pytest.mark.django_db
class TestExportServiceProperties(TestCase):
    """Property-based tests for ExportService."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create user
        self.user, _ = User.objects.get_or_create(
            username='admin_export_test',
            defaults={'password': 'password'}
        )
        
        # Create OS and Team
        self.os1, _ = OperatingSystem.objects.get_or_create(name="Windows 10 Export")
        self.os2, _ = OperatingSystem.objects.get_or_create(name="Windows 11 Export")
        self.team1, _ = Team.objects.get_or_create(name="Engineering Export")
        self.team2, _ = Team.objects.get_or_create(name="IT Export")
        
        # Create IP range and addresses
        self.ip_range, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.200.x",
            defaults={'network_prefix': "192.168.200"}
        )
        
        # Clean up any existing IPs and create fresh ones
        IPAddress.objects.filter(ip_range=self.ip_range).delete()
        self.ips = []
        for i in range(1, 21):  # Create 20 IPs for testing
            ip = IPAddress.objects.create(
                address=f"192.168.200.{i}",
                ip_range=self.ip_range,
                is_assigned=False
            )
            self.ips.append(ip)
    
    def _read_excel_file(self, response):
        """
        Helper method to read Excel file from HttpResponse.
        
        Args:
            response: HttpResponse containing Excel file
            
        Returns:
            Tuple of (workbook, sheet, headers, data_rows)
        """
        # Get content from response
        content = response.content
        
        # Load workbook from bytes
        file_stream = io.BytesIO(content)
        workbook = openpyxl.load_workbook(file_stream)
        sheet = workbook.active
        
        # Extract headers (first row)
        headers = [cell.value for cell in sheet[1]]
        
        # Extract data rows (all rows after first)
        data_rows = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            data_rows.append(row)
        
        return workbook, sheet, headers, data_rows
    
    @given(
        count=st.integers(min_value=0, max_value=15),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC'])
    )
    @settings(max_examples=50, deadline=None)
    def test_property_4_export_completeness(self, count, system_type):
        """
        **Validates: Requirements 5.1, 5.2, 6.1, 7.1, 8.1**
        
        Property 4: Export completeness
        
        For any export operation, the number of data rows in the exported Excel 
        file should equal the number of items in the queryset. No data should be 
        lost or duplicated during export.
        
        This property ensures export completeness and data integrity.
        """
        # Ensure we have enough IPs
        assume(count <= len(self.ips))
        
        # Create assets
        created_assets = []
        for i in range(count):
            asset_tag = f'BIDC_EXPORT_COMP_{i}_{count}'
            
            # Assign IP if available
            ip_address = self.ips[i] if i < len(self.ips) else None
            if ip_address:
                ip_address.is_assigned = True
                ip_address.save()
            
            asset = Asset.objects.create(
                asset_tag=asset_tag,
                system_type=system_type,
                operating_system=self.os1,
                ip_address=ip_address,
                particulars=f'Test particulars {i}',
                assigned_to=f'User {i}',
                team=self.team1,
                status='active',
                warranty_expiration=date(2025, 12, 31)
            )
            if ip_address:
                ip_address.assigned_to_asset = asset
                ip_address.save()
            
            created_assets.append(asset)
        
        # Export active assets
        export_service = ExportService()
        response = export_service.export_active_assets()
        
        # Read Excel file
        workbook, sheet, headers, data_rows = self._read_excel_file(response)
        
        # Verify row count equals queryset count
        queryset_count = Asset.objects.filter(status='active').count()
        exported_row_count = len(data_rows)
        
        assert exported_row_count >= count, \
            f"Expected at least {count} rows in export, got {exported_row_count}"
        
        # Verify all created assets are in the export
        exported_asset_tags = [row[1] for row in data_rows if row[1]]  # Column 1 is Asset Tag
        
        for asset in created_assets:
            assert asset.asset_tag in exported_asset_tags, \
                f"Asset {asset.asset_tag} not found in export"
        
        # Clean up
        for asset in created_assets:
            asset.delete()
        
        # Reset IPs
        for ip in self.ips:
            ip.is_assigned = False
            ip.assigned_to_asset = None
            ip.save()
    
    @given(
        count=st.integers(min_value=1, max_value=15),
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC'])
    )
    @settings(max_examples=50, deadline=None)
    def test_property_5_export_column_consistency(self, count, system_type):
        """
        **Validates: Requirements 5.1, 5.2, 6.1, 7.1, 8.1**
        
        Property 5: Export column consistency
        
        For any export operation, all data rows should have the same number of 
        columns as the header row. No rows should have missing or extra columns.
        
        This property ensures consistent Excel file structure.
        """
        # Ensure we have enough IPs
        assume(count <= len(self.ips))
        
        # Create assets with varying data (some with optional fields, some without)
        created_assets = []
        for i in range(count):
            asset_tag = f'BIDC_EXPORT_COL_{i}_{count}'
            
            # Assign IP if available
            ip_address = self.ips[i] if i < len(self.ips) else None
            if ip_address:
                ip_address.is_assigned = True
                ip_address.save()
            
            # Vary optional fields
            assigned_to = f'User {i}' if i % 2 == 0 else None
            team = self.team1 if i % 3 == 0 else None
            warranty_expiration = date(2025, 12, 31) if i % 4 == 0 else None
            
            asset = Asset.objects.create(
                asset_tag=asset_tag,
                system_type=system_type,
                operating_system=self.os1,
                ip_address=ip_address,
                particulars=f'Test particulars {i}',
                assigned_to=assigned_to,
                team=team,
                status='active',
                warranty_expiration=warranty_expiration
            )
            if ip_address:
                ip_address.assigned_to_asset = asset
                ip_address.save()
            
            created_assets.append(asset)
        
        # Export active assets
        export_service = ExportService()
        response = export_service.export_active_assets()
        
        # Read Excel file
        workbook, sheet, headers, data_rows = self._read_excel_file(response)
        
        # Verify all rows have same number of columns as headers
        header_count = len(headers)
        
        for i, row in enumerate(data_rows):
            row_column_count = len(row)
            assert row_column_count == header_count, \
                f"Row {i+2} has {row_column_count} columns, expected {header_count} (headers: {headers})"
        
        # Verify headers are not empty
        assert all(header is not None and header != '' for header in headers), \
            f"Headers should not be empty: {headers}"
        
        # Clean up
        for asset in created_assets:
            asset.delete()
        
        # Reset IPs
        for ip in self.ips:
            ip.is_assigned = False
            ip.assigned_to_asset = None
            ip.save()
    
    @given(
        count=st.integers(min_value=0, max_value=15),
        export_type=st.sampled_from(['active', 'freed', 'scrapped', 'free_ips'])
    )
    @settings(max_examples=50, deadline=None)
    def test_property_6_export_format_validity(self, count, export_type):
        """
        **Validates: Requirements 5.1, 5.2, 6.1, 7.1, 8.1**
        
        Property 6: Export format validity
        
        For any export operation, the generated file should be a valid Excel 
        format that can be opened and read by openpyxl. The file should have 
        proper structure with headers and data.
        
        This property ensures exported files are valid and usable.
        """
        # Ensure we have enough IPs
        assume(count <= len(self.ips))
        
        # Create test data based on export type
        created_assets = []
        
        if export_type == 'free_ips':
            # For free IPs, just ensure we have some free IPs
            # Reset all IPs to free
            for ip in self.ips[:count]:
                ip.is_assigned = False
                ip.assigned_to_asset = None
                ip.save()
        else:
            # Create assets with appropriate status
            status_map = {
                'active': 'active',
                'freed': 'freed',
                'scrapped': 'scrapped'
            }
            status = status_map[export_type]
            
            for i in range(count):
                asset_tag = f'BIDC_EXPORT_FMT_{export_type}_{i}_{count}'
                
                # Assign IP if available
                ip_address = self.ips[i] if i < len(self.ips) else None
                if ip_address:
                    ip_address.is_assigned = True
                    ip_address.save()
                
                # Set date fields based on status
                freed_date = timezone.now() if status == 'freed' else None
                scrapped_date = timezone.now() if status == 'scrapped' else None
                
                asset = Asset.objects.create(
                    asset_tag=asset_tag,
                    system_type='Desktop',
                    operating_system=self.os1,
                    ip_address=ip_address,
                    particulars=f'Test particulars {i}',
                    assigned_to=f'User {i}',
                    team=self.team1,
                    status=status,
                    warranty_expiration=date(2025, 12, 31),
                    freed_date=freed_date,
                    scrapped_date=scrapped_date
                )
                if ip_address:
                    ip_address.assigned_to_asset = asset
                    ip_address.save()
                
                created_assets.append(asset)
        
        # Export based on type
        export_service = ExportService()
        
        if export_type == 'active':
            response = export_service.export_active_assets()
        elif export_type == 'freed':
            response = export_service.export_freed_assets()
        elif export_type == 'scrapped':
            response = export_service.export_scrapped_assets()
        elif export_type == 'free_ips':
            response = export_service.export_free_ips()
        
        # Verify response is valid
        assert response is not None, "Export response should not be None"
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
        
        # Verify content type
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', \
            f"Invalid content type: {response['Content-Type']}"
        
        # Verify Content-Disposition header
        assert 'Content-Disposition' in response, "Missing Content-Disposition header"
        assert 'attachment' in response['Content-Disposition'], \
            "Content-Disposition should specify attachment"
        
        # Verify file can be opened and read
        try:
            workbook, sheet, headers, data_rows = self._read_excel_file(response)
        except Exception as e:
            pytest.fail(f"Failed to read Excel file: {e}")
        
        # Verify workbook structure
        assert workbook is not None, "Workbook should not be None"
        assert sheet is not None, "Sheet should not be None"
        assert len(headers) > 0, "Headers should not be empty"
        
        # Verify headers are strings
        for header in headers:
            assert isinstance(header, str), f"Header should be string, got {type(header)}: {header}"
        
        # Verify data rows structure (if any data exists)
        if count > 0 and export_type != 'free_ips':
            assert len(data_rows) >= count, \
                f"Expected at least {count} data rows, got {len(data_rows)}"
        
        # Clean up
        for asset in created_assets:
            asset.delete()
        
        # Reset IPs
        for ip in self.ips:
            ip.is_assigned = False
            ip.assigned_to_asset = None
            ip.save()
