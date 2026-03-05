# Asset Tracking System - Design Document

## Overview

The Asset Tracking System is a Django-based web application that manages IT assets (computers and systems) throughout their lifecycle within an organization. The system provides comprehensive tracking of asset details, IP address management, warranty monitoring, and lifecycle state management (active, freed, scrapped). The application enforces admin-only permissions for critical operations and provides multiple specialized views for different aspects of asset management.

## Architecture

The application follows Django's MVT (Model-View-Template) architecture with additional service layers:

1. **Models Layer**: Django ORM models for data persistence (Asset, IPAddress, OperatingSystem, Team, IPRange, Attachment)
2. **Views Layer**: Django views handling HTTP requests and responses
3. **Templates Layer**: HTML templates for rendering pages
4. **Services Layer**: Business logic for asset operations, IP management, and warranty checking
5. **Permissions Layer**: Django permissions and decorators for admin-only operations
6. **Background Tasks Layer**: Scheduled tasks for warranty expiration alerts

The architecture ensures separation of concerns, maintainability, and testability.

## Components and Interfaces

### 1. Models

#### Asset Model
- **Responsibility**: Represent IT assets with all tracking information
- **Fields**:
  - `serial_number` (AutoField, primary key)
  - `asset_tag` (CharField, unique, format: "BIDC + number")
  - `system_type` (CharField, choices: Desktop/Laptop/All-in-One PC)
  - `operating_system` (ForeignKey to OperatingSystem)
  - `ip_address` (ForeignKey to IPAddress, nullable)
  - `particulars` (TextField, nullable)
  - `assigned_to` (CharField, nullable)
  - `team` (ForeignKey to Team, nullable)
  - `status` (CharField, choices: active/freed/scrapped)
  - `warranty_expiration` (DateField, nullable)
  - `freed_date` (DateTimeField, nullable)
  - `scrapped_date` (DateTimeField, nullable)
  - `created_at` (DateTimeField, auto_now_add)
  - `updated_at` (DateTimeField, auto_now)

#### IPAddress Model
- **Responsibility**: Track IP addresses and their assignment status
- **Fields**:
  - `address` (GenericIPAddressField, unique, protocol='IPv4')
  - `ip_range` (ForeignKey to IPRange)
  - `is_assigned` (BooleanField, default=False)
  - `assigned_to_asset` (ForeignKey to Asset, nullable)

#### OperatingSystem Model
- **Responsibility**: Store available operating systems
- **Fields**:
  - `name` (CharField, unique)
  - `created_at` (DateTimeField, auto_now_add)

#### Team Model
- **Responsibility**: Store organizational teams
- **Fields**:
  - `name` (CharField, unique)
  - `created_at` (DateTimeField, auto_now_add)

#### IPRange Model
- **Responsibility**: Define IP address ranges
- **Fields**:
  - `range_pattern` (CharField, unique, e.g., "192.168.10.x")
  - `network_prefix` (CharField, e.g., "192.168.10")
  - `created_at` (DateTimeField, auto_now_add)

#### Attachment Model
- **Responsibility**: Store file attachments for assets
- **Fields**:
  - `asset` (ForeignKey to Asset)
  - `file` (FileField)
  - `filename` (CharField)
  - `uploaded_at` (DateTimeField, auto_now_add)

### 2. Views

#### AssetListView
- **Responsibility**: Display active assets
- **Interface**:
  - `GET /assets/` - List all active assets
  - Context: `assets` (queryset of active assets ordered by serial_number)

#### FreeSystemsView
- **Responsibility**: Display freed assets
- **Interface**:
  - `GET /assets/freed/` - List all freed assets
  - Context: `freed_assets` (queryset of freed assets)

#### ScrappedItemsView
- **Responsibility**: Display scrapped assets
- **Interface**:
  - `GET /assets/scrapped/` - List all scrapped assets ordered by scrapped_date desc
  - Context: `scrapped_assets` (queryset)

#### FreeIPsView
- **Responsibility**: Display free IP addresses grouped by range
- **Interface**:
  - `GET /ips/free/` - List all unassigned IPs grouped by range
  - Context: `ip_ranges` (dict mapping range to list of free IPs)

#### WarrantyView
- **Responsibility**: Display assets with warranty information
- **Interface**:
  - `GET /assets/warranty/` - List all assets with warranty dates
  - Context: `assets` (queryset ordered by warranty_expiration), `expiring_soon` (assets expiring within 7 days)

