# Requirements Document

## Introduction

The Freed System Reassignment feature enables administrators to reassign healthy freed systems to new users and teams. When a system is freed but remains in healthy condition, it can be put back into active use rather than being scrapped. This feature adds a reassignment workflow that transitions freed systems back to active status, manages IP address allocation, and maintains proper tracking of system lifecycle transitions.

## Glossary

- **Freed_System**: An asset with status='freed' that has been released from its previous assignment
- **Healthy_System**: A freed system with health_status='healthy' indicating it is functional
- **Defective_System**: A freed system with health_status='defective' indicating it has issues
- **Reassignment_Service**: The service component responsible for reassigning freed systems to active status
- **IP_Management_Service**: The service component responsible for IP address allocation and release
- **Free_Systems_Page**: The web page displaying all freed systems
- **Free_IPs_Page**: The web page displaying all IP addresses with their assignment status
- **Reassignment_Form**: The web form used to collect reassignment details (user, team, IP)
- **Administrator**: A user with is_staff=True permission level
- **Active_Asset**: An asset with status='active' that is currently assigned and in use

## Requirements

### Requirement 1: Display Reassignment Action

**User Story:** As an administrator, I want to see a reassignment option for healthy freed systems, so that I can put functional systems back into active use.

#### Acceptance Criteria

1. WHEN the Free_Systems_Page is displayed, THE Free_Systems_Page SHALL show a "Reassign" button for each freed system with health_status='healthy'
2. WHEN the Free_Systems_Page is displayed, THE Free_Systems_Page SHALL NOT show a "Reassign" button for freed systems with health_status='defective'
3. WHERE the user is not an Administrator, THE Free_Systems_Page SHALL NOT display any "Reassign" buttons
4. THE "Reassign" button SHALL be visually distinct from the "Scrap" button

### Requirement 2: Reassignment Form Display

**User Story:** As an administrator, I want to fill out reassignment details, so that I can properly assign the system to a new user and team.

#### Acceptance Criteria

1. WHEN an Administrator clicks the "Reassign" button, THE Reassignment_Form SHALL display with the asset details
2. THE Reassignment_Form SHALL include an "Assigned To" text input field for the user name
3. THE Reassignment_Form SHALL include a "Team" dropdown field populated with all teams in hierarchical format
4. THE Reassignment_Form SHALL include an "IP Address" dropdown field populated with all unassigned IP addresses
5. THE Reassignment_Form SHALL include a "Manual IP" text input field for manual IP entry
6. THE Reassignment_Form SHALL display the asset_tag, system_type, and operating_system as read-only information
7. WHEN the Reassignment_Form is displayed, THE Reassignment_Form SHALL pre-populate the IP dropdown with IPAddress records where is_assigned=False

### Requirement 3: Reassignment Validation

**User Story:** As an administrator, I want the system to validate reassignment data, so that I can ensure proper asset assignment.

#### Acceptance Criteria

1. WHEN the Reassignment_Form is submitted with an empty "Assigned To" field, THE Reassignment_Service SHALL return a validation error
2. WHEN the Reassignment_Form is submitted with an empty "Team" field, THE Reassignment_Service SHALL return a validation error
3. WHEN the Reassignment_Form is submitted with both IP Address and Manual IP empty, THE Reassignment_Service SHALL return a validation error
4. WHEN the Reassignment_Form is submitted with an IP Address that has is_assigned=True, THE Reassignment_Service SHALL return a validation error
5. IF the asset health_status is not 'healthy', THEN THE Reassignment_Service SHALL return a validation error
6. IF the asset status is not 'freed', THEN THE Reassignment_Service SHALL return a validation error

### Requirement 4: Asset Status Transition

**User Story:** As an administrator, I want the freed system to become active when reassigned, so that it appears in the active assets list.

#### Acceptance Criteria

1. WHEN a valid reassignment is submitted, THE Reassignment_Service SHALL change the asset status from 'freed' to 'active'
2. WHEN a valid reassignment is submitted, THE Reassignment_Service SHALL set the asset assigned_to field to the provided user name
3. WHEN a valid reassignment is submitted, THE Reassignment_Service SHALL set the asset team field to the selected team
4. WHEN a valid reassignment is submitted, THE Reassignment_Service SHALL set the asset freed_date field to NULL
5. WHEN a valid reassignment is submitted, THE Reassignment_Service SHALL set the asset health_status field to NULL
6. WHEN a valid reassignment is submitted, THE Reassignment_Service SHALL set the asset issues_description field to NULL

