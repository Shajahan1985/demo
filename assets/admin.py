from django.contrib import admin
from .models import OperatingSystem, Team, IPRange


@admin.register(OperatingSystem)
class OperatingSystemAdmin(admin.ModelAdmin):
    """Admin configuration for OperatingSystem model."""
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    ordering = ['name']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Admin configuration for Team model."""
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    ordering = ['name']


@admin.register(IPRange)
class IPRangeAdmin(admin.ModelAdmin):
    """Admin configuration for IPRange model."""
    list_display = ['range_pattern', 'network_prefix', 'created_at']
    search_fields = ['range_pattern', 'network_prefix']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    ordering = ['range_pattern']
