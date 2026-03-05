# Implementation Plan: Asset Tracking System

## Overview

This implementation plan breaks down the Django-based Asset Tracking System into discrete, incremental coding tasks. Each task builds on previous work, with property-based tests integrated close to implementation to catch errors early. The plan follows a bottom-up approach: models → services → views → templates → integration.

## Tasks











- [x] 1. Set up Django project structure and dependencies
  - Create Django project `asset_tracker` with `assets` app
  - Create requirements.txt with Django 4.2+, pytest-django, Hypothesis, factory_boy, Celery, Redis
  - Configure settings.py for database, static files, media files, email backend
  - Set up project directory structure (models, views, services, forms, templates, static, tests)
  - _Requirements: All_

- [x] 2. Implement core data models
  - [x] 2.1 Create OperatingSystem, Team, and IPRange models
    - Implement OperatingSystem model with name field and uniqueness constraint
    - Implement Team model with name field and uniqueness constraint
    - Implement IPRange model with range_pattern and network_prefix fields
    - Add created_at timestamps to all models
    - _Requirements: 9.1, 9.3, 10.1, 10.3, 11.1, 11.3_
  
  - [x] 2.2 Write property tests for OS, Team, and IPRange uniqueness
    - **Property 18: Operating system management**
    - **Property 19: Team management**
    - **Property 20: IP range management**
    - **Validates: Requirements 9.1, 9.3, 10.1, 10.3, 11.1, 11.3**
  
  - [x] 2.3 Create IPAddress model
    - Implement IPAddress model with address, ip_range FK, is_assigned flag, assigned_to_asset FK
    - Add unique constraint on address field
    - Add index on is_assigned for query performance
    - _Requirements: 1.4, 8.1, 8.2, 8.3_
  
  - [x] 2.4 Create Asset model
    - Implement Asset model with all fields: serial_number (AutoField), asset_tag (unique), system_type (choices), operating_system FK, ip_address FK, particulars, assigned_to, team FK, status (choices), warranty_expiration, freed_date, scrapped_date, timestamps
    - Add unique constraint on asset_tag
    - Add indexes on asset_tag, status, warranty_expiration
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 13.4_
  
  - [x] 2.5 Write property tests for Asset model
    - **Property 1: Asset creation completeness**
    - **Property 2: Asset tag uniqueness enforcement**
    - **Property 3: Sequential serial number assignment**
    - **Validates: Requirements 1.1, 1.2, 1.3**
  
  - [x] 2.6 Create Attachment model
    - Implement Attachment model with asset FK, file FileField, filename, uploaded_at
    - Configure file upload path to MEDIA_ROOT/asset_attachments/
    - _Requirements: 12.1, 12.2_

- [x] 3. Create Django migrations and initialize database
  - Generate initial migrations for all models
  - Create management command to initialize IP ranges (192.168.10.x, 192.168.11.x, 192.168.70.x, 192.168.50.x)
  - Generate all 254 IP addresses (1-254) for each range in initialization command
  - Run migrations and test initialization command
  - _Requirements: 8.1, 8.2, 11.1_

- [x] 4. Implement permission system
  - [x] 4.1 Create AdminRequiredMixin for class-based views
    - Implement mixin that checks user.is_staff in dispatch method
    - Raise PermissionDenied if user is not admin
    - _Requirements: 1.5, 2.4, 3.6, 6.4_
  
  - [x] 4.2 Create admin_required decorator for function-based views
    - Implement decorator that checks user.is_staff
    - Return HTTP 403 if user is not admin
    - _Requirements: 1.5, 2.4, 3.6, 6.4_
  
  - [x] 4.3 Write property test for admin-only operations
    - **Property 5: Admin-only operation enforcement**
    - **Validates: Requirements 1.5, 2.4, 3.6, 6.4**

