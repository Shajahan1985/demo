# Requirements Document: Asset Import/Export/Filters

## Introduction

This document specifies the requirements for enhancing the Asset Tracking System with bulk import, export, and filtering capabilities. The enhancements enable administrators to efficiently manage large numbers of assets through Excel imports, allow all authenticated users to export asset data for reporting, and provide flexible filtering options on the asset list page.

## Glossary

- **Excel Import**: Bulk upload of asset data from Excel spreadsheet files (.xlsx, .xls)
- **Excel Export**: Download of asset data to Excel spreadsheet format
- **Filter**: Search criteria applied to narrow down asset list results
- **BIDC Number**: Asset tag identifier in the format "BIDC + number"
- **Active Assets**: Assets with status='active' currently in use
- **Freed Assets**: Assets with status='freed' available for reassignment
- **Scrapped Assets**: Assets with status='scrapped' permanently removed from inventory
- **Free IPs**: IP addresses not currently assigned to any asset
- **Import Validation**: Process of checking data integrity before importing
- **Import Results**: Summary showing success count, error count, and error details

## Requirements

### Requirement 1: Excel Import - File Upload

**User Story:** As an admin user, I want to upload an Excel file containing asset details, so that I can add multiple assets to the system at once.

#### Acceptance Criteria

1. WHEN an admin user accesses the import page THEN the Asset Tracking System SHALL display a file upload form accepting .xlsx and .xls files
2. WHEN an admin user selects an Excel file and submits the form THEN the Asset Tracking System SHALL validate the file format
3. WHEN an admin user uploads a non-Excel file THEN the Asset Tracking System SHALL reject the file and display error message "Invalid file format. Please upload .xlsx or .xls file"
4. WHEN an admin user uploads a file larger than 10MB THEN the Asset Tracking System SHALL reject the file and display error message "File too large. Maximum size is 10MB"
5. WHEN a non-admin user attempts to access the import page THEN the Asset Tracking System SHALL deny access and return an authorization error

### Requirement 2: Excel Import - Data Validation

**User Story:** As an admin user, I want the system to validate imported data before saving, so that I can ensure data integrity.

#### Acceptance Criteria

1. WHEN the system processes an Excel file THEN the Asset Tracking System SHALL validate that required columns exist (asset_tag, system_type, operating_system, ip_address)
2. WHEN the Excel file is missing required columns THEN the Asset Tracking System SHALL reject the import and display list of missing columns
3. WHEN the system validates a row THEN the Asset Tracking System SHALL check that asset_tag is unique
4. WHEN a row contains a duplicate asset_tag THEN the Asset Tracking System SHALL skip that row and add it to the error list with message "Asset tag already exists"
5. WHEN a row references a non-existent operating system THEN the Asset Tracking System SHALL skip that row and add it to the error list with message "Operating System not found"
6. WHEN a row references a non-existent team THEN the Asset Tracking System SHALL skip that row and add it to the error list with message "Team not found"
7. WHEN a row specifies an IP address that is already assigned THEN the Asset Tracking System SHALL skip that row and add it to the error list with message "IP address not available"
8. WHEN a row contains invalid system_type THEN the Asset Tracking System SHALL skip that row and add it to the error list with message "Invalid system type. Must be Desktop, Laptop, or All-in-One PC"
9. WHEN a row contains invalid warranty_expiration date format THEN the Asset Tracking System SHALL skip that row and add it to the error list with message "Invalid date format. Use YYYY-MM-DD"

### Requirement 3: Excel Import - Bulk Asset Creation

**User Story:** As an admin user, I want to import multiple assets at once from Excel, so that I can save time when adding many assets.

#### Acceptance Criteria

1. WHEN the system processes valid rows from Excel THEN the Asset Tracking System SHALL create asset records for each valid row
2. WHEN an asset is created from import THEN the Asset Tracking System SHALL assign a sequential serial number
3. WHEN an asset is created from import THEN the Asset Tracking System SHALL mark the specified IP address as assigned
4. WHEN an asset is created from import with optional fields (particulars, assigned_to, team, warranty_expiration) THEN the Asset Tracking System SHALL save those values
5. WHEN an asset is created from import without optional fields THEN the Asset Tracking System SHALL leave those fields empty/null
6. WHEN the import process encounters errors THEN the Asset Tracking System SHALL continue processing remaining rows
7. WHEN all rows are processed THEN the Asset Tracking System SHALL commit valid imports to the database

### Requirement 4: Excel Import - Results Display

**User Story:** As an admin user, I want to see import results showing successes and errors, so that I can identify and fix any issues.

