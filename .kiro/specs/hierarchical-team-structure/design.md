# Design Document: Hierarchical Team Structure

## Overview

This design implements a hierarchical team structure for the Asset Tracking System, transforming the current flat team model into a two-level parent-child hierarchy. The implementation maintains full backward compatibility with existing asset assignments while enabling organizational teams to be grouped under parent teams.

The design follows Django best practices for self-referential foreign keys, implements efficient query patterns using select_related/prefetch_related, and provides comprehensive validation to prevent circular references and maintain data integrity. The solution includes database migrations with rollback capability, updated admin interfaces with hierarchy visualization, and API endpoints that expose the team structure.

Key design principles:
- Backward compatibility: All existing asset-team assignments remain valid
- Data integrity: Comprehensive validation prevents invalid hierarchies
- Performance: Optimized queries minimize database hits
- User experience: Clear visual hierarchy in dropdowns and admin interfaces
- Safety: Transactional migrations with rollback support

## Architecture

### System Components

The hierarchical team structure touches several layers of the Django application:

1. **Data Layer (models.py)**
   - Modified Team model with self-referential parent field
   - Model-level validation methods for hierarchy constraints
   - Custom managers for efficient hierarchy queries
   - Database indexes for performance optimization

2. **Migration Layer (migrations/)**
   - Schema migration adding parent field to Team model
   - Data migration pre-populating team hierarchy
   - Reverse migration for rollback capability
   - Transaction management for data safety

3. **Admin Layer (admin.py)**
   - Enhanced TeamAdmin with hierarchy display
   - Custom list display showing parent-child relationships
   - Inline editing for sub-teams
   - Filtering by hierarchy level

4. **Form Layer (forms/)**
   - Custom ModelChoiceField for hierarchical team dropdown
   - Indented display of sub-teams under parents
   - Validation integration with model constraints

5. **API Layer (serializers + views)**
   - Team serializers with parent/children relationships
   - Endpoints for hierarchy traversal
   - Validation error handling

6. **View Layer (views.py)**
   - Updated asset views using hierarchical team queries
   - Team filtering with parent/child context
   - Statistics aggregation including sub-teams

### Data Flow

**Team Creation Flow:**
```
User Input → Form Validation → Model Validation → Database Save → Cache Invalidation
```

**Team Selection Flow:**
```
Form Render → Query Teams (prefetch hierarchy) → Build Hierarchical Choices → Display with Indentation
```

**Asset Assignment Flow:**
```
Select Team → Validate Team Exists → Save Asset → Update Related Queries
```

### Integration Points

- **Asset Model**: ForeignKey to Team remains unchanged, accepts any team (parent or sub-team)
- **Forms**: All forms with team selection use the new hierarchical dropdown
- **Admin**: Team admin shows hierarchy, asset admin uses hierarchical team selector
- **API**: Team endpoints include hierarchy information in responses
- **Views**: Asset list/detail views display team with hierarchy context

## Components and Interfaces

### Team Model Enhancement

```python
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
```

### Custom Team Manager

```python
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
```

### Hierarchical Team Form Field

```python
class HierarchicalTeamChoiceField(forms.ModelChoiceField):
    """Custom form field for displaying teams hierarchically."""
    
    def __init__(self, *args, **kwargs):
        kwargs['queryset'] = Team.objects.get_hierarchy()
        super().__init__(*args, **kwargs)
    
    def label_from_instance(self, obj):
        """Return label with hierarchy indentation."""
        if obj.parent:
            return f"  └─ {obj.name}"
        return obj.name
```

### Updated AssetForm

```python
class AssetForm(forms.ModelForm):
    """Form for creating and updating assets with hierarchical team selection."""
    
    team = HierarchicalTeamChoiceField(
        required=False,
        empty_label="Select Team",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Asset
        fields = [
            'asset_tag', 'system_type', 'operating_system',
            'ip_address', 'particulars', 'assigned_to',
            'team', 'warranty_expiration'
        ]
```

### Enhanced Team Admin

```python
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
```

### Team API Serializer

```python
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
            'id', 'name', 'parent_id', 'parent_name',
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
```

## Data Models

### Team Model Schema

