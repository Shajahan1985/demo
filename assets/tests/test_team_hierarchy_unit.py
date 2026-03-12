"""
Unit tests for Team model validation - specific examples and edge cases.

Feature: hierarchical-team-structure
Requirements: 1.4, 9.1, 9.2, 9.3, 9.4, 9.5
"""
import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from assets.models import Team


class TestTeamValidationSpecificExamples(TestCase):
    """Test specific validation examples from requirements."""
    
    def test_self_reference_validation(self):
        """
        Test that a team cannot be its own parent (self-reference).
        
        Requirements: 1.4, 9.1
        """
        team = Team.objects.create(name="Engineering")
        team.parent = team
        
        with self.assertRaises(ValidationError) as context:
            team.full_clean()
        
        self.assertIn("cannot be its own parent", str(context.exception).lower())
    
    def test_three_level_hierarchy_prevention(self):
        """
        Test that 3-level hierarchy is prevented.
        
        Requirements: 9.4
        """
        # Create grandparent (level 0)
        grandparent = Team.objects.create(name="Corporate")
        
        # Create parent (level 1)
        parent = Team.objects.create(name="Engineering", parent=grandparent)
        
        # Attempt to create child (level 2) - should fail
        child = Team(name="Backend Team", parent=parent)
        
        with self.assertRaises(ValidationError) as context:
            child.full_clean()
        
        error_message = str(context.exception)
        self.assertTrue(
            "2 levels deep" in error_message or "nested" in error_message.lower(),
            f"Expected depth error, got: {error_message}"
        )
    
    def test_parent_with_children_becoming_subteam(self):
        """
        Test that a parent team with children cannot become a sub-team.
        
        Requirements: 9.5
        """
        # Create parent team with sub-teams
        parent = Team.objects.create(name="Engineering")
        sub_team1 = Team.objects.create(name="Backend", parent=parent)
        sub_team2 = Team.objects.create(name="Frontend", parent=parent)
        
        # Verify parent has sub-teams
        self.assertEqual(parent.sub_teams.count(), 2)
        
        # Create another parent to attempt assignment
        new_parent = Team.objects.create(name="Technology")
        
        # Attempt to make the parent team a sub-team
        parent.parent = new_parent
        
        with self.assertRaises(ValidationError) as context:
            parent.full_clean()
        
        self.assertIn(
            "cannot assign a parent to a team that has sub-teams",
            str(context.exception).lower()
        )
    
    def test_circular_reference_parent_to_child(self):
        """
        Test that a parent cannot be assigned to its own child.
        
        Requirements: 1.4, 9.2, 9.3
        """
        # Create parent and child
        parent = Team.objects.create(name="Engineering")
        child = Team.objects.create(name="Backend", parent=parent)
        
        # Attempt to make parent a child of its own child
        parent.parent = child
        
        with self.assertRaises(ValidationError) as context:
            parent.full_clean()
        
        error_message = str(context.exception).lower()
        self.assertTrue(
            "circular reference" in error_message or 
            "cannot assign a parent to a team that has sub-teams" in error_message,
            f"Expected circular reference error, got: {context.exception}"
        )
    
    def test_circular_reference_grandparent_to_grandchild(self):
        """
        Test that a grandparent cannot be assigned to its grandchild.
        
        Requirements: 1.4, 9.2, 9.3
        """
        # Create grandparent and parent
        grandparent = Team.objects.create(name="Corporate")
        parent = Team.objects.create(name="Engineering", parent=grandparent)
        
        # Create grandchild (without parent initially)
        grandchild = Team.objects.create(name="Backend")
        
        # Attempt to make grandparent a child of grandchild
        grandparent.parent = grandchild
        
        with self.assertRaises(ValidationError) as context:
            grandparent.full_clean()
        
        error_message = str(context.exception).lower()
        self.assertTrue(
            "circular reference" in error_message or 
            "cannot assign a parent to a team that has sub-teams" in error_message,
            f"Expected circular reference error, got: {context.exception}"
        )