### Requirement 5: IP Address Management for Dropdown Selection

**User Story:** As an administrator, I want IP addresses to be properly managed during reassignment, so that IP allocation remains accurate.

#### Acceptance Criteria

1. WHEN a reassignment is submitted with an IP Address from the dropdown, THE IP_Management_Service SHALL set the selected IPAddress is_assigned field to True
2. WHEN a reassignment is submitted with an IP Address from the dropdown, THE IP_Management_Service SHALL set the selected IPAddress assigned_to_asset field to the asset
3. WHEN a reassignment is submitted with an IP Address from the dropdown, THE Reassignment_Service SHALL set the asset ip_address field to the selected IPAddress
4. WHEN a reassignment is submitted with an IP Address from the dropdown, THE Reassignment_Service SHALL set the asset manual_ip field to NULL
5. IF the freed asset had a previous ip_address assigned, THEN THE IP_Management_Service SHALL set that IPAddress is_assigned field to False before assigning the new IP
6. IF the freed asset had a previous ip_address assigned, THEN THE IP_Management_Service SHALL set that IPAddress assigned_to_asset field to NULL before assigning the new IP

### Requirement 6: IP Address Management for Manual Entry

**User Story:** As an administrator, I want to use manual IP addresses during reassignment, so that I can assign IPs not tracked in the IP management system.

#### Acceptance Criteria

1. WHEN a reassignment is submitted with a Manual IP value, THE Reassignment_Service SHALL set the asset manual_ip field to the provided IP address
2. WHEN a reassignment is submitted with a Manual IP value, THE Reassignment_Service SHALL set the asset ip_address field to NULL
3. IF the freed asset had a previous ip_address assigned, THEN THE IP_Management_Service SHALL set that IPAddress is_assigned field to False
4. IF the freed asset had a previous ip_address assigned, THEN THE IP_Management_Service SHALL set that IPAddress assigned_to_asset field to NULL
5. WHEN a reassignment is submitted with a Manual IP value, THE Reassignment_Service SHALL validate the IP address format

### Requirement 7: Free Systems Page Update

**User Story:** As an administrator, I want reassigned systems to disappear from the freed systems page, so that I only see systems that still need action.

#### Acceptance Criteria

1. WHEN a reassignment is successfully completed, THE Free_Systems_Page SHALL NOT display the reassigned asset
2. WHEN the Free_Systems_Page is loaded, THE Free_Systems_Page SHALL only display assets with status='freed'

### Requirement 8: Free IPs Page Accuracy

**User Story:** As an administrator, I want the Free IPs page to accurately reflect IP assignment status, so that I can see which IPs are available.

#### Acceptance Criteria

1. WHEN a reassignment uses an IP from the dropdown, THE Free_IPs_Page SHALL mark that IP as occupied
2. WHEN a freed system's old IP is released during reassignment, THE Free_IPs_Page SHALL mark that IP as unoccupied
3. WHEN the Free_IPs_Page is loaded, THE Free_IPs_Page SHALL display IPAddress records with is_assigned=True as occupied
4. WHEN the Free_IPs_Page is loaded, THE Free_IPs_Page SHALL display IPAddress records with is_assigned=False as unoccupied
5. WHEN the Free_IPs_Page is loaded, THE Free_IPs_Page SHALL display manual IP addresses from active assets as occupied

### Requirement 9: Reassignment Success Feedback

**User Story:** As an administrator, I want confirmation when reassignment succeeds, so that I know the operation completed successfully.

#### Acceptance Criteria

1. WHEN a reassignment is successfully completed, THE Reassignment_Service SHALL redirect to the Active Assets page
2. WHEN a reassignment is successfully completed, THE Reassignment_Service SHALL display a success message containing the asset_tag
3. THE success message SHALL indicate the asset has been reassigned and is now active

### Requirement 10: Atomic Reassignment Transaction

**User Story:** As an administrator, I want reassignment to be atomic, so that partial failures do not leave the system in an inconsistent state.

#### Acceptance Criteria

1. WHEN a reassignment operation begins, THE Reassignment_Service SHALL execute all database changes within a single transaction
2. IF any validation error occurs during reassignment, THEN THE Reassignment_Service SHALL roll back all changes
3. IF any database error occurs during reassignment, THEN THE Reassignment_Service SHALL roll back all changes
4. WHEN a reassignment transaction is rolled back, THE Reassignment_Service SHALL preserve the original asset status and IP assignments
