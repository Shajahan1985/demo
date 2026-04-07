# Implementation Plan: Network Device Tracking

## Overview

This implementation plan breaks down the network device tracking feature into discrete coding tasks. The feature extends the existing Django-based asset management system to track non-system network devices (cameras, printers, punching machines, mobiles) that consume IP addresses. The implementation follows Django's MVT architecture and integrates with the existing IPAddress model and IPManagementService.

## Tasks

- [x] 1. Create NetworkDevice model and database migration
  - Create `NetworkDevice` model in `assets/models.py` with fields: device_type (CharField with choices), device_name (CharField), ip_address (OneToOneField to IPAddress), created_at, updated_at
  - Add model Meta class with ordering by device_name and indexes on device_type and device_name
  - Generate and apply Django migration
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.1_

- [ ]* 1.1 Write property test for complete device data storage
  - **Property 1: Complete Device Data Storage**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [ ]* 1.2 Write property test for IP address uniqueness
  - **Property 2: IP Address Uniqueness Across Network Devices**
  - **Validates: Requirements 1.5**

- [x] 2. Extend IPManagementService for network device support
  - [x] 2.1 Add `assign_ip_to_network_device()` method to IPManagementService
    - Accept ip_address and network_device parameters
    - Set ip_address.is_assigned = True
    - Set ip_address.assigned_to_asset = None
    - Save ip_address
    - _Requirements: 2.2, 3.3_
  
  - [x] 2.2 Add `get_ip_occupant_info()` method to IPManagementService
    - Check if IP has related network_device (using hasattr)
    - Check if IP has assigned_to_asset
    - Return dict with type ('asset', 'network_device', 'free'), name, and object
    - _Requirements: 5.1, 5.2_
  
  - [ ]* 2.3 Write property test for IP assignment on create and update
    - **Property 4: IP Assignment on Create and Update**
    - **Validates: Requirements 2.2, 3.3**
  
  - [ ]* 2.4 Write unit tests for IPManagementService extensions
    - Test assign_ip_to_network_device with valid device
    - Test get_ip_occupant_info for network device, asset, and free IP
    - _Requirements: 2.2, 3.3, 5.1_

- [x] 3. Create NetworkDeviceForm
  - Create `NetworkDeviceForm` in `assets/forms.py` as ModelForm
  - Include fields: device_type, device_name, ip_address
  - Add Bootstrap form-control classes to widgets
  - Override `__init__` to filter ip_address queryset (unassigned IPs for new, unassigned + current for updates)
  - _Requirements: 2.4, 3.5, 10.1_

- [ ]* 3.1 Write unit tests for NetworkDeviceForm
  - Test form validation with valid data
  - Test IP queryset filtering for new device
  - Test IP queryset filtering for existing device update
  - Test form validation with invalid IP format
  - _Requirements: 2.4, 10.1, 10.2_

- [x] 4. Implement NetworkDeviceService
  - [x] 4.1 Create `create_network_device()` static method
    - Accept data dict (device_type, device_name, ip_address_id) and user
    - Use transaction.atomic() for atomicity
    - Check if IP is already assigned, raise ValidationError if true
    - Create NetworkDevice instance
    - Call IPManagementService.assign_ip_to_network_device()
    - Return created device
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [x] 4.2 Create `update_network_device()` static method
    - Accept device instance, data dict, and user
    - Use transaction.atomic() for atomicity
    - If IP changed, check new IP availability, raise ValidationError if assigned
    - If IP changed, release old IP using IPManagementService.release_ip()
    - If IP changed, assign new IP using IPManagementService.assign_ip_to_network_device()
    - Update device fields and save
    - Return updated device
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 4.3 Create `delete_network_device()` static method
    - Accept device instance and user
    - Use transaction.atomic() for atomicity
    - Store reference to ip_address
    - Delete device
    - Call IPManagementService.release_ip() for the IP
    - _Requirements: 4.1, 4.2_
  
  - [ ]* 4.4 Write property test for network device creation
    - **Property 3: Network Device Creation**
    - **Validates: Requirements 2.1, 2.4**
  
  - [ ]* 4.5 Write property test for IP conflict prevention
    - **Property 5: IP Conflict Prevention**
    - **Validates: Requirements 2.3, 3.4, 9.4**
  
  - [ ]* 4.6 Write property test for network device update
    - **Property 6: Network Device Update**
    - **Validates: Requirements 3.1, 3.5**
  
  - [ ]* 4.7 Write property test for IP release on update and delete
    - **Property 7: IP Release on Update and Delete**
    - **Validates: Requirements 3.2, 4.2**
  
  - [ ]* 4.8 Write property test for network device deletion
    - **Property 8: Network Device Deletion**
    - **Validates: Requirements 4.1**
  
  - [ ]* 4.9 Write unit tests for NetworkDeviceService
    - Test create with valid data
    - Test create with already-assigned IP (expect ValidationError)
    - Test update with IP change
    - Test update with same IP
    - Test update with already-assigned new IP (expect ValidationError)
    - Test delete and verify IP released
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2_

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Create NetworkDevice views
  - [x] 6.1 Create NetworkDeviceListView
    - Inherit from AdminRequiredMixin and ListView
    - Set model = NetworkDevice, template_name, context_object_name = 'devices'
    - Override get_queryset() to use select_related('ip_address') and order by device_name
    - _Requirements: 7.1, 7.2, 7.4, 8.1, 8.2_
  
  - [x] 6.2 Create NetworkDeviceCreateView
    - Inherit from AdminRequiredMixin and CreateView
    - Set model, form_class = NetworkDeviceForm, template_name, success_url
    - Override form_valid() to call NetworkDeviceService.create_network_device()
    - Handle ValidationError and add errors to form
    - Add success message
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 8.1, 8.2_
  
  - [x] 6.3 Create NetworkDeviceUpdateView
    - Inherit from AdminRequiredMixin and UpdateView
    - Set model, form_class = NetworkDeviceForm, template_name, success_url
    - Override form_valid() to call NetworkDeviceService.update_network_device()
    - Handle ValidationError and add errors to form
    - Add success message
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 8.1, 8.2_
  
  - [x] 6.4 Create NetworkDeviceDeleteView
    - Inherit from AdminRequiredMixin and View
    - Implement get() to render confirmation template
    - Implement post() to call NetworkDeviceService.delete_network_device()
    - Add success message and redirect to list
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 8.1, 8.2_
  
  - [ ]* 6.5 Write unit tests for NetworkDevice views
    - Test list view displays devices
    - Test create view with valid data
    - Test create view with invalid data
    - Test update view with valid data
    - Test update view with IP change
    - Test delete view confirmation page
    - Test delete view post action
    - Test admin-only access (non-admin redirected)
    - _Requirements: 2.1, 2.5, 3.1, 4.1, 4.4, 7.1, 7.2, 8.1, 8.2_

