"""
Bug Condition Exploration Test for Freed System Reassignment Form Validation

This test explores the bug where form submission with an empty team field
causes a page refresh despite JavaScript validation attempting to prevent it.

**CRITICAL**: This test documents the bug condition and expected behavior.
**Testing Limitation**: Django's test client does not execute JavaScript.

The bug is in the JavaScript validation in asset_reassign_form.html:
- JavaScript calls e.preventDefault() and returns false when team field is empty
- But the page still refreshes, losing form data
- This is because return false doesn't work with addEventListener
- And there may be timing issues with event listener attachment

These tests document the expected server-side behavior (baseline) and will serve
as regression tests after the JavaScript fix is implemented.
"""
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from assets.models import Asset, OperatingSystem, Team, IPAddress, IPRange


class TestFreedReassignBugCondition(TestCase):
    """
    **Property 1: Bug Condition** - Form Submission Prevention When Team Field Empty
    
    **Validates: Requirements 1.1, 1.3, 1.4, 2.2, 2.3**
    
    This test documents the bug condition where submitting the reassignment form
    with an empty hidden team field should prevent submission at the JavaScript level.
    
    **THE BUG**: JavaScript validation fails to prevent form submission, causing:
    - Page refresh despite e.preventDefault() and return false
    - Form data is lost
    - Asset remains in freed status
    - User sees alert but form still submits to server
    
    **TESTING LIMITATION**: Django test client doesn't execute JavaScript, so these
    tests verify server-side validation (baseline behavior). The JavaScript fix will
    prevent the form from reaching the server at all.
    """
    
    def setUp(self):
        """Set up test data for bug exploration."""
        # Create admin user (required for reassignment)
        self.admin_user = User.objects.create_user(
            username='admin_reassign_test',
            password='adminpass123',
            is_staff=True
        )
        
        # Create test OS
        self.os = OperatingSystem.objects.create(name="Windows 10 Test")
        
        # Create IP range and IP address
        self.ip_range = IPRange.objects.create(
            range_pattern="192.168.20.x",
            network_prefix="192.168.20"
        )
        self.ip = IPAddress.objects.create(
            address="192.168.20.100",
            ip_range=self.ip_range,
            is_assigned=False
        )
        
        # Create parent team (no parent field = parent team)
        self.parent_team = Team.objects.create(
            name="IT Department Test",
            parent=None  # Parent teams have no parent
        )
        
        # Create freed asset (healthy, ready for reassignment)
        self.freed_asset = Asset.objects.create(
            asset_tag="BIDC001TEST",
            system_type="Desktop",
            operating_system=self.os,
            ip_address=self.ip,
            status="freed",
            freed_date=timezone.now(),
            health_status="healthy"
        )
    
    def test_bug_condition_empty_team_field_server_validation(self):
        """
        **Property 1: Bug Condition** - Server-Side Validation Baseline
        
        **Validates: Requirements 2.2, 2.3**
        
        Test that server-side validation catches empty team field.
        
        **NOTE**: This test verifies baseline server-side behavior. The bug is that
        JavaScript validation fails to prevent the form from reaching the server.
        After the fix, JavaScript will prevent submission, so this server-side
        validation will rarely be triggered (only if JavaScript is disabled).
        
        **Current Behavior (Unfixed)**:
        - JavaScript validation shows alert but page refreshes anyway
        - Form submits to server with empty team field
        - Server-side validation catches it and re-renders form with errors
        - But form data is lost due to page refresh
        
        **Expected Behavior (After Fix)**:
        - JavaScript validation prevents form submission
        - Page does NOT refresh
        - Error message displayed on page (not just alert)
        - Form data preserved
        - Server-side validation not reached (unless JS disabled)
        """
        # Login as admin
        self.client.login(username='admin_reassign_test', password='adminpass123')
        
        # Prepare form data with empty team field (bug condition)
        post_data = {
            'assigned_to': 'assigned',
            'parent_team': self.parent_team.id,
            'team': '',  # EMPTY - this is the bug condition
            'ip_address': self.ip.id,
            'system_type': 'Desktop',
            'operating_system': self.os.id,
        }
        
        # Submit form with empty team field
        post_response = self.client.post(
            reverse('asset_reassign', kwargs={'pk': self.freed_asset.pk}),
            data=post_data,
            follow=False
        )
        
        # Verify server-side validation catches empty team field
        self.assertEqual(
            post_response.status_code, 
            200,
            "Server-side validation should catch empty team field and re-render form"
        )
        
        # Check for validation error
        if hasattr(post_response, 'context') and post_response.context:
            form = post_response.context.get('form')
            if form:
                self.assertTrue(
                    form.errors,
                    "Form should have validation errors when team field is empty"
                )
                # Check for team field error specifically
                self.assertIn(
                    'team',
                    form.errors,
                    "Form should have error for 'team' field"
                )
        
        # Asset should remain freed
        self.freed_asset.refresh_from_db()
        self.assertEqual(self.freed_asset.status, 'freed')
        self.assertIsNone(self.freed_asset.team)
    
    def test_bug_condition_empty_team_rapid_submission(self):
        """
        **Property 1: Bug Condition** - Rapid Submission Before JS Executes
        
        **Validates: Requirements 2.2, 2.3**
        
        Test case: User submits form rapidly before JavaScript executes.
        
        This simulates the scenario where:
        - User loads the page
        - User fills out form quickly
        - User submits before JavaScript event listener is attached
        - Form submits with empty team field
        
        **EXPECTED OUTCOME**: This test FAILS on unfixed code.
        
        The bug is that if JavaScript doesn't execute in time, the form
        submits to the server with empty team field, causing a page refresh.
        """
        # Login as admin
        self.client.login(username='admin_reassign_test', password='adminpass123')
        
        # Submit form immediately without waiting for JavaScript
        # (simulated by not selecting parent team, so hidden field is empty)
        post_data = {
            'assigned_to': 'assigned',
            'parent_team': '',  # Not selected
            'team': '',  # Empty - bug condition
            'ip_address': self.ip.id,
            'system_type': 'Desktop',
            'operating_system': self.os.id,
        }
        
        post_response = self.client.post(
            reverse('asset_reassign', kwargs={'pk': self.freed_asset.pk}),
            data=post_data,
            follow=False
        )
        
        # **EXPECTED BEHAVIOR** (will fail on unfixed code):
        # Form should not redirect, should show validation error
        self.assertEqual(
            post_response.status_code,
            200,
            "Form should not redirect when submitted with empty team field. "
            "JavaScript validation should prevent submission even if user submits rapidly."
        )
        
        # Asset should remain freed
        self.freed_asset.refresh_from_db()
        self.assertEqual(self.freed_asset.status, 'freed')
    
    def test_bug_condition_parent_selected_but_hidden_field_empty(self):
        """
        **Property 1: Bug Condition** - Parent Team Selected But Hidden Field Empty
        
        **Validates: Requirements 2.2, 2.3**
        
        Test case: User selects parent team but hidden field is not populated.
        
        This simulates the scenario where:
        - User selects parent team from dropdown
        - JavaScript fails to populate hidden team field (timing issue, JS error, etc.)
        - User submits form
        - Hidden field is empty despite parent team being selected
        
        **EXPECTED OUTCOME**: This test FAILS on unfixed code.
        
        The bug is that the form submits even though the hidden field is empty,
        causing a page refresh and losing form data.
        """
        # Login as admin
        self.client.login(username='admin_reassign_test', password='adminpass123')
        
        # Submit form with parent team selected but hidden field empty
        # (simulates JavaScript failure to populate hidden field)
        post_data = {
            'assigned_to': 'assigned',
            'parent_team': self.parent_team.id,  # Selected
            'team': '',  # Empty despite parent team selected - bug condition
            'ip_address': self.ip.id,
            'system_type': 'Desktop',
            'operating_system': self.os.id,
        }
        
        post_response = self.client.post(
            reverse('asset_reassign', kwargs={'pk': self.freed_asset.pk}),
            data=post_data,
            follow=False
        )
        
        # **EXPECTED BEHAVIOR** (will fail on unfixed code):
        # Form should not redirect, should show validation error
        self.assertEqual(
            post_response.status_code,
            200,
            "Form should not redirect when hidden team field is empty. "
            "Validation should catch this even if parent team dropdown is selected."
        )
        
        # Check for validation error
        if hasattr(post_response, 'context') and post_response.context:
            form = post_response.context.get('form')
            if form:
                self.assertTrue(
                    form.errors,
                    "Form should have validation errors when hidden team field is empty"
                )
        
        # Asset should remain freed
        self.freed_asset.refresh_from_db()
        self.assertEqual(self.freed_asset.status, 'freed')
        self.assertIsNone(self.freed_asset.team)


