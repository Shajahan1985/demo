# Asset Tracker - Django Asset Management System

## Project Overview

This Django project implements a comprehensive asset tracking system with authentication, authorization, and advanced asset management features including bulk import, export, and filtering capabilities.

### Initial Setup Completed

1. **Django Project Created**: `asset_tracker`
2. **Authentication App Created**: `authentication`
3. **Database Initialized**: SQLite database with all migrations applied
4. **Default Roles Created**: Admin, Manager, User
5. **Superuser Created**: 
   - Username: `admin`
   - Password: `admin123`
   - Email: `admin@assettracker.com`

### Quick Start

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Configure Environment

Copy `.env.example` to `.env` and configure for your environment:

```bash
cp .env.example .env
```

For development, the default `.env` file is already configured.

#### 3. Run Migrations

```bash
python manage.py migrate
```

This will create the database and default roles (Admin, Manager, User).

#### 4. Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

#### 5. Run Development Server

```bash
python manage.py runserver
```

Access the application at `http://localhost:8000/`

### Configuration

The project uses environment variables for configuration. See `.env.example` for all available options.

#### Key Settings

##### Authentication Settings
- Login URL: `/login/`
- Login redirect: `/dashboard/`
- Logout redirect: `/login/`

##### Session Settings
- Session timeout: 2 weeks (configurable via `SESSION_COOKIE_AGE`)
- Session saved on every request
- Secure session cookies (HTTP-only, SameSite=Lax)
- CSRF protection enabled

##### Security Settings
- Password hashing: PBKDF2 with SHA256 (Django default)
- Minimum password length: 8 characters
- Password validation enabled
- CSRF protection on all forms
- XSS protection enabled
- Clickjacking protection enabled

##### Email Backend
- Development: Console backend (emails printed to console)
- Production: Configure SMTP settings in `.env`
- Password reset timeout: 1 hour (configurable)

### Default Roles

The system includes three default roles created during migration:

1. **Admin**: Full access to user and role management
   - Can create, view, edit, and delete users
   - Can create, view, edit, and delete roles
   - 8 permissions total

2. **Manager**: Can view users and manage assets
   - Can view users and roles
   - 2 permissions total

3. **User**: Basic user access
   - Can be extended with asset management permissions
   - 0 default permissions

### Security Features

- **Password Security**: PBKDF2 password hashing with SHA256
- **Session Security**: Secure, HTTP-only session cookies
- **CSRF Protection**: Enabled on all forms
- **XSS Protection**: Template auto-escaping enabled
- **Clickjacking Protection**: X-Frame-Options set to DENY
- **Input Validation**: Comprehensive form validation
- **Authentication Logging**: Failed login attempts logged
- **Permission-Based Access Control**: Role-based and individual permissions

### Testing

Run the test suite:

```bash
# Run all tests
python manage.py test

# Run with coverage
pytest --cov=assets --cov=authentication

# Run property-based tests
pytest assets/tests/ -v

# Run specific test file
pytest assets/tests/test_import_service.py -v
```

#### Test Coverage

The project includes comprehensive testing:
- **Unit Tests**: Test individual functions and methods
- **Property-Based Tests**: Test universal properties with random data (using Hypothesis)
- **Integration Tests**: Test complete workflows end-to-end

Key test areas:
- Import validation and error handling
- Export data completeness and format
- Filter composition and correctness
- Authentication and permissions
- Asset lifecycle management

### Deployment

For production deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

**Important**: Before deploying to production:
- Set `DEBUG=False` in `.env`
- Generate a new `SECRET_KEY`
- Configure `ALLOWED_HOSTS`
- Enable HTTPS and set security cookies to secure
- Configure production database (PostgreSQL/MySQL)
- Set up proper email backend
- Review all security settings

## Asset Management Features

### Excel Import (Admin Only)

Administrators can bulk import assets from Excel files to quickly add multiple assets to the system.

#### Import Instructions

1. **Access Import Page**: Navigate to `/assets/import/` or click "Import Assets" in the navigation menu (admin only)

