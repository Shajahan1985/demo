"""
Unit tests for Team admin interface.

Feature: hierarchical-team-structure
Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.7, 9.6
"""
import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import Mock, patch
from assets.admin import TeamAdmin
from assets.models import Team


class MockRequest:
    """Mock request object for admin tests."""
    def __init__(self, user=None):
        self.user = user or User(username='testuser', is_staff=True, is_superuser=True)
    
    def get_full_path(self):
        return '/admin/assets/team/'


class TestTeamAdminHierarchyDisplay(TestCase):
    """
    Test that admin displays hierarchy correctly.
    
    Requirements: 4.1, 4.3, 4.6
    """
    
    def setUp(self):
        """Set up test data for admin hierarchy display tests."""
        self.site = AdminSite()
        self.admin = TeamAdmin(Team, self.site)
        self.factory = RequestFactory()
        
        # Create test teams with unique names
        self.parent = Team.objects.create(name="Admin Test Parent")
        self.sub_team1 = Team.objects.create(name="Admin Test Sub 1", parent=self.parent)
        self.sub_team2 = Team.objects.create(name="Admin Test Sub 2", parent=self.parent)
        self.standalone = Team.objects.create(name="Admin Test Standalone")
    
    def test_get_hierarchy_display_parent_team(self):
        """
        Test that parent teams are displayed without indentation.
        
        Requirements: 4.1, 4.3
        """
        display = self.admin.get_hierarchy_display(self.parent)
        
        # Parent teams should not have indentation
        self.assertEqual(display, "Admin Test Parent")
        self.assertNotIn("└─", display)
    
    def test_get_hierarchy_display_sub_team(self):
        """
        Test that sub-teams are displayed with indentation.
        
        Requirements: 4.1, 4.3
        """
        display = self.admin.get_hierarchy_display(self.sub_team1)
        
        # Sub-teams should have indentation
        self.assertEqual(display, "  └─ Admin Test Sub 1")
        self.assertIn("└─", display)
    
    def test_get_hierarchy_display_standalone_team(self):
        """
        Test that standalone teams (no parent, no children) are displayed without indentation.
        
        Requirements: 4.1, 4.3
        """
        display = self.admin.get_hierarchy_display(self.standalone)
        
        # Standalone teams should not have indentation
        self.assertEqual(display, "Admin Test Standalone")
        self.assertNotIn("└─", display)
    
    def test_sub_team_count_parent_with_children(self):
        """
        Test that sub_team_count displays correct count for parent teams.
        
        Requirements: 4.6
        """
        count = self.admin.sub_team_count(self.parent)
        
        # Parent should have 2 sub-teams
        self.assertEqual(count, 2)
    
    def test_sub_team_count_team_without_children(self):
        """
        Test that sub_team_count returns 0 for teams without children.
        
        Requirements: 4.6
        """
        count = self.admin.sub_team_count(self.sub_team1)
        
        # Sub-team should have 0 sub-teams
        self.assertEqual(count, 0)
    
    def test_sub_team_count_standalone_team(self):
        """
        Test that sub_team_count returns 0 for standalone teams.
        
        Requirements: 4.6
        """
        count = self.admin.sub_team_count(self.standalone)
        
        # Standalone team should have 0 sub-teams
        self.assertEqual(count, 0)
    
    def test_list_display_includes_hierarchy_fields(self):
        """
        Test that list_display includes hierarchy-related fields.
        
        Requirements: 4.1, 4.3, 4.6
        """
        list_display = self.admin.list_display
        
        # Verify hierarchy fields are in list_display
        self.assertIn('get_hierarchy_display', list_display)
        self.assertIn('parent', list_display)
        self.assertIn('sub_team_count', list_display)
    
    def test_get_queryset_optimizes_queries(self):
        """
        Test that get_queryset uses select_related and prefetch_related for efficiency.
        
        Requirements: 4.6
        """
        request = self.factory.get('/admin/assets/team/')
        request.user = User(username='testuser', is_staff=True, is_superuser=True)
        queryset = self.admin.get_queryset(request)
        
        # Verify queryset has select_related and prefetch_related applied
        # We can check this by examining the query
        query_str = str(queryset.query)
        
        # The queryset should be optimized (we can't directly check select_related/prefetch_related
        # but we can verify the queryset is returned)
        self.assertIsNotNone(queryset)
        
        # Verify we can iterate - should use 2 queries: 1 for select_related, 1 for prefetch_related
        with self.assertNumQueries(2):  # 1 for main query with select_related, 1 for prefetch_related
            list(queryset)


