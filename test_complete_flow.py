#!/usr/bin/env python
"""Test the complete free and reassign flow."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from assets.models import Asset, IPAddress

print("=" * 60)
print("TESTING FREED SYSTEM IP FLOW")
print("=" * 60)

# 1. Check freed systems
print("\n1. FREED SYSTEMS:")
freed_assets = Asset.objects.filter(status='freed')
print(f"   Total freed systems: {freed_assets.count()}")

for asset in freed_assets:
    ip_info = f"IP: {asset.ip_address.address}" if asset.ip_address else "No IP"
    manual_ip_info = f"Manual IP: {asset.manual_ip}" if asset.manual_ip else ""
    print(f"   - {asset.asset_tag}: {ip_info} {manual_ip_info}")

# 2. Check if any freed system still has IP reference (should be 0)
freed_with_ip = Asset.objects.filter(status='freed', ip_address__isnull=False).count()
print(f"\n2. FREED SYSTEMS WITH IP REFERENCE: {freed_with_ip}")
if freed_with_ip > 0:
    print("   ⚠ WARNING: Some freed systems still have IP references!")
else:
    print("   ✓ GOOD: No freed systems have IP references")

# 3. Check free IPs
print("\n3. FREE IPS:")
free_ips = IPAddress.objects.filter(is_assigned=False).count()
occupied_ips = IPAddress.objects.filter(is_assigned=True).count()
print(f"   Free IPs: {free_ips}")
print(f"   Occupied IPs: {occupied_ips}")

# 4. Show some free IPs from each range
print("\n4. SAMPLE FREE IPS BY RANGE:")
from assets.services.ip_management_service import IPManagementService
ip_ranges = IPManagementService.get_all_ips_by_range()

for range_pattern, ips in ip_ranges.items():
    free_in_range = [ip for ip in ips if not ip.is_assigned and not getattr(ip, 'manual_assignment', False)]
    if free_in_range:
        print(f"   {range_pattern}: {len(free_in_range)} free IPs")
        # Show first 3 free IPs
        for ip in free_in_range[:3]:
            print(f"      - {ip.address}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