#### AssetCreateView
- **Responsibility**: Handle asset creation (admin only)
- **Interface**:
  - `GET /assets/create/` - Display asset creation form
  - `POST /assets/create/` - Process asset creation
  - Permissions: `@admin_required`

#### AssetUpdateView
- **Responsibility**: Handle asset updates (admin only)
- **Interface**:
  - `GET /assets/<id>/edit/` - Display asset edit form
  - `POST /assets/<id>/edit/` - Process asset update
  - Permissions: `@admin_required`

#### AssetFreeView
- **Responsibility**: Handle freeing assets (admin only)
- **Interface**:
  - `POST /assets/<id>/free/` - Free an asset (requires password confirmation)
  - Permissions: `@admin_required`

#### AssetScrapView
- **Responsibility**: Handle scrapping freed assets (admin only)
- **Interface**:
  - `POST /assets/<id>/scrap/` - Scrap a freed asset
  - Permissions: `@admin_required`

### 3. Services

#### AssetService
- **Responsibility**: Business logic for asset operations
- **Interface**:
  - `create_asset(data: dict, user: User) -> Asset` - Create new asset with validation
  - `update_asset(asset: Asset, data: dict, user: User) -> Asset` - Update asset with IP management
  - `free_asset(asset: Asset, user: User, password: str) -> Asset` - Free asset and release IP
  - `scrap_asset(asset: Asset, user: User) -> Asset` - Move freed asset to scrapped
  - `validate_asset_tag(asset_tag: str) -> bool` - Validate asset tag uniqueness
  - `get_active_assets() -> QuerySet` - Retrieve active assets
  - `get_freed_assets() -> QuerySet` - Retrieve freed assets
  - `get_scrapped_assets() -> QuerySet` - Retrieve scrapped assets

#### IPManagementService
- **Responsibility**: Manage IP address assignments and availability
- **Interface**:
  - `assign_ip(ip_address: IPAddress, asset: Asset) -> None` - Mark IP as assigned
  - `release_ip(ip_address: IPAddress) -> None` - Mark IP as free
  - `get_free_ips_by_range() -> dict` - Get free IPs grouped by range
  - `get_available_ips() -> QuerySet` - Get all unassigned IPs
  - `change_asset_ip(asset: Asset, new_ip: IPAddress) -> None` - Change IP and update states

#### WarrantyService
- **Responsibility**: Monitor and alert on warranty expirations
- **Interface**:
  - `check_expiring_warranties() -> QuerySet` - Find assets expiring within 7 days
  - `send_warranty_alerts(assets: QuerySet) -> None` - Send email alerts to admins
  - `get_warranty_status(asset: Asset) -> str` - Return 'active', 'expiring_soon', or 'expired'
  - `run_daily_check() -> None` - Scheduled task to check and alert

#### AttachmentService
- **Responsibility**: Manage file attachments for assets
- **Interface**:
  - `upload_attachment(asset: Asset, file: File) -> Attachment` - Store file and create record
  - `delete_attachment(attachment: Attachment) -> None` - Remove file and record
  - `get_asset_attachments(asset: Asset) -> QuerySet` - Retrieve all attachments for asset

### 4. Permissions

#### AdminRequiredMixin
- **Responsibility**: Enforce admin-only access to views
- **Interface**:
  - `dispatch(request, *args, **kwargs)` - Check user is admin before allowing access
  - Raises: `PermissionDenied` if user is not admin

#### admin_required decorator
- **Responsibility**: Decorator for function-based views requiring admin access
- **Interface**:
  - `@admin_required` - Wraps view function to check admin status

## Data Models

### Database Schema

**Table: assets_asset**
- `serial_number` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `asset_tag` (VARCHAR(50) UNIQUE NOT NULL)
- `system_type` (VARCHAR(20) NOT NULL)
- `operating_system_id` (INTEGER FOREIGN KEY)
- `ip_address_id` (INTEGER FOREIGN KEY NULL)
- `particulars` (TEXT NULL)
- `assigned_to` (VARCHAR(100) NULL)
- `team_id` (INTEGER FOREIGN KEY NULL)
- `status` (VARCHAR(20) NOT NULL DEFAULT 'active')
- `warranty_expiration` (DATE NULL)
- `freed_date` (DATETIME NULL)
- `scrapped_date` (DATETIME NULL)
- `created_at` (DATETIME NOT NULL)
- `updated_at` (DATETIME NOT NULL)

