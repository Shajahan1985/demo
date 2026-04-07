#!/usr/bin/env python
"""Update power status for all assets."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from power_monitoring.services.power_monitor_service import PowerMonitorService

print("Checking power status for all assets...")
print("This may take a few minutes...\n")

result = PowerMonitorService.check_all_assets()

print("=== Power Check Complete ===")
print(f"Total checked: {result['total_checked']}")
print(f"Online: {result['online']}")
print(f"Offline: {result['offline']}")
print(f"Errors: {result['errors']}")
print(f"Timestamp: {result['timestamp']}")