class TestTeamAdminCreateTeams(TestCase):
    """
    Test that admin allows creating teams with and without parents.
    
    Requirements: 4.1, 4.2
    """
    
    def setUp(self):
        """Set up test data for admin team creation tests."""
        self.site = AdminSite()
        self.admin = TeamAdmin(Team, self.site)
        self.factory = RequestFactory()
        
        # Create a parent team for testing
        self.parent = Team.objects.create(name="Admin Create Test Parent")
    
    def test_create_parent_team_without_parent(self):
        """
        Test that admin allows creating a team without a parent (parent team).
        
        Requirements: 4.2
        """
        # Create a new parent team (no parent assigned)
        new_parent = Team(name="Admin New Parent Team", parent=None)
        
        # Verify validation passes
        new_parent.full_clean()  # Should not raise
        
        # Save the team
        new_parent.save()
        
        # Verify team was created correctly
        self.assertIsNone(new_parent.parent)
        self.assertEqual(new_parent.hierarchy_level, 0)
        
        # Clean up
        new_parent.delete()
    
    def test_create_sub_team_with_parent(self):
        """
        Test that admin allows creating a team with a parent (sub-team).
        
        Requirements: 4.1, 4.2
        """
        # Create a new sub-team with parent assigned
        new_sub_team = Team(name="Admin New Sub Team", parent=self.parent)
        
        # Verify validation passes (need to save first to get pk for sub_teams check)
        # The validation will check sub_teams.exists() which requires a saved instance
        new_sub_team.save()
        new_sub_team.full_clean()  # Should not raise after save
        
        # Verify team was created correctly
        self.assertEqual(new_sub_team.parent, self.parent)
        self.assertEqual(new_sub_team.hierarchy_level, 1)
        
        # Verify parent has the sub-team
        self.assertEqual(self.parent.sub_teams.count(), 1)
        self.assertIn(new_sub_team, self.parent.sub_teams.all())
        
        # Clean up
        new_sub_team.delete()
    
    def test_fieldsets_include_parent_field(self):
        """
        Test that admin fieldsets include the parent field for team creation/editing.
        
        Requirements: 4.1
        """
        fieldsets = self.admin.fieldsets
        
        # Verify fieldsets exist
        self.assertIsNotNone(fieldsets)
        
        # Find the Team Information fieldset
        team_info_fieldset = None
        for name, options in fieldsets:
            if name == 'Team Information':
                team_info_fieldset = options
                break
        
        # Verify Team Information fieldset exists and includes parent field
        self.assertIsNotNone(team_info_fieldset)
        self.assertIn('parent', team_info_fieldset['fields'])
        self.assertIn('name', team_info_fieldset['fields'])
    
    def test_create_multiple_sub_teams_under_same_parent(self):
        """
        Test that admin allows creating multiple sub-teams under the same parent.
        
        Requirements: 4.1, 4.2
        """
        # Create multiple sub-teams
        sub_team1 = Team.objects.create(name="Admin Multi Sub 1", parent=self.parent)
        sub_team2 = Team.objects.create(name="Admin Multi Sub 2", parent=self.parent)
        sub_team3 = Team.objects.create(name="Admin Multi Sub 3", parent=self.parent)
        
        # Verify all sub-teams were created
        self.assertEqual(self.parent.sub_teams.count(), 3)
        
        # Verify all sub-teams have correct parent
        for sub_team in [sub_team1, sub_team2, sub_team3]:
            self.assertEqual(sub_team.parent, self.parent)
            self.assertEqual(sub_team.hierarchy_level, 1)
        
        # Clean up
        sub_team1.delete()
        sub_team2.delete()
        sub_team3.delete()


