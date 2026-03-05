# Asset Tracker - Django Authentication System

## Project Setup

This Django project implements a comprehensive authentication and authorization system for a multi-user asset tracker application.

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
pytest --cov=authentication

# Run property-based tests
pytest authentication/tests.py -v
```

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

### Project Structure

```
asset_tracker/
├── asset_tracker/          # Project settings
│   ├── settings.py        # Main settings (uses environment variables)
│   ├── urls.py            # URL configuration
│   └── wsgi.py            # WSGI configuration
├── authentication/         # Authentication app
│   ├── migrations/        # Database migrations
│   ├── templates/         # HTML templates
│   ├── views.py           # View logic
│   ├── forms.py           # Form definitions
│   ├── urls.py            # App URL patterns
│   └── tests.py           # Test suite
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

### Logging

Application logs are written to `authentication.log` in the project root.

Log levels:
- INFO: Successful operations
- WARNING: Authentication failures
- ERROR: System errors

### Next Steps

Refer to `.kiro/specs/django-auth-permissions/tasks.md` for the implementation plan.

### Support

For deployment issues, see [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section.