**Table: assets_ipaddress**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `address` (VARCHAR(15) UNIQUE NOT NULL)
- `ip_range_id` (INTEGER FOREIGN KEY NOT NULL)
- `is_assigned` (BOOLEAN DEFAULT FALSE)
- `assigned_to_asset_id` (INTEGER FOREIGN KEY NULL)

**Table: assets_operatingsystem**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `name` (VARCHAR(100) UNIQUE NOT NULL)
- `created_at` (DATETIME NOT NULL)

**Table: assets_team**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `name` (VARCHAR(100) UNIQUE NOT NULL)
- `created_at` (DATETIME NOT NULL)

**Table: assets_iprange**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `range_pattern` (VARCHAR(20) UNIQUE NOT NULL)
- `network_prefix` (VARCHAR(15) NOT NULL)
- `created_at` (DATETIME NOT NULL)

**Table: assets_attachment**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `asset_id` (INTEGER FOREIGN KEY NOT NULL)
- `file` (VARCHAR(255) NOT NULL)
- `filename` (VARCHAR(255) NOT NULL)
- `uploaded_at` (DATETIME NOT NULL)

### Indexes
- `assets_asset.asset_tag` (unique index)
- `assets_asset.status` (index for filtering)
- `assets_asset.warranty_expiration` (index for warranty queries)
- `assets_ipaddress.address` (unique index)
- `assets_ipaddress.is_assigned` (index for free IP queries)


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Asset creation completeness
*For any* valid asset data (with asset_tag, system_type, OS, IP, particulars, assigned_to, and team), creating an asset should result in an asset record containing all the provided fields.
**Validates: Requirements 1.1**

### Property 2: Asset tag uniqueness enforcement
*For any* existing asset with asset_tag A, attempting to create another asset with the same asset_tag A should be rejected with an error.
**Validates: Requirements 1.2**

### Property 3: Sequential serial number assignment
*For any* sequence of asset creations, each new asset should receive a serial number greater than all previously assigned serial numbers.
**Validates: Requirements 1.3**

### Property 4: IP assignment state transition
*For any* free IP address, when assigned to a new asset, the IP should be marked as in use and no longer appear in the free IPs list.
**Validates: Requirements 1.4, 8.3**

### Property 5: Admin-only operation enforcement
*For any* non-admin user attempting to perform add, edit, free, or scrap operations, the system should deny access and return an authorization error.
**Validates: Requirements 1.5, 2.4, 3.6, 6.4**

### Property 6: Asset update data integrity
*For any* asset and any subset of updatable fields, updating those fields should preserve all other fields unchanged.
**Validates: Requirements 2.1**

### Property 7: IP change state management
*For any* asset with IP address A, when changed to IP address B, IP A should become free and IP B should become assigned.
**Validates: Requirements 2.2**

### Property 8: Attachment preservation during updates
*For any* asset with attachments, updating non-attachment fields should preserve all existing attachments.
**Validates: Requirements 2.3**

### Property 9: Asset freeing state transition
*For any* active asset, when freed with correct admin password, the asset should move to freed status, appear on Free Systems page, not appear on Active Assets page, and have assigned_to and team fields cleared.
**Validates: Requirements 3.3, 3.5**

### Property 10: IP release on asset freeing
*For any* asset with an assigned IP address, when the asset is freed, the IP should be released and appear in the Free IPs page under the appropriate range.
**Validates: Requirements 3.4, 8.4**

### Property 11: Active assets view completeness
*For any* active asset in the system, querying the active assets list should return that asset with all fields (serial_number, asset_tag, system_type, OS, IP, assigned_to, team) present.
**Validates: Requirements 4.1**

### Property 12: View state isolation
*For any* database state containing active, freed, and scrapped assets, the active assets view should only show active assets, the freed systems view should only show freed assets, and the scrapped items view should only show scrapped assets.
**Validates: Requirements 4.2, 5.3**

### Property 13: Active assets ordering
*For any* set of active assets, the active assets list should be ordered by serial_number in ascending order.
**Validates: Requirements 4.3**

### Property 14: Freed systems view completeness
*For any* freed asset, querying the Free Systems page should return that asset with at least IP address and asset_tag visible.
**Validates: Requirements 5.1**

### Property 15: Asset scrapping state transition
*For any* freed asset, when scrapped by an admin, the asset should move to scrapped status, appear on Scrapped Items page, not appear on Free Systems page, have a scrapped_date recorded, and retain asset_tag and IP information.
**Validates: Requirements 6.1, 6.2, 6.3**

