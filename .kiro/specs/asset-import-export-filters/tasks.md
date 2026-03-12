# Implementation Plan: Asset Import/Export/Filters

## Overview

This implementation plan breaks down the Asset Import/Export/Filters feature into discrete, incremental coding tasks. The plan follows a bottom-up approach: services → forms → views → templates → integration. Each task builds on previous work, with property-based tests integrated to catch errors early.

## Tasks

- [x] 1. Set up dependencies and project structure
  - Add openpyxl to requirements.txt
  - Create services/import_service.py file
  - Create services/export_service.py file
  - Create services/filter_service.py file
  - Create forms/import_form.py file
  - Create forms/filter_form.py file
  - _Requirements: All_

- [x] 2. Implement ImportService
  - [x] 2.1 Create ImportService class with parse_excel method
    - Implement parse_excel(file) to load Excel workbook using openpyxl
    - Extract headers from first row
    - Return list of row dictionaries with column names as keys
    - Handle .xlsx and .xls file formats
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [x] 2.2 Implement validate_headers method
    - Check for required columns: asset_tag, system_type, operating_system, ip_address
    - Return True if all required columns present, False otherwise
    - _Requirements: 2.1, 2.2_
  
  - [x] 2.3 Implement validate_row method
    - Validate asset_tag is non-empty and unique
    - Validate system_type is one of: Desktop, Laptop, All-in-One PC
    - Validate operating_system exists in database
    - Validate ip_address is valid IPv4 and available
    - Validate team exists in database if provided
    - Validate warranty_expiration is valid date format if provided
    - Return tuple: (is_valid: bool, errors: List[str])
    - _Requirements: 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_
  
  - [x] 2.4 Implement import_assets method
    - Parse Excel file using parse_excel()
    - Validate headers using validate_headers()
    - Loop through rows and validate each using validate_row()
    - For valid rows, call AssetService.create_asset()
    - Track success_count, error_count, and errors list
    - Use transaction.atomic() for database integrity
    - Return dict with success_count, error_count, errors
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [x] 2.5 Write property tests for ImportService
    - **Property 1: Import validation completeness** - All imported rows pass validation
    - **Property 2: Import uniqueness** - No duplicate asset_tags in imported assets
    - **Property 3: Import IP assignment** - All imported assets have assigned IPs
    - **Validates: Requirements 2.3, 2.4, 3.1, 3.2, 3.3**

- [x] 3. Implement ExportService
  - [x] 3.1 Create ExportService class with _create_workbook helper
    - Implement _create_workbook(queryset, columns, title) to create Excel workbook
    - Write headers to first row
    - Loop through queryset and write data rows
    - Format columns with appropriate widths
    - Return openpyxl Workbook object
    - _Requirements: 5.2, 6.2, 7.2, 8.2_
  
  - [x] 3.2 Implement export_active_assets method
    - Query Asset.objects.filter(status='active').select_related('operating_system', 'team', 'ip_address')
    - Define columns: Serial Number, Asset Tag, System Type, OS, IP Address, Assigned To, Team, Warranty Expiration
    - Call _create_workbook() with queryset and columns
    - Create HttpResponse with content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    - Set Content-Disposition header with filename='active_assets.xlsx'
    - Save workbook to response
    - Return HttpResponse
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [x] 3.3 Implement export_freed_assets method
    - Query Asset.objects.filter(status='freed').select_related('operating_system', 'ip_address')
    - Define columns: Serial Number, Asset Tag, System Type, OS, IP Address, Freed Date
    - Order by freed_date descending
    - Call _create_workbook() and return HttpResponse with filename='freed_assets.xlsx'
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [x] 3.4 Implement export_scrapped_assets method
    - Query Asset.objects.filter(status='scrapped').select_related('operating_system', 'ip_address')
    - Define columns: Serial Number, Asset Tag, System Type, OS, IP Address, Scrapped Date
    - Order by scrapped_date descending
    - Call _create_workbook() and return HttpResponse with filename='scrapped_assets.xlsx'
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 3.5 Implement export_free_ips method
    - Query IPAddress.objects.filter(is_assigned=False).select_related('ip_range')
    - Define columns: IP Address, IP Range
    - Order by ip_range, then by address
    - Call _create_workbook() and return HttpResponse with filename='free_ips.xlsx'
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_
  
  - [x] 3.6 Write property tests for ExportService
    - **Property 4: Export completeness** - Exported row count equals queryset count
    - **Property 5: Export column consistency** - All rows have same number of columns as headers
    - **Property 6: Export format validity** - Generated file is valid Excel format
    - **Validates: Requirements 5.1, 5.2, 6.1, 7.1, 8.1**

