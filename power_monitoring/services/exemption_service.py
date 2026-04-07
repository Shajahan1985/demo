"""
Exemption service for managing system exemptions.
"""
from django.utils import timezone
from power_monitoring.models import SystemExemption, PowerAuditLog


class ExemptionService:
    """Service for managing system exemptions."""
    
    @staticmethod
    def create_exemption(asset, reason, user):
        """
        Create exemption for an asset.
        
        Args:
            asset: Asset to exempt
            reason: Justification for exemption
            user: User creating exemption
            
        Returns:
            SystemExemption: Created exemption
        """
        exemption, created = SystemExemption.objects.get_or_create(
            asset=asset,
            defaults={
                'reason': reason,
                'created_by': user,
                'is_active': True
            }
        )
        
        if not created:
            # Update existing exemption
            exemption.reason = reason
            exemption.created_by = user
            exemption.is_active = True
            exemption.save()
        
        # Log exemption creation
        PowerAuditLog.objects.create(
            action_type='exemption_added',
            asset=asset,
            user=user,
            details={
                'reason': reason,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        return exemption
    
    @staticmethod
    def remove_exemption(asset, user):
        """
        Remove exemption from an asset.
        
        Args:
            asset: Asset to remove exemption from
            user: User removing exemption
            
        Returns:
            bool: True if removed successfully
        """
        try:
            exemption = SystemExemption.objects.get(asset=asset)
            exemption.is_active = False
            exemption.save()
            
            # Log exemption removal
            PowerAuditLog.objects.create(
                action_type='exemption_removed',
                asset=asset,
                user=user,
                details={
                    'reason': exemption.reason,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            return True
            
        except SystemExemption.DoesNotExist:
            return False
    
    @staticmethod
    def is_exempt(asset):
        """
        Check if asset is currently exempt.
        
        Args:
            asset: Asset to check
            
        Returns:
            bool: True if exempt
        """
        try:
            exemption = SystemExemption.objects.get(asset=asset, is_active=True)
            return True
        except SystemExemption.DoesNotExist:
            return False
