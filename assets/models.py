from django.db import models
from django.core.validators import validate_ipv4_address


class OperatingSystem(models.Model):
    """Model for storing available operating systems."""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Team(models.Model):
    """Model for storing organizational teams."""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class IPRange(models.Model):
    """Model for defining IP address ranges."""
    range_pattern = models.CharField(max_length=20, unique=True, help_text="e.g., 192.168.10.x")
    network_prefix = models.CharField(max_length=15, help_text="e.g., 192.168.10")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['range_pattern']

    def __str__(self):
        return self.range_pattern


class IPAddress(models.Model):
    """Model for tracking IP addresses and their assignment status."""
    address = models.GenericIPAddressField(protocol='IPv4', unique=True, validators=[validate_ipv4_address])
    ip_range = models.ForeignKey(IPRange, on_delete=models.CASCADE, related_name='ip_addresses')
    is_assigned = models.BooleanField(default=False, db_index=True)
    assigned_to_asset = models.ForeignKey('Asset', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_ips')

    class Meta:
        ordering = ['address']
        verbose_name_plural = 'IP Addresses'

    def __str__(self):
        return self.address


class Asset(models.Model):
    """Model for tracking IT assets throughout their lifecycle."""
    
    SYSTEM_TYPE_CHOICES = [
        ('Desktop', 'Desktop'),
        ('Laptop', 'Laptop'),
        ('All-in-One PC', 'All-in-One PC'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('freed', 'Freed'),
        ('scrapped', 'Scrapped'),
    ]
    
    serial_number = models.AutoField(primary_key=True)
    asset_tag = models.CharField(max_length=50, unique=True, db_index=True, help_text="Format: BIDC + number")
    system_type = models.CharField(max_length=20, choices=SYSTEM_TYPE_CHOICES)
    operating_system = models.ForeignKey(OperatingSystem, on_delete=models.PROTECT, related_name='assets')
    ip_address = models.ForeignKey(IPAddress, on_delete=models.SET_NULL, null=True, blank=True, related_name='asset')
    particulars = models.TextField(blank=True, null=True, help_text="Detailed information about the asset")
    assigned_to = models.CharField(max_length=100, blank=True, null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    warranty_expiration = models.DateField(null=True, blank=True, db_index=True)
    freed_date = models.DateTimeField(null=True, blank=True)
    scrapped_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['serial_number']

    def __str__(self):
        return f"{self.asset_tag} ({self.system_type})"


class Attachment(models.Model):
    """Model for storing file attachments for assets."""
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='asset_attachments/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.filename} - {self.asset.asset_tag}"
