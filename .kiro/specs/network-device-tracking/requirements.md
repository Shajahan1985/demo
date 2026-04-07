# Requirements Document

## Introduction

This feature enables tracking of non-system network devices (cameras, printers, punching machines, mobiles) that consume IP addresses but are not part of the asset tracking system. These devices need IP address management to prevent conflicts and provide visibility into network resource usage. The feature integrates with the existing IP address management system to mark IPs as occupied when assigned to network devices.

## Glossary

- **Network_Device**: A non-system device (camera, printer, punching machine, mobile) that uses an IP address but is not tracked as an IT asset
- **IP_Management_System**: The existing system that tracks IP addresses and their assignment status
- **Free_IP_Page**: The web page that displays all IP addresses grouped by range with their occupied/free status
- **Admin_User**: A user with administrative privileges who can manage network devices
- **Device_Type**: The category of network device (Camera, Printer, Punching Machine, Mobile, Other)
- **Asset_Tracking_System**: The existing system for tracking IT assets (computers, laptops, etc.)

## Requirements

### Requirement 1: Store Network Device Information

**User Story:** As an admin, I want to store network device information, so that I can track which non-system devices are using network resources.

#### Acceptance Criteria

1. THE Network_Device SHALL store a device type from the predefined list (Camera, Printer, Punching Machine, Mobile, Other)
2. THE Network_Device SHALL store a device name or description
3. THE Network_Device SHALL store an assigned IP address
4. THE Network_Device SHALL store creation and modification timestamps
5. THE Network_Device SHALL enforce uniqueness of IP addresses across all network devices

### Requirement 2: Create Network Devices

**User Story:** As an admin, I want to create new network device records, so that I can register devices that are using IP addresses.

#### Acceptance Criteria

1. WHEN an Admin_User submits a valid network device form, THE System SHALL create a new Network_Device record
2. WHEN a Network_Device is created with an IP address, THE IP_Management_System SHALL mark that IP address as occupied
3. IF an Admin_User attempts to create a Network_Device with an IP address already assigned to another device or asset, THEN THE System SHALL reject the creation and display an error message
4. THE System SHALL require device type, device name, and IP address fields for Network_Device creation
5. WHEN a Network_Device is successfully created, THE System SHALL redirect the Admin_User to the network device list page

### Requirement 3: Edit Network Devices

**User Story:** As an admin, I want to edit existing network device records, so that I can update device information when changes occur.

#### Acceptance Criteria

1. WHEN an Admin_User submits an updated network device form, THE System SHALL update the Network_Device record
2. WHEN a Network_Device IP address is changed, THE IP_Management_System SHALL mark the old IP address as free
3. WHEN a Network_Device IP address is changed, THE IP_Management_System SHALL mark the new IP address as occupied
4. IF an Admin_User attempts to change an IP address to one already assigned to another device or asset, THEN THE System SHALL reject the update and display an error message
5. THE System SHALL allow updating device type, device name, and IP address fields

### Requirement 4: Delete Network Devices

**User Story:** As an admin, I want to delete network device records, so that I can remove devices that are no longer in use.

#### Acceptance Criteria

1. WHEN an Admin_User confirms deletion of a Network_Device, THE System SHALL delete the Network_Device record
2. WHEN a Network_Device is deleted, THE IP_Management_System SHALL mark the associated IP address as free
3. THE System SHALL require confirmation before deleting a Network_Device
4. WHEN a Network_Device is successfully deleted, THE System SHALL redirect the Admin_User to the network device list page

### Requirement 5: Display Network Devices in Free IP Page

**User Story:** As an admin, I want to see network devices on the Free IP page, so that I can understand which IPs are occupied by non-system devices.

#### Acceptance Criteria

1. WHEN a Network_Device occupies an IP address, THE Free_IP_Page SHALL display that IP address as occupied
2. WHEN an Admin_User hovers over an IP address occupied by a Network_Device, THE Free_IP_Page SHALL display the device name in the tooltip
3. THE Free_IP_Page SHALL visually distinguish IP addresses occupied by network devices from those occupied by assets
4. THE Free_IP_Page SHALL display network device information in the same format as asset information for consistency

### Requirement 6: Search Network Devices on Free IP Page

**User Story:** As an admin, I want to search for network devices by name or IP address on the Free IP page, so that I can quickly locate specific devices.

#### Acceptance Criteria

1. WHEN an Admin_User enters a search term in the Free_IP_Page search box, THE System SHALL filter displayed IP addresses to show only those matching the search term
2. THE System SHALL match search terms against both IP addresses and network device names
3. THE System SHALL match search terms against both IP addresses and asset assigned person names for consistency
4. WHEN a search term matches a Network_Device name, THE Free_IP_Page SHALL display the corresponding IP address
5. THE System SHALL perform case-insensitive partial matching for search terms

### Requirement 7: List Network Devices

**User Story:** As an admin, I want to view a list of all network devices, so that I can see what devices are registered in the system.

#### Acceptance Criteria

1. THE System SHALL provide a dedicated page listing all Network_Device records
2. THE Network_Device list SHALL display device type, device name, and IP address for each device
3. THE Network_Device list SHALL provide links to edit and delete each device
4. THE Network_Device list SHALL display devices in a sortable table format
5. THE System SHALL provide a link to create new network devices from the list page

### Requirement 8: Restrict Access to Admin Users

**User Story:** As a system administrator, I want to restrict network device management to admin users only, so that unauthorized users cannot modify network device records.

#### Acceptance Criteria

1. THE System SHALL require Admin_User authentication for all network device management pages
2. IF a non-admin user attempts to access network device management pages, THEN THE System SHALL redirect them to the login page
3. THE System SHALL display network device management navigation links only to Admin_User accounts
4. THE Free_IP_Page SHALL display network device information to all authenticated users for visibility

### Requirement 9: Separate from Asset Tracking

**User Story:** As an admin, I want network devices to be separate from the asset tracking system, so that non-system devices do not clutter the asset inventory.

#### Acceptance Criteria

1. THE Network_Device SHALL be stored in a separate database table from Asset records
2. THE System SHALL not include Network_Device records in asset reports or exports
3. THE System SHALL not include Network_Device records in asset search results
4. THE IP_Management_System SHALL treat IP addresses occupied by Network_Device records the same as IP addresses occupied by Asset records for conflict prevention

### Requirement 10: Validate IP Address Format

**User Story:** As an admin, I want the system to validate IP addresses, so that only valid IPv4 addresses can be assigned to network devices.

#### Acceptance Criteria

1. WHEN an Admin_User enters an IP address for a Network_Device, THE System SHALL validate that it is a valid IPv4 address
2. IF an Admin_User enters an invalid IP address format, THEN THE System SHALL reject the submission and display a validation error message
3. THE System SHALL use the same IP address validation rules for Network_Device records as for Asset records
