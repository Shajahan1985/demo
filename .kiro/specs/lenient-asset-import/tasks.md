# Implementation Plan: Lenient Asset Import

## Overview

Modify the existing `ImportService` to support lenient validation (only `asset_tag`, `system_type`, `operating_system` required), upsert logic (create or update by `asset_tag`), and display separate created/updated counts in results. Add missing-field warnings on the asset list page for incomplete records.

## Tasks

- [x] 1. Update ImportService validation methods
  - [x] 1.1 Update `validate_headers()` in `assets/services/import_service.py`
    - Change `required_columns` from `['asset_tag', 'system_type', 'operating_system', 'ip_address']` to `['asset_tag', 'system_type', 'operating_system']`
    - Update error messages to use format `"Missing required column: {column_name}"` for each missing column individually
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 1.2 Update `validate_row()` in `assets/services/import_service.py`
    - Change return signature to `Tuple[bool, List[str], bool]` returning `(is_valid, errors, is_update)`
    - Remove the `"Asset tag already exists"` rejection — instead set `is_update = True` when `asset_tag` exists in DB
    - Remove the `"IP address is required"` check — `ip_address` is now optional
    - Remove the `"Operating System is required"` error text, replace with `"Operating system is required"` (lowercase 's')
    - Add check: if `system_type` is empty/missing, add error `"System type is required"`
    - Keep existing validations for: invalid `system_type` value, OS not found, team not found, IP already assigned to another asset
    - For IP validation on update: skip `"IP address not available"` if the IP is assigned to the same asset being updated
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11_

  - [ ]* 1.3 Write property tests for validation (Properties 1–7)
    - **Property 1: Required field validation rejects rows with missing required fields**
    - **Property 2: Optional fields accepted as null**
    - **Property 3: Invalid system_type rejection**
    - **Property 4: Invalid operating_system rejection**
    - **Property 5: Invalid team rejection**
    - **Property 6: Assigned IP rejection**
    - **Property 7: Header validation requires only required columns**
    - Add tests to `assets/tests/test_import_properties.py`
    - **Validates: Requirements 1.1–1.11, 2.1–2.5**

- [x] 2. Implement upsert logic in ImportService
  - [x] 2.1 Update `import_assets()` in `assets/services/import_service.py`
    - Replace `success_count` with `created_count` and `updated_count` counters
    - Update `validate_row()` call to unpack the new `is_update` flag
    - For new assets (`is_update=False`): call `AssetService.create_asset()` with available data, passing `None` for missing optional fields (`ip_address`, `team`, `assigned_to`)
    - For existing assets (`is_update=True`): look up the existing `Asset` by `asset_tag`, build update data dict with only non-empty fields from the Excel row, call `AssetService.update_asset()` preserving existing populated values
    - Handle IP address on update: if new valid IP provided, include `ip_address` in update data; if IP cell is empty, omit `ip_address` key from update data to preserve existing IP
    - Handle `team` on update: if non-empty team provided, include `team` ID; if empty, omit key to preserve existing
    - Handle `assigned_to` on update: if non-empty, include value; if empty, omit key to preserve existing
    - Return `{'created_count': N, 'updated_count': N, 'error_count': N, 'errors': [...]}`
    - Update header validation error return to use `created_count: 0, updated_count: 0` instead of `success_count: 0`
    - Update empty file error return similarly
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 2.2 Write property tests for upsert logic (Properties 8–12)
    - **Property 8: Upsert update applies non-empty fields**
    - **Property 9: Upsert field preservation — empty values do not overwrite populated fields**
    - **Property 10: IP release and reassign on update**
    - **Property 11: Upsert create path**
    - **Property 12: Accurate created and updated counts**
    - Add tests to `assets/tests/test_import_properties.py`
    - **Validates: Requirements 3.1–3.6**

- [x] 3. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update views and templates for import results
  - [x] 4.1 Update `AssetImportView.post()` in `assets/views.py`
    - Change session storage from `success_count` to `created_count` and `updated_count`
    - Update success message to show `"X asset(s) created, Y asset(s) updated."` when either count > 0
    - _Requirements: 4.1, 4.2, 4.5_

  - [x] 4.2 Update `AssetImportResultsView.get()` in `assets/views.py`
    - Pass `created_count` and `updated_count` to template context instead of `success_count`
    - _Requirements: 4.1, 4.2_

  - [x] 4.3 Update `assets/templates/assets/asset_import_results.html`
    - Replace the single success count display with separate created and updated counts: `"✓ X asset(s) created, Y asset(s) updated."`
    - Keep the error count and detailed error list display unchanged
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 4.4 Write unit tests for import results display
    - Test that the results template renders `created_count` and `updated_count` separately
    - Test error display remains functional
    - Add tests to `assets/tests/test_views.py`
    - _Requirements: 4.1–4.5_

- [x] 5. Add missing-field warnings on asset list page
  - [x] 5.1 Update `assets/templates/assets/asset_list.html`
    - For the IP column: if `asset.ip_address` is null and `asset.manual_ip` is null, apply `missing-field` class and display `"IP is missing"` instead of `"N/A"`
    - For the Assigned To column: if `asset.assigned_to` is null or empty, apply `missing-field` class and display `"User is missing"` instead of `"N/A"`
    - For the Team column: if `asset.team` is null, apply `missing-field` class and display `"Team is missing"` instead of `"N/A"`
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 5.2 Add `.missing-field` CSS class to `assets/static/assets/css/styles.css`
    - Add rule: `.missing-field { color: #dc3545; }`
    - _Requirements: 5.5_

  - [ ]* 5.3 Write unit tests for missing-field warnings
    - Test that assets with null `ip_address` render with `missing-field` class and `"IP is missing"` text
    - Test that assets with null `assigned_to` render with `missing-field` class and `"User is missing"` text
    - Test that assets with null `team` render with `missing-field` class and `"Team is missing"` text
    - Test that fully populated assets render without `missing-field` class or warning text
    - Add tests to `assets/tests/test_views.py` or `assets/tests/test_templates.py`
    - _Requirements: 5.1–5.5_

- [x] 6. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- The design uses Python (Django), so all code examples and implementations use Python
- No model changes are needed — `ip_address`, `assigned_to`, and `team` are already nullable on the `Asset` model (Requirement 6)
- Property tests use Hypothesis, consistent with existing `assets/tests/test_import_properties.py`
- Each task references specific requirements for traceability
