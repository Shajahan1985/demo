"""
API views for the assets app.
Requires Django REST Framework to be installed.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from assets.models import Team
from assets.serializers import TeamSerializer


class TeamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Team model with hierarchy support.
    
    Provides standard CRUD operations plus custom endpoints for hierarchy navigation.
    """
    queryset = Team.objects.get_hierarchy()
    serializer_class = TeamSerializer
    
    def get_queryset(self):
        """Return optimized queryset with hierarchy relationships."""
        return Team.objects.get_hierarchy()
    
    def create(self, request, *args, **kwargs):
        """
        Create a new team with optional parent assignment.
        
        Request body:
        {
            "name": "Team Name",
            "parent": <parent_team_id>  # optional
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        """
        Update a team including parent assignment.
        
        Validates hierarchy constraints before saving.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a team.
        
        Due to CASCADE behavior, deleting a parent team will also delete all sub-teams.
        """
        instance = self.get_object()
        sub_teams_count = instance.sub_teams.count()
        self.perform_destroy(instance)
        
        return Response(
            {
                'message': 'Team deleted successfully',
                'sub_teams_deleted': sub_teams_count
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def sub_teams(self, request, pk=None):
        """
        Retrieve all sub-teams for a specific parent team.
        
        GET /api/teams/{id}/sub-teams/
        """
        team = self.get_object()
        sub_teams = team.get_all_sub_teams()
        serializer = self.get_serializer(sub_teams, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def parent_teams(self, request):
        """
        Retrieve all parent teams (teams without a parent).
        
        GET /api/teams/parent_teams/
        """
        parent_teams = Team.objects.get_parent_teams()
        serializer = self.get_serializer(parent_teams, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def hierarchy(self, request):
        """
        Retrieve the complete team hierarchy.
        
        GET /api/teams/hierarchy/
        
        Returns a structured representation of all teams organized by hierarchy.
        """
        parent_teams = Team.objects.get_parent_teams()
        hierarchy_data = []
        
        for parent in parent_teams:
            parent_data = self.get_serializer(parent).data
            parent_data['sub_teams_detail'] = self.get_serializer(
                parent.get_all_sub_teams(), many=True
            ).data
            hierarchy_data.append(parent_data)
        
        return Response(hierarchy_data)