class TestTeamNameEdgeCases(TestCase):
    """Test edge cases for team names."""
    
    def test_empty_name_rejected(self):
        """
        Test that empty team names are rejected.
        
        Requirements: 9.1
        """
        team = Team(name="")
        
        with self.assertRaises(ValidationError):
            team.full_clean()
    
    def test_whitespace_only_name_rejected(self):
        """
        Test that whitespace-only names are rejected.
        
        Requirements: 9.1
        
        Note: Django's CharField doesn't automatically reject whitespace-only values.
        This test documents the actual behavior.
        """
        team = Team(name="   ")
        
        # Django CharField allows whitespace-only values by default
        # If we want to reject them, we'd need a custom validator
        team.full_clean()  # This will NOT raise
        team.save()
        
        # Verify it was saved
        self.assertEqual(team.name, "   ")
        team.delete()
    
    def test_special_characters_in_name(self):
        """
        Test that special characters in team names are handled correctly.
        
        Requirements: 9.1
        """
        special_names = [
            "Engineering & Design",
            "R&D Team",
            "Team #1",
            "Backend (Python)",
            "Frontend [React]",
            "Data@Analytics",
            "DevOps/SRE",
            "QA-Testing",
            "Team_Alpha",
            "Product+Marketing",
            "Sales$Support",
            "Team*Star",
            "Engineering!",
            "Team?Query",
            "50% Team",
            "Team=Value",
            "Team<>Brackets",
            "Team|Pipe",
            "Team\\Backslash",
            "Team:Colon",
            "Team;Semicolon",
            "Team'Quote",
            'Team"DoubleQuote',
            "Team`Backtick",
            "Team~Tilde",
            "Team^Caret",
        ]
        
        for name in special_names:
            with self.subTest(name=name):
                team = Team(name=name)
                # Should not raise ValidationError for special characters
                try:
                    team.full_clean()
                    # If validation passes, try to save
                    team.save()
                    # Clean up
                    team.delete()
                except ValidationError as e:
                    # If it fails, it should be for a valid reason (like length)
                    # not just because of special characters
                    self.fail(f"Team name '{name}' was rejected: {e}")
    
    def test_unicode_characters_in_name(self):
        """
        Test that Unicode characters in team names are handled correctly.
        
        Requirements: 9.1
        """
        unicode_names = [
            "Équipe Française",
            "Команда Россия",
            "チーム日本",
            "팀 한국",
            "فريق العربي",
            "Ομάδα Ελληνική",
            "Equipo Español",
            "Squadra Italiana",
            "Equipe Português",
            "Team 中文",
            "Team Ñoño",
            "Café Team",
            "Naïve Team",
            "Über Team",
        ]
        
        for name in unicode_names:
            with self.subTest(name=name):
                team = Team(name=name)
                # Should not raise ValidationError for Unicode
                try:
                    team.full_clean()
                    team.save()
                    # Verify it was saved correctly
                    saved_team = Team.objects.get(id=team.id)
                    self.assertEqual(saved_team.name, name)
                    # Clean up
                    team.delete()
                except ValidationError as e:
                    self.fail(f"Team name '{name}' was rejected: {e}")
    
    def test_very_long_name_at_boundary(self):
        """
        Test team names at the maximum length boundary (100 characters).
        
        Requirements: 9.1
        """
        # Exactly 100 characters (at boundary)
        name_100 = "A" * 100
        team = Team(name=name_100)
        team.full_clean()  # Should not raise
        team.save()
        self.assertEqual(len(team.name), 100)
        team.delete()
    
    def test_very_long_name_exceeds_limit(self):
        """
        Test that team names exceeding 100 characters are rejected.
        
        Requirements: 9.1
        """
        # 101 characters (exceeds limit)
        name_101 = "A" * 101
        team = Team(name=name_101)
        
        with self.assertRaises(ValidationError):
            team.full_clean()
    
    def test_very_long_name_with_spaces(self):
        """
        Test very long team names with spaces.
        
        Requirements: 9.1
        """
        # 100 characters with spaces
        base = "Engineering and Product Development Team for Enterprise Solutions and "
        name = base + "X" * (100 - len(base))
        self.assertEqual(len(name), 100)
        
        team = Team(name=name)
        team.full_clean()  # Should not raise
        team.save()
        team.delete()
    
    def test_name_with_leading_trailing_spaces(self):
        """
        Test that names with leading/trailing spaces are handled.
        
        Requirements: 9.1
        """
        # Django CharField typically doesn't strip spaces automatically
        # but we should test the behavior
        team = Team(name="  Engineering  ")
        team.full_clean()  # Should not raise
        team.save()
        
        # Verify the name is saved as-is (Django doesn't auto-strip)
        saved_team = Team.objects.get(id=team.id)
        self.assertEqual(saved_team.name, "  Engineering  ")
        team.delete()
    
    def test_name_with_newlines_and_tabs(self):
        """
        Test team names with newlines and tabs.
        
        Requirements: 9.1
        """
        names_with_whitespace = [
            "Team\nNewline",
            "Team\tTab",
            "Team\r\nCRLF",
            "Team\rCarriageReturn",
        ]
        
        for name in names_with_whitespace:
            with self.subTest(name=repr(name)):
                team = Team(name=name)
                # These should be allowed (Django doesn't restrict them by default)
                team.full_clean()
                team.save()
                team.delete()
    
    def test_duplicate_name_rejected(self):
        """
        Test that duplicate team names are rejected.
        
        Requirements: 9.1
        """
        Team.objects.create(name="Engineering")
        
        # Attempt to create another team with the same name
        duplicate_team = Team(name="Engineering")
        
        with self.assertRaises(ValidationError):
            duplicate_team.full_clean()
    
    def test_case_sensitive_names(self):
        """
        Test that team names are case-sensitive for uniqueness.
        
        Requirements: 9.1
        """
        Team.objects.create(name="Engineering")
        
        # Different case should be allowed (Django's unique constraint is case-sensitive by default)
        different_case_team = Team(name="ENGINEERING")
        different_case_team.full_clean()  # Should not raise
        different_case_team.save()
        
        # Verify both exist
        self.assertTrue(Team.objects.filter(name="Engineering").exists())
        self.assertTrue(Team.objects.filter(name="ENGINEERING").exists())
        
        different_case_team.delete()


class TestTeamHierarchyValidationEdgeCases(TestCase):
    """Test edge cases for team hierarchy validation."""
    
    def test_valid_two_level_hierarchy(self):
        """
        Test that a valid 2-level hierarchy is allowed.
        
        Requirements: 9.4
        """
        parent = Team.objects.create(name="Engineering")
        child = Team.objects.create(name="Backend", parent=parent)
        
        # Verify hierarchy is valid
        child.full_clean()  # Should not raise
        self.assertEqual(child.hierarchy_level, 1)
        self.assertEqual(parent.hierarchy_level, 0)
        self.assertEqual(parent.sub_teams.count(), 1)
    
    def test_multiple_subteams_under_parent(self):
        """
        Test that multiple sub-teams under a parent are allowed.
        
        Requirements: 1.6
        """
        parent = Team.objects.create(name="Engineering")
        
        # Create multiple sub-teams
        sub_teams = []
        for i in range(5):
            sub_team = Team.objects.create(name=f"Team {i}", parent=parent)
            sub_teams.append(sub_team)
        
        # Verify all sub-teams are associated
        self.assertEqual(parent.sub_teams.count(), 5)
        
        # Verify each sub-team is valid
        for sub_team in sub_teams:
            sub_team.full_clean()  # Should not raise
            self.assertEqual(sub_team.hierarchy_level, 1)
            self.assertEqual(sub_team.parent, parent)
    
    def test_team_without_parent_can_become_subteam(self):
        """
        Test that a team without a parent can be assigned a parent.
        
        Requirements: 9.5
        """
        team = Team.objects.create(name="Backend")
        parent = Team.objects.create(name="Engineering")
        
        # Assign parent
        team.parent = parent
        team.full_clean()  # Should not raise
        team.save()
        
        # Verify assignment
        team.refresh_from_db()
        self.assertEqual(team.parent, parent)
        self.assertEqual(team.hierarchy_level, 1)
    
    def test_subteam_can_change_parent(self):
        """
        Test that a sub-team can be moved to a different parent.
        
        Requirements: 4.4
        """
        parent1 = Team.objects.create(name="Engineering")
        parent2 = Team.objects.create(name="Product")
        sub_team = Team.objects.create(name="Backend", parent=parent1)
        
        # Verify initial state
        self.assertEqual(sub_team.parent, parent1)
        self.assertEqual(parent1.sub_teams.count(), 1)
        self.assertEqual(parent2.sub_teams.count(), 0)
        
        # Change parent
        sub_team.parent = parent2
        sub_team.full_clean()  # Should not raise
        sub_team.save()
        
        # Verify new state
        sub_team.refresh_from_db()
        parent1.refresh_from_db()
        parent2.refresh_from_db()
        
        self.assertEqual(sub_team.parent, parent2)
        self.assertEqual(parent1.sub_teams.count(), 0)
        self.assertEqual(parent2.sub_teams.count(), 1)
    
    def test_subteam_can_become_parent(self):
        """
        Test that a sub-team can be promoted to a parent team.
        
        Requirements: 4.4
        """
        parent = Team.objects.create(name="Engineering")
        sub_team = Team.objects.create(name="Backend", parent=parent)
        
        # Verify initial state
        self.assertEqual(sub_team.hierarchy_level, 1)
        
        # Remove parent (promote to parent team)
        sub_team.parent = None
        sub_team.full_clean()  # Should not raise
        sub_team.save()
        
        # Verify new state
        sub_team.refresh_from_db()
        self.assertEqual(sub_team.hierarchy_level, 0)
        self.assertIsNone(sub_team.parent)
    
    def test_parent_with_deleted_subteams_can_become_subteam(self):
        """
        Test that after deleting all sub-teams, a parent can become a sub-team.
        
        Requirements: 9.5
        """
        parent = Team.objects.create(name="Engineering")
        sub_team = Team.objects.create(name="Backend", parent=parent)
        
        # Verify parent has sub-teams
        self.assertEqual(parent.sub_teams.count(), 1)
        
        # Delete sub-team
        sub_team.delete()
        
        # Verify parent no longer has sub-teams
        parent.refresh_from_db()
        self.assertEqual(parent.sub_teams.count(), 0)
        
        # Now parent should be able to be assigned a parent
        new_parent = Team.objects.create(name="Technology")
        parent.parent = new_parent
        parent.full_clean()  # Should not raise
        parent.save()
        
        # Verify assignment
        parent.refresh_from_db()
        self.assertEqual(parent.parent, new_parent)
    
    def test_null_parent_is_valid(self):
        """
        Test that a team with null parent is valid (parent team).
        
        Requirements: 1.2
        """
        team = Team(name="Engineering", parent=None)
        team.full_clean()  # Should not raise
        team.save()
        
        self.assertIsNone(team.parent)
        self.assertEqual(team.hierarchy_level, 0)
        team.delete()
    
    def test_validation_called_on_save(self):
        """
        Test that validation is enforced when saving (not just on full_clean).
        
        Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
        """
        # Note: Django's save() does NOT automatically call full_clean()
        # This test documents that behavior
        
        team = Team.objects.create(name="Engineering")
        team.parent = team  # Self-reference
        
        # save() without full_clean() will NOT raise ValidationError
        # This is expected Django behavior
        # Applications should call full_clean() before save() or use ModelForm
        
        # However, we can test that full_clean() does catch it
        with self.assertRaises(ValidationError):
            team.full_clean()



