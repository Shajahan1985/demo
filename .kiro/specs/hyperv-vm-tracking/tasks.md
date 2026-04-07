# Implementation Plan: Hyper-V VM Tracking

## Overview

This implementation plan breaks down the Hyper-V VM tracking feature into discrete coding tasks. The feature adds VM tracking capabilities to the Django Asset Tracker, including a new HyperVVM model, dedicated forms for VM entry, service layer logic, views for CRUD operations, templates with bidirectional relationship display, and comprehensive testing.

The implementation follows a bottom-up approach: database layer first, then models and services, followed by forms and views, and finally templates and URL configuration. Testing tasks are integrated throughout to validate functionality incrementally.

## Tasks

- [ ] 1. Create database migration for HyperVVM model
  - Create Django migration file for the HyperVVM model with all fields (name, host_machine, ip_address, manual_ip, is_active, notes, timestamps)
  - Add foreign key constraints (PROTECT for host_machine, SET_NULL for ip_address)
  - Add database indexes on name, host_machine_id + is_active, and ip_address_id
  - Add unique constraint on name field
  - _Requirements: 1.1, 2.1, 2.3, 9.1, 9.2_

- [ ] 2. Implement HyperVVM model
  - [ ] 2.1 Create HyperVVM model class in assets/models.py
    - Define all model fields with appropriate types and constraints
    - Implement __str__ method to display VM name and host
    - Add Meta class with ordering, verbose names, and indexes
    - Implement get_display_ip() method to return tracked or manual IP
    - Implement get_host_ip() method to return host machine IP
    - _Requirements: 1.1, 2.3, 4.1, 4.2_
  
  - [ ] 2.2 Implement model validation in clean() method
    - Validate IP uniqueness across VMs (excluding current instance)
    - Add validation error messages for duplicate IPs
    - _Requirements: 8.2, 8.3, 8.5_
  
  - [ ]* 2.3 Write property test for HyperVVM model
    - **Property 1: VM CRUD Operations**
    - **Validates: Requirements 1.1, 1.3, 1.4, 1.5, 1.7**
  
  - [ ]* 2.4 Write property test for bidirectional relationship
    - **Property 3: Bidirectional VM-Host Relationship**
    - **Validates: Requirements 2.3, 2.6, 3.1**
  
  - [ ]* 2.5 Write property test for VM serialization
    - **Property 17: VM Serialization Round-Trip**
    - **Validates: Requirements 11.3**

- [ ] 3. Implement HyperVService business logic
  - [ ] 3.1 Create HyperVService class in assets/services/hyperv_service.py
    - Implement create_vm() method with transaction handling and IP assignment
    - Implement update_vm() method with IP change handling
    - Implement delete_vm() method with IP release
    - Implement get_vms_for_host() method to query VMs by host
    - Implement get_host_for_vm_ip() method to find host from VM IP
    - _Requirements: 1.3, 1.4, 1.5, 2.5, 6.4, 6.5_
  
  - [ ]* 3.2 Write unit tests for HyperVService
    - Test VM creation with valid data
    - Test VM creation without IP address
    - Test VM update with host reassignment
    - Test VM deletion with IP release
    - Test error handling for invalid data
    - _Requirements: 1.3, 1.4, 1.5, 2.5_
  
  - [ ]* 3.3 Write property test for host deletion protection
    - **Property 4: Host Deletion Protection**
    - **Validates: Requirements 2.4**
  
  - [ ]* 3.4 Write property test for VM host reassignment
    - **Property 5: VM Host Reassignment**
    - **Validates: Requirements 2.5, 11.1, 11.2**

- [ ] 4. Extend IPManagementService for VM support
  - [ ] 4.1 Add VM-related methods to IPManagementService
    - Implement get_all_ips_by_range_with_vms() to include VM relationship data
    - Implement is_common_vm_range() to identify 192.168.50.x
    - Implement is_rare_vm_range() to identify 192.168.10.x, 11.x, 70.x
    - Update IP assignment/release methods to handle VM IPs
    - _Requirements: 6.1, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4_
  
  - [ ]* 4.2 Write unit tests for IP range classification
    - Test common VM range identification (192.168.50.x)
    - Test rare VM range identification (192.168.10.x, 11.x, 70.x)
    - Test non-VM ranges return False
    - _Requirements: 7.3, 7.4_
  
  - [ ]* 4.3 Write property test for IP occupation status
    - **Property 9: VM IP Occupation Status**
    - **Validates: Requirements 6.1, 6.4**
  
  - [ ]* 4.4 Write property test for IP reassignment
    - **Property 11: VM IP Reassignment**
    - **Validates: Requirements 6.5**
  
  - [ ]* 4.5 Write property test for IP range classification
    - **Property 12: IP Range Classification**
    - **Validates: Requirements 7.1, 7.2, 7.5**