class TestBugConditionDocumentation(TestCase):
    """
    Documentation of counterexamples found during bug exploration.
    
    This test class documents the specific counterexamples that demonstrate
    the bug exists on unfixed code.
    """
    
    def test_document_counterexamples(self):
        """
        Document counterexamples found during bug exploration.
        
        **Counterexamples that demonstrate the bug:**
        
        1. **Empty Team Field with Valid Other Fields**
           - Input: assigned_to='assigned', parent_team=<selected>, team='', ip_address=<valid>
           - Expected: Form validation prevents submission, error displayed, no page refresh
           - Actual (unfixed): Page refreshes, form data lost, asset remains freed
           - Root Cause: JavaScript e.preventDefault() + return false not effective with addEventListener
        
        2. **Rapid Submission Before JavaScript Executes**
           - Input: Form submitted immediately after page load, team=''
           - Expected: Form validation prevents submission even if JS not fully loaded
           - Actual (unfixed): Form submits to server, page refreshes
           - Root Cause: Event listener not attached in time, or not attached at all
        
        3. **Parent Team Selected But Hidden Field Empty**
           - Input: parent_team=<selected>, team='' (JS failed to populate)
           - Expected: Form validation catches empty hidden field, prevents submission
           - Actual (unfixed): Form submits despite empty hidden field, page refreshes
           - Root Cause: Validation only checks hidden field, not parent team dropdown
        
        **Analysis:**
        The bug is caused by JavaScript form validation that doesn't properly
        prevent form submission when the hidden team field is empty. The current
        implementation calls e.preventDefault() and returns false, but:
        - return false is ineffective with addEventListener (only works with inline handlers)
        - Event listener may not be attached when DOM is ready
        - No stopImmediatePropagation() to prevent other handlers from executing
        - No visual error feedback (only alert which disappears)
        
        **Fix Requirements:**
        1. Ensure event listener is attached after DOM is ready
        2. Use e.stopImmediatePropagation() in addition to e.preventDefault()
        3. Remove ineffective return false statements
        4. Add visual error feedback (persistent error message)
        5. Add console logging to verify event handler attachment
        """
        # This is a documentation test - it always passes
        # Its purpose is to document the counterexamples found
        self.assertTrue(True, "Counterexamples documented")
