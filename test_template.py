#!/usr/bin/env python
"""Test the template rendering."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from django.template import Context, Template
from power_monitoring.services.power_monitor_service import PowerMonitorService
from power_monitoring.models import MonitoringConfig
from django.utils import timezone

# Get online assets
online_assets = PowerMonitorService.get_online_assets(exclude_exempt=True)
config = MonitoringConfig.get_config()

print(f"online_assets type: {type(online_assets)}")
print(f"online_assets count: {online_assets.count()}")
print(f"online_assets bool: {bool(online_assets)}")
print(f"online_assets list length: {len(list(online_assets))}")

# Test the template conditional
template_str = """
{% if online_assets %}
HAS ASSETS: {{ online_assets.count }}
{% else %}
NO ASSETS
{% endif %}
"""

template = Template(template_str)
context = Context({'online_assets': online_assets})
rendered = template.render(context)

print(f"\nTemplate rendered output:")
print(rendered)