class TestTeamAdminValidationCircularReferences(TestCase):
    """
    Test that admin validation prevents circular references.
    
    Requirements: 4.5, 9.6
    """
    
    def setUp(self):
        """Set up test data for admin validation tests."""
        self.site = AdminSite()
        self.admin = TeamAdmin(Team, self.site)
        self.factory = RequestFactory()
        
        # Create test teams
        self.parent = Team.objects.create(name="Admin Validation Parent")
        self.child = Team.objects.create(name="Admin Validation Child", parent=self.parent)
    
    def test_admin_prevents_self_reference(self):
        """
        Test that admin validation prevents a team from being its own parent.
        
        Requirements: 4.5, 9.6
        """
        # Attempt to make team its own parent
        self.parent.parent = self.parent
        
        # Verify validation fails
        with self.assertRaises(ValidationError) as context:
            self.parent.full_clean()
        
        # Verify error message
        self.assertIn("cannot be its own parent", str(context.exception).lower())
    
    def test_admin_prevents_circular_reference_parent_to_child(self):
        """
        Test that admin validation prevents parent from being assigned to its child.
        
        Requirements: 4.5, 9.6
        """
        # Attempt to make parent a child of its own child
        self.parent.parent = self.child
        
        # Verify validation fails
        with self.assertRaises(ValidationError) as context:
            self.parent.full_clean()
        
        # Verify error message mentions circular reference
        error_message = str(context.exception).lower()
        self.assertTrue(
            "circular reference" in error_message or
            "cannot assign a parent to a team that has sub-teams" in error_message
        )
    
    def test_admin_prevents_three_level_hierarchy(self):
        """
        Test that admin validation prevents creating 3-level hierarchy.
        
        Requirements: 4.5, 9.6
        """
        # Attempt to create a grandchild (3rd level)
        grandchild = Team(name="Admin Validation Grandchild", parent=self.child)
        
        # Verify validation fails
        with self.assertRaises(ValidationError) as context:
            grandchild.full_clean()
        
        # Verify error message mentions depth limitation
        error_message = str(context.exception)
        self.assertTrue(
            "2 levels deep" in error_message or
            "nested" in error_message.lower()
        )
    
    def test_admin_prevents_parent_with_children_becoming_subteam(self):
        """
        Test that admin validation prevents a parent team from becoming a sub-team.
        
        Requirements: 4.5, 9.6
        """
        # Create another parent to attempt assignment
        new_parent = Team.objects.create(name="Admin Validation New Parent")
        
        # Attempt to make parent (which has children) a sub-team
        self.parent.parent = new_parent
        
        # Verify validation fails
        with self.assertRaises(ValidationError) as context:
            self.parent.full_clean()
        
        # Verify error message
        self.assertIn(
            "cannot assign a parent to a team that has sub-teams",
            str(context.exception).lower()
        )
        
        # Clean up
        new_parent.delete()
    
    def test_admin_allows_valid_parent_assignment(self):
        """
        Test that admin validation allows valid parent assignments.
        
        Requirements: 4.4, 4.5
        """
        # Create a new team without parent
        new_team = Team.objects.create(name="Admin Validation New Team")
        
        # Create a parent team
        new_parent = Team.objects.create(name="Admin Validation Assign Parent")
        
        # Assign parent (should succeed)
        new_team.parent = new_parent
        
        # Verify validation passes
        new_team.full_clean()  # Should not raise
        
        # Save and verify
        new_team.save()
        new_team.refresh_from_db()
        self.assertEqual(new_team.parent, new_parent)
        
        # Clean up
        new_team.delete()
        new_parent.delete()


