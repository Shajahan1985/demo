# Design Document: Network Range Scanner

## Overview

The Network Range Scanner extends the existing power monitoring system by enabling discovery of online systems across specified IP address ranges. Currently, the system only monitors assets already registered in the database with assigned IP addresses. This feature adds proactive network scanning to discover both tracked and untracked systems, providing comprehensive visibility into network-connected devices.

The scanner integrates with the existing `PowerMonitorService` detection methods (ICMP ping with TCP port fallback) to ensure consistent online/offline determination across the system. Scan results are persisted for historical analysis, enabling administrators to track network changes over time and identify unmanaged systems.

Key capabilities:
- Scan multiple configurable IP ranges in CIDR notation
- Parallel scanning for performance (10+ concurrent checks)
- Distinguish tracked assets from discovered systems
- Historical scan result storage (90+ days retention)
- Manual scan triggering via UI
- CSV export for external analysis

## Architecture

The Network Range Scanner follows Django's MVT (Model-View-Template) architecture and integrates with the existing `power_monitoring` app structure. The design emphasizes separation of concerns with distinct layers for scanning logic, data persistence, and presentation.

### Component Layers

**Service Layer** (`network_scanner_service.py`)
- Core scanning logic and IP range expansion
- Integration with `PowerMonitorService` for detection
- Parallel execution coordination
- Asset lookup and classification

**Model Layer** (Django ORM models)
- `ScanJob`: Represents a single scan execution with metadata
- `ScanResult`: Individual IP check results with tracking status
- `ScanConfiguration`: Configurable IP ranges and scan parameters

**View Layer** (Django views)
- Scan initiation endpoint
- Results display with filtering
- Export functionality
- Real-time scan status

**Template Layer** (Django templates)
- Scan control interface
- Results table with sorting/filtering
- Visual distinction for tracked vs discovered systems

### Integration Points

1. **PowerMonitorService**: Reuses existing `check_asset_status()` logic for consistent detection
2. **Asset Model**: Queries for IP address matching to classify tracked vs discovered
3. **IPAddress Model**: Validates scanned IPs against managed IP ranges
4. **Celery** (optional): Background task execution for long-running scans

### Data Flow

```
User triggers scan → ScanJob created → IP ranges expanded → 
Parallel IP checks (PowerMonitorService) → Asset lookup → 
ScanResult records created → Summary returned → UI updated
```

## Components and Interfaces

### Models

#### ScanConfiguration
Stores configurable IP ranges and scan parameters.

```python
class ScanConfiguration(models.Model):
    ip_ranges = models.JSONField(
        default=list,
        help_text="List of IP ranges in CIDR notation"
    )
    concurrent_checks = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    timeout_seconds = models.IntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### ScanJob
Represents a single scan execution.

```python
class ScanJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    started_at = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_ips = models.IntegerField(default=0)
    online_count = models.IntegerField(default=0)
    offline_count = models.IntegerField(default=0)
    tracked_count = models.IntegerField(default=0)
    discovered_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### ScanResult
Individual IP check result.

```python
class ScanResult(models.Model):
    DETECTION_METHOD_CHOICES = [
        ('icmp', 'ICMP Ping'),
        ('tcp_22', 'TCP Port 22'),
        ('tcp_80', 'TCP Port 80'),
        ('tcp_443', 'TCP Port 443'),
        ('none', 'Not Detected'),
    ]
    
    scan_job = models.ForeignKey(
        ScanJob,
        on_delete=models.CASCADE,
        related_name='results'
    )
    ip_address = models.GenericIPAddressField(protocol='IPv4', db_index=True)
    is_online = models.BooleanField(default=False, db_index=True)
    detection_method = models.CharField(
        max_length=20,
        choices=DETECTION_METHOD_CHOICES,
        default='none'
    )
    is_tracked = models.BooleanField(default=False, db_index=True)
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scan_results'
    )
    checked_at = models.DateTimeField(auto_now_add=True, db_index=True)
```

### Service Interface

#### NetworkScannerService