**Table: assets_team**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique team identifier |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Team name |
| parent_id | INTEGER | FOREIGN KEY (assets_team.id), NULL, INDEX | Reference to parent team |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | Creation timestamp |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `name`
- INDEX on `parent_id`
- COMPOSITE INDEX on `(parent_id, name)` for efficient hierarchy queries

**Foreign Key Constraints:**
- `parent_id` REFERENCES `assets_team(id)` ON DELETE CASCADE

### Relationships

**Team → Team (Self-Referential)**
- Type: One-to-Many (parent to sub-teams)
- Field: `parent` (ForeignKey)
- Related Name: `sub_teams`
- On Delete: CASCADE (when parent deleted, sub-teams are also deleted)
- Null: True (parent teams have no parent)

**Asset → Team (Unchanged)**
- Type: Many-to-One
- Field: `team` (ForeignKey)
- Related Name: `assets`
- On Delete: SET_NULL
- Null: True (assets can have no team)

### Data Constraints

1. **Uniqueness**: Team names must be unique across all teams
2. **Hierarchy Depth**: Maximum 2 levels (parent and sub-team)
3. **No Circular References**: A team cannot be its own ancestor
4. **No Self-Reference**: A team cannot be its own parent
5. **Parent Constraint**: Teams with sub-teams cannot become sub-teams themselves

### Pre-populated Data Structure

```
Marketing (parent)
Developers (parent)
  ├─ Bethovans Team
  ├─ QC Team
  ├─ App Team
  ├─ Hotel Team
  ├─ Suma Team
  ├─ Iboss Team
  ├─ Robin Team
  ├─ Jojo Team
  ├─ Sandeep Team
  ├─ Dulfi Team
  ├─ Design Team
  ├─ Justine MJ Team
  ├─ Jinson Team
  ├─ Jerly Team
  ├─ DBA Team
  ├─ JOJO Team
  ├─ BA Team
  ├─ Adhun Team
  └─ Aymen Team
Data Center Team (parent)
Accounts Team (parent)
Iboss Support Team (parent)
Not Applicable (special option)
```

### Migration Strategy

**Migration 1: Add parent field**
```python
operations = [
    migrations.AddField(
        model_name='team',
        name='parent',
        field=models.ForeignKey(
            blank=True,
            null=True,
            on_delete=django.db.models.deletion.CASCADE,
            related_name='sub_teams',
            to='assets.team'
        ),
    ),
    migrations.AddIndex(
        model_name='team',
        index=models.Index(fields=['parent', 'name'], name='assets_team_parent_name_idx'),
    ),
]
```

