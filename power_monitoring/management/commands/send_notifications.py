"""
Management command to manually send power monitoring notifications.
"""
from django.core.management.base import BaseCommand
from power_monitoring.services.notification_service import NotificationService


class Command(BaseCommand):
    help = 'Send power monitoring notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--after-hours',
            action='store_true',
            help='Send after-hours notification instead of daily notification',
        )

    def handle(self, *args, **options):
        is_after_hours = options['after_hours']
        
        if is_after_hours:
            self.stdout.write('Sending after-hours notification...')
            success = NotificationService.send_after_hours_notification()
            notification_type = 'after-hours'
        else:
            self.stdout.write('Sending daily notification...')
            success = NotificationService.send_daily_notification()
            notification_type = 'daily'
        
        if success:
            self.stdout.write(self.style.SUCCESS(
                f'\n{notification_type.capitalize()} notification sent successfully!'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'\nFailed to send {notification_type} notification. Check logs for details.'
            ))
