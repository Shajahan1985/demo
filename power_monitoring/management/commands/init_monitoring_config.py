"""
Management command to initialize MonitoringConfig with default values.
"""
from django.core.management.base import BaseCommand
from power_monitoring.models import MonitoringConfig


class Command(BaseCommand):
    help = 'Initialize MonitoringConfig with default values if not exists'

    def handle(self, *args, **options):
        self.stdout.write('Initializing monitoring configuration...')
        
        config, created = MonitoringConfig.objects.get_or_create(pk=1)
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                '\nMonitoring configuration created successfully!'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '\nMonitoring configuration already exists.'
            ))
        
        # Display the configuration details
        self.stdout.write(
            f'\nCurrent Configuration:'
            f'\n  Check Interval: {config.check_interval_minutes} minutes'
            f'\n  After Hours Cutoff: {config.after_hours_cutoff.strftime("%I:%M %p")}'
            f'\n  Daily Notification Time: {config.notification_time.strftime("%I:%M %p")}'
            f'\n  After Hours Notification Time: {config.after_hours_notification_time.strftime("%I:%M %p")}'
            f'\n  Ping Timeout: {config.ping_timeout_seconds} seconds'
            f'\n  Failure Threshold: {config.failure_threshold} consecutive failures'
        )
