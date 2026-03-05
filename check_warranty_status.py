#!/usr/bin/env python
"""
Warranty Status Check Script
Run with: python manage.py shell < check_warranty_status.py
"""

from assets.models import Asset
from assets.services.warranty_service import WarrantyService
from django.utils import timezone

print("=" * 50)
print("WARRANTY STATUS CHECK")
print("=" * 50)
print()

# Get all assets with warranties
assets_with_warranty = Asset.objects.filter(warranty_expiration__isnull=False)
total_with_warranty = assets_with_warranty.count()

print(f"Total assets with warranty: {total_with_warranty}")
print()

if total_with_warranty == 0:
    print("No assets with warranty information found.")
    print("Create some assets with warranty dates to test this feature.")
else:
    # Check expiring soon (within 7 days)
    expiring_soon = WarrantyService.check_expiring_warranties()
    print("EXPIRING SOON (Within 7 days)")
    print("-" * 50)
    if expiring_soon.exists():
        for asset in expiring_soon:
            days_left = (asset.warranty_expiration - timezone.now().date()).days
            status = "⚠️  URGENT" if days_left <= 3 else "⚠️  Warning"
            print(f"  {status} {asset.asset_tag}: {days_left} day(s) left")
            print(f"           Expires: {asset.warranty_expiration}")
            print(f"           Assigned to: {asset.assigned_to or 'Unassigned'}")
            print()
    else:
        print("  ✓ No warranties expiring within 7 days")
    print()

    # Check expired
    today = timezone.now().date()
    expired = assets_with_warranty.filter(warranty_expiration__lt=today)
    print("EXPIRED WARRANTIES")
    print("-" * 50)
    if expired.exists():
        for asset in expired:
            days_ago = (today - asset.warranty_expiration).days
            print(f"  ❌ {asset.asset_tag}: expired {days_ago} day(s) ago")
            print(f"           Expired on: {asset.warranty_expiration}")
            print(f"           Assigned to: {asset.assigned_to or 'Unassigned'}")
            print()
    else:
        print("  ✓ No expired warranties")
    print()

    # Check active warranties (not expiring soon, not expired)
    active_warranties = assets_with_warranty.filter(
        warranty_expiration__gte=today
    ).exclude(
        pk__in=expiring_soon.values_list('pk', flat=True)
    )
    print("ACTIVE WARRANTIES (Not expiring soon)")
    print("-" * 50)
    if active_warranties.exists():
        for asset in active_warranties:
            days_left = (asset.warranty_expiration - timezone.now().date()).days
            print(f"  ✓ {asset.asset_tag}: {days_left} day(s) remaining")
            print(f"           Expires: {asset.warranty_expiration}")
            print()
    else:
        print("  No active warranties found")
    print()

    # Summary
    print("SUMMARY")
    print("-" * 50)
    print(f"Total with warranty:  {total_with_warranty}")
    print(f"Expiring soon:        {expiring_soon.count()}")
    print(f"Expired:              {expired.count()}")
    print(f"Active (safe):        {active_warranties.count()}")
    print()

print("=" * 50)
print("WARRANTY CHECK COMPLETE")
print("=" * 50)
