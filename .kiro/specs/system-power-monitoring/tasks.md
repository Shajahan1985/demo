# Implementation Plan: System Power Monitoring

## Overview

This implementation plan breaks down the System Power Monitoring feature into discrete coding tasks. The feature adds power monitoring capabilities to the existing Django Asset Tracker application, including automated status checks, remote shutdown, email notifications, and after-hours tracking. Tasks are organized to build incrementally, with early validation through testing and checkpoints at key milestones.

## Tasks

- [x] 1. Set up power monitoring Django app structure
  - Create `power_monitoring` Django app with standard structure
  - Add app to INSTALLED_APPS in settings
  - Create initial `__init__.py`, `apps.py`, `admin.py`, `views.py`, `urls.py` files
  - Set up `services` package for business logic layer
  - _Requirements: 1.1, 2.1, 3.1, 4.1_

- [x] 2. Implement database models
  - [x] 2.1 Create PowerStatus model
    - Implement model with fields: asset (OneToOne), is_online, last_checked, last_status_change, online_since, consecutive_failures
    - Add indexes for is_online and last_checked fields
    - Add Meta class with verbose_name_plural and composite indexes
    - _Requirements: 1.2, 1.3, 1.4, 1.5_
  
  - [ ]* 2.2 Write property test for PowerStatus model
    - **Property 2: Online Status Recording**
    - **Property 3: Offline Status Recording**
    - **Validates: Requirements 1.2, 1.3**
  
  - [x] 2.3 Create SystemExemption model
    - Implement model with fields: asset (OneToOne), reason, created_by, created_at, is_active
    - Add index for is_active field
    - _Requirements: 6.1, 6.3, 6.4_
  
  - [ ]* 2.4 Write property test for SystemExemption model
    - **Property 36: Exemption Creation**
    - **Property 38: Exemption Reason Recording**
    - **Validates: Requirements 6.1, 6.3**
  
  - [x] 2.5 Create PowerAuditLog model
    - Implement model with fields: timestamp, action_type, asset, user, details (JSONField)
    - Define ACTION_TYPES choices
    - Add composite indexes for timestamp/action_type and asset/timestamp
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [x] 2.6 Create NotificationRecipient model
    - Implement model with fields: email (unique), is_active, created_at
    - Add email validation
    - _Requirements: 5.1, 5.3, 5.7_
  
  - [ ]* 2.7 Write property test for NotificationRecipient model
    - **Property 32: Email Format Validation**
    - **Validates: Requirements 5.3**
  
  - [x] 2.8 Create MonitoringConfig singleton model
    - Implement model with fields: check_interval_minutes, after_hours_cutoff, notification_time, after_hours_notification_time, ping_timeout_seconds, failure_threshold
    - Add field validators for ranges
    - Override save() to enforce singleton pattern (pk=1)
    - Add get_config() classmethod
    - _Requirements: 7.1, 7.2, 7.3, 8.1, 8.2_
  
  - [ ]* 2.9 Write property test for MonitoringConfig model
    - **Property 41: Check Interval Configuration**
    - **Property 43: Check Interval Validation**
    - **Validates: Requirements 7.1, 7.3**
  
  - [x] 2.10 Create and run database migrations
    - Generate migrations for all models
    - Review migration files for correctness
    - Apply migrations to create database tables
    - _Requirements: All model-related requirements_

- [x] 3. Checkpoint - Verify models and database schema
  - Ensure all migrations apply successfully, verify model relationships in Django shell, ask the user if questions arise.

