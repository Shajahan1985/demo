# Implementation Plan: Network Range Scanner

## Overview

This implementation extends the existing Django power monitoring system with network range scanning capabilities. The scanner will discover online systems across configured IP ranges, distinguish tracked assets from discovered systems, and persist scan history for analysis. The implementation integrates with the existing `PowerMonitorService` for consistent detection methods and follows Django's MVT architecture.

## Tasks

- [x] 1. Create database models and migrations
  - [x] 1.1 Create ScanConfiguration model with IP range storage
    - Define model with JSONField for ip_ranges, concurrent_checks, timeout_seconds, is_active fields
    - Add validators for concurrent_checks (1-50) and timeout_seconds (1-10)
    - Create and apply Django migration
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 1.2 Write property test for ScanConfiguration
    - **Property 2: Multiple IP Range Configuration**
    - **Validates: Requirements 1.1**

  - [x] 1.3 Create ScanJob model with status tracking
    - Define model with status choices (pending, running, completed, failed)
    - Add fields: started_at, completed_at, total_ips, online_count, offline_count, tracked_count, discovered_count, error_message
    - Add database indexes on status and started_at fields
    - Create and apply Django migration
    - _Requirements: 4.2, 5.3_

  - [x] 1.4 Create ScanResult model with detection details
    - Define model with ForeignKey to ScanJob and optional ForeignKey to Asset
    - Add fields: ip_address (GenericIPAddressField), is_online, detection_method, is_tracked, checked_at
    - Add detection_method choices (icmp, tcp_22, tcp_80, tcp_443, none)
    - Add database indexes on ip_address, is_online, is_tracked, checked_at
    - Create composite index on (scan_job_id, is_online, is_tracked)
    - Create and apply Django migration
    - _Requirements: 2.4, 3.1, 4.1, 4.5_
    
  - [ ]* 1.5 Write property test for scan summary consistency
    - **Property 7: Scan Summary Consistency**
    - **Validates: Requirements 2.6**

- [x] 2. Implement core scanning service
  - [x] 2.1 Create NetworkScannerService class with CIDR expansion
    - Implement expand_cidr_range() method using ipaddress module
    - Exclude network and broadcast addresses from expansion
    - Raise ValueError for invalid CIDR notation
    - _Requirements: 1.2, 1.4, 1.5_

  - [ ]* 2.2 Write property tests for CIDR expansion
    - **Property 1: CIDR Range Expansion Round Trip**
    - **Validates: Requirements 1.2**
    - **Property 3: Invalid CIDR Rejection**
    - **Validates: Requirements 1.4**
    - **Property 4: Network and Broadcast Exclusion**
    - **Validates: Requirements 1.5**

  - [x] 2.3 Implement IP status checking with PowerMonitorService integration
    - Implement check_ip_status() method that calls PowerMonitorService.check_asset_status()
    - Return tuple of (is_online, detection_method)
    - Handle ICMP ping with TCP port fallback (ports 22, 80, 443)
    - Apply timeout parameter (default 2 seconds)
    - _Requirements: 2.2, 2.3, 7.3_

  - [ ]* 2.4 Write property test for TCP fallback
    - **Property 6: TCP Fallback on ICMP Failure**
    - **Validates: Requirements 2.3**

  - [x] 2.5 Implement asset lookup and classification
    - Implement find_tracked_asset() method to query Asset model by IP address
    - Return Asset instance or None
    - Handle multiple assets with same IP (return first match)
    - _Requirements: 3.1, 3.2, 3.4_

  - [ ]* 2.6 Write property test for asset classification
    - **Property 8: Asset Classification Completeness**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement parallel scan execution
  - [x] 4.1 Implement execute_scan() method with parallel processing
    - Load active ScanConfiguration to get IP ranges
    - Expand all CIDR ranges to individual IPs
    - Update ScanJob status to 'running' and set started_at timestamp
    - Use ThreadPoolExecutor with concurrent_checks workers (default 10)
    - For each IP: call check_ip_status(), find_tracked_asset(), create ScanResult
    - Bulk create ScanResult records in batches of 100 for performance
    - Update ScanJob with summary counts (total_ips, online_count, offline_count, tracked_count, discovered_count)
    - Set ScanJob status to 'completed' and completed_at timestamp
    - Handle exceptions by setting status to 'failed' with error_message
    - _Requirements: 2.1, 2.5, 2.6, 4.1, 4.2, 7.1, 7.4_

  - [ ]* 4.2 Write property test for scan completeness
    - **Property 5: Scan Completeness**
    - **Validates: Requirements 2.1**

  - [ ]* 4.3 Write property test for scan result persistence
    - **Property 9: Scan Result Persistence**
    - **Validates: Requirements 4.1**

  - [ ]* 4.4 Write property test for scan job metadata
    - **Property 10: Scan Job Metadata Completeness**
    - **Validates: Requirements 4.2**

  - [ ]* 4.5 Write property test for detection method recording
    - **Property 11: Detection Method Recording**
    - **Validates: Requirements 4.5**

