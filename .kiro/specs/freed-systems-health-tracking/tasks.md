# Implementation Plan: Freed Systems Health Tracking

## Overview

This implementation plan breaks down the Freed Systems Health Tracking feature into discrete coding tasks. The feature adds manual entry capabilities for freed systems and health status tracking with issue descriptions. The implementation follows a bottom-up approach: database migrations first, then model updates, forms, service layer enhancements, views, templates, and URL configuration. Each task builds on previous steps to ensure incremental validation.

## Tasks

- [x] 1. Create database migrations for new fields
  - [x] 1.1 Create migration for Asset model fields (health_status, issues_description)
    - Add health_status CharField(max_length=20, choices=[('healthy', 'Healthy'), ('defective', 'Defective')], null=True, blank=True)
    - Add issues_description TextField(blank=True, null=True)
    - _Requirements: 2.1, 3.1_
  
  - [ ]* 1.2 Write unit tests for model field constraints
    - Test health_status accepts only 'healthy' and 'defective' values
    - Test issues_description accepts multi-line text
    - Test both fields accept NULL values
    - _Requirements: 2.1, 3.1_

- [x] 2. Update Asset model
  - [x] 2.1 Add health_status field to Asset model
    - Define HEALTH_STATUS_CHOICES constant
    - Add CharField with choices, null=True, blank=True
    - Add appropriate help_text
    - _Requirements: 2.1_
  
  - [x] 2.2 Add issues_description field to Asset model
    - Define TextField with null=True, blank=True
    - Add appropriate help_text
    - _Requirements: 3.1_
  
  - [ ]* 2.3 Write property test for health status persistence
    - **Property 1: Manual Entry Creates Freed Asset with Correct State**
    - **Validates: Requirements 1.2, 1.3**
    - Test that any valid manual entry creates asset with status='freed', freed_date set, assigned_to=NULL, team=NULL
    - _Requirements: 1.2, 1.3_

- [x] 3. Checkpoint - Run migrations and verify model changes
  - Ensure migrations apply successfully, verify new fields exist in database, ask the user if questions arise.

- [x] 4. Create FreedSystemForm
  - [x] 4.1 Implement FreedSystemForm class
    - Inherit from ModelForm with Asset model
    - Include fields: asset_tag, system_type, operating_system, ip_address, manual_ip, health_status, issues_description, manufacturer, particulars
    - Make health_status required in __init__
    - _Requirements: 1.1, 2.2_
  
  - [x] 4.2 Implement custom clean() method for FreedSystemForm
    - Validate that defective systems have non-empty issues_description
    - Allow healthy systems to have empty issues_description
    - Raise ValidationError with appropriate messages
    - _Requirements: 3.2, 3.3, 3.4_
  
  - [ ]* 4.3 Write unit tests for FreedSystemForm
    - Test form accepts valid data with healthy status
    - Test form accepts valid data with defective status and issues
    - Test form rejects defective status without issues
    - Test form accepts healthy status with empty issues
    - Test form validates required fields
    - _Requirements: 1.1, 1.5, 2.2, 3.2, 3.3, 3.4_
  
  - [ ]* 4.4 Write property test for defective systems validation
    - **Property 6: Defective Systems Require Issues Description**
    - **Validates: Requirements 3.2, 3.4**
    - Test that any form submission with health_status='defective' and empty issues_description fails validation
    - _Requirements: 3.2, 3.4_
  
  - [ ]* 4.5 Write property test for healthy systems validation
    - **Property 7: Healthy Systems Allow Empty Issues**
    - **Validates: Requirements 3.3**
    - Test that any form submission with health_status='healthy' succeeds regardless of issues_description
    - _Requirements: 3.3_

- [x] 5. Create FreedSystemEditForm
  - [x] 5.1 Implement FreedSystemEditForm class
    - Inherit from ModelForm with Asset model
    - Include fields: health_status, issues_description, particulars
    - Make health_status required in __init__
    - _Requirements: 5.2_
  
  - [x] 5.2 Implement custom clean() method for FreedSystemEditForm
    - Use same validation logic as FreedSystemForm
    - Validate defective → issues_description dependency
    - _Requirements: 5.3, 5.4_
  
  - [ ]* 5.3 Write unit tests for FreedSystemEditForm
    - Test form accepts health_status change to defective with issues
    - Test form rejects health_status change to defective without issues
    - Test form accepts health_status change to healthy with cleared issues
    - Test form accepts health_status change to healthy with existing issues
    - _Requirements: 5.3, 5.4_
  
  - [ ]* 5.4 Write property test for edit form conditional validation
    - **Property 15: Edit Form Enforces Conditional Validation**
    - **Validates: Requirements 5.3, 5.4**
    - Test that any edit changing health_status to 'defective' requires issues_description
    - _Requirements: 5.3, 5.4_