- [x] 4. Implement PowerMonitorService
  - [x] 4.1 Implement check_asset_status method
    - Execute ICMP ping command using subprocess
    - Handle timeout using configured ping_timeout_seconds
    - Return boolean indicating online/offline status
    - Handle network errors gracefully
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ]* 4.2 Write property test for check_asset_status
    - **Property 1: Power Status Check Coverage**
    - **Validates: Requirements 1.1**
  
  - [x] 4.3 Implement update_power_status method
    - Update or create PowerStatus record for asset
    - Update last_checked timestamp
    - Detect status changes and update last_status_change
    - Update online_since when transitioning to online
    - Handle consecutive_failures counter
    - Create PowerAuditLog entry for status changes
    - _Requirements: 1.4, 1.5, 9.1_
  
  - [ ]* 4.4 Write property test for update_power_status
    - **Property 4: Last Check Timestamp Update**
    - **Property 5: Status Change Timestamp Update**
    - **Validates: Requirements 1.4, 1.5**
  
  - [x] 4.5 Implement check_all_assets method
    - Query all active Assets with IP addresses
    - Call check_asset_status for each asset
    - Call update_power_status with results
    - Return summary dict with counts
    - _Requirements: 1.1, 1.6_
  
  - [ ]* 4.6 Write property test for check_all_assets
    - **Property 6: Exempt System Monitoring**
    - **Validates: Requirements 1.6**
  
  - [x] 4.7 Implement get_online_assets method
    - Query PowerStatus for is_online=True
    - Optionally exclude exempt systems
    - Return QuerySet with related asset data
    - _Requirements: 2.1_
  
  - [x] 4.8 Implement get_after_hours_assets method
    - Get current time and config after_hours_cutoff
    - Query online assets where online_since < cutoff
    - Exclude exempt systems
    - Return QuerySet
    - _Requirements: 8.3, 8.8_
  
  - [ ]* 4.9 Write unit tests for PowerMonitorService
    - Test network timeout handling
    - Test consecutive failure threshold
    - Test exempt system filtering
    - _Requirements: 1.1, 1.2, 1.3, 1.6_

- [x] 5. Implement ShutdownManagerService
  - [x] 5.1 Implement can_shutdown method
    - Check if user has staff permissions
    - Check if asset is exempt
    - Return tuple (bool, reason_string)
    - _Requirements: 3.2, 3.3_
  
  - [ ]* 5.2 Write property test for can_shutdown
    - **Property 16: Shutdown Authorization**
    - **Property 17: Exempt System Shutdown Prevention**
    - **Validates: Requirements 3.2, 3.3**
  
  - [x] 5.3 Implement shutdown_asset method
    - Call can_shutdown to verify permissions
    - Execute Windows shutdown command via subprocess
    - Handle command failures and timeouts
    - Update PowerStatus to offline on success
    - Create PowerAuditLog entry with result
    - Return tuple (success, message)
    - _Requirements: 3.1, 3.4, 3.5, 3.6_
  
  - [ ]* 5.4 Write property test for shutdown_asset
    - **Property 15: Shutdown Command Execution**
    - **Property 18: Shutdown Audit Logging**
    - **Property 20: Successful Shutdown Status Update**
    - **Validates: Requirements 3.1, 3.4, 3.6**
  
  - [x] 5.5 Implement bulk_shutdown method
    - Iterate through asset list
    - Call shutdown_asset for each non-exempt asset
    - Collect results in summary dict
    - Return dict with success/failure counts
    - _Requirements: 3.7_
  
  - [ ]* 5.6 Write property test for bulk_shutdown
    - **Property 21: Bulk Shutdown Execution**
    - **Validates: Requirements 3.7**
  
  - [ ]* 5.7 Write unit tests for ShutdownManagerService
    - Test shutdown command failure handling
    - Test permission denied scenarios
    - Test exempt system blocking
    - _Requirements: 3.2, 3.3, 3.5_

