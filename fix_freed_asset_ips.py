#!/usr/bin/env python
"""Fix freed assets that still have IP address references."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from assets.models import Asset

# Find freed assets with IP references
freed_with_ips = Asset.objects.filter(status='freed', ip_address__isnull=False)

print(f'Found {freed_with_ips.count()} freed assets with IP references')

if freed_with_ips.exists():
    print('\nClearing IP references from freed assets:')
    for asset in freed_with_ips:
        ip_addr = asset.ip_address.address if asset.ip_address else 'None'
        print(f'  - {asset.asset_tag}: Clearing IP {ip_addr}')
        asset.ip_address = None
        asset.save()
    
    print(f'\n✓ Fixed {freed_with_ips.count()} freed assets')
else:
    print('\n✓ No freed assets with IP references found')

print('\nVerifying fix...')
remaining = Asset.objects.filter(status='freed', ip_address__isnull=False).count()
print(f'Freed assets with IP references: {remaining}')

if remaining == 0:
    print('✓ All freed assets have been fixed!')
else:
    print(f'⚠ Warning: {remaining} freed assets still have IP references')