- [x] 6. Checkpoint - Verify form validation logic
  - Ensure all form tests pass, verify validation rules work correctly, ask the user if questions arise.

- [x] 7. Enhance AssetService with new methods
  - [x] 7.1 Implement create_freed_asset() method
    - Accept data dict and user parameter
    - Validate asset_tag uniqueness
    - Create Asset with status='freed', freed_date=now(), assigned_to=None, team=None
    - Set health_status and issues_description from data
    - Return created asset instance
    - _Requirements: 1.2, 1.3, 1.4_
  
  - [ ]* 7.2 Write unit tests for create_freed_asset()
    - Test successful creation with valid data
    - Test rejection of duplicate asset_tag
    - Test all freed asset fields are set correctly
    - Test health_status and issues_description are saved
    - _Requirements: 1.2, 1.3, 1.4_
  
  - [ ]* 7.3 Write property test for duplicate asset tag rejection
    - **Property 2: Duplicate Asset Tag Rejection**
    - **Validates: Requirements 1.4**
    - Test that any asset_tag that already exists results in validation error
    - _Requirements: 1.4_
  
  - [ ]* 7.4 Write property test for missing required fields
    - **Property 3: Missing Required Fields Validation**
    - **Validates: Requirements 1.5**
    - Test that any form submission with missing required fields fails validation
    - _Requirements: 1.5_
  
  - [ ]* 7.5 Write property test for health status requirement
    - **Property 4: Health Status Required for Manual Entry**
    - **Validates: Requirements 2.2**
    - Test that any manual entry without health_status fails validation
    - _Requirements: 2.2_
  
  - [x] 7.6 Implement update_freed_asset() method
    - Accept asset, data dict, and user parameter
    - Validate asset.status == 'freed'
    - Update health_status, issues_description, particulars
    - Save and return updated asset
    - _Requirements: 5.5_
  
  - [ ]* 7.7 Write unit tests for update_freed_asset()
    - Test successful update with valid data
    - Test rejection of non-freed assets
    - Test all fields are updated correctly
    - _Requirements: 5.5_
  
  - [ ]* 7.8 Write property test for valid edit updates
    - **Property 16: Valid Edit Updates Asset**
    - **Validates: Requirements 5.5**
    - Test that any freed asset with valid edit data has fields updated correctly
    - _Requirements: 5.5_
  
  - [x] 7.9 Update free_asset() method
    - Add health_status='healthy' when freeing an asset
    - Set issues_description=None when freeing an asset
    - Maintain existing logic for status, freed_date, assigned_to, team
    - _Requirements: 2.3, 4.1, 4.2_
  
  - [ ]* 7.10 Write unit tests for updated free_asset()
    - Test health_status is set to 'healthy' by default
    - Test issues_description is cleared
    - Test existing functionality still works
    - _Requirements: 2.3, 4.1, 4.2_
  
  - [ ]* 7.11 Write property test for free asset default health status
    - **Property 5: Free Asset Sets Healthy Default**
    - **Validates: Requirements 2.3, 4.1, 4.2**
    - Test that any active asset freed through free_asset has health_status='healthy'
    - _Requirements: 2.3, 4.1, 4.2_
  
  - [ ]* 7.12 Write property test for password requirement
    - **Property 11: Password Required for Freeing Assets**
    - **Validates: Requirements 4.3**
    - Test that any attempt to free asset without valid password fails
    - _Requirements: 4.3_

- [x] 8. Checkpoint - Verify service layer enhancements
  - Ensure all service tests pass, verify business logic works correctly, ask the user if questions arise.

- [x] 9. Create FreedSystemCreateView
  - [x] 9.1 Implement FreedSystemCreateView class
    - Inherit from LoginRequiredMixin, UserPassesTestMixin, CreateView
    - Set model=Asset, form_class=FreedSystemForm
    - Set template_name='assets/freed_system_create.html'
    - Set success_url=reverse_lazy('freed_systems')
    - Implement test_func() to require staff permissions
    - _Requirements: 1.1_
  
  - [x] 9.2 Implement form_valid() method for FreedSystemCreateView
    - Call AssetService.create_freed_asset() with form data and user
    - Add success message using Django messages framework
    - Handle ValidationError and add to form errors
    - Redirect to success_url on success
    - _Requirements: 1.2, 1.4_
  
  - [ ]* 9.3 Write unit tests for FreedSystemCreateView
    - Test staff user can access view
    - Test non-staff user is denied access
    - Test successful form submission creates freed asset
    - Test validation errors are displayed
    - Test success message is shown
    - _Requirements: 1.1, 1.2, 1.4_

