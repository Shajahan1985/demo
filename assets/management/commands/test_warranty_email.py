"""
Management command to test warranty email functionality.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from assets.models import Asset, OperatingSystem, IPAddress, IPRange
from assets.services.warranty_service import WarrantyService


class Command(BaseCommand):
    help = 'Test warranty email functionality by creating test assets and sending alerts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test assets with expiring warranties',
        )

    def handle(self, *args, **options):
        if options['create_test_data']:
            self.create_test_data()
        
        # Check for expiring warranties
        self.stdout.write('Checking for expiring warranties...')
        expiring_assets = WarrantyService.check_expiring_warranties()
        
        if not expiring_assets.exists():
            self.stdout.write(self.style.WARNING('No assets with expiring warranties found.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {expiring_assets.count()} asset(s) with expiring warranties:'))
        
        for asset in expiring_assets:
            days_remaining = (asset.warranty_expiration - timezone.now().date()).days
            self.stdout.write(f'  - {asset.asset_tag} ({asset.system_type}): '
                            f'Expires {asset.warranty_expiration} ({days_remaining} days)')
        
        # Send warranty alerts
        self.stdout.write('\nSending warranty alert emails...')
        WarrantyService.send_warranty_alerts(expiring_assets)
        self.stdout.write(self.style.SUCCESS('Warranty alert emails sent successfully!'))
        self.stdout.write('\nNote: Check your email backend configuration to see the emails.')
        self.stdout.write('If using console backend, emails will be printed to the console.')
    
    def create_test_data(self):
        """Create test assets with expiring warranties."""
        self.stdout.write('Creating test data...')
        
        # Get or create OS
        os, _ = OperatingSystem.objects.get_or_create(name='Windows 10')
        
        # Get or create IP range
        ip_range, _ = IPRange.objects.get_or_create(
            range_pattern='192.168.10.x',
            defaults={'network_prefix': '192.168.10'}
        )
        
        # Create test assets with warranties expiring soon
        today = timezone.now().date()
        test_assets = [
            {
                'asset_tag': 'BIDC_TEST001',
                'system_type': 'Desktop',
                'days_until_expiry': 2,
            },
            {
                'asset_tag': 'BIDC_TEST002',
                'system_type': 'Laptop',
                'days_until_expiry': 5,
            },
            {
                'asset_tag': 'BIDC_TEST003',
                'system_type': 'All-in-One PC',
                'days_until_expiry': 7,
            },
        ]
        
        for i, asset_data in enumerate(test_assets, start=1):
            # Create IP address
            ip_address, _ = IPAddress.objects.get_or_create(
                address=f'192.168.10.{200 + i}',
                defaults={
                    'ip_range': ip_range,
                    'is_assigned': True
                }
            )
            
            # Create or update asset
            expiry_date = today + timedelta(days=asset_data['days_until_expiry'])
            asset, created = Asset.objects.update_or_create(
                asset_tag=asset_data['asset_tag'],
                defaults={
                    'system_type': asset_data['system_type'],
                    'operating_system': os,
                    'ip_address': ip_address,
                    'assigned_to': f'Test User {i}',
                    'status': 'active',
                    'warranty_expiration': expiry_date,
                }
            )
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'  {action}: {asset.asset_tag} (expires in {asset_data["days_until_expiry"]} days)')
        
        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
