# Requirements Document: Lenient Asset Import

## Introduction

This document specifies the requirements for making the Asset Tracking System's Excel import process lenient. Currently, the import rejects rows that are missing fields such as ip_address, team, or assigned_to. The new behavior treats asset_tag, system_type, and operating_system as mandatory fields while making all other fields optional. It imports assets with whatever data is available, supports upsert logic (update existing assets by asset_tag), and visually flags incomplete records on the asset list page so administrators can identify and fill in missing data.

## Glossary

- **Asset Tracking System**: The Django application responsible for managing IT assets and their lifecycle
- **Import Service**: The backend service (ImportService) that parses Excel files, validates data, and creates or updates asset records
- **Asset Tag**: A unique identifier for each asset (format: BIDC + number), a required field for import
- **Lenient Import**: An import mode where asset_tag, system_type, and operating_system are required; all other fields are optional and missing data is accepted without error
- **Upsert**: A combined create-or-update operation — if an asset_tag already exists, the record is updated; otherwise a new record is created
- **Missing Field**: An asset field that is empty, null, or not provided in the import file
- **Missing Field Warning**: A visual indicator (red text with tooltip) displayed on the asset list page for fields that are empty or null
- **Completeness Indicator**: A per-asset visual cue showing whether the asset record has all fields populated

## Requirements

### Requirement 1: Lenient Validation — asset_tag, system_type, and operating_system Required

**User Story:** As an admin user, I want to import assets with partial data, so that I can onboard assets even when full details like IP address, team, or assigned user are not yet available.

#### Acceptance Criteria

1. WHEN the Import Service validates a row from the Excel file, THE Import Service SHALL treat asset_tag, system_type, and operating_system as required fields
2. WHEN a row is missing the asset_tag value or the asset_tag is empty, THE Import Service SHALL reject that row and add it to the error list with message "Asset tag is required"
3. WHEN a row is missing the system_type value or the system_type is empty, THE Import Service SHALL reject that row and add it to the error list with message "System type is required"
4. WHEN a row is missing the operating_system value or the operating_system is empty, THE Import Service SHALL reject that row and add it to the error list with message "Operating system is required"
5. WHEN a row has valid required fields but is missing ip_address, THE Import Service SHALL accept the row and leave ip_address as null
6. WHEN a row has valid required fields but is missing assigned_to, THE Import Service SHALL accept the row and leave assigned_to as null
7. WHEN a row has valid required fields but is missing team, THE Import Service SHALL accept the row and leave team as null
8. WHEN a row provides a system_type value that is not Desktop, Laptop, or All-in-One PC, THE Import Service SHALL reject that row and add it to the error list with message "Invalid system type. Must be Desktop, Laptop, or All-in-One PC"
9. WHEN a row provides an operating_system value that does not exist in the database, THE Import Service SHALL reject that row and add it to the error list with message "Operating System not found"
10. WHEN a row provides a team value that does not exist in the database, THE Import Service SHALL reject that row and add it to the error list with message "Team not found"
11. WHEN a row provides an ip_address that is already assigned to another asset, THE Import Service SHALL reject that row and add it to the error list with message "IP address not available"

### Requirement 2: Header Validation — Required Columns

**User Story:** As an admin user, I want the import to succeed as long as the Excel file has the required columns, so that I can use simplified spreadsheets.

#### Acceptance Criteria

1. WHEN the Import Service validates Excel headers, THE Import Service SHALL require the asset_tag, system_type, and operating_system columns to be present
2. WHEN the Excel file is missing the asset_tag column, THE Import Service SHALL reject the import and display error message "Missing required column: asset_tag"
3. WHEN the Excel file is missing the system_type column, THE Import Service SHALL reject the import and display error message "Missing required column: system_type"
4. WHEN the Excel file is missing the operating_system column, THE Import Service SHALL reject the import and display error message "Missing required column: operating_system"
5. WHEN the Excel file contains the required columns but is missing optional columns (ip_address, team, assigned_to), THE Import Service SHALL proceed with the import and treat missing columns as null values for all rows

### Requirement 3: Upsert Logic — Update Existing Assets by asset_tag

**User Story:** As an admin user, I want the import to update existing assets when the asset_tag already exists, so that I can bulk-update asset records from a spreadsheet without duplicates being rejected.

#### Acceptance Criteria

1. WHEN a row contains an asset_tag that already exists in the database, THE Import Service SHALL update the existing asset record with the non-empty fields from the Excel row
2. WHEN updating an existing asset, THE Import Service SHALL preserve existing field values for any fields that are empty or missing in the Excel row
3. WHEN updating an existing asset's ip_address, THE Import Service SHALL release the old IP address and assign the new IP address
4. WHEN updating an existing asset, THE Import Service SHALL not overwrite a populated field with a null or empty value from the Excel row
5. WHEN a row contains an asset_tag that does not exist in the database, THE Import Service SHALL create a new asset record with whatever data is provided
6. WHEN the import completes, THE Import Service SHALL report the count of newly created assets and the count of updated assets separately in the results

### Requirement 4: Import Results — Distinguish Creates and Updates

**User Story:** As an admin user, I want to see how many assets were created versus updated after an import, so that I can understand the impact of the import operation.

#### Acceptance Criteria

1. WHEN the import process completes, THE Asset Tracking System SHALL display the number of newly created assets
2. WHEN the import process completes, THE Asset Tracking System SHALL display the number of updated assets
3. WHEN the import process completes, THE Asset Tracking System SHALL display the number of rows with errors
4. WHEN there are import errors, THE Asset Tracking System SHALL display a detailed error list showing row number and specific error messages for each failed row
5. WHEN the import has both creates and updates with no errors, THE Asset Tracking System SHALL display a success message summarizing both counts

### Requirement 5: Visual Warnings for Missing Fields on Asset List

**User Story:** As a user, I want to see which assets have missing or incomplete data on the asset list page, so that I can identify records that need attention.

#### Acceptance Criteria

1. WHEN an active asset has no ip_address, THE Asset Tracking System SHALL display the IP cell with red text and a warning message "IP is missing"
2. WHEN an active asset has a null or empty assigned_to field, THE Asset Tracking System SHALL display the Assigned To cell with red text and a warning message "User is missing"
3. WHEN an active asset has a null team, THE Asset Tracking System SHALL display the Team cell with red text and a warning message "Team is missing"
4. WHEN an active asset has all fields populated, THE Asset Tracking System SHALL display all cells in the default style without any warning indicators
5. WHEN displaying a missing field warning, THE Asset Tracking System SHALL use a CSS class "missing-field" that applies red color (#dc3545) to the cell text

### Requirement 6: No Model Changes — system_type and operating_system Remain Required

**User Story:** As a developer, I want the Asset model to keep system_type and operating_system as required fields, so that data integrity is maintained.

#### Acceptance Criteria

1. THE Asset model SHALL continue to enforce system_type as a required non-null field
2. THE Asset model SHALL continue to enforce operating_system as a required non-null field
3. THE Asset model SHALL continue to enforce asset_tag as unique and non-null
4. THE Asset model SHALL continue to allow ip_address, assigned_to, and team as nullable fields
