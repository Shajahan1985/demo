#!/usr/bin/env python
"""Quick script to check power monitoring data."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from power_monitoring.services.power_monitor_service import PowerMonitorService
from power_monitoring.models import PowerStatus
from assets.models import Asset

print("=== Power Monitoring Debug ===\n")

# Check PowerStatus records
total_status = PowerStatus.objects.count()
online_status = PowerStatus.objects.filter(is_online=True).count()
print(f"Total PowerStatus records: {total_status}")
print(f"Online PowerStatus records: {online_status}\n")

# Check active assets with IPs
active_with_ip = Asset.objects.filter(status='active', ip_address__isnull=False).count()
print(f"Active assets with IP addresses: {active_with_ip}\n")

# Check what get_online_assets returns
online_assets = PowerMonitorService.get_online_assets(exclude_exempt=True)
print(f"get_online_assets() count: {online_assets.count()}")

if online_assets.count() > 0:
    print("\nFirst 5 online assets:")
    for asset in online_assets[:5]:
        ip = asset.ip_address.address if asset.ip_address else "No IP"
        print(f"  - {asset.asset_tag}: {ip}")
else:
    print("\nNo online assets returned by get_online_assets()")
    print("\nChecking why...")
    
    # Check if there are assets with power_status
    assets_with_status = Asset.objects.filter(
        status='active',
        power_status__isnull=False
    ).count()
    print(f"Active assets with power_status relation: {assets_with_status}")
    
    # Check if there are online power statuses
    online_statuses = PowerStatus.objects.filter(is_online=True)
    print(f"\nOnline PowerStatus records: {online_statuses.count()}")
    
    if online_statuses.count() > 0:
        print("Sample online PowerStatus records:")
        for ps in online_statuses[:5]:
            print(f"  - Asset: {ps.asset.asset_tag}, Online: {ps.is_online}")
