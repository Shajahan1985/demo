"""
IP management service for handling IP address assignments.
"""
from django.db import transaction
from assets.models import IPAddress, Asset


class IPManagementService:
    """Service class for IP address management."""
    
    @staticmethod
    def assign_ip(ip_address, asset):
        """
        Mark IP as assigned and link to asset.
        
        Args:
            ip_address: IPAddress instance to assign
            asset: Asset instance to assign the IP to
        """
        with transaction.atomic():
            ip_address.is_assigned = True
            ip_address.assigned_to_asset = asset
            ip_address.save()
    
    @staticmethod
    def release_ip(ip_address):
        """
        Mark IP as free and clear asset link.
        
        Args:
            ip_address: IPAddress instance to release
        """
        from django.utils import timezone
        
        with transaction.atomic():
            ip_address.is_assigned = False
            ip_address.assigned_to_asset = None
            ip_address.freed_date = timezone.now()
            ip_address.save()
    
    @staticmethod
    def change_asset_ip(asset, new_ip):
        """
        Release old IP and assign new IP to asset.
        
        Args:
            asset: Asset instance to change IP for
            new_ip: IPAddress instance to assign to the asset
        """
        with transaction.atomic():
            # Release old IP if exists
            if asset.ip_address:
                IPManagementService.release_ip(asset.ip_address)
            
            # Assign new IP
            IPManagementService.assign_ip(new_ip, asset)
            
            # Update asset's IP reference
            asset.ip_address = new_ip
            asset.save()
    
    @staticmethod
    def get_free_ips_by_range():
        """
        Return dict of ranges to free IPs, sorted numerically.
        
        Returns:
            dict: Dictionary mapping IP range patterns to lists of free IP addresses
        """
        free_ips = IPAddress.objects.filter(is_assigned=False).select_related('ip_range')
        
        result = {}
        for ip in free_ips:
            range_pattern = ip.ip_range.range_pattern
            if range_pattern not in result:
                result[range_pattern] = []
            result[range_pattern].append(ip)
        
        # Sort IPs numerically within each range
        for range_pattern in result:
            result[range_pattern] = sorted(
                result[range_pattern],
                key=lambda ip: tuple(map(int, ip.address.split('.')))
            )
        
        return result
    
    @staticmethod
    def get_all_ips_by_range():
        """
        Return dict of ranges to all IPs (both free and occupied), sorted numerically.
        Includes assigned user information for occupied IPs.
        Also checks for manual IP assignments to prevent IP conflicts.
        
        Returns:
            dict: Dictionary mapping IP range patterns to lists of all IP addresses
        """
        all_ips = IPAddress.objects.all().select_related('ip_range', 'assigned_to_asset')
        
        result = {}
        for ip in all_ips:
            range_pattern = ip.ip_range.range_pattern
            if range_pattern not in result:
                result[range_pattern] = []
            
            # Check if this IP is used as a manual IP by any active asset
            manual_asset = Asset.objects.filter(
                manual_ip=ip.address,
                status='active'
            ).first()
            
            # If IP is used manually but not marked as assigned, mark it
            if manual_asset and not ip.is_assigned:
                ip.manual_assignment = True
                ip.manual_assigned_asset = manual_asset
            else:
                ip.manual_assignment = False
                ip.manual_assigned_asset = None
            
            result[range_pattern].append(ip)
        
        # Sort IPs numerically within each range
        for range_pattern in result:
            result[range_pattern] = sorted(
                result[range_pattern],
                key=lambda ip: tuple(map(int, ip.address.split('.')))
            )
        
        return result
    
    @staticmethod
    def get_available_ips():
        """
        Return queryset of unassigned IPs.
        
        Returns:
            QuerySet: QuerySet of unassigned IPAddress instances
        """
        return IPAddress.objects.filter(is_assigned=False).select_related('ip_range')
    
    @staticmethod
    def assign_ip_to_network_device(ip_address, network_device):
        """
        Assign IP address to network device.
        
        Args:
            ip_address: IPAddress instance
            network_device: NetworkDevice instance
        """
        with transaction.atomic():
            ip_address.is_assigned = True
            ip_address.assigned_to_asset = None  # Network devices don't use this field
            ip_address.save()
    
    @staticmethod
    def get_ip_occupant_info(ip_address):
        """
        Get information about what occupies an IP address.
        
        Args:
            ip_address: IPAddress instance
        
        Returns:
            dict: {'type': 'asset'|'network_device'|'free', 'name': str, 'object': Asset|NetworkDevice|None}
        """
        if hasattr(ip_address, 'network_device'):
            return {
                'type': 'network_device',
                'name': ip_address.network_device.device_name,
                'object': ip_address.network_device
            }
        elif ip_address.assigned_to_asset:
            return {
                'type': 'asset',
                'name': ip_address.assigned_to_asset.assigned_to or 'Unassigned',
                'object': ip_address.assigned_to_asset
            }
        else:
            return {
                'type': 'free',
                'name': None,
                'object': None
            }
