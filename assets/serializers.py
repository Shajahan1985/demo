"""
Serializers for the assets app API.
Requires Django REST Framework to be installed.
"""
from rest_framework import serializers
from assets.models import Team


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team model with hierarchy information."""
    
    parent_id = serializers.IntegerField(source='parent.id', read_only=True, allow_null=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    sub_teams = serializers.SerializerMethodField()
    is_parent = serializers.BooleanField(read_only=True)
    hierarchy_level = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Team
        fields = [
            'id', 'name', 'parent', 'parent_id', 'parent_name',
            'sub_teams', 'is_parent', 'hierarchy_level', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_sub_teams(self, obj):
        """Return list of sub-team IDs and names."""
        return [
            {'id': sub.id, 'name': sub.name}
            for sub in obj.sub_teams.all()
        ]
    
    def validate_parent(self, value):
        """Validate parent assignment."""
        if value:
            # Check for circular reference
            if value == self.instance:
                raise serializers.ValidationError("A team cannot be its own parent.")
            
            # Check depth limit
            if value.parent:
                raise serializers.ValidationError(
                    "Teams can only be nested 2 levels deep."
                )
            
            # Check if team has sub-teams
            if self.instance and self.instance.sub_teams.exists():
                raise serializers.ValidationError(
                    "Cannot assign a parent to a team that has sub-teams."
                )
        
        return value
    
    def validate(self, attrs):
        """Validate the entire team instance."""
        # For new instances, we can't call clean() until after save
        # because it might try to access related objects
        if self.instance:
            # Updating existing instance - we can validate
            instance = self.instance
            for attr, value in attrs.items():
                setattr(instance, attr, value)
            
            # Call model's clean method for validation
            try:
                instance.clean()
            except Exception as e:
                raise serializers.ValidationError(str(e))
        
        return attrs