- [x] 5. Implement IP management service
  - [x] 5.1 Create IPManagementService class
    - Implement assign_ip(ip_address, asset) to mark IP as assigned and link to asset
    - Implement release_ip(ip_address) to mark IP as free and clear asset link
    - Implement change_asset_ip(asset, new_ip) to release old IP and assign new IP
    - Implement get_free_ips_by_range() to return dict of ranges to free IPs
    - Implement get_available_ips() to return queryset of unassigned IPs
    - _Requirements: 1.4, 2.2, 3.4, 8.1, 8.2, 8.3, 8.4_
  
  - [x] 5.2 Write property tests for IP management
    - **Property 4: IP assignment state transition**
    - **Property 7: IP change state management**
    - **Property 10: IP release on asset freeing**
    - **Property 17: Free IPs grouping by range**
    - **Validates: Requirements 1.4, 2.2, 3.4, 8.1, 8.2, 8.3, 8.4**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement asset service
  - [x] 7.1 Create AssetService class with core operations
    - Implement create_asset(data, user) with validation and IP assignment
    - Implement update_asset(asset, data, user) with IP change handling
    - Implement validate_asset_tag(asset_tag) for uniqueness checking
    - Implement get_active_assets(), get_freed_assets(), get_scrapped_assets() querysets
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 4.1, 4.2, 5.1, 5.3, 7.1_
  
  - [x] 7.2 Write property tests for asset creation and updates
    - **Property 6: Asset update data integrity**
    - **Property 11: Active assets view completeness**
    - **Validates: Requirements 2.1, 4.1**
  
  - [x] 7.3 Implement free_asset(asset, user, password) method
    - Verify user password using Django's check_password
    - Change asset status to 'freed'
    - Clear assigned_to and team fields
    - Set freed_date to current datetime
    - Release IP address using IPManagementService
    - _Requirements: 3.3, 3.4, 3.5_
  
  - [x] 7.4 Write property test for asset freeing
    - **Property 9: Asset freeing state transition**
    - **Validates: Requirements 3.3, 3.5**
  
  - [x] 7.5 Implement scrap_asset(asset, user) method
    - Verify asset status is 'freed'
    - Change asset status to 'scrapped'
    - Set scrapped_date to current datetime
    - Retain asset_tag, IP address, and attachments
    - _Requirements: 6.1, 6.2, 6.3_
  
  - [x] 7.6 Write property test for asset scrapping
    - **Property 15: Asset scrapping state transition**
    - **Validates: Requirements 6.1, 6.2, 6.3**

- [x] 8. Implement attachment service
  - [x] 8.1 Create AttachmentService class
    - Implement upload_attachment(asset, file) to save file and create Attachment record
    - Implement delete_attachment(attachment) to remove file from storage and delete record
    - Implement get_asset_attachments(asset) to return queryset of attachments
    - Configure file size limits and allowed file types
    - _Requirements: 12.1, 12.2, 12.3, 12.4_
  
  - [x] 8.2 Write property tests for attachments
    - **Property 8: Attachment preservation during updates**
    - **Property 21: Attachment upload and association**
    - **Property 22: Attachment deletion completeness**
    - **Property 23: Attachment preservation on scrapping**
    - **Validates: Requirements 2.3, 12.1, 12.2, 12.3, 12.4**

- [x] 9. Implement warranty service
  - [x] 9.1 Create WarrantyService class
    - Implement check_expiring_warranties() to find assets expiring within 7 days
    - Implement get_warranty_status(asset) to return 'active', 'expiring_soon', or 'expired'
    - Implement send_warranty_alerts(assets) to send email to admin users
    - Configure email template for warranty alerts
    - _Requirements: 13.2, 13.3, 13.7_
  
  - [x] 9.2 Write property tests for warranty checking
    - **Property 24: Warranty expiration identification**
    - **Property 25: Warranty alert email delivery**
    - **Property 27: Warranty expiration status marking**
    - **Validates: Requirements 13.2, 13.3, 13.7**
  
  - [x] 9.3 Create Celery task for daily warranty check
    - Implement run_daily_check() as Celery task
    - Call check_expiring_warranties() and send_warranty_alerts()
    - Configure Celery beat schedule to run daily at 9:00 AM
    - _Requirements: 13.2, 13.3_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Create Django forms
  - [x] 11.1 Create AssetForm for create and update operations
    - Include fields: asset_tag, system_type, operating_system, ip_address, particulars, assigned_to, team, warranty_expiration
    - Add validation for required fields
    - Populate dropdowns for system_type, operating_system, ip_address, team
    - _Requirements: 1.1, 2.1_
  
  - [x] 11.2 Create FreeAssetForm for password confirmation
    - Include password field
    - Add password validation
    - _Requirements: 3.2, 3.3_
  
  - [x] 11.3 Create AttachmentForm for file uploads
    - Include file field with size and type validation
    - _Requirements: 12.1_

