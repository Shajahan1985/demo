# Requirements Document

## Introduction

The Network Range Scanner feature enables discovery of online systems across specified IP address ranges for power monitoring purposes. Currently, the power monitoring system only checks assets already registered in the database with assigned IP addresses. This feature extends monitoring capabilities by scanning entire IP ranges to discover both tracked and untracked systems, providing visibility into all network-connected devices within designated subnets.

## Glossary

- **Scanner**: The network range scanning component
- **IP_Range**: A contiguous block of IP addresses defined by a subnet (e.g., 192.168.10.0/24)
- **Scan_Job**: A single execution of network range scanning across one or more IP ranges
- **Detection_Method**: The technique used to determine if an IP address is online (ICMP ping or TCP port check)
- **Scan_Result**: The outcome of checking a single IP address during a scan
- **Tracked_Asset**: An asset that exists in the database with an assigned IP address
- **Discovered_System**: An IP address found to be online but not associated with any tracked asset
- **Power_Monitor_Service**: The existing service that performs multi-method detection (ping + TCP fallback)

## Requirements

### Requirement 1: Define Target IP Ranges

**User Story:** As a system administrator, I want to configure which IP ranges to scan, so that I can monitor specific network segments.

#### Acceptance Criteria

1. THE Scanner SHALL support configuration of multiple IP_Range targets
2. THE Scanner SHALL support IP_Range specification in CIDR notation (e.g., 192.168.10.0/24)
3. THE Scanner SHALL include the following default IP_Range values: 192.168.10.0/24, 192.168.11.0/24, 192.168.70.0/24, 192.168.50.0/24
4. WHEN an IP_Range is configured, THE Scanner SHALL validate that it represents a valid IPv4 subnet
5. THE Scanner SHALL exclude network addresses (x.x.x.0) and broadcast addresses (x.x.x.255) from scanning

### Requirement 2: Perform Network Range Scanning

**User Story:** As a system administrator, I want to scan entire IP ranges, so that I can discover all online systems in my network.

#### Acceptance Criteria

1. WHEN a Scan_Job is initiated, THE Scanner SHALL check all IP addresses within configured IP_Range targets
2. FOR ALL IP addresses checked, THE Scanner SHALL use the same Detection_Method as Power_Monitor_Service (ICMP ping with TCP port fallback)
3. THE Scanner SHALL attempt TCP port checks on ports 22, 80, and 443 when ICMP ping fails
4. THE Scanner SHALL record each Scan_Result with IP address, online status, and detection method used
5. THE Scanner SHALL perform parallel scanning to improve performance
6. WHEN scanning completes, THE Scanner SHALL return a summary including total IPs scanned, online count, and offline count

### Requirement 3: Distinguish Tracked vs Discovered Systems

**User Story:** As a system administrator, I want to see which online IPs are already tracked in the database versus newly discovered, so that I can identify unmanaged systems.

#### Acceptance Criteria

1. FOR ALL Scan_Result entries with online status, THE Scanner SHALL determine if the IP address matches a Tracked_Asset
2. WHEN an online IP address matches a Tracked_Asset, THE Scanner SHALL mark the Scan_Result as "tracked" and include asset details
3. WHEN an online IP address does not match any Tracked_Asset, THE Scanner SHALL mark the Scan_Result as "discovered"
4. THE Scanner SHALL include Tracked_Asset information (asset tag, hostname, status) in Scan_Result when available

### Requirement 4: Store Scan History

**User Story:** As a system administrator, I want to review historical scan results, so that I can track network changes over time.

#### Acceptance Criteria

1. WHEN a Scan_Job completes, THE Scanner SHALL persist all Scan_Result entries to the database
2. THE Scanner SHALL record the following for each Scan_Job: start time, end time, total IPs scanned, online count, offline count
3. THE Scanner SHALL retain Scan_Result data for at least 90 days
4. THE Scanner SHALL associate each Scan_Result with its parent Scan_Job
5. THE Scanner SHALL record which Detection_Method successfully detected each online system

### Requirement 5: Manual Scan Triggering

**User Story:** As a system administrator, I want to manually trigger network scans from the UI, so that I can get current network status on demand.

#### Acceptance Criteria

1. THE Scanner SHALL provide a user interface control to initiate a Scan_Job
2. WHEN a user initiates a Scan_Job, THE Scanner SHALL begin scanning within 5 seconds
3. WHILE a Scan_Job is running, THE Scanner SHALL prevent initiation of concurrent Scan_Jobs
4. WHEN a Scan_Job is already running, THE Scanner SHALL display a message indicating a scan is in progress
5. WHEN a Scan_Job completes, THE Scanner SHALL display a completion notification with summary statistics

### Requirement 6: Display Scan Results

**User Story:** As a system administrator, I want to view scan results in the UI, so that I can see which systems are online and their tracking status.

#### Acceptance Criteria

1. THE Scanner SHALL display Scan_Result entries in a tabular format
2. THE Scanner SHALL display the following columns: IP address, online status, tracking status, asset tag (if tracked), hostname (if tracked), detection method
3. THE Scanner SHALL provide filtering options for: all results, tracked only, discovered only, online only, offline only
4. THE Scanner SHALL sort results by IP address in ascending order by default
5. THE Scanner SHALL display the timestamp of the most recent Scan_Job
6. WHEN displaying Discovered_System entries, THE Scanner SHALL visually distinguish them from Tracked_Asset entries

### Requirement 7: Scan Performance

**User Story:** As a system administrator, I want scans to complete in a reasonable timeframe, so that I can get timely network status information.

#### Acceptance Criteria

1. THE Scanner SHALL scan at least 10 IP addresses concurrently
2. THE Scanner SHALL complete a full scan of 1016 IP addresses (4 ranges × 254 addresses) within 10 minutes
3. THE Scanner SHALL use a timeout of 2 seconds for each Detection_Method attempt
4. THE Scanner SHALL limit concurrent network operations to prevent system resource exhaustion

### Requirement 8: Scan Result Export

**User Story:** As a system administrator, I want to export scan results, so that I can analyze them in external tools or share with colleagues.

#### Acceptance Criteria

1. THE Scanner SHALL provide an export function for Scan_Result data
2. THE Scanner SHALL support CSV format for export
3. WHEN exporting, THE Scanner SHALL include all Scan_Result fields: IP address, online status, tracking status, asset tag, hostname, detection method, timestamp
4. THE Scanner SHALL generate export files with descriptive filenames including the Scan_Job timestamp
