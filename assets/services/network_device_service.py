"""
Network device service for managing non-system network devices.
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from assets.models import NetworkDevice, IPAddress
from assets.services.ip_management_service import IPManagementService


class NetworkDeviceService:
    """Service class for network device management."""
    
    @staticmethod
    def create_network_device(data, user):
        """
        Create network device with IP assignment.
        
        Args:
            data: Dictionary with device_type, device_name, ip_address_id
            user: User creating the device
        
        Returns:
            NetworkDevice: Created device instance
        
        Raises:
            ValidationError: If IP is already assigned
        """
        with transaction.atomic():
            ip_address = IPAddress.objects.get(id=data['ip_address_id'])
            
            if ip_address.is_assigned:
                raise ValidationError({'ip_address': 'IP address already in use'})
            
            device = NetworkDevice.objects.create(
                device_type=data['device_type'],
                device_name=data['device_name'],
                ip_address=ip_address
            )
            
            # Mark IP as assigned using existing service
            IPManagementService.assign_ip_to_network_device(ip_address, device)
            
            return device
    
    @staticmethod
    def update_network_device(device, data, user):
        """
        Update network device with IP change handling.
        
        Args:
            device: NetworkDevice instance to update
            data: Dictionary with updated fields
            user: User updating the device
        
        Returns:
            NetworkDevice: Updated device instance
        
        Raises:
            ValidationError: If new IP is already assigned
        """
        with transaction.atomic():
            old_ip = device.ip_address
            new_ip_id = data.get('ip_address_id')
            
            if new_ip_id and str(old_ip.id) != str(new_ip_id):
                new_ip = IPAddress.objects.get(id=new_ip_id)
                
                if new_ip.is_assigned:
                    raise ValidationError({'ip_address': 'IP address already in use'})
                
                # Release old IP
                IPManagementService.release_ip(old_ip)
                
                # Assign new IP
                device.ip_address = new_ip
                IPManagementService.assign_ip_to_network_device(new_ip, device)
            
            # Update other fields
            device.device_type = data.get('device_type', device.device_type)
            device.device_name = data.get('device_name', device.device_name)
            device.save()
            
            return device
    
    @staticmethod
    def delete_network_device(device, user):
        """
        Delete network device and release IP.
        
        Args:
            device: NetworkDevice instance to delete
            user: User deleting the device
        """
        with transaction.atomic():
            ip_address = device.ip_address
            device.delete()
            IPManagementService.release_ip(ip_address)
