# Requirements Document

## Introduction

This document specifies requirements for enhancing the scrapped items functionality in the Asset Tracker application. The enhancement includes capturing additional information about scrapped assets (manufacturer, scrapping reason), automatically releasing IP addresses when assets are scrapped, and providing visibility into IP address lifecycle across scrapped items and free IP pages.

## Glossary

- **Asset**: A hardware system tracked in the Asset Tracker application
- **Scrapped_Items_Page**: The web page displaying all assets that have been scrapped
- **Free_IPs_Page**: The web page displaying IP addresses that are available for assignment
- **IP_Address**: The network IP address assigned to an asset
- **BIDC_Number**: The asset tag identifier (asset_tag field in the Asset model)
- **System_Type**: The category or type of the asset hardware
- **System_Make**: The manufacturer or brand of the asset hardware
- **Scrapping_Date**: The date when an asset was marked as scrapped
- **Scrapping_Reason**: The explanation for why an asset was scrapped
- **Asset_Tracker**: The Django-based application for managing hardware assets

## Requirements

### Requirement 1: Capture Asset Manufacturer Information

**User Story:** As an IT administrator, I want to record the manufacturer of each asset, so that I can track which vendors' equipment is being scrapped.

#### Acceptance Criteria

1. THE Asset_Tracker SHALL store a System_Make field for each Asset
2. WHEN an Asset is created or updated, THE Asset_Tracker SHALL accept a System_Make value
3. THE Asset_Tracker SHALL display the System_Make on the Scrapped_Items_Page

### Requirement 2: Capture Scrapping Reason

**User Story:** As an IT administrator, I want to record why an asset was scrapped, so that I can analyze failure patterns and make informed purchasing decisions.

#### Acceptance Criteria

1. THE Asset_Tracker SHALL store a Scrapping_Reason field for each Asset
2. WHEN an Asset is marked as scrapped, THE Asset_Tracker SHALL require a Scrapping_Reason value
3. THE Asset_Tracker SHALL display the Scrapping_Reason on the Scrapped_Items_Page

### Requirement 3: Display Complete Scrapped Asset Information

**User Story:** As an IT administrator, I want to see comprehensive information about scrapped assets, so that I can maintain complete records and audit trails.

#### Acceptance Criteria

1. THE Scrapped_Items_Page SHALL display the IP_Address for each scrapped Asset
2. THE Scrapped_Items_Page SHALL display the BIDC_Number for each scrapped Asset
3. THE Scrapped_Items_Page SHALL display the System_Type for each scrapped Asset
4. THE Scrapped_Items_Page SHALL display the System_Make for each scrapped Asset
5. THE Scrapped_Items_Page SHALL display the Scrapping_Date for each scrapped Asset
6. THE Scrapped_Items_Page SHALL display the Scrapping_Reason for each scrapped Asset

### Requirement 4: Automatic IP Address Release on Scrapping

**User Story:** As an IT administrator, I want IP addresses to be automatically released when assets are scrapped, so that I can reuse IP addresses without manual intervention.

#### Acceptance Criteria

1. WHEN an Asset is marked as scrapped, THE Asset_Tracker SHALL release the Asset's IP_Address
2. WHEN an IP_Address is released from a scrapped Asset, THE Asset_Tracker SHALL make the IP_Address available on the Free_IPs_Page
3. THE Asset_Tracker SHALL preserve the original IP_Address value in the scrapped Asset record for historical reference

### Requirement 5: Display Freed IP Addresses

**User Story:** As an IT administrator, I want to see which IP addresses came from scrapped assets, so that I know which IPs are available for reassignment.

#### Acceptance Criteria

1. THE Free_IPs_Page SHALL display IP_Address values that were released from scrapped Assets
2. THE Free_IPs_Page SHALL indicate which IP_Address values are available for assignment
3. THE Free_IPs_Page SHALL display the date when each IP_Address was freed

### Requirement 6: Track IP Address Reassignment

**User Story:** As an IT administrator, I want to see when a freed IP address has been reassigned, so that I don't accidentally assign the same IP to multiple assets.

#### Acceptance Criteria

1. WHEN a freed IP_Address is assigned to a new Asset, THE Free_IPs_Page SHALL display the IP_Address in red color
2. WHEN a freed IP_Address is assigned to a new Asset, THE Free_IPs_Page SHALL indicate the IP_Address is no longer available
3. WHEN an IP_Address is reassigned, THE Asset_Tracker SHALL update the Free_IPs_Page within 1 second

### Requirement 7: Remove Reassigned IPs from Scrapped Items Display

**User Story:** As an IT administrator, I want scrapped items to show current IP status, so that I understand which IPs are still available from scrapped equipment.

#### Acceptance Criteria

1. WHEN a scrapped Asset's IP_Address has been reassigned to another Asset, THE Scrapped_Items_Page SHALL indicate the IP_Address is no longer available
2. WHEN a scrapped Asset's IP_Address has been reassigned, THE Scrapped_Items_Page SHALL display the IP_Address field differently to show it is occupied
3. THE Scrapped_Items_Page SHALL preserve the historical IP_Address value for audit purposes