- [x] 4. Implement FilterService
  - [x] 4.1 Create FilterService class with filter methods
    - Implement filter_by_os(queryset, os_id) to filter by operating_system_id
    - Implement filter_by_asset_tag(queryset, asset_tag) to filter by asset_tag__icontains
    - Implement filter_by_team(queryset, team_id) to filter by team_id
    - Implement filter_by_assigned_user(queryset, user_name) to filter by assigned_to__icontains
    - _Requirements: 9.3, 10.2, 11.3, 12.2_
  
  - [x] 4.2 Implement apply_filters method
    - Accept queryset and filters dict as parameters
    - Check each filter key (operating_system, asset_tag, team, assigned_to)
    - Apply corresponding filter method if value is provided
    - Combine filters with AND logic
    - Return filtered queryset
    - _Requirements: 13.1, 13.2, 13.3_
  
  - [x] 4.3 Write property tests for FilterService
    - **Property 7: Filter monotonicity** - Filtered set size ≤ original set size
    - **Property 8: Filter composition** - apply_filters(qs, {f1, f2}) = apply_filters(apply_filters(qs, {f1}), {f2})
    - **Property 9: Filter idempotence** - apply_filters(apply_filters(qs, f), f) = apply_filters(qs, f)
    - **Validates: Requirements 13.1, 13.2, 13.3**

- [x] 5. Create Django forms
  - [x] 5.1 Create AssetImportForm
    - Add FileField for Excel file upload
    - Add file validation for .xlsx and .xls extensions
    - Add file size validation (max 10MB)
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [x] 5.2 Create AssetFilterForm
    - Add ChoiceField for operating_system (dropdown)
    - Add CharField for asset_tag (text input)
    - Add ChoiceField for team (dropdown)
    - Add CharField for assigned_to (text input)
    - Make all fields optional
    - Populate dropdowns from database in __init__
    - _Requirements: 9.1, 9.2, 10.1, 11.1, 11.2, 12.1_

- [x] 6. Implement import views
  - [x] 6.1 Create AssetImportView with AdminRequiredMixin
    - Display AssetImportForm on GET
    - Process form submission on POST
    - Validate file format and size
    - Call ImportService.import_assets() with uploaded file
    - Handle import results and display success/error messages
    - Redirect to results page with import summary
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 6.2 Create import results template
    - Display success count
    - Display error count
    - Show detailed error list with row numbers and messages
    - Add link to return to asset list
    - Add link to try import again
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 7. Implement export views
  - [x] 7.1 Create AssetExportActiveView
    - Call ExportService.export_active_assets()
    - Return HttpResponse with Excel file
    - Require authentication (LoginRequiredMixin)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [x] 7.2 Create AssetExportFreedView
    - Call ExportService.export_freed_assets()
    - Return HttpResponse with Excel file
    - Require authentication (LoginRequiredMixin)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [x] 7.3 Create AssetExportScrappedView
    - Call ExportService.export_scrapped_assets()
    - Return HttpResponse with Excel file
    - Require authentication (LoginRequiredMixin)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 7.4 Create FreeIPsExportView
    - Call ExportService.export_free_ips()
    - Return HttpResponse with Excel file
    - Require authentication (LoginRequiredMixin)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 8. Update AssetListView with filtering
  - [x] 8.1 Modify AssetListView to accept filter parameters
    - Initialize AssetFilterForm with request.GET
    - Validate filter form
    - Call FilterService.apply_filters() with form.cleaned_data
    - Pass filtered queryset to template
    - Pass filter form to template context
    - Preserve filter values in URL parameters
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 10.1, 10.2, 10.3, 11.1, 11.2, 11.3, 12.1, 12.2, 12.3, 13.1, 13.2, 13.3, 13.4, 13.5_
  
  - [x] 8.2 Write integration tests for filtered views
    - Test single filter application
    - Test multiple filter combination
    - Test filter with no matches
    - Test clear filters functionality
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 14.1, 14.2, 14.3, 14.4_

- [x] 9. Create URL configuration
  - Add URL pattern /assets/import/ → AssetImportView
  - Add URL pattern /assets/import/results/ → Import results template
  - Add URL pattern /assets/export/active/ → AssetExportActiveView
  - Add URL pattern /assets/export/freed/ → AssetExportFreedView
  - Add URL pattern /assets/export/scrapped/ → AssetExportScrappedView
  - Add URL pattern /ips/export/free/ → FreeIPsExportView
  - Update existing /assets/ URL to use updated AssetListView
  - _Requirements: All_