2. **Download Template**: Click "Download Sample Template" to get a properly formatted Excel file

3. **Prepare Your Data**: Fill in the Excel file with your asset data:
   - **Required Columns**:
     - `asset_tag`: Unique identifier (e.g., BIDC001)
     - `system_type`: Desktop, Laptop, or All-in-One PC
     - `operating_system`: Must match an existing OS in the system
     - `ip_address`: Valid IPv4 address that is not already assigned
   
   - **Optional Columns**:
     - `particulars`: Additional notes or specifications
     - `assigned_to`: Name of person assigned to the asset
     - `team`: Must match an existing team in the system
     - `warranty_expiration`: Date in YYYY-MM-DD format

4. **Upload File**: Select your Excel file (.xlsx or .xls, max 10MB) and click "Import Assets"

5. **Review Results**: The system will display:
   - Number of successfully imported assets
   - Number of rows with errors
   - Detailed error list showing row numbers and specific issues

#### Import Validation Rules

- **Asset Tag**: Must be unique across all assets
- **System Type**: Must be exactly "Desktop", "Laptop", or "All-in-One PC"
- **Operating System**: Must exist in the database (create OS first if needed)
- **IP Address**: Must be valid IPv4 format and not already assigned
- **Team**: Must exist in the database if provided
- **Warranty Date**: Must be in YYYY-MM-DD format if provided

#### Import Error Handling

- Invalid rows are skipped and reported in the error list
- Valid rows are imported successfully even if some rows have errors
- Each error includes the row number, asset data, and specific error message
- Common errors:
  - "Asset tag already exists" - Use a unique asset tag
  - "Operating System not found" - Create the OS first or check spelling
  - "Team not found" - Create the team first or check spelling
  - "IP address not available" - IP is already assigned or invalid format
  - "Invalid system type" - Must be Desktop, Laptop, or All-in-One PC
  - "Invalid date format" - Use YYYY-MM-DD format

### Excel Export (All Authenticated Users)

Export asset data to Excel for reporting, analysis, or backup purposes.

#### Available Exports

1. **Active Assets** (`/assets/export/active/`)
   - All assets with status='active'
   - Columns: Serial Number, Asset Tag, System Type, OS, IP Address, Assigned To, Team, Warranty Expiration
   - Filename: `active_assets.xlsx`
   - Ordered by serial number

2. **Freed Assets** (`/assets/export/freed/`)
   - All assets with status='freed' (available for reassignment)
   - Columns: Serial Number, Asset Tag, System Type, OS, IP Address, Freed Date
   - Filename: `freed_assets.xlsx`
   - Ordered by freed date (most recent first)

3. **Scrapped Assets** (`/assets/export/scrapped/`)
   - All assets with status='scrapped' (permanently removed)
   - Columns: Serial Number, Asset Tag, System Type, OS, IP Address, Scrapped Date
   - Filename: `scrapped_assets.xlsx`
   - Ordered by scrapped date (most recent first)

4. **Free IP Addresses** (`/ips/export/free/`)
   - All unassigned IP addresses
   - Columns: IP Address, IP Range
   - Filename: `free_ips.xlsx`
   - Grouped by IP range and ordered numerically

#### Export Instructions

1. Navigate to the relevant page (asset list, freed systems, scrapped items, or free IPs)
2. Click the "Export to Excel" button
3. The Excel file will download automatically
4. Open in Excel, LibreOffice, or Google Sheets

### Asset Filtering

Filter the asset list to quickly find specific assets based on multiple criteria.

#### Available Filters

1. **Operating System**: Dropdown list of all available operating systems
2. **Asset Tag**: Text search (partial match, case-insensitive)
3. **Team**: Dropdown list of all teams
4. **Assigned To**: Text search for user names (partial match, case-insensitive)

#### Filter Instructions

1. **Apply Single Filter**:
   - Select or enter your filter criteria
   - Click "Apply Filters"
   - Results update to show only matching assets

