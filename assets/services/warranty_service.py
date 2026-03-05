"""
Warranty service for monitoring and alerting on warranty expirations.
"""
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from assets.models import Asset


class WarrantyService:
    """Service class for warranty management."""
    
    @staticmethod
    def check_expiring_warranties():
        """
        Find assets with warranties expiring within 7 days.
        
        Returns:
            QuerySet: Assets with warranties expiring within 7 days from today.
        """
        today = timezone.now().date()
        expiry_threshold = today + timedelta(days=7)
        
        return Asset.objects.filter(
            warranty_expiration__gte=today,
            warranty_expiration__lte=expiry_threshold,
            status='active'
        ).select_related('operating_system', 'team', 'ip_address')
    
    @staticmethod
    def get_warranty_status(asset):
        """
        Get the warranty status of an asset.
        
        Args:
            asset: Asset instance to check warranty status for.
        
        Returns:
            str: 'active', 'expiring_soon', or 'expired'
        """
        if not asset.warranty_expiration:
            return 'active'
        
        today = timezone.now().date()
        
        if asset.warranty_expiration < today:
            return 'expired'
        elif asset.warranty_expiration <= today + timedelta(days=7):
            return 'expiring_soon'
        else:
            return 'active'
    
    @staticmethod
    def send_warranty_alerts(assets):
        """
        Send email alerts to admin users about expiring warranties.
        
        Args:
            assets: QuerySet or list of assets with expiring warranties.
        """
        if not assets:
            return
        
        # Get all admin users
        admin_users = User.objects.filter(is_staff=True, is_active=True)
        admin_emails = [user.email for user in admin_users if user.email]
        
        if not admin_emails:
            return
        
        # Prepare asset data with days remaining
        today = timezone.now().date()
        assets_with_days = []
        for asset in assets:
            asset.days_remaining = (asset.warranty_expiration - today).days
            assets_with_days.append(asset)
        
        # Build email content
        subject = 'Asset Warranty Expiration Alert'
        
        # Render text and HTML templates
        context = {'assets': assets_with_days}
        text_content = render_to_string('assets/emails/warranty_alert.txt', context)
        html_content = render_to_string('assets/emails/warranty_alert.html', context)
        
        # Create email with both text and HTML versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_emails,
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        try:
            email.send(fail_silently=False)
        except Exception as e:
            # Log error but don't raise to prevent task failure
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send warranty alert email: {str(e)}")
