# Implementation Plan: Enhanced Scrapped Items

## Overview

This implementation plan breaks down the enhanced scrapped items feature into discrete coding tasks. The feature adds manufacturer and scrapping reason fields to assets, automatically releases IP addresses when assets are scrapped, and provides comprehensive visibility into IP address lifecycle across scrapped items and free IP pages.

The implementation follows a bottom-up approach: database migrations first, then model updates, service layer enhancements, and finally template updates. Each task builds on previous steps to ensure incremental validation.

## Tasks

- [x] 1. Create database migrations for new fields
  - [x] 1.1 Create migration for Asset model fields (manufacturer, scrapping_reason)
    - Add manufacturer CharField(max_length=100, blank=True, null=True)
    - Add scrapping_reason TextField(blank=True, null=True)
    - _Requirements: 1.1, 1.2, 2.1, 2.2_
  
  - [x] 1.2 Create migration for IPAddress model field (freed_date)
    - Add freed_date DateTimeField(null=True, blank=True)
    - _Requirements: 5.3_
  
  - [x]* 1.3 Write unit tests for model field constraints
    - Test manufacturer max_length constraint
    - Test scrapping_reason accepts multi-line text
    - Test freed_date accepts datetime values
    - _Requirements: 1.1, 2.1, 5.3_

- [x] 2. Update Asset and IPAddress models
  - [x] 2.1 Add manufacturer field to Asset model
    - Define field with appropriate help_text
    - Ensure field is optional (blank=True, null=True)
    - _Requirements: 1.1, 1.2_
  
  - [x] 2.2 Add scrapping_reason field to Asset model
    - Define TextField with appropriate help_text
    - Ensure field is optional at model level (validation at service layer)
    - _Requirements: 2.1, 2.2_
  
  - [x] 2.3 Add freed_date field to IPAddress model
    - Define DateTimeField with appropriate help_text
    - Ensure field is optional (null=True, blank=True)
    - _Requirements: 5.3_
  
  - [x]* 2.4 Write property test for manufacturer persistence
    - **Property 1: Manufacturer field persistence**
    - **Validates: Requirements 1.1, 1.2**
    - Test that any asset with a manufacturer value stores and retrieves it correctly
    - _Requirements: 1.1, 1.2_

- [x] 3. Checkpoint - Run migrations and verify model changes
  - Ensure migrations apply successfully, verify new fields exist in database, ask the user if questions arise.

- [x] 4. Enhance IPManagementService.release_ip() method
  - [x] 4.1 Update release_ip() to set freed_date
    - Add freed_date = timezone.now() when releasing IP
    - Maintain existing is_assigned and assigned_to_asset clearing logic
    - _Requirements: 5.3_
  
  - [x]* 4.2 Write unit tests for release_ip() enhancements
    - Test freed_date is set when IP is released
    - Test freed_date is a valid datetime
    - Test existing functionality still works (is_assigned, assigned_to_asset)
    - _Requirements: 5.3_
  
  - [x]* 4.3 Write property test for freed date setting
    - **Property 7: Freed date is set on IP release**
    - **Validates: Requirements 5.3**
    - Test that any released IP has freed_date set to current timestamp
    - _Requirements: 5.3_

- [x] 5. Enhance AssetService.scrap_asset() method
  - [x] 5.1 Add scrapping_reason parameter to scrap_asset()
    - Update method signature: scrap_asset(asset, user, scrapping_reason)
    - Add validation for non-empty scrapping_reason
    - Set asset.scrapping_reason = scrapping_reason
    - _Requirements: 2.1, 2.2_
  
  - [x] 5.2 Add IP release logic to scrap_asset()
    - Check if asset has an IP address (asset.ip_address is not None)
    - Call IPManagementService.release_ip(asset.ip_address)
    - Preserve asset.ip_address reference (do not set to None)
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x]* 5.3 Write unit tests for scrap_asset() enhancements
    - Test scrapping with valid reason succeeds
    - Test scrapping with empty reason raises ValidationError
    - Test scrapping with whitespace-only reason raises ValidationError
    - Test IP is released when asset has IP
    - Test IP reference is preserved on asset after scrapping
    - Test scrapping asset without IP succeeds
    - _Requirements: 2.1, 2.2, 4.1, 4.2, 4.3_
  
  - [x]* 5.4 Write property test for scrapping reason validation
    - **Property 2: Scrapping reason validation**
    - **Validates: Requirements 2.1, 2.2**
    - Test that any freed asset cannot be scrapped with empty/whitespace reason
    - _Requirements: 2.1, 2.2_
  
  - [x]* 5.5 Write property test for IP release on scrapping
    - **Property 4: IP release on scrapping**
    - **Validates: Requirements 4.1**
    - Test that any freed asset with IP has IP released when scrapped
    - _Requirements: 4.1_
  
  - [x]* 5.6 Write property test for IP reference preservation
    - **Property 6: IP reference preservation on scrapping**
    - **Validates: Requirements 4.3, 7.3**
    - Test that any scrapped asset retains its IP reference after scrapping
    - _Requirements: 4.3_
  
  - [x]* 5.7 Write property test for released IP in free IPs
    - **Property 5: Released IP appears in free IPs**
    - **Validates: Requirements 4.2, 5.1**
    - Test that any IP from scrapped asset appears in free IPs queryset
    - _Requirements: 4.2, 5.1_