- [x] 6. Implement NotificationService
  - [x] 6.1 Implement get_active_recipients method
    - Query NotificationRecipient for is_active=True
    - Return list of email addresses
    - Return default recipient if list is empty
    - _Requirements: 5.1, 5.2, 5.6_
  
  - [ ]* 6.2 Write property test for get_active_recipients
    - **Property 30: Recipient List Persistence**
    - **Property 34: Default Recipient Fallback**
    - **Validates: Requirements 5.1, 5.6**
  
  - [x] 6.3 Implement format_notification_email method
    - Build HTML email template with asset table
    - Include user name, IP address, online duration for each asset
    - Highlight after-hours systems if is_after_hours=True
    - Generate appropriate subject line
    - Return tuple (subject, html_body)
    - _Requirements: 4.3, 4.4, 4.5, 4.6, 4.8, 4.9_
  
  - [ ]* 6.4 Write property test for format_notification_email
    - **Property 24: Email Content - User Names**
    - **Property 25: Email Content - IP Addresses**
    - **Property 26: Email Content - Online Duration**
    - **Validates: Requirements 4.3, 4.4, 4.5**
  
  - [x] 6.5 Implement send_daily_notification method
    - Get online non-exempt assets
    - Return early if no assets found
    - Get active recipients
    - Format email with asset data
    - Send email using Django email backend
    - Create PowerAuditLog entry
    - Return success boolean
    - _Requirements: 4.1, 4.2, 4.7_
  
  - [x] 6.6 Implement send_after_hours_notification method
    - Get after-hours assets
    - Return early if no assets found
    - Get active recipients
    - Format email with after-hours flag
    - Send email using Django email backend
    - Create PowerAuditLog entry
    - Return success boolean
    - _Requirements: 8.6, 8.7_
  
  - [ ]* 6.7 Write property test for notification methods
    - **Property 22: Notification Asset Identification**
    - **Property 23: Email Sending on Online Assets**
    - **Property 31: Multiple Recipient Support**
    - **Validates: Requirements 4.1, 4.2, 5.2**
  
  - [ ]* 6.8 Write unit tests for NotificationService
    - Test email formatting with various asset counts
    - Test SMTP connection failure handling
    - Test empty recipient list fallback
    - _Requirements: 4.2, 5.6_

- [x] 7. Implement ExemptionService
  - [x] 7.1 Implement create_exemption method
    - Create SystemExemption record
    - Set created_by to user
    - Create PowerAuditLog entry
    - Return created exemption
    - _Requirements: 6.1, 6.3, 6.4, 9.4_
  
  - [x] 7.2 Implement remove_exemption method
    - Set is_active=False on exemption
    - Create PowerAuditLog entry
    - Return success boolean
    - _Requirements: 6.2, 9.4_
  
  - [ ]* 7.3 Write property test for exemption methods
    - **Property 37: Exemption Removal**
    - **Property 39: Exemption Creator Recording**
    - **Property 51: Exemption Change Audit Logging**
    - **Validates: Requirements 6.2, 6.4, 9.4**
  
  - [x] 7.4 Implement is_exempt method
    - Check if asset has active exemption
    - Return boolean
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 7.5 Write unit tests for ExemptionService
    - Test exemption creation with reason
    - Test exemption removal (soft delete)
    - Test is_exempt with active/inactive exemptions
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 8. Checkpoint - Verify service layer functionality
  - Ensure all services pass tests, verify service integration with models, ask the user if questions arise.

- [x] 9. Implement Celery tasks
  - [x] 9.1 Create check_power_status_task
    - Define shared_task decorator
    - Call PowerMonitorService.check_all_assets()
    - Log results
    - Return summary dict
    - _Requirements: 1.1, 7.4_
  
  - [x] 9.2 Create send_daily_notification_task
    - Define shared_task decorator
    - Call NotificationService.send_daily_notification()
    - Return success status
    - _Requirements: 4.2, 7.5_
  
  - [x] 9.3 Create send_after_hours_notification_task
    - Define shared_task decorator
    - Call NotificationService.send_after_hours_notification()
    - Return success status
    - _Requirements: 8.6, 8.7_
  
  - [x] 9.4 Configure Celery Beat schedule
    - Add periodic task for check_power_status_task using MonitoringConfig.check_interval_minutes
    - Add crontab task for send_daily_notification_task using MonitoringConfig.notification_time
    - Add crontab task for send_after_hours_notification_task using MonitoringConfig.after_hours_notification_time
    - _Requirements: 7.1, 7.2, 7.4, 7.5_
  
  - [ ]* 9.5 Write unit tests for Celery tasks
    - Test task execution with mocked services
    - Test task scheduling configuration
    - Use CELERY_TASK_ALWAYS_EAGER for synchronous testing
    - _Requirements: 7.4, 7.5_