- [x] 10. Create FreedSystemEditView
  - [x] 10.1 Implement FreedSystemEditView class
    - Inherit from LoginRequiredMixin, UserPassesTestMixin, UpdateView
    - Set model=Asset, form_class=FreedSystemEditForm
    - Set template_name='assets/freed_system_edit.html'
    - Set success_url=reverse_lazy('freed_systems')
    - Implement test_func() to require staff permissions
    - Override get_queryset() to filter status='freed'
    - _Requirements: 5.1, 5.2_
  
  - [x] 10.2 Implement form_valid() method for FreedSystemEditView
    - Call AssetService.update_freed_asset() with asset, form data, and user
    - Add success message using Django messages framework
    - Handle ValidationError and add to form errors
    - Redirect to success_url on success
    - _Requirements: 5.5_
  
  - [ ]* 10.3 Write unit tests for FreedSystemEditView
    - Test staff user can access view
    - Test non-staff user is denied access
    - Test view only shows freed assets
    - Test form is pre-populated with current data
    - Test successful form submission updates asset
    - Test validation errors are displayed
    - _Requirements: 5.1, 5.2, 5.5_
  
  - [ ]* 10.4 Write property test for edit form pre-population
    - **Property 14: Edit Form Pre-populated with Current Data**
    - **Validates: Requirements 5.2**
    - Test that any freed asset edit form is initialized with current values
    - _Requirements: 5.2_

- [x] 11. Update FreeSystemsView
  - [x] 11.1 Verify FreeSystemsView queryset
    - Ensure queryset filters status='freed'
    - Ensure queryset uses select_related for operating_system and ip_address
    - Ensure queryset orders by -freed_date
    - No code changes needed if already correct
    - _Requirements: 4.4, 4.5_
  
  - [ ]* 11.2 Write unit tests for FreeSystemsView
    - Test view displays all freed assets
    - Test view includes manually created and freed-from-active assets
    - Test queryset is optimized with select_related
    - _Requirements: 4.4, 4.5_
  
  - [ ]* 11.3 Write property test for both asset types displayed
    - **Property 12: Both Manual and Freed Assets Displayed**
    - **Validates: Requirements 4.4**
    - Test that any combination of manual and freed assets appears in queryset
    - _Requirements: 4.4_

- [x] 12. Checkpoint - Verify view layer functionality
  - Ensure all view tests pass, verify views work correctly, ask the user if questions arise.

- [x] 13. Create freed_system_create.html template
  - [x] 13.1 Create template file
    - Extend assets/base.html
    - Add page title "Add Freed System"
    - Create form with CSRF token
    - Render form fields using {{ form.as_p }}
    - Add "Create Freed System" submit button
    - Add "Cancel" link back to freed_systems page
    - _Requirements: 1.1_
  
  - [ ]* 13.2 Write template tests for freed_system_create.html
    - Test form is rendered
    - Test all required fields are present
    - Test submit and cancel buttons are present
    - _Requirements: 1.1_

- [x] 14. Create freed_system_edit.html template
  - [x] 14.1 Create template file
    - Extend assets/base.html
    - Add page title "Edit Freed System: {{ asset.asset_tag }}"
    - Create form with CSRF token
    - Render form fields using {{ form.as_p }}
    - Add "Update" submit button
    - Add "Cancel" link back to freed_systems page
    - _Requirements: 5.1_
  
  - [ ]* 14.2 Write template tests for freed_system_edit.html
    - Test form is rendered
    - Test asset_tag is displayed in title
    - Test form fields are present
    - Test submit and cancel buttons are present
    - _Requirements: 5.1_
  
  - [ ]* 14.3 Write property test for edit action availability
    - **Property 13: Edit Action Available for All Freed Systems**
    - **Validates: Requirements 5.1**
    - Test that any freed asset has edit link in rendered HTML
    - _Requirements: 5.1_