- [x] 6. Checkpoint - Verify service layer changes
  - Ensure all tests pass, verify IP release logic works correctly, ask the user if questions arise.

- [x] 7. Update scrapped items template
  - [x] 7.1 Add System Make column to scrapped items table
    - Add table header for "System Make"
    - Add table cell displaying asset.manufacturer
    - Handle missing manufacturer gracefully (display empty or "N/A")
    - _Requirements: 1.3, 3.4_
  
  - [x] 7.2 Add Scrapping Reason column to scrapped items table
    - Add table header for "Scrapping Reason"
    - Add table cell displaying asset.scrapping_reason
    - _Requirements: 2.3, 3.6_
  
  - [x] 7.3 Enhance IP Address column with reassignment indicator
    - Display IP address value for all scrapped assets
    - Add conditional styling: if IP is reassigned (is_assigned=True), display in red with "(Reassigned)" label
    - If IP is still free, display in normal color
    - Handle missing IP address (display "N/A")
    - _Requirements: 3.1, 7.1, 7.2_
  
  - [x]* 7.4 Write template tests for scrapped items page
    - Test all required fields are displayed (IP, asset tag, system type, manufacturer, scrapped date, scrapping reason)
    - Test "(Reassigned)" label appears for reassigned IPs
    - Test red color styling for reassigned IPs
    - Test missing manufacturer displays gracefully
    - Test missing IP displays "N/A"
    - _Requirements: 1.3, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.1, 7.2_
  
  - [x]* 7.5 Write property test for scrapped items page display
    - **Property 3: Scrapped items page displays all required fields**
    - **Validates: Requirements 1.3, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
    - Test that any scrapped asset has all fields in rendered HTML
    - _Requirements: 1.3, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [x]* 7.6 Write property test for IP reassignment status display
    - **Property 10: Scrapped items page shows IP reassignment status**
    - **Validates: Requirements 7.1, 7.2**
    - Test that any scrapped asset with reassigned IP shows indicator in HTML
    - _Requirements: 7.1, 7.2_

- [x] 8. Update free IPs template
  - [x] 8.1 Add freed date display to free IPs page
    - Add freed_date display for each IP address
    - Format date as "Freed: YYYY-MM-DD"
    - Only show freed_date for IPs that have been released (freed_date is not None)
    - _Requirements: 5.3_
  
  - [x] 8.2 Enhance IP availability status indicator
    - Add CSS class or styling to distinguish free vs. occupied IPs
    - Display occupied IPs in red color
    - Add title/tooltip showing availability status
    - _Requirements: 5.2, 6.1, 6.2_
  
  - [x]* 8.3 Write template tests for free IPs page
    - Test freed_date is displayed when present
    - Test freed_date format is correct
    - Test red color styling for reassigned IPs
    - Test availability status is indicated
    - _Requirements: 5.2, 5.3, 6.1, 6.2_
  
  - [x]* 8.4 Write property test for free IPs availability status
    - **Property 8: Free IPs page shows availability status**
    - **Validates: Requirements 5.2, 6.2**
    - Test that any IP on free IPs page indicates availability in HTML
    - _Requirements: 5.2, 6.2_
  
  - [x]* 8.5 Write property test for reassigned IPs display
    - **Property 9: Reassigned IPs display in red on free IPs page**
    - **Validates: Requirements 6.1**
    - Test that any reassigned IP has red color styling in HTML
    - _Requirements: 6.1_

- [x] 9. Update views to pass new data to templates
  - [x] 9.1 Verify scrapped items view includes IP address relationship
    - Ensure queryset uses select_related('ip_address') for efficiency
    - Verify all required fields are accessible in template context
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [x] 9.2 Verify free IPs view includes freed_date and assignment status
    - Ensure IPManagementService.get_all_ips_by_range() returns freed_date
    - Verify is_assigned status is accessible in template context
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2_

- [x] 10. Update forms to include new fields
  - [x] 10.1 Add manufacturer field to asset creation/edit form
    - Add manufacturer field to AssetForm
    - Make field optional in form
    - _Requirements: 1.2_
  
  - [x] 10.2 Add scrapping_reason field to scrap asset form
    - Add scrapping_reason field to scrap asset form/modal
    - Make field required in form validation
    - Add appropriate help text
    - _Requirements: 2.2_
  
  - [x]* 10.3 Write form validation tests
    - Test manufacturer field accepts valid values
    - Test scrapping_reason field rejects empty values
    - Test scrapping_reason field rejects whitespace-only values
    - _Requirements: 1.2, 2.2_

- [x] 11. Final checkpoint and integration testing
  - [x]* 11.1 Write end-to-end integration test
    - Create active asset with IP and manufacturer
    - Free the asset
    - Scrap the asset with reason
    - Verify IP is released and appears in free IPs
    - Verify scrapped items page shows all fields
    - Assign IP to new asset
    - Verify scrapped items page shows "(Reassigned)"
    - Verify free IPs page shows IP as occupied in red
    - _Requirements: All_
  
  - [x] 11.2 Final checkpoint - Ensure all tests pass
    - Run full test suite
    - Verify all functionality works end-to-end
    - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation follows Django best practices for models, services, and templates
- All database changes are handled through Django migrations
- IP address references are preserved on scrapped assets for historical audit trails
