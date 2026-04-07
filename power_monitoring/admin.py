"""
Django admin configuration for power monitoring.
"""
from django.contrib import admin
from .models import PowerStatus, SystemExemption, PowerAuditLog, NotificationRecipient, MonitoringConfig


@admin.register(PowerStatus)
class PowerStatusAdmin(admin.ModelAdmin):
    """Admin interface for PowerStatus."""
    list_display = ['asset', 'is_online', 'last_checked', 'online_since', 'consecutive_failures']
    list_filter = ['is_online', 'last_checked']
    search_fields = ['asset__asset_tag', 'asset__assigned_to']
    readonly_fields = ['asset', 'is_online', 'last_checked', 'last_status_change', 'online_since', 'consecutive_failures']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SystemExemption)
class SystemExemptionAdmin(admin.ModelAdmin):
    """Admin interface for SystemExemption."""
    list_display = ['asset', 'reason', 'created_by', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['asset__asset_tag', 'reason']
    readonly_fields = ['created_at']


@admin.register(PowerAuditLog)
class PowerAuditLogAdmin(admin.ModelAdmin):
    """Admin interface for PowerAuditLog."""
    list_display = ['timestamp', 'action_type', 'asset', 'user']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['asset__asset_tag', 'user__username']
    readonly_fields = ['timestamp', 'action_type', 'asset', 'user', 'details']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    """Admin interface for NotificationRecipient."""
    list_display = ['email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['email']
    readonly_fields = ['created_at']


@admin.register(MonitoringConfig)
class MonitoringConfigAdmin(admin.ModelAdmin):
    """Admin interface for MonitoringConfig."""
    list_display = ['check_interval_minutes', 'after_hours_cutoff', 'notification_time']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# Network Scanner Admin

from .models import ScanConfiguration, ScanJob, ScanResult


@admin.register(ScanConfiguration)
class ScanConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for ScanConfiguration."""
    list_display = ['id', 'is_active', 'concurrent_checks', 'timeout_seconds', 'created_at']
    list_filter = ['is_active', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('IP Ranges', {
            'fields': ('ip_ranges', 'is_active')
        }),
        ('Scan Parameters', {
            'fields': ('concurrent_checks', 'timeout_seconds')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ScanJob)
class ScanJobAdmin(admin.ModelAdmin):
    """Admin interface for ScanJob."""
    list_display = ['id', 'status', 'started_at', 'total_ips', 'online_count', 'tracked_count', 'discovered_count']
    list_filter = ['status', 'started_at']
    search_fields = ['id']
    readonly_fields = ['status', 'started_at', 'completed_at', 'total_ips', 'online_count', 
                      'offline_count', 'tracked_count', 'discovered_count', 'error_message', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    """Admin interface for ScanResult."""
    list_display = ['ip_address', 'is_online', 'is_tracked', 'asset', 'detection_method', 'checked_at']
    list_filter = ['is_online', 'is_tracked', 'detection_method', 'checked_at']
    search_fields = ['ip_address', 'asset__asset_tag']
    readonly_fields = ['scan_job', 'ip_address', 'is_online', 'detection_method', 
                      'is_tracked', 'asset', 'checked_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