- [x] 10. Create HTML templates
  - [x] 10.1 Create asset_import.html template
    - Display file upload form with AssetImportForm
    - Add file input with accept=".xlsx,.xls"
    - Add submit button "Import Assets"
    - Add instructions for Excel format
    - Show sample Excel template download link
    - _Requirements: 1.1, 1.2_
  
  - [x] 10.2 Create asset_import_results.html template
    - Display success count with green styling
    - Display error count with red styling if > 0
    - Show detailed error table with columns: Row Number, Asset Tag, Errors
    - Add "Back to Assets" button
    - Add "Import More Assets" button
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 10.3 Update asset_list.html template with filters
    - Add filter form section at top of page
    - Display OS dropdown filter
    - Display Asset Tag text input filter
    - Display Team dropdown filter
    - Display Assigned To text input filter
    - Add "Apply Filters" button
    - Add "Clear Filters" button
    - Show active filter count badge
    - _Requirements: 9.1, 9.2, 10.1, 11.1, 11.2, 12.1, 14.1_
  
  - [x] 10.4 Add export buttons to existing templates
    - Add "Export to Excel" button to asset_list.html
    - Add "Export to Excel" button to freed_systems.html
    - Add "Export to Excel" button to scrapped_items.html
    - Add "Export to Excel" button to free_ips.html
    - Style buttons consistently with existing UI
    - _Requirements: 5.1, 6.1, 7.1, 8.1_
  
  - [x] 10.5 Update navigation menu
    - Add "Import Assets" link to navigation (admin only)
    - Ensure export buttons are visible to all authenticated users
    - _Requirements: 1.5, 15.6_

- [x] 11. Create sample Excel template
  - Create sample_import_template.xlsx file
  - Include headers: asset_tag, system_type, operating_system, ip_address, particulars, assigned_to, team, warranty_expiration
  - Add 2-3 sample rows with example data
  - Add comments/notes explaining each column
  - Store in media/templates/ directory
  - Add download link in import form template
  - _Requirements: 1.1, 2.1_

- [x] 12. Add CSS styling for new features
  - Style filter form with consistent spacing
  - Style import form with file upload styling
  - Style import results table with color coding
  - Style export buttons to match existing buttons
  - Add responsive design for mobile devices
  - Style "Clear Filters" button distinctly
  - _Requirements: All_

- [x] 13. Integration testing
  - [x] 13.1 Test complete import workflow
    - Test: Upload valid Excel → Verify assets created → Check IPs assigned
    - Test: Upload Excel with errors → Verify error reporting → Verify partial import
    - Test: Upload invalid file → Verify rejection
    - Test: Non-admin access → Verify permission denied
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1-2.9, 3.1-3.7, 4.1-4.5_
  
  - [x] 13.2 Test complete export workflow
    - Test: Export active assets → Verify Excel file → Check all columns present
    - Test: Export freed assets → Verify correct data
    - Test: Export scrapped assets → Verify correct data
    - Test: Export free IPs → Verify grouping by range
    - Test: Export with no data → Verify headers-only file
    - _Requirements: 5.1-5.6, 6.1-6.5, 7.1-7.5, 8.1-8.6_
  
  - [x] 13.3 Test complete filtering workflow
    - Test: Apply single filter → Verify results
    - Test: Apply multiple filters → Verify AND logic
    - Test: Clear filters → Verify all assets shown
    - Test: Filter with no matches → Verify empty message
    - Test: Filter persistence → Verify values preserved after page reload
    - _Requirements: 9.1-9.4, 10.1-10.3, 11.1-11.3, 12.1-12.3, 13.1-13.5, 14.1-14.4_
  
  - [x] 13.4 Test integration with existing features
    - Test: Import assets → Verify they appear in asset list
    - Test: Import assets → Free one → Verify it appears in freed list → Export freed list
    - Test: Apply filters → Export filtered results → Verify Excel matches filtered view
    - Test: Import with existing AssetService validation → Verify all rules enforced
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

- [x] 14. Performance testing and optimization
  - Test import with large file (1000+ rows)
  - Test export with large dataset (1000+ assets)
  - Test filtering with large dataset
  - Add database indexes if needed (asset_tag, status already indexed)
  - Consider pagination for filtered results if needed
  - _Requirements: All_

- [x] 15. Documentation and deployment
  - Update README with import/export/filter instructions
  - Document Excel import format and requirements
  - Add user guide for filtering features
  - Update requirements.txt with openpyxl version
  - Create migration if any model changes needed
  - Test deployment on staging environment
  - _Requirements: All_

## Notes

- All import operations are admin-only (AdminRequiredMixin)
- All export operations require authentication (LoginRequiredMixin)
- All filter operations are available to authenticated users
- Import uses existing AssetService.create_asset() for consistency
- Export uses select_related() for query optimization
- Filters use Django ORM for SQL injection protection
- Property tests validate universal correctness properties
- Integration tests validate complete workflows
- The implementation maintains existing functionality while adding new features
- Excel operations use openpyxl library for .xlsx and .xls support