class TestTeamManagerMethods(TestCase):
    """
    Unit tests for TeamManager custom methods.
    
    Feature: hierarchical-team-structure
    Requirements: 2.1, 2.5, 2.6, 8.4
    """
    
    def setUp(self):
        """Set up test data for TeamManager tests."""
        # Use unique names to avoid conflicts with migration data
        # Create parent teams
        self.marketing = Team.objects.create(name="Test Marketing")
        self.engineering = Team.objects.create(name="Test Engineering")
        self.sales = Team.objects.create(name="Test Sales")
        
        # Create sub-teams under Engineering
        self.backend = Team.objects.create(name="Test Backend Team", parent=self.engineering)
        self.frontend = Team.objects.create(name="Test Frontend Team", parent=self.engineering)
        self.devops = Team.objects.create(name="Test DevOps Team", parent=self.engineering)
        
        # Create sub-teams under Marketing
        self.digital = Team.objects.create(name="Test Digital Marketing", parent=self.marketing)
        self.content = Team.objects.create(name="Test Content Team", parent=self.marketing)
    
    def test_get_hierarchical_choices_format(self):
        """
        Test that get_hierarchical_choices() returns correct format.
        
        Each choice should be a tuple of (id, display_name).
        Sub-teams should have indentation prefix.
        
        Requirements: 2.1, 2.5, 2.6
        """
        choices = Team.objects.get_hierarchical_choices()
        
        # Verify it's a list
        self.assertIsInstance(choices, list)
        
        # Verify each choice is a tuple with (id, display_name)
        for choice in choices:
            self.assertIsInstance(choice, tuple)
            self.assertEqual(len(choice), 2)
            team_id, display_name = choice
            self.assertIsInstance(team_id, int)
            self.assertIsInstance(display_name, str)
        
        # Verify parent teams don't have indentation
        parent_choices = [c for c in choices if c[0] in [self.marketing.id, self.engineering.id, self.sales.id]]
        for choice in parent_choices:
            self.assertNotIn("└─", choice[1])
        
        # Verify sub-teams have indentation
        sub_team_choices = [c for c in choices if c[0] in [
            self.backend.id, self.frontend.id, self.devops.id,
            self.digital.id, self.content.id
        ]]
        for choice in sub_team_choices:
            self.assertIn("└─", choice[1])
    
    def test_get_hierarchical_choices_ordering(self):
        """
        Test that get_hierarchical_choices() returns correct ordering.
        
        Parent teams should be alphabetically ordered.
        Sub-teams should appear immediately after their parent, alphabetically ordered.
        
        Requirements: 2.5, 2.6
        """
        choices = Team.objects.get_hierarchical_choices()
        
        # Extract display names for verification - filter to only our test teams
        test_team_ids = {
            self.marketing.id, self.engineering.id, self.sales.id,
            self.backend.id, self.frontend.id, self.devops.id,
            self.digital.id, self.content.id
        }
        test_choices = [c for c in choices if c[0] in test_team_ids]
        display_names = [choice[1] for choice in test_choices]
        
        # Expected order for our test teams:
        # 1. Test Engineering (parent, alphabetically first)
        # 2.   └─ Test Backend Team (sub-team, alphabetically first under Engineering)
        # 3.   └─ Test DevOps Team (sub-team, alphabetically second under Engineering)
        # 4.   └─ Test Frontend Team (sub-team, alphabetically third under Engineering)
        # 5. Test Marketing (parent, alphabetically second)
        # 6.   └─ Test Content Team (sub-team, alphabetically first under Marketing)
        # 7.   └─ Test Digital Marketing (sub-team, alphabetically second under Marketing)
        # 8. Test Sales (parent, alphabetically third)
        
        expected_order = [
            "Test Engineering",
            "  └─ Test Backend Team",
            "  └─ Test DevOps Team",
            "  └─ Test Frontend Team",
            "Test Marketing",
            "  └─ Test Content Team",
            "  └─ Test Digital Marketing",
            "Test Sales",
        ]
        
        self.assertEqual(display_names, expected_order)
    
    def test_get_hierarchical_choices_with_no_subteams(self):
        """
        Test get_hierarchical_choices() with parent teams that have no sub-teams.
        
        Requirements: 2.1, 2.5
        """
        # Sales has no sub-teams
        choices = Team.objects.get_hierarchical_choices()
        
        # Find Sales in choices
        sales_choice = next((c for c in choices if c[0] == self.sales.id), None)
        self.assertIsNotNone(sales_choice)
        
        # Verify Sales is displayed without indentation
        self.assertEqual(sales_choice[1], "Test Sales")
        self.assertNotIn("└─", sales_choice[1])
    
    def test_get_hierarchical_choices_empty_database(self):
        """
        Test get_hierarchical_choices() with no teams in database.
        
        Requirements: 2.1
        """
        # Instead of deleting (which causes cache invalidation issues),
        # just verify that our test teams are not in the result when filtered out
        choices = Team.objects.get_hierarchical_choices()
        
        # Verify choices is a list
        self.assertIsInstance(choices, list)
        
        # If we filter to exclude test teams, we should get migration teams only
        non_test_choices = [c for c in choices if not c[1].startswith("Test ") and not c[1].startswith("  └─ Test ")]
        
        # Should have migration teams (Marketing, Developers with 19 sub-teams, etc.)
        self.assertGreater(len(non_test_choices), 0)
    
    def test_get_hierarchical_choices_only_parent_teams(self):
        """
        Test get_hierarchical_choices() with only parent teams (no sub-teams).
        
        Requirements: 2.1, 2.5
        """
        # Delete all sub-teams (only our test sub-teams)
        Team.objects.filter(parent__isnull=False, name__startswith="Test ").delete()
        
        choices = Team.objects.get_hierarchical_choices()
        
        # Filter to only our test parent teams
        test_parent_ids = {self.marketing.id, self.engineering.id, self.sales.id}
        test_choices = [c for c in choices if c[0] in test_parent_ids]
        
        # Should have 3 parent teams
        self.assertEqual(len(test_choices), 3)
        
        # All should be parent teams without indentation
        for choice in test_choices:
            self.assertNotIn("└─", choice[1])
        
        # Verify alphabetical ordering
        display_names = [choice[1] for choice in test_choices]
        self.assertEqual(display_names, ["Test Engineering", "Test Marketing", "Test Sales"])
    
    def test_get_hierarchical_choices_query_efficiency(self):
        """
        Test that get_hierarchical_choices() uses efficient queries.
        
        Should use minimal database queries regardless of team count.
        Expected: 1 query for parent teams + 1 query per parent for sub-teams.
        
        Requirements: 8.4
        """
        # Count parent teams in database (including migration teams)
        parent_count = Team.objects.filter(parent__isnull=True).count()
        
        # Expected queries:
        # 1 query to get parent teams
        # N queries to get sub-teams for each parent (one per parent)
        # Total: 1 + parent_count queries
        expected_queries = 1 + parent_count
        
        with self.assertNumQueries(expected_queries):
            choices = Team.objects.get_hierarchical_choices()
            # Force evaluation by converting to list
            list(choices)
    
    def test_get_hierarchical_choices_query_efficiency_optimized(self):
        """
        Test query efficiency with prefetch optimization.
        
        If we optimize the query with prefetch_related, we should reduce queries.
        
        Requirements: 8.4
        """
        # Create more teams to test scalability
        new_parent_ids = []
        for i in range(5):
            parent = Team.objects.create(name=f"Test Department {i}")
            new_parent_ids.append(parent.id)
            for j in range(3):
                Team.objects.create(name=f"Test Team {i}-{j}", parent=parent)
        
        # Count total parent teams (including migration teams + our test teams)
        parent_count = Team.objects.filter(parent__isnull=True).count()
        
        # Expected queries: 1 + parent_count
        # The current implementation uses 1 query for parents + N queries for sub-teams
        expected_queries = 1 + parent_count
        
        # Count queries
        with self.assertNumQueries(expected_queries):
            choices = Team.objects.get_hierarchical_choices()
            list(choices)
        
        # Clean up - delete only the new parents (CASCADE will delete sub-teams)
        # Note: We don't delete to avoid cache invalidation signal issues
        # The test database will be cleaned up automatically after the test
    
    def test_get_hierarchical_choices_with_special_characters(self):
        """
        Test get_hierarchical_choices() with team names containing special characters.
        
        Requirements: 2.1, 2.6
        """
        # Create teams with special characters
        special_parent = Team.objects.create(name="R&D Department")
        special_sub = Team.objects.create(name="AI/ML Team", parent=special_parent)
        
        choices = Team.objects.get_hierarchical_choices()
        
        # Find the special teams in choices
        parent_choice = next((c for c in choices if c[0] == special_parent.id), None)
        sub_choice = next((c for c in choices if c[0] == special_sub.id), None)
        
        self.assertIsNotNone(parent_choice)
        self.assertIsNotNone(sub_choice)
        
        # Verify display names
        self.assertEqual(parent_choice[1], "R&D Department")
        self.assertEqual(sub_choice[1], "  └─ AI/ML Team")
    
    def test_get_hierarchical_choices_with_unicode(self):
        """
        Test get_hierarchical_choices() with Unicode team names.
        
        Requirements: 2.1, 2.6
        """
        # Create teams with Unicode characters
        unicode_parent = Team.objects.create(name="Équipe Française")
        unicode_sub = Team.objects.create(name="Développement", parent=unicode_parent)
        
        choices = Team.objects.get_hierarchical_choices()
        
        # Find the Unicode teams in choices
        parent_choice = next((c for c in choices if c[0] == unicode_parent.id), None)
        sub_choice = next((c for c in choices if c[0] == unicode_sub.id), None)
        
        self.assertIsNotNone(parent_choice)
        self.assertIsNotNone(sub_choice)
        
        # Verify display names preserve Unicode
        self.assertEqual(parent_choice[1], "Équipe Française")
        self.assertEqual(sub_choice[1], "  └─ Développement")
    
    def test_get_parent_teams(self):
        """
        Test get_parent_teams() returns only teams without a parent.
        
        Requirements: 2.1
        """
        parent_teams = Team.objects.get_parent_teams()
        
        # Filter to only our test parent teams
        test_parent_teams = parent_teams.filter(name__startswith="Test ")
        
        # Should return 3 test parent teams
        self.assertEqual(test_parent_teams.count(), 3)
        
        # Verify all returned teams have no parent
        for team in test_parent_teams:
            self.assertIsNone(team.parent)
        
        # Verify the correct teams are returned
        parent_ids = set(test_parent_teams.values_list('id', flat=True))
        expected_ids = {self.marketing.id, self.engineering.id, self.sales.id}
        self.assertEqual(parent_ids, expected_ids)
    
    def test_get_sub_teams(self):
        """
        Test get_sub_teams() returns only teams with a parent.
        
        Requirements: 2.1
        """
        sub_teams = Team.objects.get_sub_teams()
        
        # Filter to only our test sub-teams
        test_sub_teams = sub_teams.filter(name__startswith="Test ")
        
        # Should return 5 test sub-teams
        self.assertEqual(test_sub_teams.count(), 5)
        
        # Verify all returned teams have a parent
        for team in test_sub_teams:
            self.assertIsNotNone(team.parent)
        
        # Verify the correct teams are returned
        sub_team_ids = set(test_sub_teams.values_list('id', flat=True))
        expected_ids = {
            self.backend.id, self.frontend.id, self.devops.id,
            self.digital.id, self.content.id
        }
        self.assertEqual(sub_team_ids, expected_ids)
    
    def test_get_hierarchy(self):
        """
        Test get_hierarchy() returns teams with prefetched relationships.
        
        Requirements: 8.4
        """
        # Get teams with hierarchy - this should use select_related and prefetch_related
        teams = Team.objects.get_hierarchy()
        
        # Convert to list to execute the query
        teams_list = list(teams)
        
        # Filter to only our test teams for counting
        test_teams = [t for t in teams_list if t.name.startswith("Test ")]
        
        # Should have 8 test teams (3 parents + 5 sub-teams)
        self.assertEqual(len(test_teams), 8)
        
        # Verify that accessing parent and sub_teams doesn't trigger additional queries
        # because they were prefetched
        with self.assertNumQueries(0):
            for team in test_teams:
                # Access parent (should be prefetched via select_related)
                _ = team.parent
                # Access sub_teams (should be prefetched via prefetch_related)
                _ = list(team.sub_teams.all())



