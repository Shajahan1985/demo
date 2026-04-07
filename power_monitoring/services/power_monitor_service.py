"""
Power monitoring service for checking asset power status.
"""
import subprocess
import platform
import socket
from django.utils import timezone
from django.db import transaction
from power_monitoring.models import PowerStatus, PowerAuditLog, MonitoringConfig, SystemExemption
from assets.models import Asset


class PowerMonitorService:
    """Service for monitoring asset power status."""
    
    @staticmethod
    def check_tcp_port(ip_address, port, timeout=2):
        """
        Check if a TCP port is open on the target IP.
        
        Args:
            ip_address: IP address to check
            port: TCP port number
            timeout: Connection timeout in seconds
            
        Returns:
            bool: True if port is open, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip_address, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    @staticmethod
    def check_asset_status(asset):
        """
        Check if an asset is online via multiple detection methods.
        First tries ICMP ping, then falls back to TCP port checks for Linux systems.
        
        Args:
            asset: Asset to check
            
        Returns:
            bool: True if online, False if offline
        """
        if not asset.ip_address:
            return False
        
        config = MonitoringConfig.get_config()
        timeout = config.ping_timeout_seconds
        ip_addr = asset.ip_address.address
        
        # Method 1: Try ICMP ping first
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', '-w' if platform.system().lower() == 'windows' else '-W', 
                      str(timeout * 1000) if platform.system().lower() == 'windows' else str(timeout),
                      ip_addr]
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 1
            )
            
            if result.returncode == 0:
                return True
                
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            print(f"Ping error for {asset.asset_tag}: {e}")
        
        # Method 2: Fallback to TCP port checks (for Linux systems blocking ICMP)
        # Try common ports: SSH (22), HTTP (80), HTTPS (443)
        common_ports = [22, 80, 443]
        
        for port in common_ports:
            if PowerMonitorService.check_tcp_port(ip_addr, port, timeout=2):
                return True
        
        return False
    
    @staticmethod
    def update_power_status(asset, is_online):
        """
        Update power status for an asset and log changes.
        
        Args:
            asset: Asset to update
            is_online: New online status
            
        Returns:
            PowerStatus: Updated power status object
        """
        with transaction.atomic():
            # Get or create power status
            power_status, created = PowerStatus.objects.get_or_create(
                asset=asset,
                defaults={'is_online': is_online}
            )
            
            # Check if status changed
            status_changed = power_status.is_online != is_online
            
            if status_changed:
                # Update status change timestamp
                power_status.last_status_change = timezone.now()
                
                # Update online_since
                if is_online:
                    power_status.online_since = timezone.now()
                    power_status.consecutive_failures = 0
                else:
                    power_status.online_since = None
                
                # Log status change
                PowerAuditLog.objects.create(
                    action_type='status_change',
                    asset=asset,
                    details={
                        'old_status': 'online' if power_status.is_online else 'offline',
                        'new_status': 'online' if is_online else 'offline',
                        'timestamp': timezone.now().isoformat()
                    }
                )
            
            # Update status and consecutive failures
            power_status.is_online = is_online
            if not is_online and not status_changed:
                power_status.consecutive_failures += 1
            
            power_status.save()
            
            return power_status
    
    @staticmethod
    def check_all_assets():
        """
        Check power status for all active assets with IP addresses.
        
        Returns:
            dict: Summary of check results
        """
        # Get all active assets with IP addresses
        assets = Asset.objects.filter(
            status='active',
            ip_address__isnull=False
        ).select_related('ip_address')
        
        online_count = 0
        offline_count = 0
        error_count = 0
        
        for asset in assets:
            try:
                is_online = PowerMonitorService.check_asset_status(asset)
                PowerMonitorService.update_power_status(asset, is_online)
                
                if is_online:
                    online_count += 1
                else:
                    offline_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Error checking {asset.asset_tag}: {e}")
        
        return {
            'total_checked': assets.count(),
            'online': online_count,
            'offline': offline_count,
            'errors': error_count,
            'timestamp': timezone.now().isoformat()
        }
    
    @staticmethod
    def get_online_assets(exclude_exempt=True):
        """
        Get all currently online assets.
        
        Args:
            exclude_exempt: Whether to exclude exempt systems
            
        Returns:
            QuerySet: Online assets
        """
        queryset = Asset.objects.filter(
            power_status__is_online=True,
            status='active'
        ).select_related('ip_address', 'power_status')
        
        if exclude_exempt:
            queryset = queryset.exclude(
                exemption__is_active=True
            )
        
        return queryset
    
    @staticmethod
    def get_after_hours_assets():
        """
        Get assets online after the configured cutoff time.
        
        Returns:
            QuerySet: After-hours assets
        """
        from datetime import datetime
        
        config = MonitoringConfig.get_config()
        current_time = timezone.now().time()
        
        # Check if current time is after cutoff
        if current_time < config.after_hours_cutoff:
            # Not after hours yet, return empty queryset
            return Asset.objects.none()
        
        # Get online non-exempt assets
        return PowerMonitorService.get_online_assets(exclude_exempt=True)