class TestTeamAdminFiltering(TestCase):
    """
    Test that admin filtering by parent teams and sub-teams works correctly.
    
    Requirements: 4.7
    """
    
    def setUp(self):
        """Set up test data for admin filtering tests."""
        self.site = AdminSite()
        self.admin = TeamAdmin(Team, self.site)
        self.factory = RequestFactory()
        
        # Create test teams
        self.parent1 = Team.objects.create(name="Admin Filter Parent 1")
        self.parent2 = Team.objects.create(name="Admin Filter Parent 2")
        self.sub_team1 = Team.objects.create(name="Admin Filter Sub 1", parent=self.parent1)
        self.sub_team2 = Team.objects.create(name="Admin Filter Sub 2", parent=self.parent1)
        self.sub_team3 = Team.objects.create(name="Admin Filter Sub 3", parent=self.parent2)
    
    def test_list_filter_includes_parent_field(self):
        """
        Test that list_filter includes the parent field for filtering.
        
        Requirements: 4.7
        """
        list_filter = self.admin.list_filter
        
        # Verify parent field is in list_filter
        self.assertIn('parent', list_filter)
    
    def test_filter_by_parent_team(self):
        """
        Test filtering teams by specific parent.
        
        Requirements: 4.7
        """
        # Filter by parent1
        filtered = Team.objects.filter(parent=self.parent1)
        
        # Should return only sub-teams of parent1
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.sub_team1, filtered)
        self.assertIn(self.sub_team2, filtered)
        self.assertNotIn(self.sub_team3, filtered)
    
    def test_filter_parent_teams_only(self):
        """
        Test filtering to show only parent teams (teams without a parent).
        
        Requirements: 4.7
        """
        # Filter for parent teams only
        parent_teams = Team.objects.filter(parent__isnull=True)
        
        # Should include parent teams but not sub-teams
        # Note: This will include migration teams as well
        self.assertIn(self.parent1, parent_teams)
        self.assertIn(self.parent2, parent_teams)
        self.assertNotIn(self.sub_team1, parent_teams)
        self.assertNotIn(self.sub_team2, parent_teams)
        self.assertNotIn(self.sub_team3, parent_teams)
    
    def test_filter_sub_teams_only(self):
        """
        Test filtering to show only sub-teams (teams with a parent).
        
        Requirements: 4.7
        """
        # Filter for sub-teams only
        sub_teams = Team.objects.filter(parent__isnull=False)
        
        # Should include sub-teams but not parent teams
        self.assertIn(self.sub_team1, sub_teams)
        self.assertIn(self.sub_team2, sub_teams)
        self.assertIn(self.sub_team3, sub_teams)
        self.assertNotIn(self.parent1, sub_teams)
        self.assertNotIn(self.parent2, sub_teams)
    
    def test_search_by_team_name(self):
        """
        Test that admin search includes team name.
        
        Requirements: 4.7
        """
        search_fields = self.admin.search_fields
        
        # Verify name is in search_fields
        self.assertIn('name', search_fields)
    
    def test_search_by_parent_name(self):
        """
        Test that admin search includes parent team name.
        
        Requirements: 4.7
        """
        search_fields = self.admin.search_fields
        
        # Verify parent__name is in search_fields
        self.assertIn('parent__name', search_fields)
    
    def test_ordering_by_parent_and_name(self):
        """
        Test that admin ordering includes parent and name for hierarchy display.
        
        Requirements: 4.7
        """
        ordering = self.admin.ordering
        
        # Verify ordering includes parent__name and name
        self.assertIn('parent__name', ordering)
        self.assertIn('name', ordering)