- [x] 12. Implement views for asset management
  - [x] 12.1 Create AssetListView
    - Display all active assets ordered by serial_number
    - Filter assets with status='active'
    - Pass assets queryset to template context
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 12.2 Write property tests for asset list views
    - **Property 12: View state isolation**
    - **Property 13: Active assets ordering**
    - **Validates: Requirements 4.2, 4.3, 5.3**
  
  - [x] 12.3 Create AssetCreateView with AdminRequiredMixin
    - Display AssetForm on GET
    - Process form submission on POST using AssetService.create_asset()
    - Handle validation errors and display messages
    - Redirect to asset list on success
    - _Requirements: 1.1, 1.2, 1.5_
  
  - [x] 12.4 Create AssetUpdateView with AdminRequiredMixin
    - Display AssetForm pre-filled with asset data on GET
    - Process form submission on POST using AssetService.update_asset()
    - Handle IP changes through IPManagementService
    - Redirect to asset list on success
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [x] 12.5 Create AssetFreeView with AdminRequiredMixin
    - Display confirmation dialog and password prompt
    - Process POST with password verification
    - Call AssetService.free_asset() with password
    - Handle incorrect password errors
    - Redirect to freed systems page on success
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 13. Implement views for freed and scrapped assets
  - [x] 13.1 Create FreeSystemsView
    - Display all freed assets
    - Filter assets with status='freed'
    - Include delete/scrap button for each asset
    - _Requirements: 5.1, 5.3_
  
  - [x] 13.2 Write property test for freed systems view
    - **Property 14: Freed systems view completeness**
    - **Validates: Requirements 5.1**
  
  - [x] 13.3 Create AssetScrapView with AdminRequiredMixin
    - Verify asset is freed before scrapping
    - Call AssetService.scrap_asset()
    - Redirect to scrapped items page on success
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [x] 13.4 Create ScrappedItemsView
    - Display all scrapped assets ordered by scrapped_date descending
    - Filter assets with status='scrapped'
    - Show asset_tag, IP address, scrapped_date
    - _Requirements: 7.1, 7.2_
  
  - [x] 13.5 Write property test for scrapped items view
    - **Property 16: Scrapped items view completeness and ordering**
    - **Validates: Requirements 7.1, 7.2**

- [x] 14. Implement IP and warranty views
  - [x] 14.1 Create FreeIPsView
    - Call IPManagementService.get_free_ips_by_range()
    - Pass grouped IPs dict to template context
    - Display IPs organized by range (192.168.10.x, 192.168.11.x, 192.168.70.x, 192.168.50.x)
    - _Requirements: 8.1, 8.2_
  
  - [x] 14.2 Create WarrantyView
    - Display all assets with warranty_expiration dates
    - Order by warranty_expiration ascending
    - Call WarrantyService.check_expiring_warranties() for highlighting
    - Mark expired warranties using WarrantyService.get_warranty_status()
    - _Requirements: 13.4, 13.5, 13.6, 13.7_
  
  - [x] 14.3 Write property test for warranty view
    - **Property 26: Warranty page completeness and ordering**
    - **Validates: Requirements 13.4, 13.6**

- [x] 15. Create URL configuration
  - Define URL patterns for all views
  - Map /assets/ to AssetListView
  - Map /assets/create/ to AssetCreateView
  - Map /assets/<id>/edit/ to AssetUpdateView
  - Map /assets/<id>/free/ to AssetFreeView
  - Map /assets/freed/ to FreeSystemsView
  - Map /assets/<id>/scrap/ to AssetScrapView
  - Map /assets/scrapped/ to ScrappedItemsView
  - Map /ips/free/ to FreeIPsView
  - Map /assets/warranty/ to WarrantyView
  - _Requirements: All_

