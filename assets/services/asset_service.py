"""
Asset service for business logic related to asset operations.
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from assets.models import Asset, IPAddress
from assets.services.ip_management_service import IPManagementService


class AssetService:
    """Service class for asset management operations."""
    
    @staticmethod
    def create_asset(data, user):
        """
        Create new asset with validation and IP assignment.
        
        Args:
            data: Dictionary containing asset data (asset_tag, system_type, operating_system,
                  ip_address, particulars, assigned_to, team, warranty_expiration)
            user: User creating the asset (for audit/permission checks)
        
        Returns:
            Asset: The created asset instance
        
        Raises:
            ValidationError: If asset_tag is not unique or required fields are missing
        """
        with transaction.atomic():
            # Validate asset tag uniqueness
            asset_tag = data.get('asset_tag')
            if not AssetService.validate_asset_tag(asset_tag):
                raise ValidationError({'asset_tag': 'Asset tag already exists'})
            
            # Extract IP address if provided
            ip_address_id = data.get('ip_address')
            ip_address = None
            if ip_address_id:
                try:
                    ip_address = IPAddress.objects.get(id=ip_address_id)
                    if ip_address.is_assigned:
                        raise ValidationError({'ip_address': 'IP address already in use'})
                except IPAddress.DoesNotExist:
                    raise ValidationError({'ip_address': 'Invalid IP address'})
            
            # Create asset
            asset = Asset.objects.create(
                asset_tag=data.get('asset_tag'),
                system_type=data.get('system_type'),
                hardware_serial_number=data.get('hardware_serial_number', ''),
                manufacturer=data.get('manufacturer', ''),
                operating_system_id=data.get('operating_system'),
                manual_ip=data.get('manual_ip'),
                particulars=data.get('particulars', ''),
                assigned_to=data.get('assigned_to', ''),
                team_id=data.get('team'),
                warranty_expiration=data.get('warranty_expiration'),
                status='active'
            )
            
            # Assign IP if provided
            if ip_address:
                IPManagementService.assign_ip(ip_address, asset)
                asset.ip_address = ip_address
                asset.save()
            
            return asset
    
    @staticmethod
    def update_asset(asset, data, user):
        """
        Update asset with IP change handling.
        
        Args:
            asset: Asset instance to update
            data: Dictionary containing updated asset data
            user: User updating the asset (for audit/permission checks)
        
        Returns:
            Asset: The updated asset instance
        
        Raises:
            ValidationError: If validation fails
        """
        with transaction.atomic():
            # Check if asset tag is being changed and validate uniqueness
            new_asset_tag = data.get('asset_tag')
            if new_asset_tag and new_asset_tag != asset.asset_tag:
                if not AssetService.validate_asset_tag(new_asset_tag):
                    raise ValidationError({'asset_tag': 'Asset tag already exists'})
                asset.asset_tag = new_asset_tag
            
            # Handle IP address change (only if 'ip_address' key is present in data)
            if 'ip_address' in data:
                new_ip_address_id = data.get('ip_address')
                if new_ip_address_id:
                    try:
                        new_ip = IPAddress.objects.get(id=new_ip_address_id)
                        # Only change if different from current IP
                        if asset.ip_address != new_ip:
                            if new_ip.is_assigned and new_ip.assigned_to_asset != asset:
                                raise ValidationError({'ip_address': 'IP address already in use'})
                            IPManagementService.change_asset_ip(asset, new_ip)
                    except IPAddress.DoesNotExist:
                        raise ValidationError({'ip_address': 'Invalid IP address'})
                elif new_ip_address_id is None and asset.ip_address:
                    # IP is explicitly being cleared (switching to manual IP or no IP)
                    IPManagementService.release_ip(asset.ip_address)
                    asset.ip_address = None
            
            # Update other fields
            if 'system_type' in data:
                asset.system_type = data['system_type']
            if 'manufacturer' in data:
                asset.manufacturer = data['manufacturer']
            if 'operating_system' in data:
                asset.operating_system_id = data['operating_system']
            if 'manual_ip' in data:
                asset.manual_ip = data['manual_ip']
            if 'particulars' in data:
                asset.particulars = data['particulars']
            if 'assigned_to' in data:
                asset.assigned_to = data['assigned_to']
            if 'team' in data:
                asset.team_id = data['team']
            if 'warranty_expiration' in data:
                asset.warranty_expiration = data['warranty_expiration']
            if 'hardware_serial_number' in data:
                asset.hardware_serial_number = data['hardware_serial_number']
            
            asset.save()
            return asset
    
    @staticmethod
    def validate_asset_tag(asset_tag):
        """
        Validate asset tag uniqueness.
        
        Args:
            asset_tag: String asset tag to validate
        
        Returns:
            bool: True if asset tag is unique, False if it already exists
        """
        if not asset_tag:
            return False
        return not Asset.objects.filter(asset_tag=asset_tag).exists()
    
    @staticmethod
    def get_active_assets():
        """
        Retrieve active assets queryset.
        
        Returns:
            QuerySet: QuerySet of active assets ordered by serial_number
        """
        return Asset.objects.filter(status='active').select_related(
            'operating_system', 'ip_address', 'team'
        ).order_by('serial_number')
    
    @staticmethod
    def get_freed_assets():
        """
        Retrieve freed assets queryset.
        
        Returns:
            QuerySet: QuerySet of freed assets
        """
        return Asset.objects.filter(status='freed').select_related(
            'ip_address'
        ).order_by('-freed_date')
    
    @staticmethod
    def get_scrapped_assets():
        """
        Retrieve scrapped assets queryset.
        
        Returns:
            QuerySet: QuerySet of scrapped assets ordered by scrapped_date descending
        """
        return Asset.objects.filter(status='scrapped').select_related(
            'ip_address'
        ).order_by('-scrapped_date')
    
    @staticmethod
    def free_asset(asset, user, password):
        """
        Free an asset and release its IP address.
        
        Args:
            asset: Asset instance to free
            user: User freeing the asset (for password verification)
            password: Password to verify before freeing
        
        Returns:
            Asset: The freed asset instance
        
        Raises:
            ValidationError: If password is incorrect or asset cannot be freed
        """
        from django.contrib.auth.hashers import check_password
        from django.utils import timezone
        
        with transaction.atomic():
            # Verify user password
            if not check_password(password, user.password):
                raise ValidationError({'password': 'Incorrect password'})
            
            # Verify asset is active
            if asset.status != 'active':
                raise ValidationError({'status': 'Only active assets can be freed'})
            
            # Change status to freed
            asset.status = 'freed'
            
            # Clear assigned_to and team fields
            asset.assigned_to = None
            asset.team = None
            
            # Set freed_date to current datetime
            asset.freed_date = timezone.now()
            
            # Set health status to healthy by default
            asset.health_status = 'healthy'
            asset.issues_description = None
            
            # Release IP address if assigned and clear the reference
            if asset.ip_address:
                IPManagementService.release_ip(asset.ip_address)
                asset.ip_address = None
            
            # Clear manual IP as well
            asset.manual_ip = None
            
            asset.save()
            return asset
    
    @staticmethod
    def scrap_asset(asset, user, scrapping_reason):
        """
        Move freed asset to scrapped status.
        
        Args:
            asset: Asset instance to scrap
            user: User scrapping the asset (for audit/permission checks)
            scrapping_reason: Explanation for why the asset is being scrapped
        
        Returns:
            Asset: The scrapped asset instance
        
        Raises:
            ValidationError: If asset is not freed or scrapping_reason is empty
        """
        from django.utils import timezone
        
        with transaction.atomic():
            # Verify asset status is 'freed'
            if asset.status != 'freed':
                raise ValidationError({'status': 'Only freed assets can be scrapped'})
            
            # Validate scrapping_reason is provided and non-empty
            if not scrapping_reason or not scrapping_reason.strip():
                raise ValidationError({'scrapping_reason': 'Scrapping reason is required'})
            
            # Change asset status to 'scrapped'
            asset.status = 'scrapped'
            
            # Set scrapped_date to current datetime
            asset.scrapped_date = timezone.now()
            
            # Set scrapping_reason
            asset.scrapping_reason = scrapping_reason
            
            # Release IP address if assigned (preserve reference on asset for historical record)
            if asset.ip_address:
                IPManagementService.release_ip(asset.ip_address)
            
            asset.save()
            return asset

    @staticmethod
    def create_freed_asset(data, user):
        """
        Create a new freed system directly without requiring an active asset.
        
        Args:
            data: Dictionary containing asset fields
            user: User creating the asset
            
        Returns:
            Asset: Created asset instance
            
        Raises:
            ValidationError: If validation fails
        """
        from django.utils import timezone
        
        with transaction.atomic():
            # Validate asset_tag uniqueness
            asset_tag = data.get('asset_tag')
            if Asset.objects.filter(asset_tag=asset_tag).exists():
                raise ValidationError({'asset_tag': 'Asset tag already exists.'})
            
            # Handle IP address assignment
            ip_address_id = data.get('ip_address')
            ip_address = None
            if ip_address_id:
                try:
                    from assets.models import IPAddress
                    ip_address = IPAddress.objects.get(id=ip_address_id)
                    if ip_address.is_assigned:
                        raise ValidationError({'ip_address': 'IP address already in use'})
                except IPAddress.DoesNotExist:
                    raise ValidationError({'ip_address': 'Invalid IP address'})
            
            # Create asset with freed status
            asset = Asset.objects.create(
                asset_tag=data['asset_tag'],
                system_type=data['system_type'],
                operating_system=data['operating_system'],  # Changed from operating_system_id
                ip_address=ip_address,
                manual_ip=data.get('manual_ip'),
                manufacturer=data.get('manufacturer'),
                particulars=data.get('particulars'),
                health_status=data['health_status'],
                issues_description=data.get('issues_description'),
                status='freed',
                freed_date=timezone.now(),
                assigned_to=None,
                team=None
            )
            
            # Assign IP if provided
            if ip_address:
                IPManagementService.assign_ip(ip_address, asset)
            
            return asset
    
    @staticmethod
    def update_freed_asset(asset, data, user):
        """
        Update health status and issues for a freed system.
        
        Args:
            asset: Asset instance to update
            data: Dictionary containing updated fields
            user: User performing the update
            
        Returns:
            Asset: Updated asset instance
            
        Raises:
            ValidationError: If asset is not freed or validation fails
        """
        with transaction.atomic():
            if asset.status != 'freed':
                raise ValidationError('Only freed assets can be updated with this method.')
            
            # Update fields
            asset.health_status = data['health_status']
            asset.issues_description = data.get('issues_description')
            if 'particulars' in data:
                asset.particulars = data.get('particulars')
            
            asset.save()
            return asset
    
    @staticmethod
    def reassign_asset(asset, data, user):
        """
        Reassign freed asset to active status with new assignment details.
        
        Args:
            asset: Asset instance to reassign
            data: Dictionary containing reassignment data (assigned_to, team, ip_address_id, 
                  manual_ip, operating_system, system_type, manufacturer, particulars, 
                  warranty_expiration)
            user: User performing the reassignment
        
        Returns:
            Asset: Updated asset instance
        
        Raises:
            ValidationError: If validation fails
        """
        with transaction.atomic():
            # Validate asset status is 'freed'
            if asset.status != 'freed':
                raise ValidationError({'status': 'Only freed assets can be reassigned'})
            
            # Validate asset health_status is 'healthy'
            if asset.health_status != 'healthy':
                raise ValidationError({'health_status': 'Only healthy freed assets can be reassigned'})
            
            # Release old IP if exists
            if asset.ip_address:
                IPManagementService.release_ip(asset.ip_address)
                asset.ip_address = None
            
            # Handle new IP assignment
            ip_address_id = data.get('ip_address_id')
            manual_ip = data.get('manual_ip')
            
            if ip_address_id:
                # Dropdown IP selection
                try:
                    new_ip = IPAddress.objects.get(id=ip_address_id)
                    if new_ip.is_assigned:
                        raise ValidationError({'ip_address': 'IP address is already assigned'})
                    IPManagementService.assign_ip(new_ip, asset)
                    asset.ip_address = new_ip
                    asset.manual_ip = None
                except IPAddress.DoesNotExist:
                    raise ValidationError({'ip_address': 'Invalid IP address'})
            elif manual_ip:
                # Manual IP entry
                asset.manual_ip = manual_ip
                asset.ip_address = None
            
            # Update asset fields
            asset.status = 'active'
            asset.assigned_to = data.get('assigned_to')
            asset.team_id = data.get('team')
            asset.operating_system_id = data.get('operating_system')
            asset.system_type = data.get('system_type')
            asset.manufacturer = data.get('manufacturer', '')
            asset.particulars = data.get('particulars', '')
            asset.warranty_expiration = data.get('warranty_expiration')
            
            # Clear freed-related fields
            asset.freed_date = None
            asset.health_status = None
            asset.issues_description = None
            
            asset.save()
            return asset

