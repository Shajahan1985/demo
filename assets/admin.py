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
    """Admin configuration for Team model with hierarchy support."""
    list_display = ['get_hierarchy_display', 'parent', 'sub_team_count', 'created_at']
    list_filter = ['parent', 'created_at']
    search_fields = ['name', 'parent__name']
    readonly_fields = ['created_at', 'sub_team_count']
    ordering = ['parent__name', 'name']
    
    fieldsets = (
        ('Team Information', {
            'fields': ('name', 'parent')
        }),
        ('Metadata', {
            'fields': ('created_at', 'sub_team_count'),
            'classes': ('collapse',)
        }),
    )
    
    def get_hierarchy_display(self, obj):
        """Display team name with hierarchy indication."""
        return obj.get_hierarchy_display()
    get_hierarchy_display.short_description = 'Team Name'
    
    def sub_team_count(self, obj):
        """Display count of sub-teams."""
        return obj.sub_teams.count()
    sub_team_count.short_description = 'Sub-Teams'
    
    def get_queryset(self, request):
        """Optimize queries with select_related."""
        return super().get_queryset(request).select_related('parent').prefetch_related('sub_teams')
    
    def delete_model(self, request, obj):
        """Override delete to log cascade information."""
        sub_teams = list(obj.sub_teams.all())
        if sub_teams:
            from django.contrib import messages
            sub_team_names = ', '.join([st.name for st in sub_teams])
            messages.warning(
                request,
                f"Deleting parent team '{obj.name}' will also delete {len(sub_teams)} sub-team(s): {sub_team_names}"
            )
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """Override bulk delete to log cascade information."""
        from django.contrib import messages
        total_sub_teams = 0
        for obj in queryset:
            total_sub_teams += obj.sub_teams.count()
        
        if total_sub_teams > 0:
            messages.warning(
                request,
                f"Deleting these teams will also delete {total_sub_teams} sub-team(s) due to cascade behavior."
            )
        super().delete_queryset(request, queryset)


@admin.register(IPRange)
class IPRangeAdmin(admin.ModelAdmin):
    """Admin configuration for IPRange model."""
    list_display = ['range_pattern', 'network_prefix', 'created_at']
    search_fields = ['range_pattern', 'network_prefix']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    ordering = ['range_pattern']
