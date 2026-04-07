# Implementation Plan: Freed System Reassignment

## Overview

This implementation plan converts the freed system reassignment design into actionable coding tasks. The feature enables administrators to reassign healthy freed systems back to active status with proper IP management and validation. The implementation follows Django MVC architecture with a service layer pattern, building incrementally from form and validation logic through service layer orchestration to UI integration.

## Tasks

- [x] 1. Create reassignment form with validation
  - Create `ReassignmentForm` in `assets/forms.py` with fields: assigned_to (CharField), team (ModelChoiceField), ip_address (ModelChoiceField), manual_ip (GenericIPAddressField)
  - Implement `clean()` method to validate at least one IP field is provided and not both
  - Implement `clean_manual_ip()` to validate IPv4 format
  - Filter ip_address queryset to only show IPAddress records with is_assigned=False
  - Configure team field to use hierarchical display via Team.objects.get_hierarchical_choices()
  - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.7, 3.1, 3.2, 3.3, 3.4, 6.5_

- [ ]* 1.1 Write property test for form validation
  - **Property 4: Empty assigned_to validation**
  - **Validates: Requirements 3.1**
  - Generate empty/whitespace strings for assigned_to field, verify validation error returned

- [ ]* 1.2 Write property test for IP validation
  - **Property 5: Assigned IP validation**
  - **Validates: Requirements 3.4**
  - Generate IPAddress records with is_assigned=True, verify validation error when selected

- [ ]* 1.3 Write property test for manual IP format
  - **Property 12: Manual IP format validation**
  - **Validates: Requirements 6.5**
  - Generate invalid IPv4 formats, verify validation error returned

- [x] 2. Implement asset reassignment service method
  - Add `reassign_asset(asset, data, user)` static method to AssetService in `assets/services.py`
  - Validate asset.status == 'freed' and asset.health_status == 'healthy', raise ValidationError if not
  - Wrap all operations in transaction.atomic() for atomicity
  - Release old IP if asset.ip_address exists: set is_assigned=False, assigned_to_asset=None
  - Handle dropdown IP selection: set IPAddress.is_assigned=True, assigned_to_asset=asset, asset.ip_address=selected IP, asset.manual_ip=None
  - Handle manual IP entry: set asset.manual_ip=provided IP, asset.ip_address=None
  - Update asset fields: status='active', assigned_to=data['assigned_to'], team=data['team'], freed_date=None, health_status=None, issues_description=None
  - Save asset and return updated instance
  - _Requirements: 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 10.1, 10.2, 10.3, 10.4_

- [ ]* 2.1 Write property test for asset status validation
  - **Property 7: Asset status validation**
  - **Validates: Requirements 3.6**
  - Generate assets with various statuses (active, scrapped), verify validation error for non-freed assets

- [ ]* 2.2 Write property test for health status validation
  - **Property 6: Health status validation**
  - **Validates: Requirements 3.5**
  - Generate assets with health_status != 'healthy', verify validation error returned

- [ ]* 2.3 Write property test for complete state transition
  - **Property 8: Complete state transition on reassignment**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**
  - Generate valid reassignment data, verify all asset fields updated correctly (status, assigned_to, team, freed_date, health_status, issues_description)

- [ ]* 2.4 Write property test for dropdown IP assignment
  - **Property 9: Dropdown IP assignment**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
  - Generate reassignments with dropdown IP selection, verify IPAddress.is_assigned=True, assigned_to_asset set, asset.ip_address set, asset.manual_ip=None

- [ ]* 2.5 Write property test for old IP release
  - **Property 10: Old IP release**
  - **Validates: Requirements 5.5, 5.6, 6.3, 6.4**
  - Generate freed assets with existing ip_address, verify old IP released (is_assigned=False, assigned_to_asset=None) after reassignment

- [ ]* 2.6 Write property test for manual IP assignment
  - **Property 11: Manual IP assignment**
  - **Validates: Requirements 6.1, 6.2**
  - Generate reassignments with manual IP, verify asset.manual_ip set and asset.ip_address=None

- [ ]* 2.7 Write property test for transaction atomicity
  - **Property 17: Transaction atomicity on failure**
  - **Validates: Requirements 10.2, 10.3, 10.4**
  - Generate failing reassignments (validation errors, simulated DB errors), verify all changes rolled back and original state preserved

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Create reassignment view
  - Create `AssetReassignView` class-based view in `assets/views.py` inheriting from AdminRequiredMixin and View
  - Implement `get(request, pk)` method: fetch asset by pk, verify status='freed' and health_status='healthy', instantiate ReassignmentForm, render asset_reassign_form.html with asset and form context
  - Implement `post(request, pk)` method: fetch asset, instantiate ReassignmentForm with POST data, validate form, call AssetService.reassign_asset() on valid form, redirect to active assets page with success message on success, re-render form with errors on failure
  - Handle ValidationError from service layer and display as form errors
  - Return 404 if asset not found, 403 if user not admin
  - _Requirements: 2.1, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 9.1, 9.2, 9.3_

