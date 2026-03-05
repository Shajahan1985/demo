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
                operating_system_id=data.get('operating_system'),
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
            
            # Handle IP address change
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
                # IP is being cleared
                IPManagementService.release_ip(asset.ip_address)
                asset.ip_address = None
            
            # Update other fields
            if 'system_type' in data:
                asset.system_type = data['system_type']
            if 'operating_system' in data:
                asset.operating_system_id = data['operating_system']
            if 'particulars' in data:
                asset.particulars = data['particulars']
            if 'assigned_to' in data:
                asset.assigned_to = data['assigned_to']
            if 'team' in data:
                asset.team_id = data['team']
            if 'warranty_expiration' in data:
                asset.warranty_expiration = data['warranty_expiration']
            
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
            
            # Release IP address if assigned
            if asset.ip_address:
                IPManagementService.release_ip(asset.ip_address)
            
            asset.save()
            return asset
    
    @staticmethod
    def scrap_asset(asset, user):
        """
        Move freed asset to scrapped status.
        
        Args:
            asset: Asset instance to scrap
            user: User scrapping the asset (for audit/permission checks)
        
        Returns:
            Asset: The scrapped asset instance
        
        Raises:
            ValidationError: If asset is not freed
        """
        from django.utils import timezone
        
        with transaction.atomic():
            # Verify asset status is 'freed'
            if asset.status != 'freed':
                raise ValidationError({'status': 'Only freed assets can be scrapped'})
            
            # Change asset status to 'scrapped'
            asset.status = 'scrapped'
            
            # Set scrapped_date to current datetime
            asset.scrapped_date = timezone.now()
            
            # Retain asset_tag, IP address, and attachments (no changes needed)
            
            asset.save()
            return asset