```python
class NetworkScannerService:
    @staticmethod
    def expand_cidr_range(cidr: str) -> List[str]:
        """
        Expand CIDR notation to list of IP addresses.
        Excludes network and broadcast addresses.
        
        Args:
            cidr: IP range in CIDR notation (e.g., "192.168.10.0/24")
            
        Returns:
            List of IP address strings
            
        Raises:
            ValueError: If CIDR notation is invalid
        """
        pass
    
    @staticmethod
    def check_ip_status(ip: str, timeout: int = 2) -> Tuple[bool, str]:
        """
        Check if IP is online using PowerMonitorService methods.
        
        Args:
            ip: IP address to check
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (is_online, detection_method)
        """
        pass
    
    @staticmethod
    def find_tracked_asset(ip: str) -> Optional[Asset]:
        """
        Find asset with matching IP address.
        
        Args:
            ip: IP address to lookup
            
        Returns:
            Asset instance or None
        """
        pass
    
    @staticmethod
    def execute_scan(scan_job: ScanJob) -> Dict[str, Any]:
        """
        Execute network scan for configured IP ranges.
        
        Args:
            scan_job: ScanJob instance to execute
            
        Returns:
            Summary dictionary with counts and statistics
        """
        pass
    
    @staticmethod
    def export_results_csv(scan_job: ScanJob) -> str:
        """
        Export scan results to CSV format.
        
        Args:
            scan_job: ScanJob to export
            
        Returns:
            CSV content as string
        """
        pass
```

### View Endpoints

