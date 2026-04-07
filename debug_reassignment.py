#!/usr/bin/env python
"""Debug the reassignment form to see what IPs are available."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from assets.models import Asset, IPAddress
from assets.forms.asset_forms import ReassignmentForm

print("=" * 60)
print("DEBUG: REASSIGNMENT FORM IP AVAILABILITY")
print("=" * 60)

# Get a freed asset
freed_asset = Asset.objects.filter(status='freed', health_status='healthy').first()

if not freed_asset:
    print("\n⚠ No healthy freed assets found!")
else:
    print(f"\nTesting with freed asset: {freed_asset.asset_tag}")
    print(f"  Status: {freed_asset.status}")
    print(f"  Health: {freed_asset.health_status}")
    print(f"  Current IP: {freed_asset.ip_address}")
    print(f"  Current Manual IP: {freed_asset.manual_ip}")
    
    # Create the form
    form = ReassignmentForm(asset=freed_asset)
    
    # Check IP dropdown options
    ip_queryset = form.fields['ip_address'].queryset
    print(f"\n📋 IP DROPDOWN OPTIONS:")
    print(f"  Total IPs available: {ip_queryset.count()}")
    
    if ip_queryset.count() > 0:
        print(f"\n  First 10 available IPs:")
        for ip in ip_queryset[:10]:
            print(f"    - {ip.address} (Range: {ip.ip_range.range_pattern})")
    else:
        print("  ⚠ NO IPs AVAILABLE IN DROPDOWN!")
    
    # Check all free IPs in database
    all_free_ips = IPAddress.objects.filter(is_assigned=False)
    print(f"\n📊 DATABASE FREE IPS:")
    print(f"  Total free IPs in database: {all_free_ips.count()}")
    
    if all_free_ips.count() > 0:
        print(f"\n  First 10 free IPs from database:")
        for ip in all_free_ips[:10]:
            print(f"    - {ip.address} (is_assigned={ip.is_assigned})")

print("\n" + "=" * 60)
