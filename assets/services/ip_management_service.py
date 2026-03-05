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
        with transaction.atomic():
            ip_address.is_assigned = False
            ip_address.assigned_to_asset = None
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
        Return dict of ranges to free IPs.
        
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
        
        return result
    
    @staticmethod
    def get_available_ips():
        """
        Return queryset of unassigned IPs.
        
        Returns:
            QuerySet: QuerySet of unassigned IPAddress instances
        """
        return IPAddress.objects.filter(is_assigned=False).select_related('ip_range')
