"""
Filter service for applying search criteria to asset querysets.

This service handles building filtered querysets based on user-provided
filter criteria, supporting multiple simultaneous filters.
"""

from typing import Dict, Optional
from django.db.models import QuerySet


class FilterService:
    """Service for filtering asset querysets."""
    
    def __init__(self):
        """Initialize the filter service."""
        pass
    
    def filter_by_os(self, queryset: QuerySet, os_id: int) -> QuerySet:
        """
        Filter assets by operating system.
        
        Args:
            queryset: Base QuerySet to filter
            os_id: Operating system ID
            
        Returns:
            Filtered QuerySet
        """
        return queryset.filter(operating_system_id=os_id)
    
    def filter_by_system_type(self, queryset: QuerySet, system_type: str) -> QuerySet:
        """
        Filter assets by system type.
        
        Args:
            queryset: Base QuerySet to filter
            system_type: System type string
            
        Returns:
            Filtered QuerySet
        """
        return queryset.filter(system_type=system_type)
    
    def filter_by_asset_tag(self, queryset: QuerySet, asset_tag: str) -> QuerySet:
        """
        Filter assets by BIDC number (asset tag).
        
        Args:
            queryset: Base QuerySet to filter
            asset_tag: Asset tag search string (partial match)
            
        Returns:
            Filtered QuerySet
        """
        return queryset.filter(asset_tag__icontains=asset_tag)
    
    def filter_by_team(self, queryset: QuerySet, team_id: int) -> QuerySet:
        """
        Filter assets by team.
        
        Args:
            queryset: Base QuerySet to filter
            team_id: Team ID
            
        Returns:
            Filtered QuerySet
        """
        return queryset.filter(team_id=team_id)
    
    def filter_by_assigned_user(self, queryset: QuerySet, user_name: str) -> QuerySet:
        """
        Filter assets by assigned user name.
        
        Args:
            queryset: Base QuerySet to filter
            user_name: User name search string (partial match)
            
        Returns:
            Filtered QuerySet
        """
        return queryset.filter(assigned_to__icontains=user_name)
    
    def filter_by_ip_address(self, queryset: QuerySet, ip_address: str) -> QuerySet:
        """
        Filter assets by IP address.
        
        Args:
            queryset: Base QuerySet to filter
            ip_address: IP address search string (partial match)
            
        Returns:
            Filtered QuerySet
        """
        return queryset.filter(ip_address__address__icontains=ip_address)
    
    def apply_filters(self, queryset: QuerySet, filters: Dict) -> QuerySet:
        """
        Apply multiple filters to asset queryset.
        
        Args:
            queryset: Base QuerySet to filter
            filters: Dictionary of filter parameters
            
        Returns:
            Filtered QuerySet with all filters applied
        """
        filtered_qs = queryset
        
        # Filter by operating system
        os_filter = filters.get('operating_system')
        if os_filter:
            try:
                os_id = int(os_filter)
                filtered_qs = self.filter_by_os(filtered_qs, os_id)
            except (ValueError, TypeError):
                pass
        
        # Filter by system type
        if filters.get('system_type'):
            filtered_qs = self.filter_by_system_type(filtered_qs, filters['system_type'])
        
        # Filter by asset tag (partial match)
        if filters.get('asset_tag'):
            filtered_qs = self.filter_by_asset_tag(filtered_qs, filters['asset_tag'])
        
        # Filter by team
        team_filter = filters.get('team')
        if team_filter:
            try:
                team_id = int(team_filter)
                filtered_qs = self.filter_by_team(filtered_qs, team_id)
            except (ValueError, TypeError):
                pass
        
        # Filter by assigned user (partial match)
        if filters.get('assigned_to'):
            filtered_qs = self.filter_by_assigned_user(filtered_qs, filters['assigned_to'])
        
        # Filter by IP address (partial match)
        if filters.get('ip_address'):
            filtered_qs = self.filter_by_ip_address(filtered_qs, filters['ip_address'])
        
        return filtered_qs
