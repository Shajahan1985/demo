from django.db import models
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class TeamManager(models.Manager):
    """Custom manager for efficient team hierarchy queries."""
    
    def get_hierarchy(self):
        """Get all teams with parent relationships prefetched."""
        return self.select_related('parent').prefetch_related('sub_teams')
    
    def get_parent_teams(self):
        """Get only parent teams (teams without a parent)."""
        return self.filter(parent__isnull=True)
    
    def get_sub_teams(self):
        """Get only sub-teams (teams with a parent)."""
        return self.filter(parent__isnull=False)
    
    def get_hierarchical_choices(self):
        """
        Get teams formatted for dropdown display with hierarchy.
        Returns list of tuples: (id, display_name)
        """
        choices = []
        parent_teams = self.get_parent_teams().order_by('name')
        
        for parent in parent_teams:
            choices.append((parent.id, parent.name))
            sub_teams = parent.sub_teams.all().order_by('name')
            for sub in sub_teams:
                choices.append((sub.id, f"  └─ {sub.name}"))
        
        return choices


class OperatingSystem(models.Model):
    """Model for storing available operating systems."""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Team(models.Model):
    """Model for storing organizational teams with hierarchical support."""
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_teams',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TeamManager()

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['parent', 'name']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def clean(self):
        """Validate team hierarchy constraints."""
        # Prevent self-reference
        if self.parent == self:
            raise ValidationError("A team cannot be its own parent.")

        # Prevent circular references
        if self.parent and self._creates_circular_reference():
            raise ValidationError("This parent assignment would create a circular reference.")

        # Prevent depth > 2 (only parent and sub-team levels)
        if self.parent and self.parent.parent:
            raise ValidationError("Teams can only be nested 2 levels deep (parent and sub-team).")

        # Prevent converting parent with children to sub-team
        if self.parent and self.sub_teams.exists():
            raise ValidationError("Cannot assign a parent to a team that has sub-teams.")

    def _creates_circular_reference(self):
        """Check if assigning this parent would create a circular reference."""
        current = self.parent
        while current:
            if current == self:
                return True
            current = current.parent
        return False

    @property
    def is_parent(self):
        """Check if this team has sub-teams."""
        return self.sub_teams.exists()

    @property
    def hierarchy_level(self):
        """Return hierarchy level: 0 for parent, 1 for sub-team."""
        return 1 if self.parent else 0

    def get_all_sub_teams(self):
        """Get all sub-teams for this team."""
        return self.sub_teams.all()

    def get_hierarchy_display(self):
        """Get display string with hierarchy context."""
        if self.parent:
            return f"  └─ {self.name}"
        return self.name
    
    def get_asset_count(self, include_sub_teams=True):
        """
        Get count of assets assigned to this team.
        
        Args:
            include_sub_teams: If True and this is a parent team, include assets from sub-teams
        
        Returns:
            int: Total count of assets
        """
        from django.db.models import Q
        
        if include_sub_teams and self.is_parent:
            # Include assets from this team and all sub-teams
            # Query from Asset model to include both direct assignments and sub-team assignments
            return Asset.objects.filter(
                Q(team=self) | Q(team__parent=self)
            ).count()
        else:
            # Only count assets directly assigned to this team
            return self.assets.count()
    
    def get_asset_statistics(self, include_sub_teams=True):
        """
        Get detailed statistics for assets assigned to this team.
        
        Args:
            include_sub_teams: If True and this is a parent team, include assets from sub-teams
        
        Returns:
            dict: Statistics including total count, by status, by system type
        """
        from django.db.models import Q, Count
        
        if include_sub_teams and self.is_parent:
            # Include assets from this team and all sub-teams
            # Query from Asset model to include both direct assignments and sub-team assignments
            assets = Asset.objects.filter(
                Q(team=self) | Q(team__parent=self)
            )
        else:
            # Only assets directly assigned to this team
            assets = self.assets.all()
        
        return {
            'total': assets.count(),
            'by_status': dict(assets.values('status').annotate(count=Count('status')).values_list('status', 'count')),
            'by_system_type': dict(assets.values('system_type').annotate(count=Count('system_type')).values_list('system_type', 'count')),
        }




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
    hardware_serial_number = models.CharField(max_length=100, blank=True, null=True, help_text="Hardware serial number (required for Laptop and All-in-One PC)")
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


# Signal handlers for cache invalidation
@receiver(post_save, sender=Team)
def invalidate_team_hierarchy_cache_on_save(sender, instance, **kwargs):
    """Invalidate team hierarchy cache when a team is saved."""
    cache.delete('team_hierarchy')
    cache.delete(f'team_{instance.id}_hierarchy')
    if instance.parent:
        cache.delete(f'team_{instance.parent.id}_sub_teams')


@receiver(post_delete, sender=Team)
def invalidate_team_hierarchy_cache_on_delete(sender, instance, **kwargs):
    """Invalidate team hierarchy cache when a team is deleted."""
    cache.delete('team_hierarchy')
    cache.delete(f'team_{instance.id}_hierarchy')
    # Check if parent exists before accessing it (it might be deleted via CASCADE)
    try:
        if instance.parent_id:  # Use parent_id to avoid database query
            cache.delete(f'team_{instance.parent_id}_sub_teams')
    except:
        pass  # Parent might already be deleted
