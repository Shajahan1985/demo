#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from assets.models import OperatingSystem

# Add Windows 11
os_obj, created = OperatingSystem.objects.get_or_create(name='Windows 11')
if created:
    print("Windows 11 added successfully!")
else:
    print("Windows 11 already exists.")
