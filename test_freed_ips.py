#!/usr/bin/env python
"""Test script to check freed assets with IP addresses."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from assets.models import Asset

# Check freed assets
freed = Asset.objects.filter(status='freed')
print(f'Total freed assets: {freed.count()}')

# Check freed assets with IP reference
with_ip = freed.filter(ip_address__isnull=False)
print(f'Freed assets with IP reference: {with_ip.count()}')

if with_ip.exists():
    print('\nFreed assets still holding IP references:')
    for asset in with_ip:
        ip_addr = asset.ip_address.address if asset.ip_address else 'None'
        is_assigned = asset.ip_address.is_assigned if asset.ip_address else 'N/A'
        print(f'  - {asset.asset_tag}: IP={ip_addr}, is_assigned={is_assigned}')
else:
    print('\nNo freed assets with IP references (this is correct!)')

# Check freed assets with manual IP
with_manual_ip = freed.filter(manual_ip__isnull=False)
print(f'\nFreed assets with manual IP: {with_manual_ip.count()}')
if with_manual_ip.exists():
    for asset in with_manual_ip:
        print(f'  - {asset.asset_tag}: manual_ip={asset.manual_ip}')