**POST /power-monitoring/scan/start/**
- Initiates a new scan job
- Returns: `{"scan_job_id": int, "status": str}`
- Error: 409 if scan already running

**GET /power-monitoring/scan/status/<job_id>/**
- Returns scan job status and progress
- Returns: `{"status": str, "progress": dict}`

**GET /power-monitoring/scan/results/<job_id>/**
- Displays scan results with filtering
- Query params: `filter` (all|tracked|discovered|online|offline)

**GET /power-monitoring/scan/export/<job_id>/**
- Exports results as CSV
- Returns: CSV file download

**GET /power-monitoring/scan/history/**
- Lists recent scan jobs
- Paginated results

## Data Models

### Database Schema

```
ScanConfiguration
├── id (PK)
├── ip_ranges (JSON)
├── concurrent_checks (INT)
├── timeout_seconds (INT)
├── is_active (BOOL)
├── created_at (DATETIME)
└── updated_at (DATETIME)

ScanJob
├── id (PK)
├── status (VARCHAR)
├── started_at (DATETIME, indexed)
├── completed_at (DATETIME)
├── total_ips (INT)
├── online_count (INT)
├── offline_count (INT)
├── tracked_count (INT)
├── discovered_count (INT)
├── error_message (TEXT)
└── created_at (DATETIME)

ScanResult
├── id (PK)
├── scan_job_id (FK → ScanJob)
├── ip_address (IPv4, indexed)
├── is_online (BOOL, indexed)
├── detection_method (VARCHAR)
├── is_tracked (BOOL, indexed)
├── asset_id (FK → Asset, nullable)
└── checked_at (DATETIME, indexed)
```

### Indexes

- `ScanJob.status` - Fast filtering by scan status
- `ScanJob.started_at` - Chronological ordering
- `ScanResult.ip_address` - IP lookup
- `ScanResult.is_online` - Online/offline filtering
- `ScanResult.is_tracked` - Tracked/discovered filtering
- `ScanResult.checked_at` - Temporal queries
- Composite: `(scan_job_id, is_online, is_tracked)` - Common filter combinations

### Data Retention

Scan results older than 90 days are automatically purged via a scheduled Celery task:

```python
@periodic_task(run_every=crontab(hour=2, minute=0))  # Daily at 2 AM
def cleanup_old_scan_results():
    cutoff_date = timezone.now() - timedelta(days=90)
    ScanJob.objects.filter(created_at__lt=cutoff_date).delete()
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following redundancies:
- Properties 3.2, 3.3, and 3.4 all relate to asset classification and can be combined into a single comprehensive property about correct classification
- Properties 2.4 and 4.2 both relate to data completeness and can be consolidated
- Property 4.4 (referential integrity) is implicitly validated by Django's ORM and database constraints

### Property 1: CIDR Range Expansion Round Trip

*For any* valid CIDR notation string, expanding it to IP addresses and reconstructing the CIDR range should preserve the network prefix and subnet mask.

**Validates: Requirements 1.2**

### Property 2: Multiple IP Range Configuration

*For any* list of valid CIDR ranges, storing them in ScanConfiguration and retrieving them should return the same list of ranges.

**Validates: Requirements 1.1**

### Property 3: Invalid CIDR Rejection

*For any* invalid CIDR notation string (malformed IP, invalid subnet mask, non-IPv4), attempting to configure it should raise a validation error.

**Validates: Requirements 1.4**

### Property 4: Network and Broadcast Exclusion

*For any* CIDR range, expanding it to individual IP addresses should exclude both the network address (x.x.x.0) and broadcast address (x.x.x.255).

**Validates: Requirements 1.5**

### Property 5: Scan Completeness

*For any* set of configured IP ranges, executing a scan should produce scan results for exactly the set of valid host IPs (excluding network and broadcast addresses) across all ranges.

**Validates: Requirements 2.1**

### Property 6: TCP Fallback on ICMP Failure

*For any* IP address where ICMP ping fails, the scanner should attempt TCP port checks on ports 22, 80, and 443 before marking the IP as offline.

**Validates: Requirements 2.3**

### Property 7: Scan Summary Consistency

*For any* completed scan job, the summary counts should satisfy: total_ips = online_count + offline_count, and online_count = tracked_count + discovered_count.

**Validates: Requirements 2.6**

### Property 8: Asset Classification Completeness

*For any* scan result marked as online, the is_tracked field should be true if and only if the IP address matches an existing Asset with that IP, and when tracked, asset details (asset_tag, hostname, status) should be populated.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 9: Scan Result Persistence

*For any* completed scan job, all scan results should be retrievable from the database with their associated scan_job_id, and the count of persisted results should equal the total_ips count.

**Validates: Requirements 4.1**

### Property 10: Scan Job Metadata Completeness

*For any* completed scan job, the following fields should be non-null and valid: started_at, completed_at, total_ips, online_count, offline_count, and completed_at should be after started_at.

**Validates: Requirements 4.2**

### Property 11: Detection Method Recording

*For any* scan result marked as online, the detection_method field should be one of ['icmp', 'tcp_22', 'tcp_80', 'tcp_443'] and not 'none'.

**Validates: Requirements 4.5**

### Property 12: Concurrent Scan Prevention

*For any* scan job in 'running' status, attempting to initiate a new scan job should result in an error response indicating a scan is already in progress.

**Validates: Requirements 5.3**

### Property 13: Result Filtering Correctness

*For any* scan job and filter type (tracked_only, discovered_only, online_only, offline_only), the filtered results should contain only records matching the filter criteria.

**Validates: Requirements 6.3**

### Property 14: IP Address Sorting

*For any* list of scan results, sorting by IP address should produce results in ascending numerical order (not lexicographic string order).

**Validates: Requirements 6.4**

### Property 15: CSV Export Validity

*For any* scan job, exporting to CSV should produce valid CSV content that can be parsed back, with all rows containing the required fields: ip_address, is_online, is_tracked, asset_tag, hostname, detection_method, checked_at.

**Validates: Requirements 8.2, 8.3**

### Property 16: Export Filename Format

*For any* scan job with a known timestamp, the generated export filename should match the pattern `scan_results_YYYY-MM-DD_HH-MM-SS.csv` where the timestamp corresponds to the scan job's started_at time.

**Validates: Requirements 8.4**

## Error Handling

### Input Validation Errors

**Invalid CIDR Notation**
- Trigger: User provides malformed CIDR (e.g., "192.168.1.0/33", "invalid.ip.0.0/24")
- Response: Return HTTP 400 with error message: "Invalid CIDR notation: {cidr}"
- Logging: Log validation error with user ID and input

**Empty IP Range Configuration**
- Trigger: Attempting to start scan with no configured IP ranges
- Response: Return HTTP 400 with error message: "No IP ranges configured for scanning"
- Logging: Log configuration error

### Operational Errors

**Concurrent Scan Attempt**
- Trigger: User initiates scan while another scan is running
- Response: Return HTTP 409 with error message: "Scan already in progress (Job ID: {id})"
- Logging: Log concurrent attempt with user ID

**Network Timeout**
- Trigger: Individual IP check exceeds timeout threshold
- Response: Mark IP as offline with detection_method='none'
- Logging: Log timeout for IP address (debug level)

**Database Connection Failure**
- Trigger: Unable to persist scan results
- Response: Mark scan job as 'failed' with error_message
- Logging: Log database error with full stack trace
- Recovery: Retry logic with exponential backoff (3 attempts)

**Asset Lookup Failure**
- Trigger: Database error during asset classification
- Response: Mark result as is_tracked=False, asset=None
- Logging: Log lookup error with IP address
- Graceful degradation: Continue scan with remaining IPs

### Resource Exhaustion

**Too Many Concurrent Scans**
- Prevention: Single scan limit enforced at application level
- Mitigation: Queue-based approach if multiple scans needed

**Memory Pressure**
- Prevention: Process results in batches of 100 IPs
- Mitigation: Bulk create ScanResult records to reduce memory footprint

**Network Socket Exhaustion**
- Prevention: Limit concurrent checks to configured maximum (default 10)
- Mitigation: Connection pooling and proper socket cleanup

### Error Recovery

**Partial Scan Failure**
- If scan fails mid-execution, mark scan job as 'failed'
- Preserve partial results already persisted
- Include error_message with failure reason and last successful IP

**Database Transaction Rollback**
- Wrap scan result persistence in database transaction
- On failure, rollback entire batch and retry
- After 3 failures, mark scan as failed

## Testing Strategy

### Dual Testing Approach

The Network Range Scanner will be validated using both unit tests and property-based tests. These approaches are complementary:

- **Unit tests** verify specific examples, edge cases, and integration points
- **Property tests** verify universal properties across randomized inputs

### Unit Testing Focus

Unit tests will cover:

1. **Specific Examples**
   - Default IP range configuration (192.168.10.0/24, etc.)
   - Known IP addresses with expected online/offline status
   - Specific CIDR expansions (e.g., /24 → 254 IPs, /30 → 2 IPs)

2. **Edge Cases**
   - Empty scan results (no IPs online)
   - All IPs online scenario
   - Single IP range (/32 subnet)
   - Large subnet (/16) handling

3. **Integration Points**
   - PowerMonitorService integration (mock external checks)
   - Asset model queries (test with known database state)
   - CSV export formatting (verify specific output)

4. **Error Conditions**
   - Invalid CIDR notation handling
   - Concurrent scan prevention
   - Database connection failures
   - Network timeout scenarios

### Property-Based Testing Configuration

Property tests will use **Hypothesis** (Python's property-based testing library) with the following configuration:

- **Minimum 100 iterations** per property test (due to randomization)
- **Test tagging**: Each property test references its design document property
- **Tag format**: `# Feature: network-range-scanner, Property {number}: {property_text}`

### Property Test Implementation

Each correctness property will be implemented as a single property-based test:

**Property 1: CIDR Range Expansion Round Trip**
```python
@given(st.ip_addresses(v=4), st.integers(min_value=8, max_value=30))
@settings(max_examples=100)
def test_cidr_expansion_round_trip(ip, prefix_len):
    # Feature: network-range-scanner, Property 1
    # Test CIDR expansion and reconstruction
```

**Property 4: Network and Broadcast Exclusion**
```python
@given(st.ip_addresses(v=4), st.integers(min_value=8, max_value=30))
@settings(max_examples=100)
def test_network_broadcast_exclusion(ip, prefix_len):
    # Feature: network-range-scanner, Property 4
    # Verify network and broadcast addresses excluded
```

**Property 7: Scan Summary Consistency**
```python
@given(st.lists(st.booleans(), min_size=1, max_size=100))
@settings(max_examples=100)
def test_scan_summary_consistency(online_statuses):
    # Feature: network-range-scanner, Property 7
    # Verify count arithmetic consistency
```

**Property 13: Result Filtering Correctness**
```python
@given(st.lists(st.booleans()), st.lists(st.booleans()), 
       st.sampled_from(['tracked_only', 'discovered_only', 'online_only', 'offline_only']))
@settings(max_examples=100)
def test_result_filtering(online_flags, tracked_flags, filter_type):
    # Feature: network-range-scanner, Property 13
    # Verify filtering returns correct subset
```

### Test Coverage Goals

- **Line coverage**: Minimum 85% for service layer
- **Branch coverage**: Minimum 80% for error handling paths
- **Property coverage**: 100% of correctness properties implemented
- **Integration coverage**: All external service integrations mocked and tested

### Testing Tools

- **pytest**: Test runner and framework
- **Hypothesis**: Property-based testing library
- **pytest-django**: Django-specific test utilities
- **factory_boy**: Test data generation for models
- **freezegun**: Time mocking for timestamp tests
- **responses**: HTTP mocking for external calls

### Continuous Integration

All tests (unit + property) will run on:
- Every commit to feature branch
- Pull request creation/update
- Pre-merge validation
- Nightly full test suite execution

Property tests with failures will report the minimal failing example for debugging.