### Property 16: Scrapped items view completeness and ordering
*For any* set of scrapped assets, the Scrapped Items page should display all of them with asset_tag, IP address, and scrapped_date, ordered by scrapped_date in descending order.
**Validates: Requirements 7.1, 7.2**

### Property 17: Free IPs grouping by range
*For any* set of free IP addresses from multiple ranges, the Free IPs page should display them grouped by their respective IP ranges (192.168.10.x, 192.168.11.x, 192.168.70.x, 192.168.50.x).
**Validates: Requirements 8.1, 8.2**

### Property 18: Operating system management
*For any* new OS name, adding it should make it available in the OS list, and attempting to add a duplicate OS name should be rejected.
**Validates: Requirements 9.1, 9.3**

### Property 19: Team management
*For any* new team name, adding it should make it available in the teams list, and attempting to add a duplicate team name should be rejected.
**Validates: Requirements 10.1, 10.3**

### Property 20: IP range management
*For any* new IP range pattern, adding it should make IPs from that range available, and attempting to add a duplicate range should be rejected.
**Validates: Requirements 11.1, 11.3**

### Property 21: Attachment upload and association
*For any* asset and any file, uploading the file should store it and associate it with the asset, making it retrievable when querying the asset's attachments.
**Validates: Requirements 12.1, 12.2**

### Property 22: Attachment deletion completeness
*For any* attachment, deleting it should remove both the file from storage and the attachment record from the asset.
**Validates: Requirements 12.3**

### Property 23: Attachment preservation on scrapping
*For any* asset with attachments, scrapping the asset should retain all attachments for historical reference.
**Validates: Requirements 12.4**

### Property 24: Warranty expiration identification
*For any* set of assets with various warranty dates, running the daily check should identify exactly those assets with warranties expiring within 7 days from the current date.
**Validates: Requirements 13.2**

### Property 25: Warranty alert email delivery
*For any* asset with warranty expiring within 7 days, the daily check should trigger an alert email to admin users.
**Validates: Requirements 13.3**

### Property 26: Warranty page completeness and ordering
*For any* set of assets with warranty dates, the Warranty page should display all of them with warranty_expiration dates, ordered by warranty_expiration in ascending order.
**Validates: Requirements 13.4, 13.6**

### Property 27: Warranty expiration status marking
*For any* asset with warranty_expiration date in the past, the Warranty page should mark it as expired.
**Validates: Requirements 13.7**


## Error Handling

### Input Validation Errors
- **Duplicate Asset Tag**: Return HTTP 400 with error message "Asset tag already exists"
- **Missing Required Fields**: Return HTTP 400 with field-specific error messages
- **Invalid IP Address Format**: Return HTTP 400 with "Invalid IP address format"
- **Invalid System Type**: Restrict to choices in model, return HTTP 400 if invalid

### Permission Errors
- **Non-Admin Access**: Return HTTP 403 Forbidden with "Admin access required"
- **Incorrect Password on Free**: Return HTTP 401 with "Incorrect password"

### Database Errors
- **Connection Failure**: Log error, return HTTP 500 with "Database connection error"
- **Integrity Constraint Violation**: Return HTTP 400 with specific constraint error
- **Transaction Failure**: Rollback transaction, log error, return HTTP 500

### File Upload Errors
- **File Too Large**: Return HTTP 413 with "File size exceeds limit"
- **Invalid File Type**: Return HTTP 400 with "File type not allowed"
- **Storage Failure**: Log error, return HTTP 500 with "File upload failed"

### Business Logic Errors
- **Freeing Non-Active Asset**: Return HTTP 400 with "Only active assets can be freed"
- **Scrapping Non-Freed Asset**: Return HTTP 400 with "Only freed assets can be scrapped"
- **Assigning Already-Assigned IP**: Return HTTP 400 with "IP address already in use"