- [x] 7. Create NetworkDevice templates
  - [x] 7.1 Create network_device_list.html template
    - Extend base template
    - Display table with columns: Device Type, Device Name, IP Address, Actions
    - Add edit and delete links for each device
    - Add "Create New Device" button linking to create view
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 7.2 Create network_device_form.html template
    - Extend base template
    - Render form with CSRF token
    - Display form fields with Bootstrap styling
    - Add submit and cancel buttons
    - Display validation errors
    - _Requirements: 2.4, 3.5_
  
  - [x] 7.3 Create network_device_confirm_delete.html template
    - Extend base template
    - Display device information
    - Show confirmation message
    - Add confirm and cancel buttons
    - _Requirements: 4.3_

- [x] 8. Add URL patterns for NetworkDevice views
  - Add URL patterns in `assets/urls.py` for list, create, update, delete views
  - Use path() with appropriate URL patterns and view names
  - _Requirements: 7.1, 7.5, 2.5, 3.1, 4.4_

- [ ]* 8.1 Write unit tests for URL routing
  - Test all URL patterns resolve to correct views
  - Test URL reverse lookup
  - _Requirements: 7.1, 7.5_

- [x] 9. Update FreeIPsView to display network devices
  - [x] 9.1 Modify FreeIPsView.get_context_data()
    - For each IP in ip_ranges, call IPManagementService.get_ip_occupant_info()
    - Add occupant_type and occupant_name to ip_data dict
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [x] 9.2 Implement search functionality in FreeIPsView
    - Get search query from request.GET.get('search')
    - Create _filter_ips_by_search() method
    - Filter IPs by matching query against IP address or occupant_name (case-insensitive)
    - Add filtered_ranges to context if search query present
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 9.3 Write property test for IP occupancy display
    - **Property 9: IP Occupancy Display**
    - **Validates: Requirements 5.1**
  
  - [ ]* 9.4 Write property test for search by IP address
    - **Property 10: Search by IP Address**
    - **Validates: Requirements 6.1, 6.5**
  
  - [ ]* 9.5 Write property test for search by device name
    - **Property 11: Search by Device Name**
    - **Validates: Requirements 6.2, 6.4, 6.5**
  
  - [ ]* 9.6 Write property test for search by asset assigned person
    - **Property 12: Search by Asset Assigned Person**
    - **Validates: Requirements 6.3, 6.5**
  
  - [ ]* 9.7 Write unit tests for FreeIPsView updates
    - Test IP occupancy display for network device
    - Test IP occupancy display for asset
    - Test IP occupancy display for free IP
    - Test search by IP address
    - Test search by network device name
    - Test search by asset assigned person
    - Test case-insensitive search
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 10. Update Free IPs page template
  - Modify free_ips.html template to display occupant_type and occupant_name
  - Add visual distinction for network devices vs assets (e.g., different CSS classes or icons)
  - Update tooltip to show device name for network devices
  - Add search input field with form submission
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 10.1 Write property test for device list display content
  - **Property 13: Device List Display Content**
  - **Validates: Requirements 7.2**

- [x] 11. Ensure asset export excludes network devices
  - Review existing asset export functionality
  - Verify that export queries only Asset model, not NetworkDevice
  - Add comment or documentation if needed
  - _Requirements: 9.2_

- [ ]* 11.1 Write property test for asset export exclusion
  - **Property 14: Asset Export Exclusion**
  - **Validates: Requirements 9.2**

- [x] 12. Ensure asset search excludes network devices
  - Review existing asset search functionality
  - Verify that search queries only Asset model, not NetworkDevice
  - Add comment or documentation if needed
  - _Requirements: 9.3_

- [ ]* 12.1 Write property test for asset search exclusion
  - **Property 15: Asset Search Exclusion**
  - **Validates: Requirements 9.3**

- [ ]* 13. Write property test for IP address format validation
  - **Property 16: IP Address Format Validation**
  - **Validates: Requirements 10.1, 10.2, 10.3**

- [x] 14. Add navigation links for network device management
  - Update navigation template to include link to network device list
  - Use AdminRequiredMixin or template tag to show link only to admin users
  - _Requirements: 8.3_

- [ ] 15. Final checkpoint - Ensure all tests pass
  - Run full test suite
  - Verify all property-based tests pass with 100 iterations
  - Verify all unit tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- All database operations use Django's transaction.atomic() for atomicity
- Property tests use Hypothesis with minimum 100 iterations
- The feature integrates with existing IPAddress model and IPManagementService
- Network devices are stored separately from assets to avoid cluttering asset inventory
- Admin-only access is enforced using AdminRequiredMixin on all management views
