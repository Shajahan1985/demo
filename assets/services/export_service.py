"""
Export service for generating Excel files from asset data.

This service handles creating Excel workbooks from querysets
and generating downloadable files for various asset views.
"""

from typing import List, Callable, Any
import openpyxl
from openpyxl import Workbook
from django.http import HttpResponse
from django.db.models import QuerySet


class ExportService:
    """Service for exporting assets to Excel files."""
    
    def __init__(self):
        """Initialize the export service."""
        pass
    
    def _create_workbook(self, queryset: QuerySet, columns: List[str], title: str, 
                         row_extractor: Callable[[Any], List[Any]] = None) -> Workbook:
        """
        Create Excel workbook from queryset.
        
        Args:
            queryset: Django QuerySet containing data to export
            columns: List of column names for headers
            title: Title for the worksheet
            row_extractor: Optional function to extract row data from each queryset item.
                          If not provided, items are used as-is (for list of lists).
            
        Returns:
            openpyxl Workbook object with headers, data, and formatted columns
        """
        # Create new workbook and set title
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = title
        
        # Write headers to first row
        sheet.append(columns)
        
        # Loop through queryset and write data rows
        for item in queryset:
            if row_extractor:
                row_data = row_extractor(item)
            else:
                # If no extractor provided, assume item is already a list/tuple
                row_data = item if isinstance(item, (list, tuple)) else [item]
            sheet.append(row_data)
        
        # Format columns with appropriate widths
        for column_cells in sheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter
            
            for cell in column_cells:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            
            # Set column width with some padding (minimum 10, maximum 50)
            adjusted_width = min(max(max_length + 2, 10), 50)
            sheet.column_dimensions[column_letter].width = adjusted_width
        
        return workbook
    
    def export_active_assets(self) -> HttpResponse:
        """
        Export all active assets to Excel file.
        
        Returns:
            HttpResponse with Excel file attachment
        """
        from assets.models import Asset
        
        # Query active assets with related data
        queryset = Asset.objects.filter(status='active').select_related(
            'operating_system', 'team', 'ip_address'
        ).order_by('serial_number')
        
        # Define columns for export
        columns = [
            'Serial Number',
            'Asset Tag',
            'System Type',
            'OS',
            'IP Address',
            'Assigned To',
            'Team',
            'Warranty Expiration'
        ]
        
        # Define row extractor function
        def extract_row(asset):
            return [
                asset.serial_number,
                asset.asset_tag,
                asset.system_type,
                asset.operating_system.name,
                asset.ip_address.address if asset.ip_address else '',
                asset.assigned_to or '',
                asset.team.name if asset.team else '',
                asset.warranty_expiration.strftime('%Y-%m-%d') if asset.warranty_expiration else ''
            ]
        
        # Create workbook
        workbook = self._create_workbook(queryset, columns, 'Active Assets', extract_row)
        
        # Create HttpResponse with Excel content type
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Set Content-Disposition header with filename
        response['Content-Disposition'] = 'attachment; filename=active_assets.xlsx'
        
        # Save workbook to response
        workbook.save(response)
        
        return response
    
    def export_freed_assets(self) -> HttpResponse:
        """
        Export all freed assets to Excel file.
        
        Returns:
            HttpResponse with Excel file attachment
        """
        from assets.models import Asset
        
        # Query freed assets with related data, ordered by freed_date descending
        queryset = Asset.objects.filter(status='freed').select_related(
            'operating_system', 'ip_address'
        ).order_by('-freed_date')
        
        # Define columns for export
        columns = [
            'Serial Number',
            'Asset Tag',
            'System Type',
            'OS',
            'IP Address',
            'Freed Date'
        ]
        
        # Define row extractor function
        def extract_row(asset):
            return [
                asset.serial_number,
                asset.asset_tag,
                asset.system_type,
                asset.operating_system.name,
                asset.ip_address.address if asset.ip_address else '',
                asset.freed_date.strftime('%Y-%m-%d %H:%M:%S') if asset.freed_date else ''
            ]
        
        # Create workbook
        workbook = self._create_workbook(queryset, columns, 'Freed Assets', extract_row)
        
        # Create HttpResponse with Excel content type
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Set Content-Disposition header with filename
        response['Content-Disposition'] = 'attachment; filename=freed_assets.xlsx'
        
        # Save workbook to response
        workbook.save(response)
        
        return response
    
    def export_scrapped_assets(self) -> HttpResponse:
        """
        Export all scrapped assets to Excel file.
        
        Returns:
            HttpResponse with Excel file attachment
        """
        from assets.models import Asset
        
        # Query scrapped assets with related data, ordered by scrapped_date descending
        queryset = Asset.objects.filter(status='scrapped').select_related(
            'operating_system', 'ip_address'
        ).order_by('-scrapped_date')
        
        # Define columns for export
        columns = [
            'Serial Number',
            'Asset Tag',
            'System Type',
            'OS',
            'IP Address',
            'Scrapped Date'
        ]
        
        # Define row extractor function
        def extract_row(asset):
            return [
                asset.serial_number,
                asset.asset_tag,
                asset.system_type,
                asset.operating_system.name,
                asset.ip_address.address if asset.ip_address else '',
                asset.scrapped_date.strftime('%Y-%m-%d %H:%M:%S') if asset.scrapped_date else ''
            ]
        
        # Create workbook
        workbook = self._create_workbook(queryset, columns, 'Scrapped Assets', extract_row)
        
        # Create HttpResponse with Excel content type
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Set Content-Disposition header with filename
        response['Content-Disposition'] = 'attachment; filename=scrapped_assets.xlsx'
        
        # Save workbook to response
        workbook.save(response)
        
        return response
    
    def export_free_ips(self) -> HttpResponse:
        """
        Export all free IP addresses to Excel file.
        
        Returns:
            HttpResponse with Excel file attachment
        """
        from assets.models import IPAddress
        
        # Query free IP addresses with related ip_range, ordered by ip_range then by address
        queryset = IPAddress.objects.filter(is_assigned=False).select_related(
            'ip_range'
        ).order_by('ip_range__range_pattern', 'address')
        
        # Define columns for export
        columns = [
            'IP Address',
            'IP Range'
        ]
        
        # Define row extractor function
        def extract_row(ip):
            return [
                ip.address,
                ip.ip_range.range_pattern
            ]
        
        # Create workbook
        workbook = self._create_workbook(queryset, columns, 'Free IPs', extract_row)
        
        # Create HttpResponse with Excel content type
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Set Content-Disposition header with filename
        response['Content-Disposition'] = 'attachment; filename=free_ips.xlsx'
        
        # Save workbook to response
        workbook.save(response)
        
        return response
