# Requirements Document

## Introduction

This document specifies the requirements for an Asset Tracking System that manages IT assets (computers and systems) within an organization. The system tracks asset assignments, IP addresses, system details, and lifecycle states (active, freed, scrapped) while enforcing admin-only permissions for critical operations.

## Glossary

- **Asset Tracking System**: The Django application component responsible for managing IT assets and their lifecycle
- **Asset**: A physical IT system (Desktop, Laptop, or All-in-One PC) tracked by the system
- **Asset Tag**: A unique identifier for each asset in the format "BIDC + number"
- **System Type**: The category of asset (Desktop, Laptop, All-in-One PC)
- **IP Address**: A network address assigned to an asset from predefined ranges
- **IP Range**: A series of IP addresses (e.g., 192.168.10.x, 192.168.11.x, 192.168.70.x, 192.168.50.x)
- **Free System**: An asset that has been released from active use but not yet scrapped
- **Scrapped System**: An asset that has been permanently removed from inventory
- **Admin User**: A user with elevated privileges to manage assets
- **Team**: A group within the organization to which assets are assigned
- **Particulars**: Detailed information about an asset including attachments and images

## Requirements

### Requirement 1

**User Story:** As an admin user, I want to add new assets to the system, so that I can track all IT equipment in the organization.

#### Acceptance Criteria

1. WHEN an admin user submits an asset creation form with asset tag, system type, OS, IP address, particulars, assigned to, and team THEN the Asset Tracking System SHALL create a new asset record with all specified details
2. WHEN an admin user attempts to create an asset with a duplicate asset tag THEN the Asset Tracking System SHALL reject the creation and display an error message
3. WHEN an admin user creates an asset THEN the Asset Tracking System SHALL assign a sequential serial number to the asset
4. WHEN an admin user selects an IP address for a new asset THEN the Asset Tracking System SHALL mark that IP address as in use
5. WHEN a non-admin user attempts to add an asset THEN the Asset Tracking System SHALL deny access and return an authorization error

### Requirement 2

**User Story:** As an admin user, I want to edit existing asset information, so that I can keep asset records up to date.

#### Acceptance Criteria

1. WHEN an admin user submits updated information for an asset THEN the Asset Tracking System SHALL save the changes and maintain data integrity
2. WHEN an admin user changes the IP address of an asset THEN the Asset Tracking System SHALL mark the old IP as free and the new IP as in use
3. WHEN an admin user updates asset particulars THEN the Asset Tracking System SHALL preserve existing attachments unless explicitly removed
4. WHEN a non-admin user attempts to edit an asset THEN the Asset Tracking System SHALL deny access and return an authorization error

### Requirement 3

**User Story:** As an admin user, I want to free assets that are no longer in use, so that I can track available equipment.

#### Acceptance Criteria

1. WHEN an admin user initiates the free action on an asset THEN the Asset Tracking System SHALL display a confirmation message "Do you want to free this system?"
2. WHEN an admin user confirms freeing an asset THEN the Asset Tracking System SHALL prompt for the admin password
3. WHEN an admin user provides correct password and confirms THEN the Asset Tracking System SHALL move the asset to the Free Systems page
4. WHEN an asset is freed THEN the Asset Tracking System SHALL move its IP address to the Free IPs page under the appropriate IP range
5. WHEN an asset is freed THEN the Asset Tracking System SHALL clear the assigned to and team fields
6. WHEN a non-admin user attempts to free an asset THEN the Asset Tracking System SHALL deny access and return an authorization error

### Requirement 4

**User Story:** As an admin user, I want to view all active assets, so that I can see what equipment is currently in use.

#### Acceptance Criteria

1. WHEN a user requests the assets list THEN the Asset Tracking System SHALL display all active assets with serial number, asset tag, system type, OS, IP address, assigned to, and team
2. WHEN displaying the assets list THEN the Asset Tracking System SHALL exclude freed and scrapped assets
3. WHEN displaying the assets list THEN the Asset Tracking System SHALL order assets by serial number

### Requirement 5

**User Story:** As an admin user, I want to view freed systems, so that I can see what equipment is available for reassignment or scrapping.

#### Acceptance Criteria

1. WHEN a user requests the Free Systems page THEN the Asset Tracking System SHALL display all freed assets with IP address and asset tag
2. WHEN displaying freed systems THEN the Asset Tracking System SHALL provide a delete option for each system
3. WHEN displaying freed systems THEN the Asset Tracking System SHALL exclude active and scrapped assets

### Requirement 6

**User Story:** As an admin user, I want to scrap freed systems, so that I can permanently remove obsolete equipment from inventory.

#### Acceptance Criteria