**Migration 2: Populate team hierarchy**
```python
def populate_teams(apps, schema_editor):
    Team = apps.get_model('assets', 'Team')
    
    # Create or update parent teams
    parent_teams = {
        'Marketing': Team.objects.get_or_create(name='Marketing')[0],
        'Developers': Team.objects.get_or_create(name='Developers')[0],
        'Data Center Team': Team.objects.get_or_create(name='Data Center Team')[0],
        'Accounts Team': Team.objects.get_or_create(name='Accounts Team')[0],
        'Iboss Support Team': Team.objects.get_or_create(name='Iboss Support Team')[0],
    }
    
    # Create Not Applicable option
    Team.objects.get_or_create(name='Not Applicable')
    
    # Create sub-teams under Developers
    developers_parent = parent_teams['Developers']
    sub_team_names = [
        'Bethovans Team', 'QC Team', 'App Team', 'Hotel Team',
        'Suma Team', 'Iboss Team', 'Robin Team', 'Jojo Team',
        'Sandeep Team', 'Dulfi Team', 'Design Team', 'Justine MJ Team',
        'Jinson Team', 'Jerly Team', 'DBA Team', 'JOJO Team',
        'BA Team', 'Adhun Team', 'Aymen Team'
    ]
    
    for name in sub_team_names:
        team, created = Team.objects.get_or_create(name=name)
        if created or not team.parent:
            team.parent = developers_parent
            team.save()

def reverse_populate_teams(apps, schema_editor):
    Team = apps.get_model('assets', 'Team')
    # Clear parent relationships but preserve teams
    Team.objects.all().update(parent=None)

operations = [
    migrations.RunPython(populate_teams, reverse_populate_teams),
]
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Circular Reference Prevention

*For any* team and any proposed parent assignment, if the assignment would create a circular reference (including self-reference or assignment to a descendant), then the validation should fail with a descriptive error message.

**Validates: Requirements 1.4, 4.5, 9.1, 9.2, 9.3, 10.6**

### Property 2: Hierarchy Depth Limitation

*For any* team, if it has a parent that already has a parent, then validation should fail, ensuring the hierarchy never exceeds 2 levels.

**Validates: Requirements 9.4**

### Property 3: Parent Team Constraint

*For any* team that has sub-teams, attempting to assign it a parent should fail validation, preventing parent teams from becoming sub-teams.

**Validates: Requirements 9.5**

### Property 4: Team Classification by Hierarchy Level

*For any* team, its hierarchy_level property should return 0 if it has no parent (parent team) and 1 if it has a parent (sub-team).

**Validates: Requirements 1.2, 1.3**

### Property 5: Multiple Sub-Teams Support

*For any* parent team, it should be possible to create and associate multiple sub-teams, and all sub-teams should be retrievable via the sub_teams relationship.

**Validates: Requirements 1.6**

### Property 6: Parent Deletion Cascades to Sub-Teams

*For any* parent team with sub-teams, deleting the parent team should also delete all associated sub-teams due to CASCADE behavior.

**Validates: Requirements 1.7**

### Property 7: Team Deletion Sets Asset Team to Null

*For any* team assigned to one or more assets, deleting the team should set the team field to None for all associated assets due to SET_NULL behavior.

**Validates: Requirements 5.6**

### Property 8: Hierarchical Dropdown Ordering

*For any* set of teams, the hierarchical choices should list parent teams in alphabetical order, with each parent's sub-teams listed immediately after in alphabetical order.

**Validates: Requirements 2.1, 2.5, 2.6**

### Property 9: Sub-Team Display Indentation

*For any* sub-team, its display representation in dropdowns and lists should include visual indentation markers (such as "└─") to indicate hierarchy level.

**Validates: Requirements 2.2, 2.7**

### Property 10: Both Parent and Sub-Team Selection Allowed

*For any* team (whether parent or sub-team), it should be a valid choice in team selection forms and dropdowns.

**Validates: Requirements 2.3**

### Property 11: Asset Team Assignment Flexibility

*For any* asset and any team (parent or sub-team), assigning or updating the asset's team field to that team should succeed.

**Validates: Requirements 5.2, 5.5**

### Property 12: Asset Team Display

*For any* asset with an assigned team, the display representation should show the team name, and for sub-teams, should include hierarchy context.

**Validates: Requirements 5.4, 6.3**

### Property 13: Team Filter Inclusivity

*For any* team, filtering assets by that team should return all assets directly assigned to that team.

**Validates: Requirements 6.5**

### Property 14: Parent Team Statistics Aggregation

*For any* parent team, statistics should aggregate data from all assets assigned to the parent team and all its sub-teams.

**Validates: Requirements 6.6**

### Property 15: Form Team Validation

*For any* team selection form, submitting an invalid team ID (non-existent team) should fail validation with an appropriate error.

**Validates: Requirements 6.2**

### Property 16: Migration Data Preservation

*For any* existing teams and asset-team assignments before migration, after running the migration forward and optionally backward, all team names and asset assignments should be preserved.

**Validates: Requirements 3.8, 5.3, 7.6**

### Property 17: Migration Idempotency

*For any* state of the database, running the team hierarchy migration multiple times should not create duplicate teams; existing teams with matching names should be updated rather than duplicated.

**Validates: Requirements 3.9**

### Property 18: Migration Rollback on Error

*For any* migration execution that encounters an error, all changes should be rolled back, leaving the database in its pre-migration state.

**Validates: Requirements 7.3**

### Property 19: Migration Reversibility

*For any* database state, running the migration forward then backward should restore the original flat team structure while preserving team names.

**Validates: Requirements 7.5**

### Property 20: Cache Invalidation on Hierarchy Change

*For any* cached team hierarchy data, when a team's parent assignment is modified, the cached data should be invalidated and refreshed on next access.

**Validates: Requirements 8.6**

### Property 21: Team Queryset Filtering

*For any* queryset filter (parent teams only or sub-teams only), the results should contain only teams matching the filter criteria.

**Validates: Requirements 4.7**

### Property 22: API Sub-Team Serialization

*For any* sub-team serialized via the API, the response should include the parent_id and parent_name fields with non-null values.

**Validates: Requirements 10.1**

### Property 23: API Parent Team Serialization

*For any* parent team serialized via the API, the response should include a sub_teams list containing all associated sub-team IDs and names.

**Validates: Requirements 10.2**

### Property 24: API Sub-Team Retrieval

*For any* parent team, the API endpoint for retrieving sub-teams should return all and only the sub-teams associated with that parent.

**Validates: Requirements 10.4**

### Property 25: API Validation Error Responses

*For any* API request that violates hierarchy constraints, the response should have a 400 status code and include a descriptive error message.

**Validates: Requirements 10.7**


## Error Handling

### Validation Errors

**Circular Reference Detection**
- Error Type: `ValidationError`
- Message: "This parent assignment would create a circular reference."
- Trigger: Attempting to set a team's parent to itself or one of its descendants
- Handling: Raised during model clean() method, caught by forms and API serializers
- User Impact: Form displays error, API returns 400 with error details

**Self-Reference Prevention**
- Error Type: `ValidationError`
- Message: "A team cannot be its own parent."
- Trigger: Attempting to set parent = self
- Handling: Raised during model clean() method
- User Impact: Form displays error, API returns 400

**Hierarchy Depth Violation**
- Error Type: `ValidationError`
- Message: "Teams can only be nested 2 levels deep (parent and sub-team)."
- Trigger: Attempting to create a sub-team under another sub-team
- Handling: Raised during model clean() method
- User Impact: Form displays error, API returns 400

**Parent Team Constraint Violation**
- Error Type: `ValidationError`
- Message: "Cannot assign a parent to a team that has sub-teams."
- Trigger: Attempting to make a parent team into a sub-team
- Handling: Raised during model clean() method
- User Impact: Form displays error, API returns 400

**Duplicate Team Name**
- Error Type: `IntegrityError`
- Message: "Team with this name already exists."
- Trigger: Attempting to create a team with a non-unique name
- Handling: Database constraint, caught by Django and converted to form error
- User Impact: Form displays uniqueness error

### Migration Errors

**Migration Rollback**
- Error Type: Various (database errors, integrity errors)
- Handling: All migrations run within transactions; any error triggers automatic rollback
- Logging: All errors logged with full traceback
- User Impact: Migration fails cleanly, database remains in pre-migration state
- Recovery: Fix underlying issue and re-run migration

**Data Integrity Violations**
- Error Type: `IntegrityError`
- Trigger: Existing data conflicts with new constraints
- Handling: Pre-migration validation checks for conflicts
- User Impact: Migration fails with descriptive error about conflicting data
- Recovery: Manually resolve data conflicts, then re-run migration

### API Errors

**Invalid Team ID**
- Status Code: 404
- Response: `{"detail": "Team not found."}`
- Trigger: Requesting a non-existent team
- Handling: Django REST Framework default 404 handling

**Hierarchy Validation Failure**
- Status Code: 400
- Response: `{"parent": ["This parent assignment would create a circular reference."]}`
- Trigger: API request violating hierarchy constraints
- Handling: Serializer validation, returns field-specific errors

**Missing Required Fields**
- Status Code: 400
- Response: `{"name": ["This field is required."]}`
- Trigger: Creating team without required fields
- Handling: Serializer validation

**Permission Denied**
- Status Code: 403
- Response: `{"detail": "You do not have permission to perform this action."}`
- Trigger: Non-admin user attempting to modify teams
- Handling: Django REST Framework permission classes

### Database Errors

**Foreign Key Constraint Violation**
- Error Type: `IntegrityError`
- Trigger: Attempting to assign non-existent parent_id
- Handling: Database constraint, caught and converted to validation error
- User Impact: Form displays error about invalid parent selection

**Cascade Deletion**
- Behavior: Deleting parent team automatically deletes sub-teams
- Warning: Admin interface should display warning before deletion
- Logging: All cascade deletions logged for audit trail
- User Impact: Confirmation dialog shows affected sub-teams

### Form Errors

**Invalid Team Selection**
- Error Type: `ValidationError`
- Message: "Select a valid choice. That choice is not one of the available choices."
- Trigger: Submitting form with invalid team ID
- Handling: Django form validation
- User Impact: Form displays error, submission rejected

**Empty Required Fields**
- Error Type: `ValidationError`
- Message: "This field is required."
- Trigger: Submitting form without required team name
- Handling: Django form validation
- User Impact: Form displays error inline

### Error Logging

All errors are logged with appropriate severity levels:

- **ERROR**: Validation failures, migration errors, database errors
- **WARNING**: Cascade deletions, cache invalidation failures
- **INFO**: Successful migrations, team hierarchy changes
- **DEBUG**: Query performance, cache hits/misses

Log format includes:
- Timestamp
- User (if applicable)
- Action attempted
- Error type and message
- Stack trace (for exceptions)
- Request context (for API errors)

## Testing Strategy

### Overview

The testing strategy employs a dual approach combining property-based testing for universal correctness guarantees with unit testing for specific examples and edge cases. This comprehensive approach ensures both broad input coverage and targeted validation of critical scenarios.

### Property-Based Testing

**Framework**: Hypothesis (Python property-based testing library)

**Configuration**:
- Minimum 100 iterations per property test
- Deadline: 500ms per test case
- Database strategy: Use Django's TestCase with transaction rollback
- Seed: Fixed seed for reproducibility in CI/CD

**Test Organization**:
- Location: `assets/tests/test_team_hierarchy_properties.py`
- Each property from the design document maps to one property-based test
- Tests tagged with: `# Feature: hierarchical-team-structure, Property {N}: {description}`

