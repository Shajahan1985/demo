# Requirements Document

## Introduction

This feature enhances the Freed Systems page in the Django Asset Tracker application by adding manual system entry capabilities and health status tracking. Currently, systems can only be freed through the "Free Asset" action on active assets. This enhancement allows direct entry of freed systems and tracks their operational health status with issue descriptions for defective systems.

## Glossary

- **Freed_System**: An asset with status='freed' that is no longer assigned to any user or team
- **Health_Status**: An indicator showing whether a freed system is operational (Healthy) or non-operational (Defective)
- **Manual_Entry_Form**: A form that allows direct creation of freed systems without requiring a pre-existing active asset
- **Issue_Description**: A text field describing problems with a defective freed system
- **Freed_Systems_Page**: The web page displaying all assets with status='freed'
- **Asset_Service**: The service layer component responsible for asset lifecycle operations

## Requirements

### Requirement 1: Manual Freed System Entry

**User Story:** As an administrator, I want to manually add freed systems directly, so that I can track systems that were never in the active inventory.

#### Acceptance Criteria

1. THE Manual_Entry_Form SHALL accept asset_tag, system_type, operating_system, and IP_address as input fields
2. WHEN the Manual_Entry_Form is submitted with valid data, THE Asset_Service SHALL create a new asset with status='freed' and freed_date set to the current timestamp
3. WHEN the Manual_Entry_Form is submitted with valid data, THE Asset_Service SHALL set assigned_to and team fields to NULL
4. WHEN the Manual_Entry_Form is submitted with a duplicate asset_tag, THE Asset_Service SHALL return a validation error
5. WHEN the Manual_Entry_Form is submitted with missing required fields, THE Asset_Service SHALL return validation errors for each missing field

### Requirement 2: Health Status Tracking

**User Story:** As an administrator, I want to mark freed systems as healthy or defective, so that I can track which systems are operational and which need attention.

#### Acceptance Criteria

1. THE Asset SHALL include a health_status field with allowed values 'healthy' and 'defective'
2. WHEN a freed system is created through the Manual_Entry_Form, THE Asset_Service SHALL require selection of health_status
3. WHEN an active asset is freed through the existing free_asset operation, THE Asset_Service SHALL set health_status to 'healthy' by default
4. THE Freed_Systems_Page SHALL display the health_status for each freed system
5. WHEN health_status is 'healthy', THE Freed_Systems_Page SHALL display a visual indicator using green color or a checkmark icon
6. WHEN health_status is 'defective', THE Freed_Systems_Page SHALL display a visual indicator using red color or a warning icon

### Requirement 3: Issue Description for Defective Systems

**User Story:** As an administrator, I want to describe issues with defective systems, so that I can document what problems exist and track repair needs.

#### Acceptance Criteria

1. THE Asset SHALL include an issues_description field for storing text descriptions
2. WHEN health_status is set to 'defective', THE Manual_Entry_Form SHALL require the issues_description field to be populated
3. WHEN health_status is set to 'healthy', THE Manual_Entry_Form SHALL allow issues_description to be empty or NULL
4. WHEN health_status is 'defective' and issues_description is empty, THE Asset_Service SHALL return a validation error
5. THE Freed_Systems_Page SHALL display the issues_description for systems with health_status='defective'
6. WHEN health_status is 'healthy', THE Freed_Systems_Page SHALL not display the issues_description field

### Requirement 4: Existing Functionality Preservation

**User Story:** As an administrator, I want the existing asset freeing process to continue working, so that my current workflows are not disrupted.

#### Acceptance Criteria

1. WHEN an active asset is freed through the existing free_asset operation, THE Asset_Service SHALL set status to 'freed' and freed_date to the current timestamp
2. WHEN an active asset is freed through the existing free_asset operation, THE Asset_Service SHALL set assigned_to and team to NULL
3. WHEN an active asset is freed through the existing free_asset operation, THE Asset_Service SHALL require password confirmation before processing
4. THE Freed_Systems_Page SHALL display both manually entered freed systems and systems freed from active inventory
5. THE Freed_Systems_Page SHALL display asset_tag, system_type, operating_system, IP_address, and freed_date for all freed systems

### Requirement 5: Health Status Updates

**User Story:** As an administrator, I want to update the health status of freed systems, so that I can reflect changes in system condition over time.

#### Acceptance Criteria

1. THE Freed_Systems_Page SHALL provide an edit action for each freed system
2. WHEN the edit action is invoked, THE Asset_Service SHALL display a form pre-populated with current asset data
3. WHEN health_status is changed from 'healthy' to 'defective' in the edit form, THE Asset_Service SHALL require issues_description to be provided
4. WHEN health_status is changed from 'defective' to 'healthy' in the edit form, THE Asset_Service SHALL allow issues_description to be cleared
5. WHEN the edit form is submitted with valid data, THE Asset_Service SHALL update the asset record and display a success message
