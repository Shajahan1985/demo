"""
Sync IP address assignment status with actual asset assignments.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from assets.models import IPAddress, Asset

def sync_ip_assignments():
    """Sync all IP address is_assigned flags with actual asset assignments."""
    
    print("Syncing IP address assignments...")
    
    # Get all IPs
    all_ips = IPAddress.objects.all()
    total = all_ips.count()
    updated = 0
    
    for ip in all_ips:
        # Check if this IP is assigned to any active asset
        is_actually_assigned = Asset.objects.filter(
            ip_address=ip,
            status='active'
        ).exists()
        
        # Update if mismatch
        if ip.is_assigned != is_actually_assigned:
            ip.is_assigned = is_actually_assigned
            ip.save()
            updated += 1
            status = "assigned" if is_actually_assigned else "unassigned"
            print(f"  Updated {ip.address}: marked as {status}")
    
    print(f"\nSync complete!")
    print(f"Total IPs: {total}")
    print(f"Updated: {updated}")
    print(f"Already correct: {total - updated}")

if __name__ == '__main__':
    sync_ip_assignments()