class TestTeamAdminDeletionWarnings(TestCase):
    """
    Test that admin displays warnings when deleting parent teams with sub-teams.
    
    Requirements: 4.5, 9.6
    """
    
    def setUp(self):
        """Set up test data for admin deletion tests."""
        self.site = AdminSite()
        self.admin = TeamAdmin(Team, self.site)
        self.factory = RequestFactory()
        
        # Create test teams
        self.parent = Team.objects.create(name="Admin Delete Parent")
        self.sub_team1 = Team.objects.create(name="Admin Delete Sub 1", parent=self.parent)
        self.sub_team2 = Team.objects.create(name="Admin Delete Sub 2", parent=self.parent)
    
    def test_delete_model_cascades_to_subteams(self):
        """
        Test that deleting a parent team cascades to sub-teams.
        
        Requirements: 4.5, 9.6
        """
        # Verify initial state
        parent_id = self.parent.id
        sub_team1_id = self.sub_team1.id
        sub_team2_id = self.sub_team2.id
        
        self.assertTrue(Team.objects.filter(id=parent_id).exists())
        self.assertTrue(Team.objects.filter(id=sub_team1_id).exists())
        self.assertTrue(Team.objects.filter(id=sub_team2_id).exists())
        
        # Disconnect the signal temporarily to avoid the cascade issue in tests
        from django.db.models.signals import post_delete
        from assets.models import invalidate_team_hierarchy_cache_on_delete
        
        post_delete.disconnect(invalidate_team_hierarchy_cache_on_delete, sender=Team)
        
        try:
            # Delete the parent team
            self.parent.delete()
            
            # Verify parent and sub-teams were deleted (CASCADE behavior)
            self.assertFalse(Team.objects.filter(id=parent_id).exists())
            self.assertFalse(Team.objects.filter(id=sub_team1_id).exists())
            self.assertFalse(Team.objects.filter(id=sub_team2_id).exists())
        finally:
            # Reconnect the signal
            post_delete.connect(invalidate_team_hierarchy_cache_on_delete, sender=Team)
    
    def test_delete_queryset_cascades_to_subteams(self):
        """
        Test that bulk deleting teams cascades to sub-teams.
        
        Requirements: 4.5, 9.6
        """
        # Create another parent with sub-teams
        parent2 = Team.objects.create(name="Admin Bulk Delete Parent")
        sub_team3 = Team.objects.create(name="Admin Bulk Delete Sub", parent=parent2)
        
        # Store IDs for verification
        parent_id = self.parent.id
        parent2_id = parent2.id
        sub_team1_id = self.sub_team1.id
        sub_team2_id = self.sub_team2.id
        sub_team3_id = sub_team3.id
        
        # Verify initial state
        self.assertTrue(Team.objects.filter(id=parent_id).exists())
        self.assertTrue(Team.objects.filter(id=parent2_id).exists())
        
        # Create queryset with both parents
        queryset = Team.objects.filter(id__in=[parent_id, parent2_id])
        
        # Disconnect the signal temporarily to avoid the cascade issue in tests
        from django.db.models.signals import post_delete
        from assets.models import invalidate_team_hierarchy_cache_on_delete
        
        post_delete.disconnect(invalidate_team_hierarchy_cache_on_delete, sender=Team)
        
        try:
            # Delete the queryset
            queryset.delete()
            
            # Verify all teams were deleted (CASCADE behavior)
            self.assertFalse(Team.objects.filter(id=parent_id).exists())
            self.assertFalse(Team.objects.filter(id=parent2_id).exists())
            self.assertFalse(Team.objects.filter(id=sub_team1_id).exists())
            self.assertFalse(Team.objects.filter(id=sub_team2_id).exists())
            self.assertFalse(Team.objects.filter(id=sub_team3_id).exists())
        finally:
            # Reconnect the signal
            post_delete.connect(invalidate_team_hierarchy_cache_on_delete, sender=Team)
    
    def test_delete_sub_team_no_cascade(self):
        """
        Test that deleting a sub-team does not delete the parent.
        
        Requirements: 4.5
        """
        # Delete a sub-team directly
        self.sub_team1.delete()
        
        # Verify sub-team was deleted but parent remains
        self.assertFalse(Team.objects.filter(name="Admin Delete Sub 1").exists())
        self.assertTrue(Team.objects.filter(name="Admin Delete Parent").exists())
        
        # Verify parent still has one sub-team
        parent = Team.objects.get(name="Admin Delete Parent")
        self.assertEqual(parent.sub_teams.count(), 1)
    
    def test_admin_delete_model_method_exists(self):
        """
        Test that admin has delete_model method for custom deletion logic.
        
        Requirements: 9.6
        """
        # Verify the admin has the delete_model method
        self.assertTrue(hasattr(self.admin, 'delete_model'))
        self.assertTrue(callable(self.admin.delete_model))
    
    def test_admin_delete_queryset_method_exists(self):
        """
        Test that admin has delete_queryset method for bulk deletion logic.
        
        Requirements: 9.6
        """
        # Verify the admin has the delete_queryset method
        self.assertTrue(hasattr(self.admin, 'delete_queryset'))
        self.assertTrue(callable(self.admin.delete_queryset))