- [ ] 5. Checkpoint - Ensure all tests pass
  - Run all model and service tests
  - Verify database migrations apply cleanly
  - Ensure all tests pass, ask the user if questions arise

- [ ] 6. Create HyperVVMForm for VM entry
  - [ ] 6.1 Implement HyperVVMForm in assets/forms/hyperv_forms.py
    - Create form class with Meta configuration
    - Add host_machine_ip field as ModelChoiceField with IP-based selection
    - Implement __init__ to populate available IPs and set initial values
    - Implement custom label_from_instance() for host dropdown display
    - Implement clean() method to set host_machine from host_machine_ip
    - Add form field widgets with Bootstrap classes
    - _Requirements: 1.2, 2.1, 2.2_
  
  - [ ]* 6.2 Write unit tests for HyperVVMForm
    - Test form validation with valid data
    - Test form validation with missing required fields
    - Test host_machine_ip dropdown population
    - Test IP address dropdown shows only available IPs
    - _Requirements: 1.2, 1.6, 2.1_
  
  - [ ]* 6.3 Write property test for required field validation
    - **Property 2: Required Field Validation**
    - **Validates: Requirements 1.6, 2.1**
  
  - [ ]* 6.4 Write property test for IP validation
    - **Property 13: IP Address Validation**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.5**

- [ ] 7. Implement VM CRUD views
  - [ ] 7.1 Create HyperVVMListView in assets/views.py
    - Implement ListView with queryset filtering for active VMs
    - Add select_related for host_machine and ip_address
    - Set template name and context object name
    - Add login_required mixin
    - _Requirements: 1.7_
  
  - [ ] 7.2 Create HyperVVMCreateView in assets/views.py
    - Implement CreateView with HyperVVMForm
    - Add admin_required mixin for permission control
    - Implement form_valid() to call HyperVService.create_vm()
    - Add success message and redirect
    - Handle validation errors
    - _Requirements: 1.3, 1.6_
  
  - [ ] 7.3 Create HyperVVMUpdateView in assets/views.py
    - Implement UpdateView with HyperVVMForm
    - Add admin_required mixin for permission control
    - Implement form_valid() to call HyperVService.update_vm()
    - Add success message and redirect
    - Handle validation errors
    - _Requirements: 1.4, 8.5_
  
  - [ ] 7.4 Create HyperVVMDetailView in assets/views.py
    - Implement DetailView with select_related for relationships
    - Set template name and context object name
    - Add login_required mixin
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [ ] 7.5 Create HyperVVMDeleteView in assets/views.py
    - Implement DeleteView with admin_required mixin
    - Implement delete() method to call HyperVService.delete_vm()
    - Add success and error messages
    - Handle deletion errors
    - _Requirements: 1.5, 6.4_
  
  - [ ]* 7.6 Write unit tests for VM views
    - Test list view returns active VMs
    - Test create view requires admin permission
    - Test update view requires admin permission
    - Test detail view displays VM information
    - Test delete view removes VM and releases IP
    - _Requirements: 1.3, 1.4, 1.5, 1.7_

- [ ] 8. Create VM templates
  - [ ] 8.1 Create hyperv_vm_list.html template
    - Display table of all active VMs with name, host, and IP
    - Add links to detail, edit, and delete pages
    - Include search and filter controls
    - Display VM count
    - _Requirements: 1.7, 10.1, 10.5_
  
  - [ ] 8.2 Create hyperv_vm_form.html template
    - Render HyperVVMForm with Bootstrap styling
    - Display host_machine_ip dropdown prominently
    - Display IP address dropdown with available IPs
    - Add form validation error display
    - Include submit and cancel buttons
    - _Requirements: 1.2, 2.1, 2.2_
  
  - [ ] 8.3 Create hyperv_vm_detail.html template
    - Display VM name, IP address, and notes
    - Display host machine section with name and IP
    - Add clickable link to host machine detail page
    - Display creation and update timestamps
    - Add edit and delete action buttons
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 9.1, 9.2_
  
  - [ ] 8.4 Create hyperv_vm_confirm_delete.html template
    - Display VM name and confirmation message
    - Show warning about IP release
    - Add confirm and cancel buttons
    - _Requirements: 1.5_
  
  - [ ]* 8.5 Write integration tests for VM templates
    - Test list template renders VM data correctly
    - Test form template displays all fields
    - Test detail template shows host information with link
    - Test delete template shows confirmation
    - _Requirements: 1.2, 1.7, 4.1, 4.2, 4.3_
  
  - [ ]* 8.6 Write property test for navigation links
    - **Property 7: Navigation Links Existence**
    - **Validates: Requirements 3.5, 3.7, 4.3, 4.6, 5.4**

