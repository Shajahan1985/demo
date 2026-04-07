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
        
        # Extract headers from the first row (normalize: lowercase, strip, spaces to underscores)
        headers = []
        for cell in sheet[1]:
            raw = cell.value
            if raw is not None:
                headers.append(str(raw).strip().lower().replace(' ', '_'))
            else:
                headers.append(None)
        
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
        required_columns = ['asset_tag', 'system_type', 'operating_system']
        missing_columns = []
        
        for required_col in required_columns:
            if required_col not in headers:
                missing_columns.append(required_col)
        
        is_valid = len(missing_columns) == 0
        return (is_valid, missing_columns)
    
    def validate_row(self, row_data: Dict[str, Any], row_number: int) -> Tuple[bool, List[str], bool]:
        """
        Validate a single row of asset data.

        Args:
            row_data: Dictionary containing asset data
            row_number: Row number in Excel file (for error reporting)

        Returns:
            Tuple of (is_valid, error_messages, is_update)
            is_update is True when the asset_tag already exists in the database.
        """
        errors = []
        is_update = False

        # Validate asset_tag is non-empty; if it exists, flag as update
        asset_tag = row_data.get('asset_tag')
        if not asset_tag or str(asset_tag).strip() == '':
            errors.append("Asset tag is required")
        else:
            if Asset.objects.filter(asset_tag=asset_tag).exists():
                is_update = True

        # Validate system_type is non-empty and one of: Desktop, Laptop, All-in-One PC
        system_type = row_data.get('system_type')
        if not system_type or str(system_type).strip() == '':
            errors.append("System type is required")
        else:
            valid_system_types = ['Desktop', 'Laptop', 'All-in-One PC']
            if system_type not in valid_system_types:
                errors.append("Invalid system type. Must be Desktop, Laptop, or All-in-One PC")

        # Validate operating_system is non-empty (will be auto-created if not in DB)
        operating_system = row_data.get('operating_system')
        if not operating_system or str(operating_system).strip() == '':
            errors.append("Operating system is required")

        # Validate ip_address if provided (ip_address is now optional)
        ip_address = row_data.get('ip_address')
        if ip_address and str(ip_address).strip() != '':
            # Validate IPv4 format
            try:
                validate_ipv4_address(str(ip_address))
            except ValidationError:
                errors.append(f"Invalid IPv4 address format: {ip_address}")
            else:
                ip_str = str(ip_address).strip()
                
                # Check if IP exists in IPAddress table
                ip_obj = IPAddress.objects.filter(address=ip_str).first()
                
                if ip_obj and ip_obj.is_assigned:
                    # IP is in the system and assigned - check if it's to the same asset
                    if is_update:
                        existing_asset = Asset.objects.filter(asset_tag=asset_tag).first()
                        if not (existing_asset and existing_asset.ip_address and existing_asset.ip_address.address == ip_str):
                            assigned_to_tag = ip_obj.assigned_to_asset.asset_tag if ip_obj.assigned_to_asset else 'unknown'
                            errors.append(f"IP {ip_str} already assigned to {assigned_to_tag}")
                    else:
                        assigned_to_tag = ip_obj.assigned_to_asset.asset_tag if ip_obj.assigned_to_asset else 'unknown'
                        errors.append(f"IP {ip_str} already assigned to {assigned_to_tag}")
                
                # Check if IP is used as manual_ip by another asset
                manual_ip_asset = Asset.objects.filter(manual_ip=ip_str).first()
                if manual_ip_asset:
                    if is_update:
                        existing_asset = Asset.objects.filter(asset_tag=asset_tag).first()
                        if not (existing_asset and existing_asset.manual_ip == ip_str):
                            errors.append(f"IP {ip_str} already used as manual IP by {manual_ip_asset.asset_tag}")
                    else:
                        errors.append(f"IP {ip_str} already used as manual IP by {manual_ip_asset.asset_tag}")

        # Validate team exists in database if provided
        team = row_data.get('team')
        if team and str(team).strip() != '':
            if not Team.objects.filter(name__iexact=str(team).strip()).exists():
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
        return (is_valid, errors, is_update)

    def import_assets(self, file, user) -> Dict[str, Any]:
        """
        Import assets from Excel file with upsert logic.
        
        Args:
            file: Uploaded Excel file object
            user: User performing the import
            
        Returns:
            Dictionary containing:
                - created_count: Number of newly created assets
                - updated_count: Number of updated existing assets
                - error_count: Number of rows with errors
                - errors: List of error details
        """
        from assets.services.asset_service import AssetService
        import logging
        logger = logging.getLogger(__name__)
        
        # Initialize counters and error list
        created_count = 0
        updated_count = 0
        error_count = 0
        errors = []
        
        try:
            # Step 1: Parse Excel file
            rows = self.parse_excel(file)
            logger.warning(f"[IMPORT DEBUG] Parsed {len(rows)} rows")
            if rows:
                logger.warning(f"[IMPORT DEBUG] Headers: {list(rows[0].keys())}")
                for i, row in enumerate(rows[:3]):
                    logger.warning(f"[IMPORT DEBUG] Row {i+2}: {row}")
            
            # Step 2: Validate headers
            if rows:
                headers = list(rows[0].keys())
                is_valid, missing_columns = self.validate_headers(headers)
                
                if not is_valid:
                    return {
                        'created_count': 0,
                        'updated_count': 0,
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
                    'created_count': 0,
                    'updated_count': 0,
                    'error_count': 0,
                    'errors': [{
                        'row': 0,
                        'data': {},
                        'errors': ['Excel file is empty']
                    }]
                }
            
            # Step 3: Process rows — each row in its own savepoint
            for row_number, row_data in enumerate(rows, start=2):  # Start at 2 (row 1 is headers)
                # Skip empty rows
                if all(value is None or str(value).strip() == '' for value in row_data.values()):
                    continue
                
                # Validate row
                is_valid, validation_errors, is_update = self.validate_row(row_data, row_number)
                
                if not is_valid:
                    error_count += 1
                    errors.append({
                        'row': row_number,
                        'data': row_data,
                        'errors': validation_errors
                    })
                    continue
                
                try:
                    with transaction.atomic():
                        # Get or create operating system (always required and validated as non-empty)
                        os_name = str(row_data.get('operating_system')).strip()
                        os_obj = OperatingSystem.objects.filter(name__iexact=os_name).first()
                        if not os_obj:
                            os_obj = OperatingSystem.objects.create(name=os_name)
                        
                        # Get IP address object if provided and non-empty
                        ip_obj = None
                        manual_ip_val = None
                        ip_address_val = row_data.get('ip_address')
                        if ip_address_val and str(ip_address_val).strip() != '':
                            ip_str = str(ip_address_val).strip()
                            ip_obj = IPAddress.objects.filter(address=ip_str).first()
                            # If IP not in system, treat as manual IP
                            if not ip_obj:
                                manual_ip_val = ip_str
                        
                        # Get team ID if provided and non-empty
                        team_id = None
                        team_name = row_data.get('team')
                        if team_name and str(team_name).strip() != '':
                            team_obj = Team.objects.get(name__iexact=str(team_name).strip())
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
                        
                        if is_update:
                            # UPDATE path: look up existing asset and build update data
                            existing_asset = Asset.objects.get(asset_tag=row_data.get('asset_tag'))
                            
                            update_data = {
                                'system_type': row_data.get('system_type'),
                                'operating_system': os_obj.id,
                            }
                            
                            # Only include ip_address if provided and non-empty
                            if ip_obj:
                                update_data['ip_address'] = ip_obj.id
                            elif manual_ip_val:
                                # Clear ip_address if switching to manual IP
                                update_data['ip_address'] = None
                            # If IP cell is empty, omit key to preserve existing IP
                            
                            # Only include manual_ip if provided
                            if manual_ip_val:
                                update_data['manual_ip'] = manual_ip_val
                            elif ip_obj:
                                # Clear manual_ip if switching to managed IP
                                update_data['manual_ip'] = None
                            
                            # Only include team if provided and non-empty
                            if team_id is not None:
                                update_data['team'] = team_id
                            # If team is empty, omit key to preserve existing
                            
                            # Only include assigned_to if provided and non-empty
                            assigned_to_val = row_data.get('assigned_to')
                            if assigned_to_val and str(assigned_to_val).strip() != '':
                                update_data['assigned_to'] = assigned_to_val
                            # If assigned_to is empty, omit key to preserve existing
                            
                            # Only include particulars if provided and non-empty
                            particulars_val = row_data.get('particulars')
                            if particulars_val and str(particulars_val).strip() != '':
                                update_data['particulars'] = particulars_val
                            
                            # Only include warranty_expiration if provided
                            if warranty_expiration is not None:
                                update_data['warranty_expiration'] = warranty_expiration
                            
                            logger.warning(f"[IMPORT DEBUG] Row {row_number} UPDATE asset_tag={row_data.get('asset_tag')} update_data={update_data}")
                            AssetService.update_asset(existing_asset, update_data, user)
                            updated_count += 1
                        else:
                            # CREATE path: create new asset with available data
                            asset_data = {
                                'asset_tag': row_data.get('asset_tag'),
                                'system_type': row_data.get('system_type'),
                                'operating_system': os_obj.id,
                                'ip_address': ip_obj.id if ip_obj else None,
                                'manual_ip': manual_ip_val,
                                'particulars': row_data.get('particulars', ''),
                                'assigned_to': row_data.get('assigned_to', ''),
                                'team': team_id,
                                'warranty_expiration': warranty_expiration
                            }
                            
                            logger.warning(f"[IMPORT DEBUG] Row {row_number} CREATE asset_data={asset_data}")
                            AssetService.create_asset(asset_data, user)
                            created_count += 1
                    
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
                'created_count': 0,
                'updated_count': 0,
                'error_count': 0,
                'errors': [{
                    'row': 0,
                    'data': {},
                    'errors': [f"Error processing file: {str(e)}"]
                }]
            }
        
        return {
            'created_count': created_count,
            'updated_count': updated_count,
            'error_count': error_count,
            'errors': errors
        }


