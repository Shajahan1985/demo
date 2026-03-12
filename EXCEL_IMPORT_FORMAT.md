# Excel Import Format and Requirements

## Overview

This document specifies the exact format and requirements for importing assets via Excel files into the Asset Tracker system.

## File Requirements

### Supported Formats
- `.xlsx` (Excel 2007 and later)
- `.xls` (Excel 97-2003)

### File Size Limit
- Maximum: 10MB
- Recommended: Under 5MB for optimal performance
- For larger datasets, split into multiple files

### File Structure
- First row must contain column headers (case-sensitive)
- Data starts from row 2
- Empty rows are ignored
- Maximum recommended rows: 1000 per file

## Column Specifications

### Required Columns

These columns MUST be present in your Excel file:

#### 1. asset_tag
- **Type**: Text
- **Required**: Yes
- **Max Length**: 50 characters
- **Validation**: Must be unique across all assets in the system
- **Format**: Alphanumeric, typically "BIDC" + number
- **Examples**: 
  - ✅ BIDC001
  - ✅ BIDC-2024-001
  - ✅ LAPTOP-123
  - ❌ (empty)
  - ❌ BIDC001 (if already exists)

#### 2. system_type
- **Type**: Text
- **Required**: Yes
- **Allowed Values**: 
  - `Desktop`
  - `Laptop`
  - `All-in-One PC`
- **Case Sensitive**: Yes (must match exactly)
- **Examples**:
  - ✅ Desktop
  - ✅ Laptop
  - ✅ All-in-One PC
  - ❌ desktop (wrong case)
  - ❌ LAPTOP (wrong case)
  - ❌ Server (not allowed)

#### 3. operating_system
- **Type**: Text
- **Required**: Yes
- **Validation**: Must match an existing Operating System name in the database
- **Case Sensitive**: Yes
- **Examples**:
  - ✅ Windows 10 Pro (if exists in system)
  - ✅ Ubuntu 22.04 (if exists in system)
  - ✅ macOS Ventura (if exists in system)
  - ❌ Windows 10 (if not in system)
  - ❌ windows 10 pro (wrong case)
- **Note**: Create Operating Systems in the admin panel before importing

#### 4. ip_address
- **Type**: Text
- **Required**: Yes
- **Format**: IPv4 address (xxx.xxx.xxx.xxx)
- **Validation**: 
  - Must be valid IPv4 format
  - Must not be already assigned to another asset
  - Must exist in the IP management system
- **Examples**:
  - ✅ 192.168.10.5
  - ✅ 10.0.0.100
  - ✅ 172.16.0.50
  - ❌ 192.168.1 (incomplete)
  - ❌ 192.168.1.256 (invalid range)
  - ❌ 192.168.10.5 (if already assigned)

### Optional Columns

These columns are optional but recommended:

#### 5. particulars
- **Type**: Text
- **Required**: No
- **Max Length**: 500 characters
- **Description**: Additional specifications, model information, or notes
- **Examples**:
  - Dell OptiPlex 7090, Intel i7, 16GB RAM, 512GB SSD
  - HP Laptop, Model 15-dy2xxx
  - Custom built workstation
- **Default**: Empty if not provided

#### 6. assigned_to
- **Type**: Text
- **Required**: No
- **Max Length**: 100 characters
- **Description**: Name of the person assigned to this asset
- **Format**: Free text (no validation against user database)
- **Examples**:
  - John Doe
  - Jane Smith
  - john.doe@company.com
- **Default**: Empty if not provided

#### 7. team
- **Type**: Text
- **Required**: No
- **Validation**: Must match an existing Team name in the database if provided
- **Case Sensitive**: Yes
- **Examples**:
  - ✅ Engineering (if exists in system)
  - ✅ IT (if exists in system)
  - ✅ Marketing (if exists in system)
  - ❌ engineering (wrong case)
  - ❌ Sales (if not in system)
- **Note**: Create Teams in the admin panel before importing
- **Default**: Empty if not provided

