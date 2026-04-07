"""
Notification service for sending power monitoring emails.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from power_monitoring.models import NotificationRecipient, PowerAuditLog, MonitoringConfig
from power_monitoring.services.power_monitor_service import PowerMonitorService


class NotificationService:
    """Service for sending power monitoring notifications."""
    
    @staticmethod
    def get_active_recipients():
        """
        Get list of active notification recipient emails.
        
        Returns:
            list: Email addresses
        """
        recipients = list(
            NotificationRecipient.objects.filter(is_active=True)
            .values_list('email', flat=True)
        )
        
        # Return default recipient if list is empty
        if not recipients:
            return [getattr(settings, 'DEFAULT_NOTIFICATION_RECIPIENT', 'shajahan.t@benzyinfotech.com')]
        
        return recipients
    
    @staticmethod
    def format_notification_email(assets, is_after_hours=False):
        """
        Format notification email subject and body.
        
        Args:
            assets: Assets to include in notification
            is_after_hours: Whether this is an after-hours notification
            
        Returns:
            tuple: (subject, html_body)
        """
        config = MonitoringConfig.get_config()
        
        # Prepare asset data
        asset_data = []
        for asset in assets:
            try:
                power_status = asset.power_status
                online_duration = None
                
                if power_status.online_since:
                    duration = timezone.now() - power_status.online_since
                    hours = int(duration.total_seconds() // 3600)
                    minutes = int((duration.total_seconds() % 3600) // 60)
                    online_duration = f"{hours}h {minutes}m"
                
                asset_data.append({
                    'asset_tag': asset.asset_tag,
                    'assigned_to': asset.assigned_to or 'Unassigned',
                    'ip_address': asset.ip_address.address if asset.ip_address else 'N/A',
                    'online_duration': online_duration or 'Unknown',
                    'is_after_hours': is_after_hours
                })
            except Exception as e:
                print(f"Error processing asset {asset.asset_tag}: {e}")
                continue
        
        # Generate subject
        if is_after_hours:
            subject = f"⚠️ {len(asset_data)} System(s) Left On After {config.after_hours_cutoff.strftime('%I:%M %p')}"
        else:
            subject = f"📊 Power Monitoring Report - {len(asset_data)} System(s) Currently Online"
        
        # Generate HTML body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .after-hours {{ background-color: #ffebee !important; }}
                .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{'After-Hours ' if is_after_hours else ''}Power Monitoring Report</h2>
                <p><strong>Report Time:</strong> {timezone.now().strftime('%Y-%m-%d %I:%M %p')}</p>
                <p><strong>Systems Found:</strong> {len(asset_data)}</p>
                {f'<p><strong>After-Hours Cutoff:</strong> {config.after_hours_cutoff.strftime("%I:%M %p")}</p>' if is_after_hours else ''}
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Asset Tag</th>
                        <th>Assigned To</th>
                        <th>IP Address</th>
                        <th>Online Duration</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for asset in asset_data:
            row_class = 'after-hours' if asset['is_after_hours'] else ''
            html_body += f"""
                    <tr class="{row_class}">
                        <td>{asset['asset_tag']}</td>
                        <td>{asset['assigned_to']}</td>
                        <td>{asset['ip_address']}</td>
                        <td>{asset['online_duration']}</td>
                    </tr>
            """
        
        html_body += """
                </tbody>
            </table>
            
            <p style="margin-top: 20px; color: #666;">
                This is an automated notification from the Asset Tracker Power Monitoring System.
            </p>
        </body>
        </html>
        """
        
        return (subject, html_body)
    
    @staticmethod
    def send_daily_notification():
        """
        Send daily notification about online systems.
        
        Returns:
            bool: True if sent successfully
        """
        # Get online non-exempt assets
        assets = PowerMonitorService.get_online_assets(exclude_exempt=True)
        
        if not assets.exists():
            return True  # No assets to report
        
        try:
            recipients = NotificationService.get_active_recipients()
            subject, html_body = NotificationService.format_notification_email(assets, is_after_hours=False)
            
            send_mail(
                subject=subject,
                message='',  # Plain text version
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                html_message=html_body,
                fail_silently=False
            )
            
            # Log notification
            PowerAuditLog.objects.create(
                action_type='notification_sent',
                details={
                    'type': 'daily',
                    'recipients': recipients,
                    'asset_count': assets.count(),
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending daily notification: {e}")
            return False
    
    @staticmethod
    def send_after_hours_notification():
        """
        Send notification about after-hours systems.
        
        Returns:
            bool: True if sent successfully
        """
        # Get after-hours assets
        assets = PowerMonitorService.get_after_hours_assets()
        
        if not assets.exists():
            return True  # No assets to report
        
        try:
            recipients = NotificationService.get_active_recipients()
            subject, html_body = NotificationService.format_notification_email(assets, is_after_hours=True)
            
            send_mail(
                subject=subject,
                message='',  # Plain text version
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                html_message=html_body,
                fail_silently=False
            )
            
            # Log notification
            PowerAuditLog.objects.create(
                action_type='notification_sent',
                details={
                    'type': 'after_hours',
                    'recipients': recipients,
                    'asset_count': assets.count(),
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending after-hours notification: {e}")
            return False