- [ ] 10. Implement REST API serializers
  - [ ] 10.1 Create PowerStatusSerializer
    - Include asset details (serial_number, asset_tag, assigned_to, ip_address)
    - Include all PowerStatus fields
    - Add computed field for online_duration
    - Add computed field for is_after_hours
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ] 10.2 Create SystemExemptionSerializer
    - Include all exemption fields
    - Include created_by username
    - _Requirements: 6.1, 6.3, 6.4_
  
  - [ ] 10.3 Create PowerAuditLogSerializer
    - Include all audit log fields
    - Include asset and user details
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [ ] 10.4 Create NotificationRecipientSerializer
    - Include all recipient fields
    - Add email validation
    - _Requirements: 5.1, 5.3_
  
  - [ ] 10.5 Create MonitoringConfigSerializer
    - Include all config fields
    - Add field validators
    - _Requirements: 7.1, 7.2, 8.1_

- [ ] 11. Implement REST API views and endpoints
  - [ ] 11.1 Create PowerStatusViewSet
    - Implement list action with filtering (online_only, exclude_exempt, after_hours_only)
    - Implement retrieve action
    - Add check_all action for triggering immediate check
    - Add check_one action for single asset check
    - Require staff permissions for check actions
    - _Requirements: 2.1, 2.6, 2.10_
  
  - [ ]* 11.2 Write property test for PowerStatusViewSet
    - **Property 7: Online Assets Display**
    - **Property 12: Exempt System Exclusion from Default View**
    - **Property 14: After-Hours Filter**
    - **Validates: Requirements 2.1, 2.6, 2.10**
  
  - [ ] 11.3 Create ShutdownViewSet
    - Implement shutdown action for single asset
    - Implement bulk_shutdown action
    - Require staff permissions
    - Return detailed success/failure messages
    - _Requirements: 3.1, 3.2, 3.7_
  
  - [ ] 11.4 Create ExemptionViewSet
    - Implement list, create, destroy actions
    - Require staff permissions for create/destroy
    - _Requirements: 6.1, 6.2, 6.5_
  
  - [ ]* 11.5 Write property test for ExemptionViewSet
    - **Property 11: Exempt Status Indication**
    - **Property 40: Exempt Asset Notification Exclusion**
    - **Validates: Requirements 2.5, 6.6_
  
  - [ ] 11.6 Create NotificationRecipientViewSet
    - Implement list, create, destroy, partial_update actions
    - Require staff permissions for modifications
    - _Requirements: 5.1, 5.4, 5.7_
  
  - [ ]* 11.7 Write property test for NotificationRecipientViewSet
    - **Property 33: Recipient Removal**
    - **Property 35: Recipient Active Status Toggle**
    - **Validates: Requirements 5.4, 5.7**
  
  - [ ] 11.8 Create MonitoringConfigViewSet
    - Implement retrieve and update actions for singleton
    - Require staff permissions for update
    - _Requirements: 7.1, 7.2, 7.3, 8.1_
  
  - [ ]* 11.9 Write property test for MonitoringConfigViewSet
    - **Property 42: Notification Time Configuration**
    - **Property 44: After-Hours Cutoff Configuration**
    - **Validates: Requirements 7.2, 8.1**
  
  - [ ] 11.10 Create PowerAuditLogViewSet
    - Implement list and retrieve actions
    - Add filtering by date_range, asset_id, action_type
    - Make read-only (no create/update/delete)
    - _Requirements: 9.5, 9.6, 9.7_
  
  - [ ]* 11.11 Write property test for PowerAuditLogViewSet
    - **Property 52: Audit Log Date Filtering**
    - **Property 53: Audit Log Asset Filtering**
    - **Property 54: Audit Log Action Type Filtering**
    - **Validates: Requirements 9.5, 9.6, 9.7**
  
  - [ ] 11.12 Configure API URL routing
    - Register all viewsets with router
    - Add API URLs to main urls.py
    - _Requirements: All API requirements_
  
  - [ ]* 11.13 Write integration tests for API endpoints
    - Test authentication and authorization
    - Test query parameter filtering
    - Test bulk operations
    - Test error responses
    - _Requirements: All API requirements_

- [ ] 12. Checkpoint - Verify API functionality
  - Ensure all API endpoints work correctly, test with API client or curl, ask the user if questions arise.