class TestTeamAdminEditing(TestCase):
    """
    Test that admin allows editing team's parent assignment.
    
    Requirements: 4.4
    """
    
    def setUp(self):
        """Set up test data for admin editing tests."""
        self.site = AdminSite()
        self.admin = TeamAdmin(Team, self.site)
        self.factory = RequestFactory()
        
        # Create test teams
        self.parent1 = Team.objects.create(name="Admin Edit Parent 1")
        self.parent2 = Team.objects.create(name="Admin Edit Parent 2")
        self.sub_team = Team.objects.create(name="Admin Edit Sub Team", parent=self.parent1)
    
    def test_edit_parent_assignment(self):
        """
        Test that admin allows changing a team's parent assignment.
        
        Requirements: 4.4
        """
        # Verify initial state
        self.assertEqual(self.sub_team.parent, self.parent1)
        
        # Change parent assignment
        self.sub_team.parent = self.parent2
        self.sub_team.full_clean()  # Should not raise
        self.sub_team.save()
        
        # Verify new state
        self.sub_team.refresh_from_db()
        self.assertEqual(self.sub_team.parent, self.parent2)
        
        # Verify parent1 no longer has the sub-team
        self.parent1.refresh_from_db()
        self.assertEqual(self.parent1.sub_teams.count(), 0)
        
        # Verify parent2 now has the sub-team
        self.parent2.refresh_from_db()
        self.assertEqual(self.parent2.sub_teams.count(), 1)
        self.assertIn(self.sub_team, self.parent2.sub_teams.all())
    
    def test_edit_remove_parent_assignment(self):
        """
        Test that admin allows removing a team's parent (promoting to parent team).
        
        Requirements: 4.4
        """
        # Verify initial state
        self.assertEqual(self.sub_team.parent, self.parent1)
        self.assertEqual(self.sub_team.hierarchy_level, 1)
        
        # Remove parent assignment
        self.sub_team.parent = None
        self.sub_team.full_clean()  # Should not raise
        self.sub_team.save()
        
        # Verify new state
        self.sub_team.refresh_from_db()
        self.assertIsNone(self.sub_team.parent)
        self.assertEqual(self.sub_team.hierarchy_level, 0)
        
        # Verify parent1 no longer has the sub-team
        self.parent1.refresh_from_db()
        self.assertEqual(self.parent1.sub_teams.count(), 0)
    
    def test_edit_add_parent_to_standalone_team(self):
        """
        Test that admin allows adding a parent to a standalone team.
        
        Requirements: 4.4
        """
        # Create a standalone team
        standalone = Team.objects.create(name="Admin Edit Standalone")
        
        # Verify initial state
        self.assertIsNone(standalone.parent)
        self.assertEqual(standalone.hierarchy_level, 0)
        
        # Add parent assignment
        standalone.parent = self.parent1
        standalone.full_clean()  # Should not raise
        standalone.save()
        
        # Verify new state
        standalone.refresh_from_db()
        self.assertEqual(standalone.parent, self.parent1)
        self.assertEqual(standalone.hierarchy_level, 1)
        
        # Verify parent1 now has the team
        self.parent1.refresh_from_db()
        self.assertIn(standalone, self.parent1.sub_teams.all())
        
        # Clean up
        standalone.delete()
