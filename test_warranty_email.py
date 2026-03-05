#!/usr/bin/env python
"""
Test Warranty Email Alert
Run with: python manage.py shell < test_warranty_email.py
"""

from assets.tasks import run_daily_warranty_check
from assets.services.warranty_service import WarrantyService

print("=" * 50)
print("TESTING WARRANTY EMAIL ALERT")
print("=" * 50)
print()

# Check for expiring warranties first
expiring = WarrantyService.check_expiring_warranties()
print(f"Found {expiring.count()} asset(s) with warranties expiring within 7 days")
print()

if expiring.count() == 0:
    print("⚠️  No assets with expiring warranties found.")
    print("   Create an asset with warranty expiring within 7 days to test email alerts.")
    print()
else:
    print("Assets that will trigger alerts:")
    for asset in expiring:
        from django.utils import timezone
        days_left = (asset.warranty_expiration - timezone.now().date()).days
        print(f"  • {asset.asset_tag}: {days_left} day(s) left")
    print()
    
    print("Triggering warranty check task...")
    print("-" * 50)
    
    try:
        # Run the task
        run_daily_warranty_check()
        print()
        print("✓ Task executed successfully!")
        print()
        print("Check the console output above for the email content.")
        print("(Email backend is set to console in development)")
        print()
    except Exception as e:
        print(f"❌ Error running task: {str(e)}")
        print()

print("=" * 50)
print("EMAIL TEST COMPLETE")
print("=" * 50)
