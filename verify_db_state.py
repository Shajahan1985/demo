#!/usr/bin/env python
"""
Database State Verification Script
Run with: python manage.py shell < verify_db_state.py
"""

from assets.models import Asset, IPAddress, OperatingSystem, Team, IPRange

print("=" * 50)
print("DATABASE STATE VERIFICATION")
print("=" * 50)
print()

# Count assets by status
active_count = Asset.objects.filter(status='active').count()
freed_count = Asset.objects.filter(status='freed').count()
scrapped_count = Asset.objects.filter(status='scrapped').count()
total_assets = active_count + freed_count + scrapped_count

print("ASSET STATUS SUMMARY")
print("-" * 50)
print(f"Active Assets:    {active_count:>5}")
print(f"Freed Assets:     {freed_count:>5}")
print(f"Scrapped Assets:  {scrapped_count:>5}")
print(f"Total Assets:     {total_assets:>5}")
print()

# Count IPs
total_ips = IPAddress.objects.count()
assigned_ips = IPAddress.objects.filter(is_assigned=True).count()
free_ips = IPAddress.objects.filter(is_assigned=False).count()

print("IP ADDRESS SUMMARY")
print("-" * 50)
print(f"Total IPs:        {total_ips:>5}")
print(f"Assigned IPs:     {assigned_ips:>5}")
print(f"Free IPs:         {free_ips:>5}")
print()

# List IP ranges
print("IP RANGES BREAKDOWN")
print("-" * 50)
for ip_range in IPRange.objects.all():
    range_ips = IPAddress.objects.filter(ip_range=ip_range)
    free_in_range = range_ips.filter(is_assigned=False).count()
    assigned_in_range = range_ips.filter(is_assigned=True).count()
    print(f"{ip_range.range_pattern:>15}: {range_ips.count():>4} total, {assigned_in_range:>4} assigned, {free_in_range:>4} free")
print()

# Operating Systems
print("OPERATING SYSTEMS")
print("-" * 50)
os_list = OperatingSystem.objects.all()
if os_list.exists():
    for os in os_list:
        asset_count = Asset.objects.filter(operating_system=os).count()
        print(f"  • {os.name} ({asset_count} assets)")
else:
    print("  No operating systems found!")
print()

# Teams
print("TEAMS")
print("-" * 50)
team_list = Team.objects.all()
if team_list.exists():
    for team in team_list:
        asset_count = Asset.objects.filter(team=team).count()
        print(f"  • {team.name} ({asset_count} assets)")
else:
    print("  No teams found!")
print()

# Recent assets
print("RECENT ASSETS (Last 5)")
print("-" * 50)
recent_assets = Asset.objects.all().order_by('-created_at')[:5]
if recent_assets.exists():
    for asset in recent_assets:
        print(f"  • {asset.asset_tag} ({asset.status}) - {asset.system_type}")
else:
    print("  No assets found!")
print()

print("=" * 50)
print("VERIFICATION COMPLETE")
print("=" * 50)
