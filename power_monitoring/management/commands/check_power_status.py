"""
Management command to manually check power status of all assets.
"""
from django.core.management.base import BaseCommand
from power_monitoring.services import PowerMonitorService


class Command(BaseCommand):
    help = 'Check power status of all assets'

    def handle(self, *args, **options):
        self.stdout.write('Checking power status of all assets...')
        
        result = PowerMonitorService.check_all_assets()
        
        self.stdout.write(self.style.SUCCESS(
            f'\nPower check completed:'
            f'\n  Total checked: {result["total_checked"]}'
            f'\n  Online: {result["online"]}'
            f'\n  Offline: {result["offline"]}'
            f'\n  Errors: {result["errors"]}'
            f'\n  Timestamp: {result["timestamp"]}'
        ))
