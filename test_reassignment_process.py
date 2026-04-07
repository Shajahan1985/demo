#!/usr/bin/env python
"""Test the actual reassignment process."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from assets.models import Asset, IPAddress, Team, OperatingSystem
from assets.services.asset_service import AssetService
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("TEST: REASSIGNMENT PROCESS")
print("=" * 60)

# Get a freed asset
freed_asset = Asset.objects.filter(status='freed', health_status='healthy').first()

if not freed_asset:
    print("\n⚠ No healthy freed assets found!")
    exit()

print(f"\n1. BEFORE REASSIGNMENT:")
print(f"   Asset: {freed_asset.asset_tag}")
print(f"   Status: {freed_asset.status}")
print(f"   Health: {freed_asset.health_status}")
print(f"   IP: {freed_asset.ip_address}")
print(f"   Manual IP: {freed_asset.manual_ip}")
print(f"   Assigned to: {freed_asset.assigned_to}")
print(f"   Team: {freed_asset.team}")

# Get a free IP
free_ip = IPAddress.objects.filter(is_assigned=False).first()
print(f"\n2. SELECTING FREE IP:")
print(f"   IP: {free_ip.address}")
print(f"   Is assigned: {free_ip.is_assigned}")

# Get a team
team = Team.objects.first()
print(f"\n3. SELECTING TEAM:")
print(f"   Team: {team.name}")

# Get an OS
os_obj = OperatingSystem.objects.first()
print(f"\n4. SELECTING OS:")
print(f"   OS: {os_obj.name}")

# Get admin user
admin_user = User.objects.filter(is_staff=True).first()

# Prepare reassignment data
data = {
    'assigned_to': 'Test User',
    'team': team.id,
    'ip_address_id': free_ip.id,
    'manual_ip': None,
    'operating_system': os_obj.id,
    'system_type': 'Desktop',
    'manufacturer': 'Dell',
    'particulars': 'Test reassignment',
    'warranty_expiration': None,
}

print(f"\n5. REASSIGNING ASSET...")
try:
    reassigned_asset = AssetService.reassign_asset(freed_asset, data, admin_user)
    
    print(f"\n6. AFTER REASSIGNMENT:")
    print(f"   Asset: {reassigned_asset.asset_tag}")
    print(f"   Status: {reassigned_asset.status}")
    print(f"   Health: {reassigned_asset.health_status}")
    print(f"   IP: {reassigned_asset.ip_address}")
    print(f"   Manual IP: {reassigned_asset.manual_ip}")
    print(f"   Assigned to: {reassigned_asset.assigned_to}")
    print(f"   Team: {reassigned_asset.team}")
    
    # Check if IP is now assigned
    free_ip.refresh_from_db()
    print(f"\n7. IP STATUS AFTER REASSIGNMENT:")
    print(f"   IP: {free_ip.address}")
    print(f"   Is assigned: {free_ip.is_assigned}")
    print(f"   Assigned to asset: {free_ip.assigned_to_asset}")
    
    print(f"\n✓ REASSIGNMENT SUCCESSFUL!")
    
except Exception as e:
    print(f"\n✗ REASSIGNMENT FAILED!")
    print(f"   Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