### Email Errors
- **SMTP Connection Failure**: Log error, continue operation (don't block on email failure)
- **Invalid Email Address**: Log warning, skip that recipient

## Testing Strategy

### Unit Testing Framework
The application will use **pytest-django** as the testing framework. Unit tests will cover:

- **Model Methods**: Test model validation, save operations, custom methods
- **View Logic**: Test view responses, context data, redirects with specific examples
- **Service Functions**: Test business logic with specific scenarios
- **Permission Checks**: Test admin-only access enforcement
- **Form Validation**: Test form cleaning and validation logic
- **Edge Cases**: Empty inputs, boundary values, special characters

### Property-Based Testing Framework
The application will use **Hypothesis** with **pytest-django** for property-based testing. Property-based tests will:

- Run a minimum of 100 iterations per property to ensure thorough coverage
- Generate random assets, IPs, teams, OS names with varying values
- Test universal properties across all possible inputs
- Each property-based test must include a comment tag in this format: `# Feature: asset-tracker, Property X: [property description]`
- Each correctness property from this design document must be implemented as a single property-based test
- Property tests should be placed close to implementation to catch errors early

### Integration Testing
- Test complete workflows: create asset → view on active page → free → verify on freed page → scrap → verify on scrapped page
- Test IP management workflows: assign IP → verify not in free list → free asset → verify IP in free list
- Test warranty workflows: create asset with warranty → run daily check → verify email sent
- Test attachment workflows: upload file → verify stored → delete → verify removed

### Test Data Strategy
- **Unit Tests**: Use Django fixtures and factory_boy for specific test cases
- **Property Tests**: Use Hypothesis strategies to generate random valid data
- **Generators**: Create custom Hypothesis strategies for asset_tags (BIDC format), IP addresses (from valid ranges), dates

### Testing Approach
- Write both unit tests and property-based tests for comprehensive coverage
- Unit tests verify specific examples and edge cases work correctly
- Property tests verify general correctness across many random inputs
- Both types of tests are valuable and complement each other
- Use Django's TestCase for database-backed tests
- Use pytest fixtures for common test setup

## Implementation Notes

### Technology Stack
- **Framework**: Django 4.2+
- **Database**: PostgreSQL (production) / SQLite (development)
- **Python**: 3.10+
- **Testing**: pytest-django, Hypothesis, factory_boy
- **Task Scheduling**: Celery with Redis (for warranty alerts)
- **Email**: Django's email backend with SMTP
- **File Storage**: Django's FileField with configurable storage backend

### Django Apps Structure
```
asset_tracker/
├── assets/              # Main app
│   ├── models.py       # All models
│   ├── views.py        # All views
│   ├── services.py     # Business logic services
│   ├── forms.py        # Django forms
│   ├── admin.py        # Django admin configuration
│   ├── permissions.py  # Permission mixins and decorators
│   ├── tasks.py        # Celery tasks for warranty checks
│   └── tests/
│       ├── test_models.py
│       ├── test_views.py
│       ├── test_services.py
│       └── test_properties.py  # Property-based tests
├── templates/
│   └── assets/
│       ├── asset_list.html
│       ├── asset_form.html
│       ├── freed_systems.html
│       ├── scrapped_items.html
│       ├── free_ips.html
│       └── warranty.html
└── static/
    └── assets/
        ├── css/
        └── js/
```

### URL Structure
- `/assets/` - Active assets list
- `/assets/create/` - Create new asset (admin only)
- `/assets/<id>/edit/` - Edit asset (admin only)
- `/assets/<id>/free/` - Free asset (admin only)
- `/assets/freed/` - Freed systems list
- `/assets/<id>/scrap/` - Scrap freed asset (admin only)
- `/assets/scrapped/` - Scrapped items list
- `/ips/free/` - Free IPs grouped by range
- `/assets/warranty/` - Warranty tracking page
- `/admin/` - Django admin for OS, Team, IPRange management

### Authentication and Permissions
- Use Django's built-in authentication system
- Create custom `is_admin` user flag or use Django's `is_staff` flag
- Implement `AdminRequiredMixin` for class-based views
- Implement `@admin_required` decorator for function-based views
- All create/edit/free/scrap operations require admin access

### File Upload Configuration
- Store attachments in `MEDIA_ROOT/asset_attachments/`
- Configure maximum file size (e.g., 10MB)
- Allow common file types: PDF, images (JPG, PNG), documents (DOC, DOCX)
- Generate unique filenames to prevent collisions

### Warranty Alert Configuration
- Schedule Celery task to run daily at configured time (e.g., 9:00 AM)
- Query assets with `warranty_expiration` between today and today + 7 days
- Send single email to all admin users with list of expiring warranties
- Email template includes asset details and days until expiration

### IP Range Initialization
- Create initial IP ranges on first deployment: 192.168.10.x, 192.168.11.x, 192.168.70.x, 192.168.50.x
- Generate all 254 IP addresses (1-254) for each range
- Use Django management command for initialization

### Future Enhancements (Out of Scope)
- Asset history tracking (audit log of all changes)
- Bulk import/export functionality
- Asset depreciation calculations
- QR code generation for asset tags
- Mobile-responsive design improvements
- Advanced search and filtering
- Dashboard with statistics and charts
- Asset reservation system