- [x] 15. Update freed_systems.html template
  - [x] 15.1 Add "Add Freed System" button
    - Add button in header-actions div for staff users
    - Link to {% url 'freed_system_create' %}
    - Use btn btn-primary styling
    - _Requirements: 1.1_
  
  - [x] 15.2 Add Health Status column to table
    - Add "Health Status" table header
    - Add table cell with conditional badge display
    - Show green badge with "✓ Healthy" for health_status='healthy'
    - Show red badge with "⚠ Defective" for health_status='defective'
    - Show gray badge with "N/A" for health_status=NULL
    - Use Bootstrap badge classes (badge-success, badge-danger, badge-secondary)
    - _Requirements: 2.4, 2.5, 2.6_
  
  - [x] 15.3 Add Issues column to table
    - Add "Issues" table header
    - Add table cell with conditional display
    - Show truncated issues_description (10 words) for defective systems
    - Show "-" for healthy systems or NULL health_status
    - _Requirements: 3.5, 3.6_
  
  - [x] 15.4 Add Edit action button
    - Add "Edit" button in Actions column for staff users
    - Link to {% url 'freed_system_edit' asset.pk %}
    - Use btn btn-sm btn-primary styling
    - _Requirements: 5.1_
  
  - [ ]* 15.5 Write template tests for freed_systems.html
    - Test "Add Freed System" button appears for staff
    - Test Health Status column displays correct badges
    - Test Issues column shows issues for defective systems
    - Test Issues column shows "-" for healthy systems
    - Test Edit button appears for staff users
    - Test all required fields are displayed
    - _Requirements: 1.1, 2.4, 2.5, 2.6, 3.5, 3.6, 4.5, 5.1_
  
  - [ ]* 15.6 Write property test for freed systems page display
    - **Property 8: Freed Systems Page Displays All Required Fields**
    - **Validates: Requirements 2.4, 4.5**
    - Test that any freed asset has all required fields in rendered HTML
    - _Requirements: 2.4, 4.5_
  
  - [ ]* 15.7 Write property test for defective systems display issues
    - **Property 9: Defective Systems Display Issues**
    - **Validates: Requirements 3.5**
    - Test that any defective freed asset with issues_description displays text in HTML
    - _Requirements: 3.5_
  
  - [ ]* 15.8 Write property test for healthy systems hide issues
    - **Property 10: Healthy Systems Hide Issues**
    - **Validates: Requirements 3.6**
    - Test that any healthy freed asset does not display issues_description
    - _Requirements: 3.6_

- [x] 16. Configure URL routing
  - [x] 16.1 Add URL patterns to assets/urls.py
    - Add path('freed/create/', FreedSystemCreateView.as_view(), name='freed_system_create')
    - Add path('freed/<int:pk>/edit/', FreedSystemEditView.as_view(), name='freed_system_edit')
    - Import new view classes
    - _Requirements: 1.1, 5.1_
  
  - [ ]* 16.2 Write URL routing tests
    - Test freed_system_create URL resolves correctly
    - Test freed_system_edit URL resolves correctly with pk parameter
    - Test URL names reverse correctly
    - _Requirements: 1.1, 5.1_

- [x] 17. Final checkpoint and integration testing
  - [ ]* 17.1 Write end-to-end manual entry integration test
    - Create freed system through FreedSystemCreateView
    - Verify asset is created with correct status and fields
    - Verify asset appears on freed_systems page
    - Verify health status badge is displayed
    - _Requirements: 1.1, 1.2, 1.3, 2.2, 2.4_
  
  - [ ]* 17.2 Write end-to-end edit integration test
    - Create freed system with healthy status
    - Edit to change health_status to defective with issues
    - Verify asset is updated correctly
    - Verify issues are displayed on freed_systems page
    - Edit to change health_status back to healthy
    - Verify issues are hidden on freed_systems page
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 3.5, 3.6_
  
  - [ ]* 17.3 Write end-to-end free asset integration test
    - Create active asset with assignment
    - Free asset through existing free_asset operation
    - Verify health_status is set to 'healthy'
    - Verify issues_description is NULL
    - Verify asset appears on freed_systems page
    - _Requirements: 2.3, 4.1, 4.2, 4.3, 4.4_
  
  - [ ]* 17.4 Write validation error integration test
    - Attempt to create freed system with defective status and no issues
    - Verify validation error is displayed 
    - Attempt to create freed system with duplicate asset_tag
    - Verify validation error is displayed
    - _Requirements: 1.4, 3.2, 3.4_
  
  - [x] 17.5 Final checkpoint - Ensure all tests pass
    - Run full test suite including property-based tests
    - Verify all functionality works end-to-end
    - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end flows across multiple components
- The feature maintains backward compatibility with existing freed assets (NULL health_status)
- All database changes are handled through Django migrations
- Forms enforce conditional validation (defective → issues_description dependency)
- Templates use Bootstrap styling for consistent UI