**Property Test Examples**:

```python
from hypothesis import given, strategies as st
from hypothesis.extra.django import TestCase
from assets.models import Team
from django.core.exceptions import ValidationError

class TeamHierarchyProperties(TestCase):
    
    @given(st.text(min_size=1, max_size=100))
    def test_property_1_circular_reference_prevention(self, team_name):
        """
        Feature: hierarchical-team-structure, Property 1
        For any team and any proposed parent assignment, if the assignment 
        would create a circular reference, validation should fail.
        """
        # Create a team
        team = Team.objects.create(name=team_name)
        
        # Attempt self-reference
        team.parent = team
        with self.assertRaises(ValidationError) as context:
            team.full_clean()
        
        self.assertIn("cannot be its own parent", str(context.exception))
    
    @given(st.text(min_size=1, max_size=100))
    def test_property_4_team_classification(self, team_name):
        """
        Feature: hierarchical-team-structure, Property 4
        For any team, hierarchy_level should return 0 for parent teams 
        and 1 for sub-teams.
        """
        # Create parent team
        parent = Team.objects.create(name=f"Parent_{team_name}")
        self.assertEqual(parent.hierarchy_level, 0)
        
        # Create sub-team
        sub = Team.objects.create(name=f"Sub_{team_name}", parent=parent)
        self.assertEqual(sub.hierarchy_level, 1)
    
    @given(st.lists(st.text(min_size=1, max_size=50), min_size=2, max_size=10, unique=True))
    def test_property_5_multiple_subteams(self, team_names):
        """
        Feature: hierarchical-team-structure, Property 5
        For any parent team, it should support multiple sub-teams.
        """
        parent_name = team_names[0]
        sub_names = team_names[1:]
        
        parent = Team.objects.create(name=parent_name)
        
        # Create multiple sub-teams
        for sub_name in sub_names:
            Team.objects.create(name=sub_name, parent=parent)
        
        # Verify all sub-teams are associated
        self.assertEqual(parent.sub_teams.count(), len(sub_names))
        retrieved_names = set(parent.sub_teams.values_list('name', flat=True))
        self.assertEqual(retrieved_names, set(sub_names))
```