#### 8. warranty_expiration
- **Type**: Date
- **Required**: No
- **Format**: YYYY-MM-DD (ISO 8601 date format)
- **Validation**: Must be a valid date
- **Examples**:
  - ✅ 2025-12-31
  - ✅ 2024-06-15
  - ✅ 2026-01-01
  - ❌ 12/31/2025 (wrong format)
  - ❌ 31-12-2025 (wrong format)
  - ❌ 2025-13-01 (invalid month)
- **Default**: Empty if not provided

## Excel Template

### Column Order

The columns can be in any order, but must have the exact header names:

```
asset_tag | system_type | operating_system | ip_address | particulars | assigned_to | team | warranty_expiration
```

### Sample Template

Download the sample template from the import page, or create your own with this structure:

| asset_tag | system_type | operating_system | ip_address    | particulars        | assigned_to | team        | warranty_expiration |
|-----------|-------------|------------------|---------------|--------------------|-------------|-------------|---------------------|
| BIDC001   | Desktop     | Windows 10 Pro   | 192.168.10.5  | Dell OptiPlex 7090 | John Doe    | Engineering | 2025-12-31          |
| BIDC002   | Laptop      | Ubuntu 22.04     | 192.168.10.6  | Dell Latitude 5420 | Jane Smith  | IT          | 2026-06-30          |
| BIDC003   | All-in-One PC | Windows 11 Pro | 192.168.10.7  | HP EliteOne 800    |             | Marketing   | 2025-09-15          |

## Validation Rules

### Pre-Import Validation

Before uploading, ensure:

1. ✅ File is .xlsx or .xls format
2. ✅ File size is under 10MB
3. ✅ First row contains all required column headers
4. ✅ Column headers match exactly (case-sensitive)
5. ✅ No completely empty rows in data section

### Row-Level Validation

Each row is validated for:

1. **Uniqueness**: asset_tag must be unique
2. **Foreign Keys**: operating_system and team must exist in database
3. **IP Availability**: ip_address must be valid and unassigned
4. **Data Types**: system_type must be one of allowed values
5. **Date Format**: warranty_expiration must be YYYY-MM-DD if provided

### Validation Behavior

- **Valid Rows**: Imported successfully
- **Invalid Rows**: Skipped and reported in error list
- **Partial Import**: Valid rows are imported even if some rows fail
- **Transaction Safety**: All imports are atomic (all or nothing per row)

## Error Messages

### Common Validation Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Missing required columns: [column_name]" | Required column header not found | Add the missing column to your Excel file |
| "Asset tag already exists" | Duplicate asset_tag in database | Use a unique asset tag |
| "Operating System not found: [os_name]" | OS doesn't exist in system | Create the OS in admin panel or fix spelling |
| "Team not found: [team_name]" | Team doesn't exist in system | Create the team in admin panel or fix spelling |
| "IP address not available: [ip]" | IP already assigned or invalid | Use a different IP or check format |
| "Invalid system type: [type]" | Wrong system_type value | Use: Desktop, Laptop, or All-in-One PC (exact case) |
| "Invalid date format: [date]" | Wrong date format | Use YYYY-MM-DD format |
| "Invalid file format" | Wrong file type | Use .xlsx or .xls files only |
| "File too large" | File exceeds 10MB | Split into smaller files |

## Import Process

### Step-by-Step Process

1. **File Upload**: User selects and uploads Excel file
2. **File Validation**: System checks file format and size
3. **Header Validation**: System verifies all required columns exist
4. **Row Processing**: System processes each row sequentially
5. **Row Validation**: Each row is validated against all rules
6. **Asset Creation**: Valid rows create new assets
7. **IP Assignment**: IP addresses are marked as assigned
8. **Error Collection**: Invalid rows are collected with error details
9. **Results Display**: Summary shows success/error counts and details

### What Happens During Import

For each valid row:
1. New Asset record is created
2. Serial number is auto-generated (sequential)
3. IP address is marked as assigned
4. Asset status is set to 'active'
5. All provided fields are saved

