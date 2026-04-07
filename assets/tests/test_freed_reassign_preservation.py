"""
Preservation Property Tests for Freed System Reassignment Form

**Property 2: Preservation** - Successful Form Submission Behavior

These tests verify that valid form submissions continue to work correctly
after the JavaScript fix is implemented. They test the baseline behavior
on UNFIXED code and should PASS to confirm what needs to be preserved.

**IMPORTANT**: These tests follow observation-first methodology:
1. Run tests on UNFIXED code to observe baseline behavior
2. Tests should PASS on unfixed code (confirms baseline)
3. After implementing fix, re-run tests to ensure no regressions

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase as HypothesisTestCase
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from assets.models import Asset, OperatingSystem, Team, IPAddress, IPRange


class TestFreedReassignPreservation(TestCase):
    """
    **Property 2: Preservation** - Successful Form Submission Behavior
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
    
    These tests verify that valid form submissions work correctly and must
    continue to work after the JavaScript fix is implemented.
    
    **EXPECTED OUTCOME**: All tests PASS on unfixed code (confirms baseline behavior)
    """
    
    def setUp(self):
        """Set up test data for preservation tests."""
        # Create admin user (required for reassignment)
        self.admin_user = User.objects.create_user(
            username='admin_preserve_test',
            password='adminpass123',
            is_staff=True
        )
        
        # Create non-admin user for access control tests
        self.regular_user = User.objects.create_user(
            username='regular_preserve_test',
            password='regularpass123',
            is_staff=False
        )
        
        # Create test OS
        self.os = OperatingSystem.objects.create(name="Windows 10 Preserve")
        
        # Create IP range and multiple IP addresses
        self.ip_range = IPRange.objects.create(
            range_pattern="192.168.30.x",
            network_prefix="192.168.30"
        )
        self.ip1 = IPAddress.objects.create(
            address="192.168.30.100",
            ip_range=self.ip_range,
            is_assigned=False
        )
        self.ip2 = IPAddress.objects.create(
            address="192.168.30.101",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create parent team
        self.parent_team = Team.objects.create(
            name="Engineering Dept",
            parent=None
        )
        
        # Create sub-team
        self.sub_team = Team.objects.create(
            name="Backend Team",
            parent=self.parent_team
        )
        
        # Create freed asset (healthy, ready for reassignment)
        self.freed_asset = Asset.objects.create(
            asset_tag="BIDC002PRESERVE",
            system_type="Desktop",
            operating_system=self.os,
            ip_address=self.ip1,
            status="freed",
            freed_date=timezone.now(),
            health_status="healthy"
        )
        
        # Create active asset for status validation test
        self.active_asset = Asset.objects.create(
            asset_tag="BIDC003ACTIVE",
            system_type="Desktop",
            operating_system=self.os,
            ip_address=self.ip2,
            status="active",
            team=self.parent_team
        )
    
    def test_preservation_valid_form_submission_with_parent_team(self):
        """
        **Property 2: Preservation** - Valid Form Submission with Parent Team
        
        **Validates: Requirements 3.1, 3.2, 3.3**
        
        Test that valid form submission with parent team (no sub-team) works correctly.
        
        This is the core preservation test: when all required fields including the
        hidden team field are properly populated, the form should submit successfully,
        reassign the asset, and redirect to the active assets page.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Login as admin
        self.client.login(username='admin_preserve_test', password='adminpass123')
        
        # Prepare valid form data with parent team
        post_data = {
            'assigned_to': 'assigned',
            'parent_team': self.parent_team.id,
            'team': self.parent_team.id,  # Hidden field properly populated
            'ip_address': self.ip1.id,
            'system_type': 'Desktop',
            'operating_system': self.os.id,
        }
        
        # Submit form
        response = self.client.post(
            reverse('asset_reassign', kwargs={'pk': self.freed_asset.pk}),
            data=post_data,
            follow=False
        )
        
        # Should redirect to active assets page (success)
        self.assertEqual(
            response.status_code,
            302,
            "Valid form submission should redirect to success page"
        )
        self.assertEqual(
            response.url,
            reverse('asset_list'),
            "Should redirect to active assets page after successful reassignment"
        )
        
        # Verify asset was reassigned
        self.freed_asset.refresh_from_db()
        self.assertEqual(
            self.freed_asset.status,
            'active',
            "Asset status should be changed to 'active' after reassignment"
        )
        self.assertEqual(
            self.freed_asset.team,
            self.parent_team,
            "Asset should be assigned to the selected team"
        )
        self.assertIsNone(
            self.freed_asset.freed_date,
            "Freed date should be cleared after reassignment"
        )
    
    def test_preservation_valid_form_submission_with_sub_team(self):
        """
        **Property 2: Preservation** - Valid Form Submission with Sub-Team
        
        **Validates: Requirements 3.1, 3.2, 3.3**
        
        Test that valid form submission with sub-team selection works correctly.
        
        When a sub-team is selected, the hidden team field should contain the
        sub-team ID, and the asset should be assigned to the sub-team.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Login as admin
        self.client.login(username='admin_preserve_test', password='adminpass123')
        
        # Prepare valid form data with sub-team
        post_data = {
            'assigned_to': 'assigned',
            'parent_team': self.parent_team.id,
            'sub_team': self.sub_team.id,
            'team': self.sub_team.id,  # Hidden field set to sub-team
            'ip_address': self.ip1.id,
            'system_type': 'Desktop',
            'operating_system': self.os.id,
        }
        
        # Submit form
        response = self.client.post(
            reverse('asset_reassign', kwargs={'pk': self.freed_asset.pk}),
            data=post_data,
            follow=False
        )
        
        # Should redirect to success page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('asset_list'))
        
        # Verify asset was assigned to sub-team
        self.freed_asset.refresh_from_db()
        self.assertEqual(self.freed_asset.status, 'active')
        self.assertEqual(
            self.freed_asset.team,
            self.sub_team,
            "Asset should be assigned to the selected sub-team"
        )
    
    def test_preservation_server_side_validation_non_freed_asset(self):
        """
        **Property 2: Preservation** - Server-Side Validation for Non-Freed Assets
        
        **Validates: Requirements 3.6**
        
        Test that server-side validation prevents reassignment of non-freed assets.
        
        Only assets with status='freed' should be reassignable. Attempting to
        reassign an active asset should result in an error message and redirect.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Login as admin
        self.client.login(username='admin_preserve_test', password='adminpass123')
        
        # Attempt to reassign active asset
        post_data = {
            'assigned_to': 'assigned',
            'parent_team': self.parent_team.id,
            'team': self.parent_team.id,
            'ip_address': self.ip2.id,
            'system_type': 'Desktop',
            'operating_system': self.os.id,
        }
        
        response = self.client.post(
            reverse('asset_reassign', kwargs={'pk': self.active_asset.pk}),
            data=post_data,
            follow=True
        )
        
        # Should redirect to freed systems page with error
        self.assertRedirects(response, reverse('freed_systems'))
        
        # Check for error message
        messages = list(response.context['messages'])
        self.assertTrue(
            any('Only freed assets can be reassigned' in str(m) for m in messages),
            "Should display error message for non-freed asset"
        )
        
        # Asset should remain active
        self.active_asset.refresh_from_db()
        self.assertEqual(self.active_asset.status, 'active')
    
    def test_preservation_access_control_non_admin(self):
        """
        **Property 2: Preservation** - Access Control for Non-Admin Users
        
        **Validates: Requirements 3.5**
        
        Test that non-admin users cannot access the reassignment page.
        
        The reassignment functionality is admin-only. Non-admin users should
        receive a 403 Forbidden response.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Login as regular user (non-admin)
        self.client.login(username='regular_preserve_test', password='regularpass123')
        
        # Attempt to access reassignment page
        response = self.client.get(
            reverse('asset_reassign', kwargs={'pk': self.freed_asset.pk})
        )
        
        # Should return 403 Forbidden
        self.assertEqual(
            response.status_code,
            403,
            "Non-admin users should receive 403 Forbidden when accessing reassignment page"
        )
        
        # Attempt to submit reassignment form
        post_data = {
            'assigned_to': 'assigned',
            'parent_team': self.parent_team.id,
            'team': self.parent_team.id,
            'ip_address': self.ip1.id,
            'system_type': 'Desktop',
            'operating_system': self.os.id,
        }
        
        response = self.client.post(
            reverse('asset_reassign', kwargs={'pk': self.freed_asset.pk}),
            data=post_data
        )
        
        # Should return 403 Forbidden
        self.assertEqual(
            response.status_code,
            403,
            "Non-admin users should receive 403 Forbidden when submitting reassignment form"
        )
        
        # Asset should remain freed
        self.freed_asset.refresh_from_db()
        self.assertEqual(self.freed_asset.status, 'freed')
    
    def test_preservation_form_display_with_all_fields(self):
        """
        **Property 2: Preservation** - Form Display with All Fields
        
        **Validates: Requirements 3.4**
        
        Test that the reassignment form displays correctly with all expected fields.
        
        The form should show:
        - Asset details (tag, type, OS, health status)
        - Team dropdowns (parent team, sub-team)
        - IP address selection
        - System type selection
        - Operating system selection
        - Other optional fields
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Login as admin
        self.client.login(username='admin_preserve_test', password='adminpass123')
        
        # Get reassignment form
        response = self.client.get(
            reverse('asset_reassign', kwargs={'pk': self.freed_asset.pk})
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that form is in context
        self.assertIn('form', response.context)
        self.assertIn('asset', response.context)
        
        # Check that asset details are displayed
        self.assertContains(response, self.freed_asset.asset_tag)
        self.assertContains(response, self.freed_asset.system_type)
        self.assertContains(response, self.freed_asset.operating_system.name)
        
        # Check that form fields are present
        form = response.context['form']
        self.assertIn('assigned_to', form.fields)
        self.assertIn('parent_team', form.fields)
        self.assertIn('sub_team', form.fields)
        self.assertIn('team', form.fields)
        self.assertIn('ip_address', form.fields)
        self.assertIn('system_type', form.fields)
        self.assertIn('operating_system', form.fields)
    
    def test_preservation_success_redirect_with_message(self):
        """
        **Property 2: Preservation** - Success Redirect with Message
        
        **Validates: Requirements 3.1**
        
        Test that successful reassignment redirects to active assets page
        with a success message.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Login as admin
        self.client.login(username='admin_preserve_test', password='adminpass123')
        
        # Submit valid form
        post_data = {
            'assigned_to': 'assigned',
            'parent_team': self.parent_team.id,
            'team': self.parent_team.id,
            'ip_address': self.ip1.id,
            'system_type': 'Desktop',
            'operating_system': self.os.id,
        }
        
        response = self.client.post(
            reverse('asset_reassign', kwargs={'pk': self.freed_asset.pk}),
            data=post_data,
            follow=True
        )
        
        # Should redirect to active assets page
        self.assertRedirects(response, reverse('asset_list'))
        
        # Check for success message
        messages = list(response.context['messages'])
        self.assertTrue(
            any('has been reassigned and is now active' in str(m) for m in messages),
            "Should display success message after reassignment"
        )


class TestFreedReassignPreservationPropertyBased(HypothesisTestCase):
    """
    Property-Based Tests for Preservation
    
    **Property 2: Preservation** - Successful Form Submission Behavior
    
    **Validates: Requirements 3.1, 3.2, 3.3**
    
    These property-based tests generate many test cases to verify that
    valid form submissions work correctly across a wide range of inputs.
    
    **EXPECTED OUTCOME**: All tests PASS on unfixed code (confirms baseline behavior)
    """
    
    def setUp(self):
        """Set up test data for property-based tests."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin_pbt_preserve',
            password='adminpass123',
            is_staff=True
        )
        
        # Create test OS
        self.os = OperatingSystem.objects.create(name="Windows 10 PBT")
        
        # Create IP range and IP addresses
        self.ip_range = IPRange.objects.create(
            range_pattern="192.168.40.x",
            network_prefix="192.168.40"
        )
        
        # Create parent team
        self.parent_team = Team.objects.create(
            name="IT Dept PBT",
            parent=None
        )
    
    @given(
        system_type=st.sampled_from(['Desktop', 'Laptop', 'All-in-One PC']),
        manufacturer=st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        particulars=st.text(min_size=0, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N', 'P')))
    )
    @settings(max_examples=20, deadline=None)
    def test_property_preservation_valid_submissions_succeed(self, system_type, manufacturer, particulars):
        """
        **Property 2: Preservation** - Valid Submissions Always Succeed
        
        **Validates: Requirements 3.1, 3.2, 3.3**
        
        Property: For any valid form submission where the hidden team field is
        properly populated, the form should submit successfully and reassign the asset.
        
        This property-based test generates many test cases with different
        system types, manufacturers, and particulars to ensure the fix doesn't
        break any valid submission scenarios.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Clean up any previous test data
        Asset.objects.filter(asset_tag__startswith='PBTP').delete()
        IPAddress.objects.filter(address__startswith='192.168.40.').delete()
        
        # Create IP address for this test
        ip = IPAddress.objects.create(
            address=f"192.168.40.{hash(system_type + manufacturer) % 200 + 10}",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create freed asset
        asset_tag = f"PBTP{hash(system_type + manufacturer + particulars) % 10000:04d}"
        freed_asset = Asset.objects.create(
            asset_tag=asset_tag,
            system_type=system_type,
            operating_system=self.os,
            ip_address=ip,
            status="freed",
            freed_date=timezone.now(),
            health_status="healthy"
        )
        
        # Login as admin
        client = Client()
        client.login(username='admin_pbt_preserve', password='adminpass123')
        
        # Prepare valid form data
        post_data = {
            'assigned_to': 'assigned',
            'parent_team': self.parent_team.id,
            'team': self.parent_team.id,  # Hidden field properly populated
            'ip_address': ip.id,
            'system_type': system_type,
            'operating_system': self.os.id,
            'manufacturer': manufacturer.strip(),
            'particulars': particulars.strip(),
        }
        
        # Submit form
        response = client.post(
            reverse('asset_reassign', kwargs={'pk': freed_asset.pk}),
            data=post_data,
            follow=False
        )
        
        # Property: Valid submissions should always redirect (success)
        self.assertEqual(
            response.status_code,
            302,
            f"Valid form submission should redirect. System type: {system_type}, "
            f"Manufacturer: {manufacturer[:20]}, Particulars: {particulars[:20]}"
        )
        
        # Property: Asset should always be reassigned to active status
        freed_asset.refresh_from_db()
        self.assertEqual(
            freed_asset.status,
            'active',
            f"Asset should be active after valid submission. System type: {system_type}"
        )
        
        # Property: Asset should be assigned to the correct team
        self.assertEqual(
            freed_asset.team,
            self.parent_team,
            f"Asset should be assigned to correct team. System type: {system_type}"
        )


class TestTeamDropdownAJAXPreservation(TestCase):
    """
    **Property 2: Preservation** - Team Dropdown AJAX Population
    
    **Validates: Requirements 3.4**
    
    Test that the team dropdown AJAX population continues to work correctly.
    
    The form uses AJAX to populate the sub-team dropdown when a parent team
    is selected. This functionality must continue to work after the fix.
    
    **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
    """
    
    def setUp(self):
        """Set up test data for AJAX tests."""
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='admin_ajax_test',
            password='adminpass123',
            is_staff=True
        )
        
        # Create parent team with sub-teams
        self.parent_team = Team.objects.create(
            name="Sales Dept",
            parent=None
        )
        self.sub_team1 = Team.objects.create(
            name="Inside Sales",
            parent=self.parent_team
        )
        self.sub_team2 = Team.objects.create(
            name="Outside Sales",
            parent=self.parent_team
        )
        
        # Create parent team without sub-teams
        self.parent_team_no_subs = Team.objects.create(
            name="HR Dept",
            parent=None
        )
    
    def test_preservation_ajax_get_sub_teams_with_children(self):
        """
        **Property 2: Preservation** - AJAX Returns Sub-Teams When They Exist
        
        **Validates: Requirements 3.4**
        
        Test that the AJAX endpoint returns sub-teams when the parent team
        has children.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Login as admin
        self.client.login(username='admin_ajax_test', password='adminpass123')
        
        # Make AJAX request
        response = self.client.get(
            '/assets/api/get-sub-teams/',
            {'parent_id': self.parent_team.id}
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Should return JSON
        data = response.json()
        
        # Should indicate sub-teams exist
        self.assertTrue(
            data.get('has_sub_teams'),
            "AJAX response should indicate sub-teams exist"
        )
        
        # Should return list of sub-teams
        self.assertIn('sub_teams', data)
        self.assertEqual(len(data['sub_teams']), 2)
        
        # Check sub-team data
        sub_team_ids = [st['id'] for st in data['sub_teams']]
        self.assertIn(self.sub_team1.id, sub_team_ids)
        self.assertIn(self.sub_team2.id, sub_team_ids)
    
    def test_preservation_ajax_get_sub_teams_without_children(self):
        """
        **Property 2: Preservation** - AJAX Returns Empty When No Sub-Teams
        
        **Validates: Requirements 3.4**
        
        Test that the AJAX endpoint returns empty list when the parent team
        has no children.
        
        **EXPECTED OUTCOME**: Test PASSES on unfixed code (baseline behavior)
        """
        # Login as admin
        self.client.login(username='admin_ajax_test', password='adminpass123')
        
        # Make AJAX request
        response = self.client.get(
            '/assets/api/get-sub-teams/',
            {'parent_id': self.parent_team_no_subs.id}
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Should return JSON
        data = response.json()
        
        # Should indicate no sub-teams
        self.assertFalse(
            data.get('has_sub_teams'),
            "AJAX response should indicate no sub-teams exist"
        )
        
        # Should return empty list
        self.assertIn('sub_teams', data)
        self.assertEqual(len(data['sub_teams']), 0)