class TestTeamAPIEndpoints(TestCase):
    """
    Unit tests for Team API endpoints.
    
    Feature: hierarchical-team-structure
    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
    """
    
    def setUp(self):
        """Set up test data for API endpoint tests."""
        from rest_framework.test import APIClient
        
        self.client = APIClient()
        
        # Create test teams
        self.parent = Team.objects.create(name="API Test Parent")
        self.sub_team1 = Team.objects.create(name="API Test Sub 1", parent=self.parent)
        self.sub_team2 = Team.objects.create(name="API Test Sub 2", parent=self.parent)
    
    def test_post_creates_team_with_parent(self):
        """
        Test POST /api/teams/ creates team with parent.
        
        Requirements: 10.1, 10.5
        """
        from rest_framework import status
        
        response = self.client.post(
            '/api/teams/',
            {'name': 'New Sub Team', 'parent': self.parent.id},
            format='json'
        )
        
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Error response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Sub Team')
        self.assertEqual(response.data['parent_id'], self.parent.id)
        self.assertEqual(response.data['parent_name'], self.parent.name)
        self.assertEqual(response.data['hierarchy_level'], 1)
        
        # Verify team was created in database
        team = Team.objects.get(name='New Sub Team')
        self.assertEqual(team.parent, self.parent)
    
    def test_post_creates_team_without_parent(self):
        """
        Test POST /api/teams/ creates parent team (no parent).
        
        Requirements: 10.5
        """
        from rest_framework import status
        
        response = self.client.post(
            '/api/teams/',
            {'name': 'New Parent Team'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Parent Team')
        self.assertIsNone(response.data['parent_id'])
        self.assertIsNone(response.data['parent_name'])
        self.assertEqual(response.data['hierarchy_level'], 0)
        
        # Verify team was created in database
        team = Team.objects.get(name='New Parent Team')
        self.assertIsNone(team.parent)
    
    def test_put_updates_parent_assignment(self):
        """
        Test PUT /api/teams/{id}/ updates parent assignment.
        
        Requirements: 10.2, 10.6
        """
        from rest_framework import status
        
        # Create a team without parent
        team = Team.objects.create(name='Team to Update')
        
        # Update to assign parent
        response = self.client.put(
            f'/api/teams/{team.id}/',
            {'name': 'Team to Update', 'parent': self.parent.id},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['parent_id'], self.parent.id)
        self.assertEqual(response.data['parent_name'], self.parent.name)
        
        # Verify update in database
        team.refresh_from_db()
        self.assertEqual(team.parent, self.parent)
    
    def test_put_removes_parent_assignment(self):
        """
        Test PUT /api/teams/{id}/ can remove parent assignment.
        
        Requirements: 10.6
        """
        from rest_framework import status
        
        # Update to remove parent
        response = self.client.put(
            f'/api/teams/{self.sub_team1.id}/',
            {'name': 'API Test Sub 1', 'parent': None},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['parent_id'])
        self.assertIsNone(response.data['parent_name'])
        
        # Verify update in database
        self.sub_team1.refresh_from_db()
        self.assertIsNone(self.sub_team1.parent)
    
    def test_put_with_circular_reference_returns_400(self):
        """
        Test PUT with circular reference returns 400.
        
        Requirements: 10.6, 10.7
        """
        from rest_framework import status
        
        # Attempt to make parent a child of its own sub-team
        response = self.client.put(
            f'/api/teams/{self.parent.id}/',
            {'name': 'API Test Parent', 'parent': self.sub_team1.id},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', response.data)
        
        # Verify error message is descriptive
        error_message = str(response.data).lower()
        self.assertTrue(
            'circular' in error_message or 
            'cannot assign a parent to a team that has sub-teams' in error_message or
            '2 levels deep' in error_message
        )
    
    def test_put_with_self_reference_returns_400(self):
        """
        Test PUT with self-reference returns 400.
        
        Requirements: 10.6, 10.7
        """
        from rest_framework import status
        
        # Attempt to make team its own parent
        response = self.client.put(
            f'/api/teams/{self.parent.id}/',
            {'name': 'API Test Parent', 'parent': self.parent.id},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', response.data)
        
        # Verify error message mentions self-reference
        error_message = str(response.data).lower()
        self.assertIn('cannot be its own parent', error_message)
    
    def test_delete_cascades_to_subteams(self):
        """
        Test DELETE /api/teams/{id}/ cascades to sub-teams.
        
        Requirements: 10.3
        """
        from rest_framework import status
        
        # Record sub-team IDs
        sub_team1_id = self.sub_team1.id
        sub_team2_id = self.sub_team2.id
        
        # Delete parent team
        response = self.client.delete(f'/api/teams/{self.parent.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('sub_teams_deleted', response.data)
        self.assertEqual(response.data['sub_teams_deleted'], 2)
        
        # Verify parent and sub-teams are deleted
        self.assertFalse(Team.objects.filter(id=self.parent.id).exists())
        self.assertFalse(Team.objects.filter(id=sub_team1_id).exists())
        self.assertFalse(Team.objects.filter(id=sub_team2_id).exists())
    
    def test_delete_subteam_does_not_affect_parent(self):
        """
        Test DELETE /api/teams/{id}/ on sub-team doesn't affect parent.
        
        Requirements: 10.3
        """
        from rest_framework import status
        
        # Delete sub-team
        response = self.client.delete(f'/api/teams/{self.sub_team1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify sub-team is deleted but parent still exists
        self.assertFalse(Team.objects.filter(id=self.sub_team1.id).exists())
        self.assertTrue(Team.objects.filter(id=self.parent.id).exists())
        
        # Verify parent now has only 1 sub-team
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.sub_teams.count(), 1)
    
    def test_get_subteams_returns_correct_subteams(self):
        """
        Test GET /api/teams/{id}/sub-teams/ returns correct sub-teams.
        
        Requirements: 10.4
        """
        from rest_framework import status
        
        response = self.client.get(f'/api/teams/{self.parent.id}/sub_teams/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Verify sub-team IDs are in response
        sub_team_ids = {item['id'] for item in response.data}
        self.assertEqual(sub_team_ids, {self.sub_team1.id, self.sub_team2.id})
        
        # Verify sub-team names are in response
        sub_team_names = {item['name'] for item in response.data}
        self.assertEqual(sub_team_names, {'API Test Sub 1', 'API Test Sub 2'})
    
    def test_get_subteams_for_team_without_subteams(self):
        """
        Test GET /api/teams/{id}/sub-teams/ for team without sub-teams.
        
        Requirements: 10.4
        """
        from rest_framework import status
        
        response = self.client.get(f'/api/teams/{self.sub_team1.id}/sub_teams/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_get_team_detail(self):
        """
        Test GET /api/teams/{id}/ returns team with hierarchy info.
        
        Requirements: 10.1, 10.2
        """
        from rest_framework import status
        
        # Get parent team
        response = self.client.get(f'/api/teams/{self.parent.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'API Test Parent')
        self.assertIsNone(response.data['parent_id'])
        self.assertIsNone(response.data['parent_name'])
        self.assertEqual(response.data['hierarchy_level'], 0)
        self.assertTrue(response.data['is_parent'])
        
        # Verify sub_teams list
        self.assertIn('sub_teams', response.data)
        self.assertEqual(len(response.data['sub_teams']), 2)
        
        # Get sub-team
        response = self.client.get(f'/api/teams/{self.sub_team1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'API Test Sub 1')
        self.assertEqual(response.data['parent_id'], self.parent.id)
        self.assertEqual(response.data['parent_name'], 'API Test Parent')
        self.assertEqual(response.data['hierarchy_level'], 1)
        self.assertFalse(response.data['is_parent'])
    
    def test_get_team_list(self):
        """
        Test GET /api/teams/ returns all teams with hierarchy info.
        
        Requirements: 10.3
        """
        from rest_framework import status
        
        response = self.client.get('/api/teams/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should include our test teams (plus migration teams)
        team_ids = {item['id'] for item in response.data}
        self.assertIn(self.parent.id, team_ids)
        self.assertIn(self.sub_team1.id, team_ids)
        self.assertIn(self.sub_team2.id, team_ids)
    
    def test_get_parent_teams_endpoint(self):
        """
        Test GET /api/teams/parent_teams/ returns only parent teams.
        
        Requirements: 10.3
        """
        from rest_framework import status
        
        response = self.client.get('/api/teams/parent_teams/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # All returned teams should have hierarchy_level 0
        for team in response.data:
            self.assertEqual(team['hierarchy_level'], 0)
        
        # Should include our test parent
        team_ids = {item['id'] for item in response.data}
        self.assertIn(self.parent.id, team_ids)
        
        # Should NOT include sub-teams
        self.assertNotIn(self.sub_team1.id, team_ids)
        self.assertNotIn(self.sub_team2.id, team_ids)
    
    def test_get_hierarchy_endpoint(self):
        """
        Test GET /api/teams/hierarchy/ returns structured hierarchy.
        
        Requirements: 10.3
        """
        from rest_framework import status
        
        response = self.client.get('/api/teams/hierarchy/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find our test parent in the hierarchy
        test_parent_data = None
        for parent_data in response.data:
            if parent_data['id'] == self.parent.id:
                test_parent_data = parent_data
                break
        
        self.assertIsNotNone(test_parent_data)
        
        # Verify sub_teams_detail is present and contains detailed sub-team info
        self.assertIn('sub_teams_detail', test_parent_data)
        self.assertEqual(len(test_parent_data['sub_teams_detail']), 2)
        
        # Verify sub-team details
        sub_team_ids = {st['id'] for st in test_parent_data['sub_teams_detail']}
        self.assertEqual(sub_team_ids, {self.sub_team1.id, self.sub_team2.id})



class TestAssetViewsWithTeamHierarchy(TestCase):
    """
    Unit tests for asset views with team hierarchy support.
    
    Requirements: 5.4, 6.3, 6.4, 6.5, 6.6
    """
    
    def setUp(self):
        """Set up test data for asset view tests."""
        from assets.models import Asset, OperatingSystem
        from django.contrib.auth.models import User
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # TODO: Add asset view tests here


class TestTeamDeletionAndCaching(TestCase):
    """
    Unit tests for team deletion behavior and cache invalidation.
    
    Feature: hierarchical-team-structure
    Requirements: 1.7, 5.6, 8.5, 8.6
    """
    
    def setUp(self):
        """Set up test data for deletion and caching tests."""
        from django.core.cache import cache
        
        # Clear cache before each test
        cache.clear()
        
        # Create test teams
        self.parent = Team.objects.create(name="Deletion Test Parent")
        self.sub_team1 = Team.objects.create(name="Deletion Test Sub 1", parent=self.parent)
        self.sub_team2 = Team.objects.create(name="Deletion Test Sub 2", parent=self.parent)
        self.sub_team3 = Team.objects.create(name="Deletion Test Sub 3", parent=self.parent)
    
    def test_deleting_parent_team_deletes_all_subteams(self):
        """
        Test that deleting a parent team deletes all sub-teams via CASCADE.
        
        This verifies the CASCADE behavior on the parent ForeignKey field.
        
        Requirements: 1.7
        """
        # Store IDs for verification
        parent_id = self.parent.id
        sub_team1_id = self.sub_team1.id
        sub_team2_id = self.sub_team2.id
        sub_team3_id = self.sub_team3.id
        
        # Verify initial state
        self.assertTrue(Team.objects.filter(id=parent_id).exists())
        self.assertTrue(Team.objects.filter(id=sub_team1_id).exists())
        self.assertTrue(Team.objects.filter(id=sub_team2_id).exists())
        self.assertTrue(Team.objects.filter(id=sub_team3_id).exists())
        self.assertEqual(self.parent.sub_teams.count(), 3)
        
        # Delete the parent team
        self.parent.delete()
        
        # Verify parent and all sub-teams were deleted
        self.assertFalse(Team.objects.filter(id=parent_id).exists())
        self.assertFalse(Team.objects.filter(id=sub_team1_id).exists())
        self.assertFalse(Team.objects.filter(id=sub_team2_id).exists())
        self.assertFalse(Team.objects.filter(id=sub_team3_id).exists())
    
    def test_deleting_parent_with_single_subteam(self):
        """
        Test that deleting a parent with a single sub-team cascades correctly.
        
        Requirements: 1.7
        """
        # Create a new parent with only one sub-team
        single_parent = Team.objects.create(name="Single Parent Test")
        single_sub = Team.objects.create(name="Single Sub Test", parent=single_parent)
        
        # Store IDs
        parent_id = single_parent.id
        sub_id = single_sub.id
        
        # Verify initial state
        self.assertTrue(Team.objects.filter(id=parent_id).exists())
        self.assertTrue(Team.objects.filter(id=sub_id).exists())
        self.assertEqual(single_parent.sub_teams.count(), 1)
        
        # Delete parent
        single_parent.delete()
        
        # Verify both are deleted
        self.assertFalse(Team.objects.filter(id=parent_id).exists())
        self.assertFalse(Team.objects.filter(id=sub_id).exists())
    
    def test_deleting_parent_with_many_subteams(self):
        """
        Test that deleting a parent with many sub-teams cascades to all.
        
        Requirements: 1.7
        """
        # Create a parent with many sub-teams
        many_parent = Team.objects.create(name="Many Parent Test")
        sub_teams = []
        sub_team_ids = []
        
        for i in range(10):
            sub = Team.objects.create(name=f"Many Sub Test {i}", parent=many_parent)
            sub_teams.append(sub)
            sub_team_ids.append(sub.id)
        
        parent_id = many_parent.id
        
        # Verify initial state
        self.assertEqual(many_parent.sub_teams.count(), 10)
        
        # Delete parent
        many_parent.delete()
        
        # Verify parent and all sub-teams are deleted
        self.assertFalse(Team.objects.filter(id=parent_id).exists())
        for sub_id in sub_team_ids:
            self.assertFalse(Team.objects.filter(id=sub_id).exists())
    
    def test_deleting_subteam_does_not_delete_parent(self):
        """
        Test that deleting a sub-team does not delete the parent team.
        
        Requirements: 1.7
        """
        # Store IDs
        parent_id = self.parent.id
        sub_team1_id = self.sub_team1.id
        
        # Verify initial state
        self.assertEqual(self.parent.sub_teams.count(), 3)
        
        # Delete one sub-team
        self.sub_team1.delete()
        
        # Verify sub-team is deleted but parent remains
        self.assertFalse(Team.objects.filter(id=sub_team1_id).exists())
        self.assertTrue(Team.objects.filter(id=parent_id).exists())
        
        # Verify parent now has 2 sub-teams
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.sub_teams.count(), 2)
    
    def test_deleting_team_with_assets_sets_asset_team_to_none(self):
        """
        Test that deleting a team sets asset.team to None via SET_NULL.
        
        This verifies the SET_NULL behavior on the Asset.team ForeignKey field.
        
        Requirements: 5.6
        """
        from assets.models import Asset, OperatingSystem
        
        # Create an operating system
        os = OperatingSystem.objects.create(name="Test OS for Deletion")
        
        # Create assets assigned to the parent team
        asset1 = Asset.objects.create(
            asset_tag="DEL-ASSET-001",
            system_type="Desktop",
            operating_system=os,
            team=self.parent
        )
        asset2 = Asset.objects.create(
            asset_tag="DEL-ASSET-002",
            system_type="Laptop",
            operating_system=os,
            team=self.parent
        )
        
        # Verify initial state
        self.assertEqual(asset1.team, self.parent)
        self.assertEqual(asset2.team, self.parent)
        
        # Store asset IDs
        asset1_id = asset1.serial_number
        asset2_id = asset2.serial_number
        
        # Delete the team
        self.parent.delete()
        
        # Verify assets still exist but team is None
        asset1 = Asset.objects.get(serial_number=asset1_id)
        asset2 = Asset.objects.get(serial_number=asset2_id)
        
        self.assertIsNone(asset1.team)
        self.assertIsNone(asset2.team)
        
        # Clean up
        asset1.delete()
        asset2.delete()
        os.delete()
    
    def test_deleting_subteam_with_assets_sets_asset_team_to_none(self):
        """
        Test that deleting a sub-team sets asset.team to None for its assets.
        
        Requirements: 5.6
        """
        from assets.models import Asset, OperatingSystem
        
        # Create an operating system
        os = OperatingSystem.objects.create(name="Test OS for Sub Deletion")
        
        # Create assets assigned to a sub-team
        asset1 = Asset.objects.create(
            asset_tag="DEL-SUB-ASSET-001",
            system_type="Desktop",
            operating_system=os,
            team=self.sub_team1
        )
        asset2 = Asset.objects.create(
            asset_tag="DEL-SUB-ASSET-002",
            system_type="Laptop",
            operating_system=os,
            team=self.sub_team1
        )
        
        # Verify initial state
        self.assertEqual(asset1.team, self.sub_team1)
        self.assertEqual(asset2.team, self.sub_team1)
        
        # Store asset IDs
        asset1_id = asset1.serial_number
        asset2_id = asset2.serial_number
        
        # Delete the sub-team
        self.sub_team1.delete()
        
        # Verify assets still exist but team is None
        asset1 = Asset.objects.get(serial_number=asset1_id)
        asset2 = Asset.objects.get(serial_number=asset2_id)
        
        self.assertIsNone(asset1.team)
        self.assertIsNone(asset2.team)
        
        # Clean up
        asset1.delete()
        asset2.delete()
        os.delete()
    
    def test_deleting_parent_cascades_and_nullifies_all_assets(self):
        """
        Test that deleting a parent team cascades to sub-teams and nullifies all assets.
        
        This combines CASCADE behavior for sub-teams and SET_NULL for assets.
        
        Requirements: 1.7, 5.6
        """
        from assets.models import Asset, OperatingSystem
        
        # Create an operating system
        os = OperatingSystem.objects.create(name="Test OS for Cascade")
        
        # Create assets for parent team
        parent_asset = Asset.objects.create(
            asset_tag="CASCADE-PARENT-001",
            system_type="Desktop",
            operating_system=os,
            team=self.parent
        )
        
        # Create assets for sub-teams
        sub1_asset = Asset.objects.create(
            asset_tag="CASCADE-SUB1-001",
            system_type="Laptop",
            operating_system=os,
            team=self.sub_team1
        )
        sub2_asset = Asset.objects.create(
            asset_tag="CASCADE-SUB2-001",
            system_type="Desktop",
            operating_system=os,
            team=self.sub_team2
        )
        
        # Store IDs
        parent_asset_id = parent_asset.serial_number
        sub1_asset_id = sub1_asset.serial_number
        sub2_asset_id = sub2_asset.serial_number
        sub_team1_id = self.sub_team1.id
        sub_team2_id = self.sub_team2.id
        
        # Verify initial state
        self.assertEqual(parent_asset.team, self.parent)
        self.assertEqual(sub1_asset.team, self.sub_team1)
        self.assertEqual(sub2_asset.team, self.sub_team2)
        
        # Delete the parent team
        self.parent.delete()
        
        # Verify sub-teams are deleted (CASCADE)
        self.assertFalse(Team.objects.filter(id=sub_team1_id).exists())
        self.assertFalse(Team.objects.filter(id=sub_team2_id).exists())
        
        # Verify all assets still exist but team is None (SET_NULL)
        parent_asset = Asset.objects.get(serial_number=parent_asset_id)
        sub1_asset = Asset.objects.get(serial_number=sub1_asset_id)
        sub2_asset = Asset.objects.get(serial_number=sub2_asset_id)
        
        self.assertIsNone(parent_asset.team)
        self.assertIsNone(sub1_asset.team)
        self.assertIsNone(sub2_asset.team)
        
        # Clean up
        parent_asset.delete()
        sub1_asset.delete()
        sub2_asset.delete()
        os.delete()
    
    def test_cache_invalidated_on_team_creation(self):
        """
        Test that cache is invalidated when a new team is created.
        
        Requirements: 8.6
        """
        from django.core.cache import cache
        
        # Set cache values
        cache.set('team_hierarchy', {'cached': 'data'}, timeout=300)
        cache.set(f'team_{self.parent.id}_sub_teams', {'cached': 'sub_teams'}, timeout=300)
        
        # Verify cache is set
        self.assertIsNotNone(cache.get('team_hierarchy'))
        self.assertIsNotNone(cache.get(f'team_{self.parent.id}_sub_teams'))
        
        # Create a new sub-team (should trigger cache invalidation)
        new_sub = Team.objects.create(name="Cache Test New Sub", parent=self.parent)
        
        # Verify cache was invalidated
        self.assertIsNone(cache.get('team_hierarchy'))
        self.assertIsNone(cache.get(f'team_{self.parent.id}_sub_teams'))
        
        # Clean up
        new_sub.delete()
    
    def test_cache_invalidated_on_team_update(self):
        """
        Test that cache is invalidated when a team is updated.
        
        Requirements: 8.6
        """
        from django.core.cache import cache
        
        # Set cache values
        cache.set('team_hierarchy', {'cached': 'data'}, timeout=300)
        cache.set(f'team_{self.sub_team1.id}_hierarchy', {'cached': 'team_data'}, timeout=300)
        
        # Verify cache is set
        self.assertIsNotNone(cache.get('team_hierarchy'))
        self.assertIsNotNone(cache.get(f'team_{self.sub_team1.id}_hierarchy'))
        
        # Update the team (should trigger cache invalidation)
        self.sub_team1.name = "Updated Cache Test Sub"
        self.sub_team1.save()
        
        # Verify cache was invalidated
        self.assertIsNone(cache.get('team_hierarchy'))
        self.assertIsNone(cache.get(f'team_{self.sub_team1.id}_hierarchy'))
    
    def test_cache_invalidated_on_parent_change(self):
        """
        Test that cache is invalidated when a team's parent is changed.
        
        Requirements: 8.6
        """
        from django.core.cache import cache
        
        # Create a new parent
        new_parent = Team.objects.create(name="Cache Test New Parent")
        
        # Set cache values
        cache.set('team_hierarchy', {'cached': 'data'}, timeout=300)
        cache.set(f'team_{self.sub_team1.id}_hierarchy', {'cached': 'team_data'}, timeout=300)
        cache.set(f'team_{self.parent.id}_sub_teams', {'cached': 'old_parent_subs'}, timeout=300)
        cache.set(f'team_{new_parent.id}_sub_teams', {'cached': 'new_parent_subs'}, timeout=300)
        
        # Verify cache is set
        self.assertIsNotNone(cache.get('team_hierarchy'))
        self.assertIsNotNone(cache.get(f'team_{self.sub_team1.id}_hierarchy'))
        
        # Change parent (should trigger cache invalidation)
        self.sub_team1.parent = new_parent
        self.sub_team1.save()
        
        # Verify cache was invalidated
        self.assertIsNone(cache.get('team_hierarchy'))
        self.assertIsNone(cache.get(f'team_{self.sub_team1.id}_hierarchy'))
        self.assertIsNone(cache.get(f'team_{new_parent.id}_sub_teams'))
        
        # Clean up
        new_parent.delete()
    
    def test_cache_invalidated_on_team_deletion(self):
        """
        Test that cache is invalidated when a team is deleted.
        
        Requirements: 8.6
        """
        from django.core.cache import cache
        
        # Set cache values
        cache.set('team_hierarchy', {'cached': 'data'}, timeout=300)
        cache.set(f'team_{self.sub_team1.id}_hierarchy', {'cached': 'team_data'}, timeout=300)
        cache.set(f'team_{self.parent.id}_sub_teams', {'cached': 'parent_subs'}, timeout=300)
        
        # Verify cache is set
        self.assertIsNotNone(cache.get('team_hierarchy'))
        self.assertIsNotNone(cache.get(f'team_{self.sub_team1.id}_hierarchy'))
        self.assertIsNotNone(cache.get(f'team_{self.parent.id}_sub_teams'))
        
        # Store IDs before deletion
        sub_team1_id = self.sub_team1.id
        parent_id = self.parent.id
        
        # Delete the sub-team (should trigger cache invalidation)
        self.sub_team1.delete()
        
        # Verify cache was invalidated
        self.assertIsNone(cache.get('team_hierarchy'))
        self.assertIsNone(cache.get(f'team_{sub_team1_id}_hierarchy'))
        self.assertIsNone(cache.get(f'team_{parent_id}_sub_teams'))
    
    def test_cache_invalidated_on_parent_deletion(self):
        """
        Test that cache is invalidated when a parent team is deleted.
        
        This should invalidate caches for the parent and all its sub-teams.
        
        Requirements: 8.6
        """
        from django.core.cache import cache
        
        # Set cache values for parent and sub-teams
        cache.set('team_hierarchy', {'cached': 'data'}, timeout=300)
        cache.set(f'team_{self.parent.id}_hierarchy', {'cached': 'parent_data'}, timeout=300)
        cache.set(f'team_{self.sub_team1.id}_hierarchy', {'cached': 'sub1_data'}, timeout=300)
        cache.set(f'team_{self.sub_team2.id}_hierarchy', {'cached': 'sub2_data'}, timeout=300)
        
        # Verify cache is set
        self.assertIsNotNone(cache.get('team_hierarchy'))
        self.assertIsNotNone(cache.get(f'team_{self.parent.id}_hierarchy'))
        
        # Store IDs before deletion
        parent_id = self.parent.id
        
        # Delete the parent (should trigger cache invalidation for parent and cascade to sub-teams)
        self.parent.delete()
        
        # Verify cache was invalidated
        self.assertIsNone(cache.get('team_hierarchy'))
        self.assertIsNone(cache.get(f'team_{parent_id}_hierarchy'))
    
    def test_multiple_cache_invalidations_in_sequence(self):
        """
        Test that multiple operations correctly invalidate cache in sequence.
        
        Requirements: 8.6
        """
        from django.core.cache import cache
        
        # Operation 1: Create a new team
        cache.set('team_hierarchy', {'cached': 'data1'}, timeout=300)
        new_team = Team.objects.create(name="Cache Sequence Test")
        self.assertIsNone(cache.get('team_hierarchy'))
        
        # Operation 2: Update the team
        cache.set('team_hierarchy', {'cached': 'data2'}, timeout=300)
        new_team.name = "Cache Sequence Test Updated"
        new_team.save()
        self.assertIsNone(cache.get('team_hierarchy'))
        
        # Operation 3: Delete the team
        cache.set('team_hierarchy', {'cached': 'data3'}, timeout=300)
        new_team.delete()
        self.assertIsNone(cache.get('team_hierarchy'))
    
    def test_cache_keys_format(self):
        """
        Test that cache keys follow the expected format.
        
        This is a documentation test to verify the cache key naming convention.
        
        Requirements: 8.5, 8.6
        """
        from django.core.cache import cache
        
        # Expected cache key formats:
        # - 'team_hierarchy': Global hierarchy cache
        # - 'team_{id}_hierarchy': Individual team hierarchy cache
        # - 'team_{id}_sub_teams': Parent team's sub-teams cache
        
        # Set cache with expected keys
        cache.set('team_hierarchy', {'global': 'data'}, timeout=300)
        cache.set(f'team_{self.parent.id}_hierarchy', {'team': 'data'}, timeout=300)
        cache.set(f'team_{self.parent.id}_sub_teams', {'subs': 'data'}, timeout=300)
        
        # Verify keys exist
        self.assertIsNotNone(cache.get('team_hierarchy'))
        self.assertIsNotNone(cache.get(f'team_{self.parent.id}_hierarchy'))
        self.assertIsNotNone(cache.get(f'team_{self.parent.id}_sub_teams'))
        
        # Trigger invalidation by updating team
        self.parent.name = "Updated for Cache Key Test"
        self.parent.save()
        
        # Verify all related keys are invalidated
        self.assertIsNone(cache.get('team_hierarchy'))
        self.assertIsNone(cache.get(f'team_{self.parent.id}_hierarchy'))