#### Acceptance Criteria

1. WHEN the import process completes THEN the Asset Tracking System SHALL display the total number of successfully imported assets
2. WHEN the import process completes THEN the Asset Tracking System SHALL display the total number of rows with errors
3. WHEN there are import errors THEN the Asset Tracking System SHALL display a detailed error list showing row number, asset data, and specific error messages for each failed row
4. WHEN the import is successful with no errors THEN the Asset Tracking System SHALL display success message and redirect to asset list page
5. WHEN the import has partial success THEN the Asset Tracking System SHALL display both success count and error details on results page

### Requirement 5: Excel Export - Active Assets

**User Story:** As an authenticated user, I want to download active assets to Excel, so that I can analyze or report on current inventory.

#### Acceptance Criteria

1. WHEN a user clicks the "Export Active Assets" button THEN the Asset Tracking System SHALL generate an Excel file containing all active assets
2. WHEN exporting active assets THEN the Asset Tracking System SHALL include columns: Serial Number, Asset Tag, System Type, OS, IP Address, Assigned To, Team, Warranty Expiration
3. WHEN exporting active assets THEN the Asset Tracking System SHALL order rows by serial number
4. WHEN exporting active assets THEN the Asset Tracking System SHALL set the filename to "active_assets.xlsx"
5. WHEN exporting active assets THEN the Asset Tracking System SHALL trigger a file download in the user's browser
6. WHEN there are no active assets THEN the Asset Tracking System SHALL generate an Excel file with headers only

### Requirement 6: Excel Export - Freed Assets

**User Story:** As an authenticated user, I want to download freed systems to Excel, so that I can track available equipment.

#### Acceptance Criteria

1. WHEN a user clicks the "Export Freed Assets" button THEN the Asset Tracking System SHALL generate an Excel file containing all freed assets
2. WHEN exporting freed assets THEN the Asset Tracking System SHALL include columns: Serial Number, Asset Tag, System Type, OS, IP Address, Freed Date
3. WHEN exporting freed assets THEN the Asset Tracking System SHALL order rows by freed date descending
4. WHEN exporting freed assets THEN the Asset Tracking System SHALL set the filename to "freed_assets.xlsx"
5. WHEN exporting freed assets THEN the Asset Tracking System SHALL trigger a file download in the user's browser

### Requirement 7: Excel Export - Scrapped Assets

**User Story:** As an authenticated user, I want to download scrapped items to Excel, so that I can maintain historical records.

#### Acceptance Criteria

1. WHEN a user clicks the "Export Scrapped Assets" button THEN the Asset Tracking System SHALL generate an Excel file containing all scrapped assets
2. WHEN exporting scrapped assets THEN the Asset Tracking System SHALL include columns: Serial Number, Asset Tag, System Type, OS, IP Address, Scrapped Date
3. WHEN exporting scrapped assets THEN the Asset Tracking System SHALL order rows by scrapped date descending
4. WHEN exporting scrapped assets THEN the Asset Tracking System SHALL set the filename to "scrapped_assets.xlsx"
5. WHEN exporting scrapped assets THEN the Asset Tracking System SHALL trigger a file download in the user's browser

### Requirement 8: Excel Export - Free IPs

**User Story:** As an authenticated user, I want to download free IP addresses to Excel, so that I can plan network assignments.

#### Acceptance Criteria

1. WHEN a user clicks the "Export Free IPs" button THEN the Asset Tracking System SHALL generate an Excel file containing all unassigned IP addresses
2. WHEN exporting free IPs THEN the Asset Tracking System SHALL include columns: IP Address, IP Range
3. WHEN exporting free IPs THEN the Asset Tracking System SHALL group IPs by range (192.168.10.x, 192.168.11.x, 192.168.70.x, 192.168.50.x)
4. WHEN exporting free IPs THEN the Asset Tracking System SHALL order IPs within each range numerically
5. WHEN exporting free IPs THEN the Asset Tracking System SHALL set the filename to "free_ips.xlsx"
6. WHEN exporting free IPs THEN the Asset Tracking System SHALL trigger a file download in the user's browser

### Requirement 9: Filtering - Operating System Filter

**User Story:** As a user, I want to filter assets by operating system, so that I can view assets running specific OS versions.

#### Acceptance Criteria

1. WHEN a user views the asset list page THEN the Asset Tracking System SHALL display an Operating System dropdown filter
2. WHEN the OS dropdown is displayed THEN the Asset Tracking System SHALL populate it with all available operating systems
3. WHEN a user selects an OS and applies the filter THEN the Asset Tracking System SHALL display only assets with that operating system
4. WHEN a user clears the OS filter THEN the Asset Tracking System SHALL display all assets again