For each invalid row:
1. Row is skipped (not imported)
2. Error details are collected
3. Row number and error message are recorded
4. Processing continues with next row

## Best Practices

### Before Import

1. **Download Template**: Always start with the official template
2. **Check Prerequisites**: Ensure Operating Systems and Teams exist
3. **Verify IPs**: Check IP availability in the system
4. **Test Small**: Import 5-10 rows first to verify format
5. **Backup Data**: Keep a copy of your Excel file

### During Import

1. **Review Errors**: Check error messages carefully
2. **Fix and Retry**: Correct errors and re-import failed rows
3. **Monitor Progress**: Watch for success/error counts
4. **Don't Duplicate**: Don't re-import successful rows

### After Import

1. **Verify Data**: Check that assets appear in the asset list
2. **Check IPs**: Verify IP addresses are marked as assigned
3. **Review Assignments**: Confirm team and user assignments
4. **Export Backup**: Export active assets as backup

## Advanced Topics

### Large Imports

For importing 1000+ assets:

1. **Split Files**: Break into files of 500-1000 rows each
2. **Sequential Import**: Import files one at a time
3. **Verify Between**: Check results between each import
4. **Track Progress**: Keep a log of which files are imported

### Handling Errors

When you receive errors:

1. **Export Errors**: Copy error details to a new Excel file
2. **Fix Issues**: Correct the data based on error messages
3. **Re-import**: Upload the corrected file
4. **Verify**: Confirm all rows import successfully

### Data Preparation

Tips for preparing your data:

1. **Consistent Naming**: Use consistent asset tag format
2. **Validate IPs**: Check IP format before importing
3. **Match Case**: Ensure OS and Team names match exactly
4. **Date Format**: Convert dates to YYYY-MM-DD
5. **Remove Duplicates**: Check for duplicate asset tags

## Troubleshooting

### Problem: All rows fail with "Operating System not found"

**Cause**: OS names don't match database entries

**Solution**:
1. Go to Django admin panel
2. Check exact OS names in the system
3. Update your Excel file to match exactly (including case)
4. Re-import

### Problem: All rows fail with "IP address not available"

**Cause**: IPs are already assigned or don't exist in IP management

**Solution**:
1. Check Free IPs page to see available IPs
2. Update your Excel file with available IPs
3. Or add new IP ranges in IP management
4. Re-import

### Problem: "Missing required columns" error

**Cause**: Column headers don't match expected names

**Solution**:
1. Download the official template
2. Copy your data into the template
3. Ensure headers are exactly: asset_tag, system_type, operating_system, ip_address
4. Re-import

### Problem: Some rows import, others fail

**Cause**: This is normal behavior - valid rows are imported, invalid rows are skipped

**Solution**:
1. Review the error list
2. Fix the data for failed rows
3. Create a new Excel file with only the failed rows (corrected)
4. Import the corrected file

## Security Considerations

### Access Control
- Import functionality is restricted to admin users only
- File uploads are validated for type and size
- Malicious file content is rejected

### Data Validation
- All input is sanitized to prevent injection attacks
- Foreign key references are validated
- IP addresses are validated for format and availability

### Audit Trail
- All imports are logged with user and timestamp
- Import results are stored for review
- Failed imports are tracked for security monitoring

## Performance Considerations

### Optimal File Size
- **Best**: 100-500 rows per file
- **Good**: 500-1000 rows per file
- **Acceptable**: 1000-2000 rows per file
- **Not Recommended**: Over 2000 rows per file

### Import Speed
- Approximately 10-20 rows per second
- 100 rows: ~5-10 seconds
- 500 rows: ~25-50 seconds
- 1000 rows: ~50-100 seconds

### Database Impact
- Each import creates database transactions
- Large imports may temporarily slow the system
- Recommended to import during off-peak hours for large datasets

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**For**: Asset Tracker System - Excel Import Feature
