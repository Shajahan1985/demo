#!/usr/bin/env python
"""Debug the power monitoring view context."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from power_monitoring.views import power_report_view

# Create a test request
factory = RequestFactory()
request = factory.get('/power-monitoring/report/')

# Get a user
user = User.objects.filter(is_staff=True).first()
request.user = user

# Call the view
response = power_report_view(request)

print("=== View Context Debug ===\n")
print(f"Response status: {response.status_code}")

if hasattr(response, 'context_data'):
    context = response.context_data
    print(f"\nContext keys: {list(context.keys())}")
    print(f"online_assets type: {type(context.get('online_assets'))}")
    print(f"online_assets count: {context.get('online_assets').count() if context.get('online_assets') else 'None'}")
else:
    print("\nNo context_data attribute - checking rendered content")
    content = response.content.decode('utf-8')
    
    # Check if the table is in the HTML
    if 'All Online Systems' in content:
        print("✓ 'All Online Systems' header found in HTML")
    else:
        print("✗ 'All Online Systems' header NOT found in HTML")
    
    if 'No systems currently online' in content:
        print("✓ 'No systems currently online' message found in HTML")
    else:
        print("✗ 'No systems currently online' message NOT found in HTML")
    
    # Count table rows
    import re
    rows = re.findall(r'<tr>', content)
    print(f"\nTotal <tr> tags in HTML: {len(rows)}")