- [x] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Create HTML templates
  - [x] 17.1 Create base template with navigation
    - Create base.html with navigation menu
    - Add links to Active Assets, Free Systems, Scrapped Items, Free IPs, Warranty pages
    - Include Bootstrap or CSS framework for styling
    - _Requirements: All_
  
  - [x] 17.2 Create asset_list.html template
    - Display table with columns: serial_number, asset_tag, system_type, OS, IP, assigned_to, team
    - Add action buttons: Edit, Free for each asset (admin only)
    - Add "Add New Asset" button (admin only)
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 17.3 Create asset_form.html template
    - Display AssetForm with all fields
    - Include dropdowns for system_type, OS, IP, team
    - Add file upload section for attachments
    - Display existing attachments with delete option
    - _Requirements: 1.1, 2.1, 12.1, 12.2_
  
  - [x] 17.4 Create freed_systems.html template
    - Display table with freed assets
    - Show IP address and asset_tag
    - Add "Scrap" button for each asset (admin only)
    - _Requirements: 5.1, 5.3_
  
  - [x] 17.5 Create scrapped_items.html template
    - Display table with scrapped assets
    - Show asset_tag, IP address, scrapped_date
    - Order by scrapped_date descending
    - _Requirements: 7.1, 7.2_
  
  - [x] 17.6 Create free_ips.html template
    - Display IPs grouped by range
    - Show range headers: 192.168.10.x, 192.168.11.x, 192.168.70.x, 192.168.50.x
    - List free IPs under each range
    - _Requirements: 8.1, 8.2_
  
  - [x] 17.7 Create warranty.html template
    - Display table with all assets having warranty dates
    - Show asset details and warranty_expiration
    - Highlight rows with warranties expiring within 7 days
    - Mark expired warranties
    - Order by warranty_expiration ascending
    - _Requirements: 13.4, 13.5, 13.6, 13.7_
  
  - [x] 17.8 Create confirmation dialogs
    - Create modal/dialog for free asset confirmation with password input
    - Create modal/dialog for scrap asset confirmation
    - _Requirements: 3.1, 3.2_

- [x] 18. Configure Django admin
  - Register OperatingSystem, Team, IPRange models in admin
  - Configure admin list displays and filters
  - Allow admin users to manage OS, teams, and IP ranges through Django admin
  - _Requirements: 9.1, 10.1, 11.1_

- [x] 19. Add static files and styling
  - Create CSS for table layouts, buttons, forms
  - Add JavaScript for confirmation dialogs and form interactions
  - Style highlighted warranty rows
  - Add responsive design for mobile devices
  - _Requirements: All_

- [x] 20. Configure Celery and email settings
  - Configure Celery with Redis broker
  - Set up Celery beat schedule for daily warranty check at 9:00 AM
  - Configure email backend (SMTP settings)
  - Create email template for warranty alerts
  - Test email sending functionality
  - _Requirements: 13.2, 13.3_

- [x] 21. Final integration and testing
  - [x] 21.1 Write integration tests for complete workflows
    - Test: create asset → view on active page → free → verify on freed page → scrap → verify on scrapped page
    - Test: assign IP → verify not in free list → free asset → verify IP in free list
    - Test: create asset with warranty → run daily check → verify email sent
    - Test: upload attachment → verify stored → delete → verify removed
    - _Requirements: All_
  
  - [x] 21.2 Manual testing of all features
    - Test all CRUD operations as admin user
    - Test permission denials as non-admin user
    - Test IP management across all operations
    - Test warranty alerts and email delivery
    - Test file uploads and downloads
    - Verify all views display correct data
    - _Requirements: All_

- [x] 22. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across random inputs
- Unit tests validate specific examples and edge cases
- Checkpoints ensure incremental validation at reasonable breaks
- The implementation follows a bottom-up approach: models → services → views → templates
- All admin-only operations are protected by permission checks
- IP address state management is handled consistently through IPManagementService
- Warranty checking is automated through Celery scheduled tasks