2. **Apply Multiple Filters**:
   - Set multiple filter criteria
   - Click "Apply Filters"
   - Results show assets matching ALL criteria (AND logic)
   - Example: OS="Windows 10" AND Team="Engineering" shows only Windows 10 assets assigned to Engineering

3. **Clear Filters**:
   - Click "Clear Filters" button to remove all filter criteria
   - Returns to showing all active assets

4. **Filter Persistence**:
   - Filter values are preserved in the URL
   - Bookmark filtered views for quick access
   - Filters remain active when navigating back to the page

#### Filter Examples

- Find all Windows 10 laptops: Set OS="Windows 10", leave others empty
- Find assets assigned to John: Enter "John" in Assigned To field
- Find Engineering team's Windows assets: Set Team="Engineering" and OS="Windows 10"
- Find specific asset: Enter "BIDC123" in Asset Tag field

### Project Structure

```
asset_tracker/
├── asset_tracker/          # Project settings
│   ├── settings.py        # Main settings (uses environment variables)
│   ├── urls.py            # URL configuration
│   └── wsgi.py            # WSGI configuration
├── assets/                 # Asset management app
│   ├── forms/             # Form definitions
│   │   ├── import_form.py # Excel import form
│   │   └── filter_form.py # Asset filter form
│   ├── services/          # Business logic
│   │   ├── import_service.py  # Excel import handling
│   │   ├── export_service.py  # Excel export generation
│   │   └── filter_service.py  # Asset filtering logic
│   ├── templates/         # HTML templates
│   ├── views.py           # View logic
│   ├── models.py          # Data models
│   └── tests/             # Test suite
├── authentication/         # Authentication app
│   ├── migrations/        # Database migrations
│   ├── templates/         # HTML templates
│   ├── views.py           # View logic
│   ├── forms.py           # Form definitions
│   └── tests.py           # Test suite
├── media/
│   └── templates/         # Excel import templates
├── .env                   # Environment variables (not in git)
├── .env.example           # Example environment configuration
├── requirements.txt       # Python dependencies
├── DEPLOYMENT.md          # Deployment guide
└── README.md              # This file
```

### Environment Variables

Key environment variables (see `.env.example` for complete list):

- `SECRET_KEY`: Django secret key (required)
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DATABASE_ENGINE`: Database engine (sqlite3/postgresql/mysql)
- `SESSION_COOKIE_SECURE`: Secure session cookies (True in production)
- `CSRF_COOKIE_SECURE`: Secure CSRF cookies (True in production)
- `EMAIL_BACKEND`: Email backend configuration
- `EMAIL_HOST`: SMTP server host
- `EMAIL_PORT`: SMTP server port

### Dependencies

Key Python packages:

- **Django 4.2+**: Web framework
- **openpyxl 3.1.2+**: Excel file reading and writing (.xlsx, .xls)
- **psycopg2-binary**: PostgreSQL database adapter
- **python-decouple**: Environment variable management
- **celery**: Task scheduling for warranty notifications
- **redis**: Celery message broker
- **Pillow**: Image handling for asset attachments
- **pytest**: Testing framework
- **hypothesis**: Property-based testing
- **pytest-django**: Django integration for pytest

Install all dependencies:
```bash
pip install -r requirements.txt
```

### Logging

Application logs are written to `authentication.log` in the project root.

Log levels:
- INFO: Successful operations
- WARNING: Authentication failures
- ERROR: System errors

### Next Steps

For detailed information about specific features:
- **Import/Export/Filtering**: See [ASSET_MANAGEMENT_GUIDE.md](ASSET_MANAGEMENT_GUIDE.md)
- **Excel Import Format**: See [EXCEL_IMPORT_FORMAT.md](EXCEL_IMPORT_FORMAT.md)
- **Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Deployment Checklist**: See [DEPLOYMENT_CHECKLIST_IMPORT_EXPORT.md](DEPLOYMENT_CHECKLIST_IMPORT_EXPORT.md)

Refer to `.kiro/specs/` for detailed implementation specifications.

### Support

For deployment issues, see [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section.