- [ ] 9. Extend Asset detail template to show hosted VMs
  - [ ] 9.1 Update asset detail template
    - Add "Hosted Virtual Machines" section
    - Display list of VMs with names and IPs
    - Add clickable links to VM detail pages
    - Show "No virtual machines" message when list is empty
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ]* 9.2 Write unit tests for asset detail VM section
    - Test VM list displays for host with VMs
    - Test empty message displays for host without VMs
    - Test VM links are clickable
    - _Requirements: 3.1, 3.2, 3.4, 3.5_
  
  - [ ]* 9.3 Write property test for bidirectional information display
    - **Property 6: Bidirectional Information Display**
    - **Validates: Requirements 3.2, 4.1, 4.2**

- [ ] 10. Checkpoint - Ensure all tests pass
  - Run all view and template tests
  - Verify VM CRUD operations work end-to-end
  - Test bidirectional navigation between VMs and hosts
  - Ensure all tests pass, ask the user if questions arise

- [ ] 11. Extend IP list page with VM relationships
  - [ ] 11.1 Update free_ips.html template
    - For each host IP: display hosted VM IPs below with indentation
    - For each VM IP: display host machine IP above
    - Add clickable links between related IPs
    - Apply range-specific styling (prominent for 192.168.50.x, subtle for rare ranges)
    - Add tooltips showing VM name and host machine on hover
    - _Requirements: 3.6, 3.7, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.2, 6.3, 7.1, 7.2, 7.5_
  
  - [ ] 11.2 Update IP list view to include VM relationship data
    - Modify view to call get_all_ips_by_range_with_vms()
    - Pass VM relationship data to template context
    - Include is_common_vm_range and is_rare_vm_range flags
    - _Requirements: 5.1, 5.2, 5.3, 7.1, 7.2_
  
  - [ ]* 11.3 Write unit tests for IP list VM relationships
    - Test host IPs display their hosted VM IPs
    - Test VM IPs display their host machine IP
    - Test links between related IPs are present
    - Test range-specific styling is applied
    - _Requirements: 3.6, 4.5, 5.1, 5.2, 5.3_
  
  - [ ]* 11.4 Write property test for IP list bidirectional relationships
    - **Property 8: IP List Bidirectional Relationships**
    - **Validates: Requirements 3.6, 4.5, 5.1, 5.2, 5.3, 5.6**
  
  - [ ]* 11.5 Write property test for VM IP display styling
    - **Property 10: VM IP Display Styling**
    - **Validates: Requirements 6.2, 6.3**

- [ ] 12. Implement VM search and filtering
  - [ ] 12.1 Add search and filter logic to HyperVVMListView
    - Add search by VM name functionality
    - Add filter by host machine functionality
    - Add filter by IP range functionality
    - Update queryset based on search/filter parameters
    - Pass filter state to template context
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ] 12.2 Update hyperv_vm_list.html with search/filter UI
    - Add search input field for VM name
    - Add dropdown for host machine filter
    - Add dropdown for IP range filter
    - Display active filters and clear buttons
    - Update VM count to reflect filtered results
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ]* 12.3 Write property test for search and filtering
    - **Property 16: VM Search and Filtering**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

- [ ] 13. Implement VM lifecycle management
  - [ ] 13.1 Add soft delete functionality
    - Update HyperVService.delete_vm() to support soft delete (is_active=False)
    - Implement IP release when VM is marked inactive
    - Update views to filter by is_active by default
    - Add option to view inactive VMs in list view
    - _Requirements: 9.3, 9.4, 9.5_
  
  - [ ]* 13.2 Write unit tests for VM lifecycle
    - Test VM timestamps are set correctly on creation
    - Test updated_at changes on modification
    - Test soft delete marks VM as inactive
    - Test soft delete releases IP address
    - Test inactive VMs are preserved in database
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ]* 13.3 Write property test for VM lifecycle timestamps
    - **Property 14: VM Lifecycle Timestamps**
    - **Validates: Requirements 9.1, 9.2**
  
  - [ ]* 13.4 Write property test for VM soft delete
    - **Property 15: VM Soft Delete**
    - **Validates: Requirements 9.3, 9.4, 9.5**

- [ ] 14. Add URL configuration for VM routes
  - Add URL patterns for all VM views (list, create, detail, update, delete)
  - Use appropriate URL names for reverse lookups
  - Ensure URL patterns follow RESTful conventions
  - _Requirements: 1.3, 1.4, 1.5, 1.7_

- [ ] 15. Final checkpoint - Integration testing
  - Run complete test suite (unit tests and property tests)
  - Test end-to-end VM creation workflow
  - Test bidirectional navigation between VMs and hosts
  - Test IP list displays VM relationships correctly
  - Test search and filtering functionality
  - Verify all 18 correctness properties pass
  - Ensure all tests pass, ask the user if questions arise

- [ ] 16. Apply database migrations
  - Run makemigrations to generate migration files
  - Review migration files for correctness
  - Run migrate to apply changes to database
  - Verify database schema matches model definitions
  - _Requirements: 1.1, 2.3_

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All code should follow Django best practices and existing project conventions
- Use transactions for operations that modify multiple models
- Apply select_related and prefetch_related for query optimization