**Generators (Hypothesis Strategies)**:

```python
# Custom strategies for generating valid team hierarchies
@st.composite
def valid_team_hierarchy(draw):
    """Generate a valid team hierarchy with parent and sub-teams."""
    parent_name = draw(st.text(min_size=1, max_size=100))
    num_subs = draw(st.integers(min_value=0, max_value=20))
    sub_names = draw(st.lists(
        st.text(min_size=1, max_size=100),
        min_size=num_subs,
        max_size=num_subs,
        unique=True
    ))
    return {'parent': parent_name, 'subs': sub_names}

@st.composite
def team_with_assets(draw):
    """Generate a team with associated assets."""
    team_name = draw(st.text(min_size=1, max_size=100))
    num_assets = draw(st.integers(min_value=1, max_value=50))
    return {'team': team_name, 'asset_count': num_assets}
```

### Unit Testing

**Framework**: pytest with Django plugin

**Test Organization**:
- Location: `assets/tests/test_team_hierarchy.py`
- Focused on specific examples, edge cases, and integration points
- Tests for migration scripts in `assets/tests/test_migrations.py`

**Unit Test Categories**:

1. **Specific Examples** (from requirements):
   - Test that "Marketing" parent team is created by migration
   - Test that "Developers" has exactly 19 sub-teams after migration
   - Test that "Not Applicable" team exists and is selectable
   - Test admin interface includes parent field in form