- [ ]* 4.1 Write unit tests for view layer
  - Test GET request displays form with correct asset details
  - Test POST with valid data redirects to active assets page with success message
  - Test POST with invalid data re-renders form with errors
  - Test non-admin users receive 403 response
  - Test invalid asset pk returns 404

- [x] 5. Create reassignment form template
  - Create `asset_reassign_form.html` template in `assets/templates/assets/`
  - Display asset details as read-only: asset_tag, system_type, operating_system
  - Render form fields: assigned_to (text input), team (dropdown), ip_address (dropdown), manual_ip (text input)
  - Add JavaScript to toggle between IP dropdown and manual IP input (mutually exclusive)
  - Include submit button "Reassign Asset" and cancel button linking back to freed systems page
  - Display form validation errors inline with fields
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 6. Update freed systems page template
  - Modify `freed_systems.html` template to add "Reassign" button for each freed asset
  - Add conditional rendering: `{% if asset.health_status == 'healthy' and user.is_staff %}`
  - Link button to `{% url 'asset_reassign' asset.pk %}`
  - Style button to be visually distinct from "Scrap" button
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 6.1 Write property test for reassign button visibility
  - **Property 1: Reassign button visibility for healthy systems**
  - **Validates: Requirements 1.1**
  - Generate freed assets with health_status='healthy' and admin users, verify button displayed

- [ ]* 6.2 Write property test for button hiding for non-admins
  - **Property 2: Reassign button hidden for non-administrators**
  - **Validates: Requirements 1.3**
  - Generate freed assets and non-admin users, verify no reassign buttons displayed

- [x] 7. Add URL routing for reassignment
  - Add URL pattern to `assets/urls.py`: `path('<int:pk>/reassign/', AssetReassignView.as_view(), name='asset_reassign')`
  - _Requirements: 2.1_

- [x] 8. Verify freed systems page filtering
  - Ensure freed systems page view filters assets by status='freed'
  - Verify reassigned assets (status='active') do not appear on freed systems page
  - _Requirements: 7.1, 7.2_

- [ ]* 8.1 Write property test for freed systems page filtering
  - **Property 13: Freed systems page filtering**
  - **Validates: Requirements 7.1, 7.2**
  - Generate assets with various statuses, verify only status='freed' assets displayed on page

- [x] 9. Verify Free IPs page accuracy
  - Ensure Free IPs page view displays IPAddress records with is_assigned=True as occupied
  - Ensure Free IPs page view displays IPAddress records with is_assigned=False as unoccupied
  - Ensure Free IPs page view displays manual IP addresses from active assets as occupied
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 9.1 Write property test for Free IPs page display
  - **Property 14: Free IPs page reflects assignment status**
  - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
  - Generate IPAddress records with various is_assigned states, verify correct display as occupied/unoccupied

- [ ]* 9.2 Write property test for manual IPs display
  - **Property 15: Manual IPs shown as occupied**
  - **Validates: Requirements 8.5**
  - Generate active assets with manual IPs, verify displayed as occupied on Free IPs page

- [x] 10. Integration testing and final validation
  - Test end-to-end reassignment flow: freed systems page → reassignment form → active assets page
  - Verify success message contains asset_tag
  - Verify IP address state changes reflected on Free IPs page
  - Verify reassigned asset disappears from freed systems page and appears on active assets page
  - Test edge cases: asset with no previous IP, asset with previous dropdown IP, asset with previous manual IP
  - _Requirements: 9.1, 9.2, 9.3, 7.1, 8.1, 8.2_

- [ ]* 10.1 Write property test for success message
  - **Property 16: Success message contains asset tag**
  - **Validates: Requirements 9.2, 9.3**
  - Generate successful reassignments, verify success message contains asset_tag

- [ ]* 10.2 Write property test for IP dropdown filtering
  - **Property 3: IP dropdown contains only unassigned IPs**
  - **Validates: Requirements 2.4, 2.7**
  - Generate reassignment form displays, verify IP dropdown only contains is_assigned=False records

- [ ] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- All database operations in reassignment service use transaction.atomic() for atomicity
- Property tests should use Hypothesis with minimum 100 iterations (@settings(max_examples=100))
- Form validation happens at both form layer and service layer for defense in depth
- IP management reuses existing IPManagementService infrastructure where applicable
