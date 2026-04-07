"""
Models for power monitoring system.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from datetime import time


class PowerStatus(models.Model):
    """Tracks power status for monitored assets."""
    
    asset = models.OneToOneField(
        'assets.Asset',
        on_delete=models.CASCADE,
        related_name='power_status',
        primary_key=True
    )
    is_online = models.BooleanField(default=False, db_index=True)
    last_checked = models.DateTimeField(auto_now=True, db_index=True)
    last_status_change = models.DateTimeField(auto_now_add=True, db_index=True)
    online_since = models.DateTimeField(null=True, blank=True)
    consecutive_failures = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Power Statuses"
        indexes = [
            models.Index(fields=['is_online', 'last_checked']),
        ]
    
    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        return f"{self.asset.asset_tag} - {status}"


class SystemExemption(models.Model):
    """Tracks systems exempt from power monitoring actions."""
    
    asset = models.OneToOneField(
        'assets.Asset',
        on_delete=models.CASCADE,
        related_name='exemption',
        primary_key=True
    )
    reason = models.TextField(help_text="Justification for exemption")
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_exemptions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        verbose_name_plural = "System Exemptions"
    
    def __str__(self):
        return f"{self.asset.asset_tag} - Exempt"


class PowerAuditLog(models.Model):
    """Audit log for power monitoring actions."""
    
    ACTION_TYPES = [
        ('status_change', 'Status Change'),
        ('shutdown_attempt', 'Shutdown Attempt'),
        ('shutdown_success', 'Shutdown Success'),
        ('shutdown_failure', 'Shutdown Failure'),
        ('exemption_added', 'Exemption Added'),
        ('exemption_removed', 'Exemption Removed'),
        ('notification_sent', 'Notification Sent'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, db_index=True)
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.CASCADE,
        related_name='power_audit_logs',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='power_actions'
    )
    details = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'action_type']),
            models.Index(fields=['asset', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action_type} - {self.timestamp}"


class NotificationRecipient(models.Model):
    """Email recipients for power monitoring notifications."""
    
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['email']
    
    def __str__(self):
        return self.email


class MonitoringConfig(models.Model):
    """Singleton configuration for power monitoring system."""
    
    check_interval_minutes = models.IntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        help_text="Interval between power status checks (1-1440 minutes)"
    )
    after_hours_cutoff = models.TimeField(
        default=time(20, 30),
        help_text="Time after which systems are considered 'after hours' (default 8:30 PM)"
    )
    notification_time = models.TimeField(
        default=time(17, 30),
        help_text="Time to send daily notification email (default 5:30 PM)"
    )
    after_hours_notification_time = models.TimeField(
        default=time(20, 45),
        help_text="Time to send after-hours notification (default 8:45 PM)"
    )
    ping_timeout_seconds = models.IntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    failure_threshold = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Number of consecutive failures before marking offline"
    )
    
    class Meta:
        verbose_name_plural = "Monitoring Configurations"
    
    def save(self, *args, **kwargs):
        """Ensure only one configuration exists."""
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration."""
        config, created = cls.objects.get_or_create(pk=1)
        return config
    
    def __str__(self):
        return f"Monitoring Config (Check every {self.check_interval_minutes} min)"


class ScanConfiguration(models.Model):
    """Configuration for network range scanning."""
    
    ip_ranges = models.JSONField(
        default=list,
        help_text="List of IP ranges in CIDR notation (e.g., ['192.168.10.0/24'])"
    )
    concurrent_checks = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Number of concurrent IP checks (1-50)"
    )
    timeout_seconds = models.IntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Timeout for each IP check in seconds (1-10)"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Scan Configurations"
    
    def __str__(self):
        return f"Scan Config ({len(self.ip_ranges)} ranges)"


class ScanJob(models.Model):
    """Represents a single network scan execution."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    started_at = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_ips = models.IntegerField(default=0)
    online_count = models.IntegerField(default=0)
    offline_count = models.IntegerField(default=0)
    tracked_count = models.IntegerField(default=0)
    discovered_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-started_at']),
        ]
    
    def __str__(self):
        return f"Scan {self.id} - {self.status} ({self.online_count}/{self.total_ips} online)"


class ScanResult(models.Model):
    """Individual IP check result from a scan job."""
    
    DETECTION_METHOD_CHOICES = [
        ('icmp', 'ICMP Ping'),
        ('tcp_22', 'TCP Port 22'),
        ('tcp_80', 'TCP Port 80'),
        ('tcp_443', 'TCP Port 443'),
        ('none', 'Not Detected'),
    ]
    
    scan_job = models.ForeignKey(
        ScanJob,
        on_delete=models.CASCADE,
        related_name='results'
    )
    ip_address = models.GenericIPAddressField(protocol='IPv4', db_index=True)
    is_online = models.BooleanField(default=False, db_index=True)
    detection_method = models.CharField(
        max_length=20,
        choices=DETECTION_METHOD_CHOICES,
        default='none'
    )
    is_tracked = models.BooleanField(default=False, db_index=True)
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scan_results'
    )
    checked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['ip_address']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['is_online']),
            models.Index(fields=['is_tracked']),
            models.Index(fields=['checked_at']),
            models.Index(fields=['scan_job', 'is_online', 'is_tracked']),
        ]
    
    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        tracked = "Tracked" if self.is_tracked else "Discovered"
        return f"{self.ip_address} - {status} ({tracked})"