2. **Edge Cases**:
   - Empty team name handling
   - Very long team names (boundary testing)
   - Special characters in team names
   - Concurrent team creation (race conditions)
   - Deleting team with many assets assigned

3. **Integration Tests**:
   - Complete workflow: create parent → create sub-teams → assign to assets
   - Migration forward → verify data → migration backward → verify restoration
   - API create team → assign to asset → retrieve via API → verify hierarchy
   - Admin interface team creation → form validation → save → verify in database

4. **Error Condition Tests**:
   - Attempt to create 3-level hierarchy (should fail)
   - Attempt circular reference (should fail)
   - Attempt to delete parent with sub-teams (should cascade)
   - Attempt to assign invalid parent_id via API (should return 400)

**Unit Test Examples**:

```python
import pytest
from django.core.exceptions import ValidationError
from assets.models import Team, Asset

@pytest.mark.django_db
class TestTeamHierarchyExamples:
    
    def test_marketing_team_created_by_migration(self):
        """Test that Marketing parent team exists after migration."""
        team = Team.objects.get(name='Marketing')
        assert team.parent is None
        assert team.hierarchy_level == 0
    
    def test_developers_has_19_subteams(self):
        """Test that Developers parent has exactly 19 sub-teams."""
        developers = Team.objects.get(name='Developers')
        assert developers.sub_teams.count() == 19
        
        expected_names = [
            'Bethovans Team', 'QC Team', 'App Team', 'Hotel Team',
            'Suma Team', 'Iboss Team', 'Robin Team', 'Jojo Team',
            'Sandeep Team', 'Dulfi Team', 'Design Team', 'Justine MJ Team',
            'Jinson Team', 'Jerly Team', 'DBA Team', 'JOJO Team',
            'BA Team', 'Adhun Team', 'Aymen Team'
        ]
        actual_names = list(developers.sub_teams.values_list('name', flat=True))
        assert set(actual_names) == set(expected_names)
    
    def test_not_applicable_team_exists(self):
        """Test that Not Applicable team is available."""
        team = Team.objects.get(name='Not Applicable')
        assert team is not None
    
    def test_three_level_hierarchy_rejected(self):
        """Test that 3-level hierarchy is prevented."""
        grandparent = Team.objects.create(name='Grandparent')
        parent = Team.objects.create(name='Parent', parent=grandparent)
        child = Team(name='Child', parent=parent)
        
        with pytest.raises(ValidationError) as exc:
            child.full_clean()
        
        assert "2 levels deep" in str(exc.value)
```

### Migration Testing

**Approach**: Test migrations in isolation using Django's migration test framework

**Test Cases**:
1. Forward migration creates parent field with correct constraints
2. Data migration creates all specified teams
3. Data migration is idempotent (can run multiple times)
4. Reverse migration removes parent field
5. Reverse migration preserves team names
6. Migration preserves existing asset-team assignments
7. Migration handles existing teams with matching names

**Migration Test Example**:

```python
from django.test import TestCase
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

class TestTeamHierarchyMigration(TestCase):
    
    def test_migration_forward_backward(self):
        """Test migration can be applied and reversed."""
        executor = MigrationExecutor(connection)
        
        # Get migration state before
        app = 'assets'
        migrate_from = [('assets', '0010_previous_migration')]
        migrate_to = [('assets', '0011_team_hierarchy')]
        
        # Apply migration
        executor.migrate(migrate_to)
        
        # Verify parent field exists
        Team = executor.loader.project_state(migrate_to).apps.get_model(app, 'Team')
        team = Team.objects.create(name='Test')
        assert hasattr(team, 'parent')
        
        # Reverse migration
        executor.migrate(migrate_from)
        
        # Verify parent field removed
        Team = executor.loader.project_state(migrate_from).apps.get_model(app, 'Team')
        team = Team.objects.first()
        assert not hasattr(team, 'parent')
```

### API Testing

**Framework**: Django REST Framework test client

**Test Coverage**:
- GET /api/teams/ - List all teams with hierarchy
- GET /api/teams/{id}/ - Retrieve single team with parent/sub-teams
- POST /api/teams/ - Create team with parent
- PUT /api/teams/{id}/ - Update team parent assignment
- DELETE /api/teams/{id}/ - Delete team (verify cascade)
- GET /api/teams/{id}/sub-teams/ - List sub-teams for parent

**API Test Example**:

```python
from rest_framework.test import APITestCase
from rest_framework import status
from assets.models import Team

class TestTeamHierarchyAPI(APITestCase):
    
    def test_create_team_with_parent(self):
        """Test creating a sub-team via API."""
        parent = Team.objects.create(name='Engineering')
        
        response = self.client.post('/api/teams/', {
            'name': 'Backend Team',
            'parent': parent.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent_id'], parent.id)
        self.assertEqual(response.data['hierarchy_level'], 1)
    
    def test_circular_reference_returns_400(self):
        """Test that circular reference returns validation error."""
        team = Team.objects.create(name='Team A')
        
        response = self.client.put(f'/api/teams/{team.id}/', {
            'name': 'Team A',
            'parent': team.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('circular', str(response.data).lower())
```

### Performance Testing

**Scope**: Verify query efficiency with large team hierarchies

**Test Scenarios**:
1. Load dropdown with 100 parent teams and 1000 sub-teams
2. Filter assets by team with 10,000 assets
3. Aggregate statistics for parent with 50 sub-teams
4. API list endpoint with pagination

**Performance Benchmarks**:
- Dropdown load: < 100ms for 1000 teams
- Asset filter: < 200ms for 10,000 assets
- Statistics aggregation: < 300ms for 50 sub-teams
- API list: < 150ms for 100 teams

**Performance Test Example**:

```python
import pytest
from django.test.utils import override_settings
from django.db import connection
from django.test import TestCase

class TestTeamHierarchyPerformance(TestCase):
    
    def test_dropdown_query_count(self):
        """Test that dropdown uses minimal queries."""
        # Create 10 parents with 10 sub-teams each
        for i in range(10):
            parent = Team.objects.create(name=f'Parent {i}')
            for j in range(10):
                Team.objects.create(name=f'Sub {i}-{j}', parent=parent)
        
        # Count queries for hierarchical choices
        with self.assertNumQueries(2):  # 1 for parents, 1 for sub-teams
            choices = Team.objects.get_hierarchical_choices()
            list(choices)  # Force evaluation
```

### Test Execution

**Local Development**:
```bash
# Run all tests
pytest assets/tests/

# Run only property tests
pytest assets/tests/test_team_hierarchy_properties.py

# Run only unit tests
pytest assets/tests/test_team_hierarchy.py

# Run with coverage
pytest --cov=assets --cov-report=html
```

**CI/CD Pipeline**:
- All tests run on every pull request
- Property tests run with fixed seed for reproducibility
- Coverage threshold: 90% for new code
- Performance tests run nightly
- Migration tests run in isolated database

### Test Data Management

**Fixtures**: Pre-populated team hierarchies for consistent testing
**Factories**: Use factory_boy for generating test data
**Cleanup**: All tests use Django's TestCase for automatic rollback
**Isolation**: Each test runs in a transaction, no cross-test pollution

### Coverage Goals

- **Line Coverage**: > 95% for team hierarchy code
- **Branch Coverage**: > 90% for validation logic
- **Property Coverage**: 100% of design properties tested
- **Edge Case Coverage**: All identified edge cases tested
- **Integration Coverage**: All API endpoints tested