1. WHEN an admin user deletes a freed system THEN the Asset Tracking System SHALL move the asset to the Scrapped Items page
2. WHEN an asset is scrapped THEN the Asset Tracking System SHALL record the date of deletion
3. WHEN an asset is scrapped THEN the Asset Tracking System SHALL retain the asset tag and IP address information
4. WHEN a non-admin user attempts to scrap an asset THEN the Asset Tracking System SHALL deny access and return an authorization error

### Requirement 7

**User Story:** As an admin user, I want to view scrapped items, so that I can maintain a historical record of removed equipment.

#### Acceptance Criteria

1. WHEN a user requests the Scrapped Items page THEN the Asset Tracking System SHALL display all scrapped assets with asset tag, IP address, and date of deletion
2. WHEN displaying scrapped items THEN the Asset Tracking System SHALL order items by date of deletion in descending order

### Requirement 8

**User Story:** As an admin user, I want to view free IP addresses organized by range, so that I can assign available IPs to new assets.

#### Acceptance Criteria

1. WHEN a user requests the Free IPs page THEN the Asset Tracking System SHALL display all unassigned IP addresses grouped by IP range
2. WHEN displaying free IPs THEN the Asset Tracking System SHALL organize addresses under their respective ranges (192.168.10.x, 192.168.11.x, 192.168.70.x, 192.168.50.x)
3. WHEN an IP address is assigned to an asset THEN the Asset Tracking System SHALL remove it from the Free IPs page
4. WHEN an asset is freed THEN the Asset Tracking System SHALL add its IP address to the Free IPs page under the appropriate range

### Requirement 9

**User Story:** As an admin user, I want to manage operating systems, so that I can add new OS options as needed.

#### Acceptance Criteria

1. WHEN an admin user adds a new operating system THEN the Asset Tracking System SHALL store the OS name and make it available in the OS dropdown
2. WHEN creating or editing an asset THEN the Asset Tracking System SHALL display all available operating systems in a dropdown list
3. WHEN an admin user attempts to add a duplicate OS name THEN the Asset Tracking System SHALL reject the addition and display an error message

### Requirement 10

**User Story:** As an admin user, I want to manage teams, so that I can organize assets by department or group.

#### Acceptance Criteria

1. WHEN an admin user adds a new team THEN the Asset Tracking System SHALL store the team name and make it available in the team dropdown
2. WHEN creating or editing an asset THEN the Asset Tracking System SHALL display all available teams in a dropdown list
3. WHEN an admin user attempts to add a duplicate team name THEN the Asset Tracking System SHALL reject the addition and display an error message

### Requirement 11

**User Story:** As an admin user, I want to manage IP ranges, so that I can add new network segments as the organization grows.

#### Acceptance Criteria

1. WHEN an admin user adds a new IP range THEN the Asset Tracking System SHALL store the range pattern and make it available in the IP address dropdown
2. WHEN creating or editing an asset THEN the Asset Tracking System SHALL display available IP addresses from all configured ranges
3. WHEN an admin user attempts to add a duplicate IP range THEN the Asset Tracking System SHALL reject the addition and display an error message

### Requirement 12

**User Story:** As an admin user, I want to attach files and images to asset records, so that I can maintain detailed documentation.

#### Acceptance Criteria

1. WHEN an admin user uploads an attachment to an asset THEN the Asset Tracking System SHALL store the file and associate it with the asset
2. WHEN viewing an asset THEN the Asset Tracking System SHALL display all associated attachments with download links
3. WHEN an admin user deletes an attachment THEN the Asset Tracking System SHALL remove the file from storage and the asset record
4. WHEN an asset is scrapped THEN the Asset Tracking System SHALL retain attachments for historical reference


### Requirement 13

**User Story:** As an admin user, I want to track asset warranty information and receive alerts before expiration, so that I can renew warranties on time.

#### Acceptance Criteria

1. WHEN an admin user adds or edits an asset THEN the Asset Tracking System SHALL allow entry of warranty expiration date
2. WHEN the system runs a daily check THEN the Asset Tracking System SHALL identify all assets with warranties expiring within 7 days
3. WHEN an asset warranty is expiring within 7 days THEN the Asset Tracking System SHALL send an alert email to admin users
4. WHEN a user requests the Warranty page THEN the Asset Tracking System SHALL display all assets with their warranty expiration dates
5. WHEN displaying the Warranty page THEN the Asset Tracking System SHALL highlight assets with warranties expiring within 7 days
6. WHEN displaying the Warranty page THEN the Asset Tracking System SHALL order assets by warranty expiration date in ascending order
7. WHEN an asset warranty has expired THEN the Asset Tracking System SHALL mark it as expired on the Warranty page