- [x] 5. Implement CSV export functionality
  - [x] 5.1 Implement export_results_csv() method
    - Query all ScanResult records for given ScanJob
    - Generate CSV with headers: ip_address, is_online, is_tracked, asset_tag, hostname, detection_method, checked_at
    - Format boolean fields as "Yes"/"No"
    - Handle null asset fields with empty strings
    - Return CSV content as string
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ]* 5.2 Write property tests for CSV export
    - **Property 15: CSV Export Validity**
    - **Validates: Requirements 8.2, 8.3**
    - **Property 16: Export Filename Format**
    - **Validates: Requirements 8.4**

- [x] 6. Create Django views and URL routing
  - [x] 6.1 Create scan initiation view (POST /power-monitoring/scan/start/)
    - Check for existing running ScanJob, return HTTP 409 if found
    - Create new ScanJob with status='pending'
    - Call NetworkScannerService.execute_scan() asynchronously or in background
    - Return JSON response with scan_job_id and status
    - Handle validation errors with HTTP 400
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 6.2 Write property test for concurrent scan prevention
    - **Property 12: Concurrent Scan Prevention**
    - **Validates: Requirements 5.3**

  - [x] 6.3 Create scan status view (GET /power-monitoring/scan/status/<job_id>/)
    - Query ScanJob by ID
    - Return JSON with status, progress counts, timestamps
    - Return HTTP 404 if job not found
    - _Requirements: 5.4_

  - [x] 6.4 Create scan results display view (GET /power-monitoring/scan/results/<job_id>/)
    - Query ScanJob and related ScanResult records
    - Apply filter parameter (all, tracked_only, discovered_only, online_only, offline_only)
    - Order results by IP address (numerical sort, not lexicographic)
    - Render results template with scan job and filtered results
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 6.5 Write property test for result filtering
    - **Property 13: Result Filtering Correctness**
    - **Validates: Requirements 6.3**

  - [ ]* 6.6 Write property test for IP address sorting
    - **Property 14: IP Address Sorting**
    - **Validates: Requirements 6.4**

  - [x] 6.7 Create CSV export view (GET /power-monitoring/scan/export/<job_id>/)
    - Query ScanJob by ID, return HTTP 404 if not found
    - Call NetworkScannerService.export_results_csv()
    - Generate filename with format: scan_results_YYYY-MM-DD_HH-MM-SS.csv
    - Return CSV as downloadable file with appropriate Content-Type header
    - _Requirements: 8.1, 8.4_

  - [x] 6.8 Create scan history view (GET /power-monitoring/scan/history/)
    - Query recent ScanJob records ordered by started_at descending
    - Paginate results (20 per page)
    - Render history template with job list
    - _Requirements: 4.3_

  - [x] 6.9 Add URL patterns to power_monitoring/urls.py
    - Register all scan-related URL patterns
    - Use appropriate URL naming for reverse lookups

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Create Django templates for UI
  - [x] 8.1 Create scan control template with manual trigger button
    - Add "Start Network Scan" button that POSTs to scan/start/
    - Display current scan status (idle, running, completed)
    - Show scan in progress message when applicable
    - Display completion notification with summary statistics
    - _Requirements: 5.1, 5.4, 5.5_

  - [x] 8.2 Create scan results table template
    - Display results in table with columns: IP Address, Status, Tracking, Asset Tag, Hostname, Detection Method
    - Add filter buttons for: All, Tracked Only, Discovered Only, Online Only, Offline Only
    - Visually distinguish discovered systems (e.g., different row color or icon)
    - Display scan timestamp
    - Add "Export CSV" button linking to export view
    - _Requirements: 6.1, 6.2, 6.3, 6.6, 8.1_

  - [x] 8.3 Create scan history template
    - Display list of recent scans with timestamps and summary counts
    - Link each scan to its results page
    - Show scan status (completed, failed, running)
    - _Requirements: 4.3_

- [ ] 9. Implement data retention cleanup
  - [ ] 9.1 Create Celery periodic task for old scan cleanup
    - Create periodic task that runs daily at 2 AM
    - Delete ScanJob records older than 90 days (cascade deletes ScanResult records)
    - Log cleanup statistics (number of jobs deleted)
    - _Requirements: 4.3_

- [x] 10. Add admin interface configuration
  - [x] 10.1 Register models in Django admin
    - Register ScanConfiguration with inline editing for ip_ranges
    - Register ScanJob with read-only fields and list filters
    - Register ScanResult with search by IP address and list filters
    - Add custom admin actions for manual scan triggering

- [x] 11. Create initial data migration for default configuration
  - [x] 11.1 Create data migration for default ScanConfiguration
    - Create ScanConfiguration instance with default IP ranges: 192.168.10.0/24, 192.168.11.0/24, 192.168.70.0/24, 192.168.50.0/24
    - Set concurrent_checks=10, timeout_seconds=2, is_active=True
    - _Requirements: 1.3_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The implementation uses Python/Django as specified in the design document
- Property tests should use Hypothesis with minimum 100 examples per test
- Parallel scanning uses ThreadPoolExecutor to avoid blocking the main thread
- Bulk operations (bulk_create) are used for performance with large IP ranges
- All timestamps use Django's timezone-aware datetime handling
