"""
Shutdown manager service for remote system shutdowns.
"""
import subprocess
from django.db import transaction
from django.utils import timezone
from power_monitoring.models import PowerStatus, PowerAuditLog, SystemExemption


class ShutdownManagerService:
    """Service for managing remote system shutdowns."""
    
    @staticmethod
    def can_shutdown(asset, user):
        """
        Check if user can shutdown an asset.
        
        Args:
            asset: Asset to check
            user: User requesting shutdown
            
        Returns:
            tuple: (can_shutdown, reason)
        """
        # Check if user has staff permissions
        if not user.is_staff:
            return (False, "Only staff members can shutdown systems")
        
        # Check if asset is exempt
        try:
            exemption = SystemExemption.objects.get(asset=asset, is_active=True)
            return (False, f"System is exempt: {exemption.reason}")
        except SystemExemption.DoesNotExist:
            pass
        
        # Check if asset has IP address
        if not asset.ip_address:
            return (False, "Asset has no IP address configured")
        
        return (True, "Shutdown authorized")
    
    @staticmethod
    def shutdown_asset(asset, user):
        """
        Execute remote shutdown command on an asset.
        
        Args:
            asset: Asset to shutdown
            user: User requesting shutdown
            
        Returns:
            tuple: (success, message)
        """
        # Check permissions
        can_shutdown, reason = ShutdownManagerService.can_shutdown(asset, user)
        if not can_shutdown:
            # Log failed attempt
            PowerAuditLog.objects.create(
                action_type='shutdown_failure',
                asset=asset,
                user=user,
                details={
                    'reason': reason,
                    'timestamp': timezone.now().isoformat()
                }
            )
            return (False, reason)
        
        try:
            with transaction.atomic():
                # Log shutdown attempt
                PowerAuditLog.objects.create(
                    action_type='shutdown_attempt',
                    asset=asset,
                    user=user,
                    details={
                        'ip_address': asset.ip_address.address,
                        'timestamp': timezone.now().isoformat()
                    }
                )
                
                # Execute shutdown command (Windows)
                command = ['shutdown', '/s', '/m', f'\\\\{asset.ip_address.address}', '/t', '0', '/f']
                
                result = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10
                )
                
                if result.returncode == 0:
                    # Update power status to offline
                    try:
                        power_status = PowerStatus.objects.get(asset=asset)
                        power_status.is_online = False
                        power_status.online_since = None
                        power_status.save()
                    except PowerStatus.DoesNotExist:
                        pass
                    
                    # Log success
                    PowerAuditLog.objects.create(
                        action_type='shutdown_success',
                        asset=asset,
                        user=user,
                        details={
                            'ip_address': asset.ip_address.address,
                            'timestamp': timezone.now().isoformat()
                        }
                    )
                    
                    return (True, f"Shutdown command sent successfully to {asset.ip_address.address}")
                else:
                    error_msg = result.stderr.decode('utf-8', errors='ignore').strip()
                    stdout_msg = result.stdout.decode('utf-8', errors='ignore').strip()
                    
                    # Provide helpful error messages
                    if 'Access is denied' in error_msg or 'Access is denied' in stdout_msg:
                        helpful_msg = f"Access Denied to {asset.ip_address.address}. You need administrator privileges on the target computer. Check: 1) Your Windows account has admin rights on target PC, 2) Remote Registry service is running on target PC, 3) Windows Firewall allows remote shutdown."
                    elif 'network path was not found' in error_msg.lower() or 'network path was not found' in stdout_msg.lower():
                        helpful_msg = f"Cannot reach {asset.ip_address.address}. The computer may be offline or network path is blocked."
                    else:
                        helpful_msg = f"Shutdown failed for {asset.ip_address.address}: {error_msg or stdout_msg or 'Unknown error'}"
                    
                    # Log failure
                    PowerAuditLog.objects.create(
                        action_type='shutdown_failure',
                        asset=asset,
                        user=user,
                        details={
                            'reason': helpful_msg,
                            'error_output': error_msg,
                            'stdout_output': stdout_msg,
                            'return_code': result.returncode,
                            'timestamp': timezone.now().isoformat()
                        }
                    )
                    
                    return (False, helpful_msg)
                    
        except subprocess.TimeoutExpired:
            PowerAuditLog.objects.create(
                action_type='shutdown_failure',
                asset=asset,
                user=user,
                details={
                    'reason': 'Command timeout',
                    'timestamp': timezone.now().isoformat()
                }
            )
            return (False, "Shutdown command timed out")
            
        except Exception as e:
            PowerAuditLog.objects.create(
                action_type='shutdown_failure',
                asset=asset,
                user=user,
                details={
                    'reason': str(e),
                    'timestamp': timezone.now().isoformat()
                }
            )
            return (False, f"Error: {str(e)}")
    
    @staticmethod
    def bulk_shutdown(assets, user):
        """
        Shutdown multiple assets.
        
        Args:
            assets: List of assets to shutdown
            user: User requesting shutdown
            
        Returns:
            dict: Summary of shutdown results
        """
        success_count = 0
        failure_count = 0
        results = []
        
        for asset in assets:
            success, message = ShutdownManagerService.shutdown_asset(asset, user)
            
            results.append({
                'asset_tag': asset.asset_tag,
                'success': success,
                'message': message
            })
            
            if success:
                success_count += 1
            else:
                failure_count += 1
        
        return {
            'total': len(assets),
            'success': success_count,
            'failure': failure_count,
            'results': results
        }