- [ ] 13. Implement web interface views
  - [x] 13.1 Create power_report_view
    - Query online assets with user and IP details
    - Query after-hours assets
    - Calculate online durations
    - Pass data to template context
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.9_
  
  - [ ]* 13.2 Write property test for power_report_view
    - **Property 8: User Name Display**
    - **Property 9: IP Address Display**
    - **Property 10: Online Duration Display**
    - **Property 13: After-Hours Highlighting**
    - **Validates: Requirements 2.2, 2.3, 2.4, 2.9**
  
  - [ ] 13.3 Create config_view
    - Display MonitoringConfig form
    - Display NotificationRecipient list and form
    - Handle form submissions
    - Require staff permissions
    - _Requirements: 7.1, 7.2, 5.1_
  
  - [ ] 13.4 Create audit_log_view
    - Query PowerAuditLog with pagination
    - Implement date, asset, action_type filters
    - Pass filtered logs to template
    - _Requirements: 9.5, 9.6, 9.7_
  
  - [ ]* 13.5 Write property test for audit_log_view
    - **Property 49: Status Change Audit Logging**
    - **Property 50: Notification Audit Logging**
    - **Validates: Requirements 9.1, 9.3**
  
  - [ ] 13.6 Configure web URL routing
    - Add URL patterns for all views
    - Include in main urls.py
    - _Requirements: 2.1, 7.1, 9.5_

- [ ] 14. Create web interface templates
  - [x] 14.1 Create report.html template
    - Display online assets table with user, IP, duration columns
    - Add after-hours highlighting with CSS
    - Add filter controls for after-hours only
    - Add refresh button
    - Add shutdown buttons for each asset
    - Show exempt systems in separate section
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_
  
  - [ ]* 14.2 Write property test for report template
    - **Property 46: After-Hours Duration Display**
    - **Property 48: Real-Time After-Hours Flagging**
    - **Validates: Requirements 8.5, 8.8**
  
  - [ ] 14.3 Create config.html template
    - Display MonitoringConfig form fields
    - Display NotificationRecipient list with add/remove controls
    - Add form validation feedback
    - _Requirements: 7.1, 7.2, 5.1, 5.4, 5.7_
  
  - [ ] 14.4 Create audit.html template
    - Display audit log table with timestamp, action, asset, user columns
    - Add filter form for date range, asset, action type
    - Add pagination controls
    - _Requirements: 9.5, 9.6, 9.7_
  
  - [ ] 14.5 Create base template and CSS styling
    - Create base template with navigation
    - Add CSS for tables, forms, buttons
    - Add CSS for after-hours highlighting
    - Ensure responsive design
    - _Requirements: 2.1, 2.9_

- [ ] 15. Create email templates
  - [ ] 15.1 Create daily_notification.html email template
    - Display online assets table
    - Include user name, IP address, online duration
    - Add clear subject line
    - Format for HTML email
    - _Requirements: 4.3, 4.4, 4.5, 4.6_
  
  - [ ] 15.2 Create after_hours_notification.html email template
    - Display after-hours assets table
    - Highlight after-hours status
    - Include duration past cutoff time
    - Add clear subject line
    - Format for HTML email
    - _Requirements: 4.8, 4.9, 8.6_
  
  - [ ]* 15.3 Write property test for email templates
    - **Property 28: After-Hours Asset Prioritization**
    - **Property 29: After-Hours Status in Email**
    - **Validates: Requirements 4.8, 4.9**

- [x] 16. Configure Django admin interface
  - [x] 16.1 Register PowerStatus in admin
    - Add list_display for key fields
    - Add list_filter for is_online
    - Add search_fields for asset
    - Make read-only
    - _Requirements: 1.1_
  
  - [x] 16.2 Register SystemExemption in admin
    - Add list_display for asset, reason, created_by, is_active
    - Add list_filter for is_active
    - Add search_fields for asset, reason
    - _Requirements: 6.1_
  
  - [x] 16.3 Register PowerAuditLog in admin
    - Add list_display for timestamp, action_type, asset, user
    - Add list_filter for action_type, timestamp
    - Add search_fields for asset
    - Make read-only
    - _Requirements: 9.1_
  
  - [x] 16.4 Register NotificationRecipient in admin
    - Add list_display for email, is_active, created_at
    - Add list_filter for is_active
    - Add search_fields for email
    - _Requirements: 5.1_
  
  - [x] 16.5 Register MonitoringConfig in admin
    - Display all config fields
    - Add field help text
    - Enforce singleton pattern
    - _Requirements: 7.1_

