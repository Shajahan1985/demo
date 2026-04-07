#!/usr/bin/env python
"""Check if the freed IPs are now showing as free."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from assets.models import IPAddress

# Check the specific IPs that were freed
ips_to_check = ['192.168.11.140', '192.168.11.55']

print('Checking freed IPs:')
for ip_addr in ips_to_check:
    try:
        ip = IPAddress.objects.get(address=ip_addr)
        status = 'FREE' if not ip.is_assigned else f'OCCUPIED (assigned to {ip.assigned_to_asset.asset_tag})'
        print(f'  - {ip_addr}: {status}')
    except IPAddress.DoesNotExist:
        print(f'  - {ip_addr}: Not in IP management system')

# Count total free IPs
free_count = IPAddress.objects.filter(is_assigned=False).count()
occupied_count = IPAddress.objects.filter(is_assigned=True).count()
total_count = IPAddress.objects.count()

print(f'\nIP Summary:')
print(f'  Total IPs: {total_count}')
print(f'  Free IPs: {free_count}')
print(f'  Occupied IPs: {occupied_count}')
