"""
Import service for bulk asset creation from Excel files.

This service handles parsing Excel files, validating data,
and creating assets in bulk using the existing AssetService.
"""

from typing import Dict, List, Tuple, Any
import openpyxl
from django.db import transaction
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
from datetime import datetime
from assets.models import Asset, OperatingSystem, Team, IPAddress


class ImportService:
    """Service for importing assets from Excel files."""
    
    def __init__(self):
        """Initialize the import service."""
        pass
    
    def parse_excel(self, file) -> List[Dict[str, Any]]:
        """
        Parse Excel file and extract asset data.
        
        Args:
            file: Uploaded Excel file object
            
        Returns:
            List of dictionaries containing row data
        """
        # Load the workbook (handles both .xlsx and .xls formats)
        workbook = openpyxl.load_workbook(file, data_only=True)
        sheet = workbook.active
        
        # Extract headers from the first row
        headers = []
        for cell in sheet[1]:
            headers.append(cell.value)
        
        # Extract data rows and create dictionaries
        rows = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            # Create dictionary mapping column names to values
            row_dict = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    row_dict[header] = row[i]
                else:
                    row_dict[header] = None
            rows.append(row_dict)
        
        return rows
    
    def validate_headers(self, headers: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate that required columns are present in Excel file.
        
        Args:
            headers: List of column headers from Excel file
            
        Returns:
            Tuple of (is_valid, missing_columns)
        """
        required_columns = ['asset_tag', 'system_type', 'operating_system', 'ip_address']
        missing_columns = []
        
        for required_col in required_columns:
            if required_col not in headers:
                missing_columns.append(required_col)
        
        is_valid = len(missing_columns) == 0
        return (is_valid, missing_columns)
    
    def validate_row(self, row_data: Dict[str, Any], row_number: int) -> Tuple[bool, List[str]]:
        """
        Validate a single row of asset data.
        
        Args:
            row_data: Dictionary containing asset data
            row_number: Row number in Excel file (for error reporting)
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate asset_tag is non-empty and unique
        asset_tag = row_data.get('asset_tag')
        if not asset_tag or str(asset_tag).strip() == '':
            errors.append("Asset tag is required")
        else:
            # Check uniqueness
            if Asset.objects.filter(asset_tag=asset_tag).exists():
                errors.append("Asset tag already exists")
        
        # Validate system_type is one of: Desktop, Laptop, All-in-One PC
        system_type = row_data.get('system_type')
        valid_system_types = ['Desktop', 'Laptop', 'All-in-One PC']
        if system_type not in valid_system_types:
            errors.append("Invalid system type. Must be Desktop, Laptop, or All-in-One PC")
        
        # Validate operating_system exists in database
        operating_system = row_data.get('operating_system')
        if not operating_system:
            errors.append("Operating System is required")
        else:
            if not OperatingSystem.objects.filter(name=operating_system).exists():
                errors.append("Operating System not found")
        
        # Validate ip_address is valid IPv4 and available
        ip_address = row_data.get('ip_address')
        if not ip_address:
            errors.append("IP address is required")
        else:
            # Validate IPv4 format
            try:
                validate_ipv4_address(str(ip_address))
            except ValidationError:
                errors.append("Invalid IPv4 address format")
            else:
                # Check if IP is available
                ip_obj = IPAddress.objects.filter(address=str(ip_address)).first()
                if not ip_obj:
                    errors.append("IP address not found in system")
                elif ip_obj.is_assigned:
                    errors.append("IP address not available")
        
        # Validate team exists in database if provided
        team = row_data.get('team')
        if team and str(team).strip() != '':
            if not Team.objects.filter(name=team).exists():
                errors.append("Team not found")
        
        # Validate warranty_expiration is valid date format if provided
        warranty_expiration = row_data.get('warranty_expiration')
        if warranty_expiration:
            # Handle different date formats
            if isinstance(warranty_expiration, datetime):
                # Already a datetime object (from Excel date cell)
                pass
            elif isinstance(warranty_expiration, str) and warranty_expiration.strip() != '':
                # Try to parse string date
                try:
                    datetime.strptime(warranty_expiration, '%Y-%m-%d')
                except ValueError:
                    errors.append("Invalid date format. Use YYYY-MM-DD")
        
        is_valid = len(errors) == 0
        return (is_valid, errors)
    
    def import_assets(self, file, user) -> Dict[str, Any]:
        """
        Import assets from Excel file.
        
        Args:
            file: Uploaded Excel file object
            user: User performing the import
            
        Returns:
            Dictionary containing:
                - success_count: Number of successfully imported assets
                - error_count: Number of rows with errors
                - errors: List of error details
        """
        from assets.services.asset_service import AssetService
        
        # Initialize counters and error list
        success_count = 0
        error_count = 0
        errors = []
        
        try:
            # Step 1: Parse Excel file
            rows = self.parse_excel(file)
            
            # Step 2: Validate headers
            if rows:
                headers = list(rows[0].keys())
                is_valid, missing_columns = self.validate_headers(headers)
                
                if not is_valid:
                    return {
                        'success_count': 0,
                        'error_count': 0,
                        'errors': [{
                            'row': 0,
                            'data': {},
                            'errors': [f"Missing required columns: {', '.join(missing_columns)}"]
                        }]
                    }
            else:
                # Empty file
                return {
                    'success_count': 0,
                    'error_count': 0,
                    'errors': [{
                        'row': 0,
                        'data': {},
                        'errors': ['Excel file is empty']
                    }]
                }
            
            # Step 3: Process rows with transaction
            with transaction.atomic():
                for row_number, row_data in enumerate(rows, start=2):  # Start at 2 (row 1 is headers)
                    # Skip empty rows
                    if all(value is None or str(value).strip() == '' for value in row_data.values()):
                        continue
                    
                    # Validate row
                    is_valid, validation_errors = self.validate_row(row_data, row_number)
                    
                    if not is_valid:
                        error_count += 1
                        errors.append({
                            'row': row_number,
                            'data': row_data,
                            'errors': validation_errors
                        })
                        continue
                    
                    # Prepare data for AssetService.create_asset()
                    try:
                        # Get operating system ID
                        os_obj = OperatingSystem.objects.get(name=row_data.get('operating_system'))
                        
                        # Get IP address ID
                        ip_obj = IPAddress.objects.get(address=str(row_data.get('ip_address')))
                        
                        # Get team ID if provided
                        team_id = None
                        team_name = row_data.get('team')
                        if team_name and str(team_name).strip() != '':
                            team_obj = Team.objects.get(name=team_name)
                            team_id = team_obj.id
                        
                        # Handle warranty_expiration date
                        warranty_expiration = row_data.get('warranty_expiration')
                        if warranty_expiration:
                            if isinstance(warranty_expiration, datetime):
                                warranty_expiration = warranty_expiration.date()
                            elif isinstance(warranty_expiration, str) and warranty_expiration.strip() != '':
                                warranty_expiration = datetime.strptime(warranty_expiration, '%Y-%m-%d').date()
                            else:
                                warranty_expiration = None
                        else:
                            warranty_expiration = None
                        
                        # Prepare data dict for create_asset
                        asset_data = {
                            'asset_tag': row_data.get('asset_tag'),
                            'system_type': row_data.get('system_type'),
                            'operating_system': os_obj.id,
                            'ip_address': ip_obj.id,
                            'particulars': row_data.get('particulars', ''),
                            'assigned_to': row_data.get('assigned_to', ''),
                            'team': team_id,
                            'warranty_expiration': warranty_expiration
                        }
                        
                        # Create asset using AssetService
                        AssetService.create_asset(asset_data, user)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append({
                            'row': row_number,
                            'data': row_data,
                            'errors': [str(e)]
                        })
        
        except Exception as e:
            # Handle unexpected errors during file parsing
            return {
                'success_count': 0,
                'error_count': 0,
                'errors': [{
                    'row': 0,
                    'data': {},
                    'errors': [f"Error processing file: {str(e)}"]
                }]
            }
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        }
