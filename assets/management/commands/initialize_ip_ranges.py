"""
Management command to initialize IP ranges and generate IP addresses.

This command creates the four required IP ranges (192.168.10.x, 192.168.11.x, 
192.168.70.x, 192.168.50.x) and generates all 254 IP addresses (1-254) for each range.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from assets.models import IPRange, IPAddress


class Command(BaseCommand):
    help = 'Initialize IP ranges and generate IP addresses for the asset tracking system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-initialization even if IP ranges already exist',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # Define the IP ranges to initialize
        ip_ranges_config = [
            {'range_pattern': '192.168.10.x', 'network_prefix': '192.168.10'},
            {'range_pattern': '192.168.11.x', 'network_prefix': '192.168.11'},
            {'range_pattern': '192.168.70.x', 'network_prefix': '192.168.70'},
            {'range_pattern': '192.168.50.x', 'network_prefix': '192.168.50'},
        ]
        
        # Check if IP ranges already exist
        existing_ranges = IPRange.objects.filter(
            range_pattern__in=[config['range_pattern'] for config in ip_ranges_config]
        ).count()
        
        if existing_ranges > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'IP ranges already exist ({existing_ranges} found). '
                    'Use --force to re-initialize.'
                )
            )
            return
        
        if force and existing_ranges > 0:
            self.stdout.write(
                self.style.WARNING('Force flag detected. Clearing existing IP ranges and addresses...')
            )
            # Delete existing IP addresses and ranges
            IPAddress.objects.filter(ip_range__range_pattern__in=[
                config['range_pattern'] for config in ip_ranges_config
            ]).delete()
            IPRange.objects.filter(
                range_pattern__in=[config['range_pattern'] for config in ip_ranges_config]
            ).delete()
        
        # Initialize IP ranges and addresses in a transaction
        with transaction.atomic():
            total_ips_created = 0
            
            for range_config in ip_ranges_config:
                # Create or get the IP range
                ip_range, created = IPRange.objects.get_or_create(
                    range_pattern=range_config['range_pattern'],
                    defaults={'network_prefix': range_config['network_prefix']}
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created IP range: {ip_range.range_pattern}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'IP range already exists: {ip_range.range_pattern}')
                    )
                
                # Generate IP addresses from 1 to 254
                ip_addresses_to_create = []
                for host_number in range(1, 255):  # 1-254
                    ip_address = f"{range_config['network_prefix']}.{host_number}"
                    
                    # Check if IP already exists
                    if not IPAddress.objects.filter(address=ip_address).exists():
                        ip_addresses_to_create.append(
                            IPAddress(
                                address=ip_address,
                                ip_range=ip_range,
                                is_assigned=False
                            )
                        )
                
                # Bulk create IP addresses for efficiency
                if ip_addresses_to_create:
                    IPAddress.objects.bulk_create(ip_addresses_to_create)
                    total_ips_created += len(ip_addresses_to_create)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  Created {len(ip_addresses_to_create)} IP addresses for {ip_range.range_pattern}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  No new IP addresses created for {ip_range.range_pattern} (already exist)'
                        )
                    )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nInitialization complete! Created {total_ips_created} IP addresses across '
                f'{len(ip_ranges_config)} IP ranges.'
            )
        )
        
        # Display statistics
        total_ips = IPAddress.objects.count()
        assigned_ips = IPAddress.objects.filter(is_assigned=True).count()
        free_ips = IPAddress.objects.filter(is_assigned=False).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCurrent IP statistics:\n'
                f'  Total IPs: {total_ips}\n'
                f'  Assigned IPs: {assigned_ips}\n'
                f'  Free IPs: {free_ips}'
            )
        )