- [x] 17. Add configuration to Django settings
  - [x] 17.1 Configure Celery settings
    - Set CELERY_BROKER_URL
    - Set CELERY_RESULT_BACKEND
    - Configure CELERY_BEAT_SCHEDULE with dynamic config loading
    - Set CELERY_TASK_ALWAYS_EAGER=False for production
    - _Requirements: 7.4, 7.5_
  
  - [x] 17.2 Configure email settings
    - Set EMAIL_BACKEND
    - Set EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS
    - Set EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
    - Set DEFAULT_FROM_EMAIL
    - _Requirements: 4.2, 5.6_
  
  - [x] 17.3 Add power monitoring settings
    - Set DEFAULT_NOTIFICATION_RECIPIENT
    - Set POWER_MONITORING_ENABLED flag
    - _Requirements: 5.6_

- [x] 18. Create management commands
  - [x] 18.1 Create check_power_status management command
    - Allow manual triggering of power status check
    - Display results summary
    - _Requirements: 1.1_
  
  - [x] 18.2 Create send_notifications management command
    - Allow manual triggering of notifications
    - Support --after-hours flag
    - Display results summary
    - _Requirements: 4.2, 8.6_
  
  - [x] 18.3 Create init_monitoring_config management command
    - Create MonitoringConfig with default values if not exists
    - Display created config
    - _Requirements: 7.6, 8.2_

- [ ] 19. Checkpoint - Verify complete feature integration
  - Ensure all components work together, test end-to-end flows, ask the user if questions arise.

- [ ] 20. Write comprehensive integration tests
  - [ ]* 20.1 Write end-to-end power check flow test
    - Test: check → status update → audit log
    - Verify all components interact correctly
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.1_
  
  - [ ]* 20.2 Write end-to-end shutdown flow test
    - Test: request → authorization → command → status update → audit log
    - Verify permission checks and exemption blocking
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6_
  
  - [ ]* 20.3 Write end-to-end notification flow test
    - Test: trigger → query assets → format email → send → audit log
    - Verify recipient handling and email content
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 9.3_
  
  - [ ]* 20.4 Write after-hours detection integration test
    - Test after-hours asset identification across services
    - Verify after-hours notification flow
    - _Requirements: 8.3, 8.6, 8.8_

- [x] 21. Create initial data fixtures
  - [x] 21.1 Create fixture for default MonitoringConfig
    - Set default check interval (15 minutes)
    - Set default notification time (5:30 PM)
    - Set default after-hours cutoff (8:30 PM)
    - Set default after-hours notification time (8:45 PM)
    - _Requirements: 7.6, 8.2_
  
  - [x] 21.2 Create fixture for default NotificationRecipient
    - Add shajahan.t@benzyinfotech.com as default recipient
    - _Requirements: 5.5, 5.6_

- [ ] 22. Add documentation
  - [ ] 22.1 Create README for power_monitoring app
    - Document feature overview
    - Document configuration options
    - Document API endpoints
    - Document management commands
    - _Requirements: All requirements_
  
  - [ ] 22.2 Add docstrings to all service methods
    - Document parameters and return values
    - Add usage examples
    - _Requirements: All requirements_
  
  - [ ] 22.3 Create user guide for web interface
    - Document how to view power report
    - Document how to shutdown systems
    - Document how to manage exemptions
    - Document how to configure monitoring
    - _Requirements: 2.1, 3.1, 6.1, 7.1_

- [ ] 23. Final checkpoint - Complete feature validation
  - Run all tests including property-based tests with full iterations, verify all requirements are met, ensure documentation is complete, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end flows across multiple components
- The feature integrates with existing Asset, IPAddress, Team, and OperatingSystem models
- Celery and Celery Beat must be running for scheduled tasks to execute
- Email configuration must be set up for notifications to work
- Windows shutdown commands require appropriate network permissions