### Requirement 10: Filtering - Asset Tag Filter

**User Story:** As a user, I want to filter assets by BIDC number, so that I can quickly find specific assets.

#### Acceptance Criteria

1. WHEN a user views the asset list page THEN the Asset Tracking System SHALL display an Asset Tag text input filter
2. WHEN a user enters text in the Asset Tag filter and applies it THEN the Asset Tracking System SHALL display only assets whose asset_tag contains the entered text (case-insensitive)
3. WHEN a user enters "BIDC123" in the Asset Tag filter THEN the Asset Tracking System SHALL match assets with tags like "BIDC123", "BIDC1234", "bidc123"
4. WHEN a user clears the Asset Tag filter THEN the Asset Tracking System SHALL display all assets again

### Requirement 11: Filtering - Team Filter

**User Story:** As a user, I want to filter assets by team, so that I can view equipment assigned to specific departments.

#### Acceptance Criteria

1. WHEN a user views the asset list page THEN the Asset Tracking System SHALL display a Team dropdown filter
2. WHEN the Team dropdown is displayed THEN the Asset Tracking System SHALL populate it with all available teams
3. WHEN a user selects a team and applies the filter THEN the Asset Tracking System SHALL display only assets assigned to that team
4. WHEN a user clears the Team filter THEN the Asset Tracking System SHALL display all assets again

### Requirement 12: Filtering - Assigned User Filter

**User Story:** As a user, I want to filter assets by assigned user name, so that I can see what equipment is assigned to specific people.

#### Acceptance Criteria

1. WHEN a user views the asset list page THEN the Asset Tracking System SHALL display an Assigned To text input filter
2. WHEN a user enters text in the Assigned To filter and applies it THEN the Asset Tracking System SHALL display only assets whose assigned_to field contains the entered text (case-insensitive)
3. WHEN a user enters "John" in the Assigned To filter THEN the Asset Tracking System SHALL match assets assigned to "John Doe", "Johnny Smith", "john.williams"
4. WHEN a user clears the Assigned To filter THEN the Asset Tracking System SHALL display all assets again

### Requirement 13: Filtering - Multiple Filters

**User Story:** As a user, I want to apply multiple filters together, so that I can narrow down results precisely.

#### Acceptance Criteria

1. WHEN a user applies multiple filters simultaneously THEN the Asset Tracking System SHALL combine filters with AND logic
2. WHEN a user filters by OS="Windows 10" AND Team="Engineering" THEN the Asset Tracking System SHALL display only assets that match both criteria
3. WHEN a user applies all four filters together THEN the Asset Tracking System SHALL display only assets matching all criteria
4. WHEN multiple filters result in no matches THEN the Asset Tracking System SHALL display "No assets found" message
5. WHEN a user applies filters THEN the Asset Tracking System SHALL preserve filter values in the form after page reload

### Requirement 14: Filtering - Clear Filters

**User Story:** As a user, I want to clear all filters at once, so that I can quickly return to viewing all assets.

#### Acceptance Criteria

1. WHEN a user has applied one or more filters THEN the Asset Tracking System SHALL display a "Clear Filters" button
2. WHEN a user clicks the "Clear Filters" button THEN the Asset Tracking System SHALL remove all filter criteria
3. WHEN filters are cleared THEN the Asset Tracking System SHALL display all active assets
4. WHEN filters are cleared THEN the Asset Tracking System SHALL reset all filter form fields to empty/default values

### Requirement 15: Integration - Existing Functionality

**User Story:** As a user, I want import/export/filter features to work seamlessly with existing functionality, so that the system remains consistent.

#### Acceptance Criteria

1. WHEN assets are imported THEN the Asset Tracking System SHALL use the existing AssetService.create_asset() method
2. WHEN assets are imported THEN the Asset Tracking System SHALL use the existing IPManagementService for IP assignment
3. WHEN assets are exported THEN the Asset Tracking System SHALL include all fields visible in the current asset list view
4. WHEN filters are applied THEN the Asset Tracking System SHALL maintain existing sorting by serial number
5. WHEN an admin imports assets THEN the Asset Tracking System SHALL enforce all existing validation rules (unique asset_tag, valid IP, etc.)
6. WHEN a user exports data THEN the Asset Tracking System SHALL respect existing permission rules (authenticated users only)
7. WHEN filters are applied THEN the Asset Tracking System SHALL only show active assets (status='active') unless on freed/scrapped pages
