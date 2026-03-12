# Asset Management User Guide

## Table of Contents

1. [Overview](#overview)
2. [Excel Import](#excel-import)
3. [Excel Export](#excel-export)
4. [Asset Filtering](#asset-filtering)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

## Overview

The Asset Tracker system provides comprehensive tools for managing IT assets including:
- **Bulk Import**: Upload multiple assets at once from Excel files
- **Export**: Download asset data for reporting and analysis
- **Filtering**: Quickly find specific assets using multiple search criteria

### User Permissions

- **Import**: Admin users only
- **Export**: All authenticated users
- **Filtering**: All authenticated users

## Excel Import

### Getting Started

1. **Access the Import Page**
   - Log in as an admin user
   - Click "Import Assets" in the navigation menu
   - Or navigate to `/assets/import/`

2. **Download the Template**
   - Click "Download Sample Template" on the import page
   - This provides a properly formatted Excel file with example data
   - Use this template to ensure your data is formatted correctly

### Preparing Your Excel File

#### Required Columns

Your Excel file must include these columns:

| Column | Description | Example | Validation |
|--------|-------------|---------|------------|
| `asset_tag` | Unique identifier for the asset | BIDC001 | Must be unique, non-empty |
| `system_type` | Type of computer system | Desktop | Must be: Desktop, Laptop, or All-in-One PC |
| `operating_system` | Operating system name | Windows 10 Pro | Must exist in the system |
| `ip_address` | IPv4 address | 192.168.10.5 | Must be valid IPv4 and available |

#### Optional Columns

| Column | Description | Example | Format |
|--------|-------------|---------|--------|
| `particulars` | Additional specifications | Dell OptiPlex 7090 | Any text |
| `assigned_to` | Person using the asset | John Doe | Any text |
| `team` | Department or team | Engineering | Must exist in the system |
| `warranty_expiration` | Warranty end date | 2025-12-31 | YYYY-MM-DD |

### Import Process

1. **Select Your File**
   - Click "Choose File" and select your Excel file
   - Supported formats: .xlsx, .xls
   - Maximum file size: 10MB

2. **Upload**
   - Click "Import Assets"
   - The system validates and processes your file
   - This may take a few seconds for large files

3. **Review Results**
   - **Success Count**: Number of assets successfully imported
   - **Error Count**: Number of rows that failed validation
   - **Error Details**: Table showing specific errors for each failed row

### Understanding Import Errors

#### Common Errors and Solutions

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Asset tag already exists" | Duplicate asset tag in database | Use a unique asset tag |
| "Operating System not found" | OS doesn't exist in system | Create the OS first or check spelling |
| "Team not found" | Team doesn't exist in system | Create the team first or check spelling |
| "IP address not available" | IP already assigned or invalid | Use a different IP or check format |
| "Invalid system type" | Wrong system type value | Use: Desktop, Laptop, or All-in-One PC |
| "Invalid date format" | Wrong date format | Use YYYY-MM-DD format (e.g., 2025-12-31) |
| "Invalid file format" | Wrong file type | Use .xlsx or .xls files only |
| "File too large" | File exceeds 10MB | Split into smaller files |

### Import Best Practices

1. **Start Small**: Test with 5-10 assets first to verify your format
2. **Use the Template**: Always start with the provided template
3. **Check Prerequisites**: Ensure Operating Systems and Teams exist before importing
4. **Verify IPs**: Check that IP addresses are available in the IP management system
5. **Unique Tags**: Use a consistent naming scheme (e.g., BIDC001, BIDC002, etc.)
6. **Date Format**: Always use YYYY-MM-DD for dates
7. **Review Errors**: Fix errors and re-import failed rows

## Excel Export

### Available Exports

#### 1. Active Assets

**Purpose**: Export all currently active assets in the system

**Access**: Asset List page → "Export to Excel" button

**Columns Included**:
- Serial Number
- Asset Tag
- System Type
- Operating System
- IP Address
- Assigned To
- Team
- Warranty Expiration

**Use Cases**:
- Monthly inventory reports
- Asset assignment tracking
- Warranty management
- Budget planning

#### 2. Freed Assets

**Purpose**: Export assets that have been freed and are available for reassignment

**Access**: Freed Systems page → "Export to Excel" button

**Columns Included**:
- Serial Number
- Asset Tag
- System Type
- Operating System
- IP Address
- Freed Date

**Use Cases**:
- Available equipment tracking
- Redeployment planning
- Asset lifecycle reporting

#### 3. Scrapped Assets

**Purpose**: Export assets that have been permanently removed from inventory

**Access**: Scrapped Items page → "Export to Excel" button

**Columns Included**:
- Serial Number
- Asset Tag
- System Type
- Operating System
- IP Address
- Scrapped Date

**Use Cases**:
- Historical records
- Disposal documentation
- Audit trails
- Asset lifecycle analysis

#### 4. Free IP Addresses

**Purpose**: Export all unassigned IP addresses

**Access**: Free IPs page → "Export to Excel" button

**Columns Included**:
- IP Address
- IP Range

**Use Cases**:
- Network planning
- IP allocation
- New asset deployment
- Network documentation

### Export Instructions

1. Navigate to the relevant page (assets, freed systems, scrapped items, or free IPs)
2. Click the "Export to Excel" button
3. The file downloads automatically to your browser's download folder
4. Open with Excel, LibreOffice Calc, or Google Sheets

### Export Tips

- **Filtered Exports**: Apply filters before exporting to get specific subsets
- **Regular Backups**: Export active assets regularly for backup purposes
- **Reporting**: Use exports for creating custom reports and dashboards
- **Data Analysis**: Import into BI tools for advanced analytics

## Asset Filtering

### Overview

Filters help you quickly find specific assets without scrolling through the entire list. You can combine multiple filters to narrow down results precisely.

### Available Filters

#### 1. Operating System Filter

**Type**: Dropdown selection

**How it works**: Shows only assets running the selected operating system

**Example**: Select "Windows 10 Pro" to see all Windows 10 Pro assets

#### 2. Asset Tag Filter

**Type**: Text input (partial match)

**How it works**: Searches for assets whose tag contains the entered text (case-insensitive)

**Examples**:
- Enter "BIDC" → Matches BIDC001, BIDC002, bidc123
- Enter "123" → Matches BIDC123, BIDC1234, TEST123

#### 3. Team Filter

**Type**: Dropdown selection

**How it works**: Shows only assets assigned to the selected team

**Example**: Select "Engineering" to see all Engineering team assets

#### 4. Assigned To Filter

**Type**: Text input (partial match)

**How it works**: Searches for assets assigned to users whose name contains the entered text (case-insensitive)

**Examples**:
- Enter "John" → Matches John Doe, Johnny Smith, john.williams
- Enter "Smith" → Matches John Smith, Jane Smith

### Using Filters

#### Single Filter

1. Select or enter your filter criteria in one field
2. Click "Apply Filters"
3. Results update to show only matching assets

#### Multiple Filters (AND Logic)

1. Set criteria in multiple filter fields
2. Click "Apply Filters"
3. Results show assets matching ALL criteria

**Example**: 
- OS = "Windows 10 Pro"
- Team = "Engineering"
- Result: Only Windows 10 Pro assets assigned to Engineering team

#### Clearing Filters

1. Click "Clear Filters" button
2. All filter fields reset to empty
3. Full asset list is displayed

### Filter Examples

#### Example 1: Find All Laptops Running Ubuntu
```
System Type: (not filterable directly, use export and filter in Excel)
Operating System: Ubuntu 22.04
Asset Tag: (leave empty)
Team: (leave empty)
Assigned To: (leave empty)
```

#### Example 2: Find John's Assets
```
Operating System: (leave empty)
Asset Tag: (leave empty)
Team: (leave empty)
Assigned To: John
```

#### Example 3: Find Engineering Team's Windows Machines
```
Operating System: Windows 10 Pro
Asset Tag: (leave empty)
Team: Engineering
Assigned To: (leave empty)
```

#### Example 4: Find Specific Asset by Tag
```
Operating System: (leave empty)
Asset Tag: BIDC123
Team: (leave empty)
Assigned To: (leave empty)
```

### Filter Tips

1. **Start Broad**: Begin with one filter and add more to narrow results
2. **Partial Matches**: Text filters match partial strings, so "John" finds "Johnny"
3. **Case Insensitive**: Text searches ignore case (BIDC = bidc)
4. **Bookmark Filters**: Filter URLs can be bookmarked for quick access
5. **Export Filtered**: Apply filters then export to get specific data subsets
6. **No Results**: If no assets match, you'll see "No assets found" message

## Best Practices

### Import Best Practices

1. **Validate Data First**: Check your Excel file for errors before importing
2. **Small Batches**: Import in batches of 50-100 assets for easier error handling
3. **Consistent Naming**: Use consistent asset tag naming conventions
4. **Pre-create References**: Create Operating Systems and Teams before importing
5. **Test Import**: Always test with a few rows first
6. **Keep Backups**: Save your Excel files as backups

### Export Best Practices

1. **Regular Exports**: Export active assets weekly for backup
2. **Filtered Exports**: Use filters to export specific subsets
3. **Date Stamping**: Rename exported files with dates (e.g., active_assets_2024-01-15.xlsx)
4. **Version Control**: Keep historical exports for trend analysis
5. **Secure Storage**: Store exports securely as they contain sensitive data

### Filter Best Practices

1. **Combine Filters**: Use multiple filters for precise results
2. **Clear Between Searches**: Clear filters before starting a new search
3. **Bookmark Common Filters**: Save frequently used filter combinations
4. **Export After Filtering**: Export filtered results for reporting
5. **Check Filter Count**: Note the number of results to verify filter accuracy

## Troubleshooting

### Import Issues

#### Problem: "Invalid file format" error
**Solution**: Ensure file is .xlsx or .xls format, not .csv or .txt

#### Problem: "File too large" error
**Solution**: Split your file into multiple smaller files (under 10MB each)

#### Problem: All rows showing errors
**Solution**: Check that your Excel file has the correct column headers (case-sensitive)

#### Problem: "Operating System not found" for all rows
**Solution**: Verify OS names exactly match those in the system (check spelling and case)

#### Problem: Import button not visible
**Solution**: Ensure you're logged in as an admin user

### Export Issues

#### Problem: Export button not visible
**Solution**: Ensure you're logged in (all authenticated users can export)

#### Problem: Export file is empty
**Solution**: This is normal if no data matches the criteria (e.g., no freed assets)

#### Problem: Export file won't open
**Solution**: Ensure you have Excel, LibreOffice, or Google Sheets installed

### Filter Issues

#### Problem: No results after applying filter
**Solution**: Try clearing filters and applying one at a time to identify the issue

#### Problem: Filter not working
**Solution**: Ensure you clicked "Apply Filters" button after entering criteria

#### Problem: Filters reset after page reload
**Solution**: This is expected behavior; filters are preserved in URL but not in session

#### Problem: Can't find specific asset
**Solution**: Try partial matches (e.g., "123" instead of "BIDC123")

### Getting Help

If you encounter issues not covered in this guide:

1. Check the main README.md for system requirements
2. Review the DEPLOYMENT.md for configuration issues
3. Check application logs in `authentication.log`
4. Contact your system administrator
5. Review the Django admin panel for data verification

## Appendix: Excel Template Format

### Sample Import Template

```
| asset_tag | system_type | operating_system | ip_address    | particulars        | assigned_to | team        | warranty_expiration |
|-----------|-------------|------------------|---------------|--------------------|-------------|-------------|---------------------|
| BIDC001   | Desktop     | Windows 10 Pro   | 192.168.10.5  | Dell OptiPlex 7090 | John Doe    | Engineering | 2025-12-31          |
| BIDC002   | Laptop      | Ubuntu 22.04     | 192.168.10.6  | Dell Latitude 5420 | Jane Smith  | IT          | 2026-06-30          |
| BIDC003   | All-in-One PC | Windows 11 Pro | 192.168.10.7  | HP EliteOne 800    | Bob Johnson | Marketing   | 2025-09-15          |
```

### Column Specifications

- **asset_tag**: Text, max 50 characters, unique
- **system_type**: Text, must be exactly: "Desktop", "Laptop", or "All-in-One PC"
- **operating_system**: Text, must match existing OS name
- **ip_address**: Text, IPv4 format (xxx.xxx.xxx.xxx)
- **particulars**: Text, max 500 characters, optional
- **assigned_to**: Text, max 100 characters, optional
- **team**: Text, must match existing team name, optional
- **warranty_expiration**: Date, YYYY-MM-DD format, optional

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**For**: Asset Tracker System
