# Deployment Guide

This guide provides step-by-step instructions for deploying the Asset Tracker Django application to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Security Settings](#security-settings)
4. [Database Setup](#database-setup)
5. [Static Files](#static-files)
6. [Email Configuration](#email-configuration)
7. [Initial Data Setup](#initial-data-setup)
8. [Production Server Setup](#production-server-setup)
9. [Post-Deployment Checklist](#post-deployment-checklist)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

- Python 3.10 or higher
- PostgreSQL or MySQL database (recommended for production)
- Web server (Nginx or Apache)
- WSGI server (Gunicorn or uWSGI)
- SSL certificate for HTTPS
- SMTP server for email functionality
- Domain name configured

---

## Environment Configuration

### 1. Create Environment File

Copy the example environment file and configure it for production:

```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file with production values:

```bash
# Django Settings
SECRET_KEY=your-very-long-random-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration (PostgreSQL example)
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=assettracker_db
DATABASE_USER=assettracker_user
DATABASE_PASSWORD=strong-database-password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Security Settings (MUST be True in production)
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000

# Session Configuration
SESSION_COOKIE_AGE=1209600
SESSION_EXPIRE_AT_BROWSER_CLOSE=False

# Email Configuration (SMTP example)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Password Reset
PASSWORD_RESET_TIMEOUT=3600
```

### 3. Generate Secret Key

Generate a new secret key for production:

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and set it as `SECRET_KEY` in your `.env` file.

---

## Security Settings

### Critical Security Checklist

Ensure these settings are configured in your `.env` file:

- ✅ `DEBUG=False` - Never run with DEBUG=True in production
- ✅ `SECRET_KEY` - Use a unique, random secret key
- ✅ `ALLOWED_HOSTS` - Set to your domain(s)
- ✅ `SESSION_COOKIE_SECURE=True` - Requires HTTPS
- ✅ `CSRF_COOKIE_SECURE=True` - Requires HTTPS
- ✅ `SECURE_SSL_REDIRECT=True` - Redirect HTTP to HTTPS
- ✅ `SECURE_HSTS_SECONDS=31536000` - Enable HSTS for 1 year

### Password Security

The application uses Django's PBKDF2 password hasher by default, which is secure and recommended. The configuration in `settings.py` includes:

```python
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]
```

Password validation enforces:
- Minimum length of 8 characters
- Not too similar to user attributes
- Not a commonly used password
- Not entirely numeric

---

## Database Setup

### PostgreSQL (Recommended)

1. **Install PostgreSQL**:
   ```bash
   sudo apt-get install postgresql postgresql-contrib
   ```

2. **Create Database and User**:
   ```bash
   sudo -u postgres psql
   ```
   
   ```sql
   CREATE DATABASE assettracker_db;
   CREATE USER assettracker_user WITH PASSWORD 'strong-database-password';
   ALTER ROLE assettracker_user SET client_encoding TO 'utf8';
   ALTER ROLE assettracker_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE assettracker_user SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE assettracker_db TO assettracker_user;
   \q
   ```

3. **Install PostgreSQL Python Adapter**:
   ```bash
   pip install psycopg2-binary
   ```

4. **Update .env**:
   ```bash
   DATABASE_ENGINE=django.db.backends.postgresql
   DATABASE_NAME=assettracker_db
   DATABASE_USER=assettracker_user
   DATABASE_PASSWORD=strong-database-password
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   ```

### MySQL (Alternative)

1. **Install MySQL**:
   ```bash
   sudo apt-get install mysql-server
   ```

2. **Create Database and User**:
   ```bash
   sudo mysql
   ```
   
   ```sql
   CREATE DATABASE assettracker_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'assettracker_user'@'localhost' IDENTIFIED BY 'strong-database-password';
   GRANT ALL PRIVILEGES ON assettracker_db.* TO 'assettracker_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

3. **Install MySQL Python Adapter**:
   ```bash
   pip install mysqlclient
   ```

4. **Update .env**:
   ```bash
   DATABASE_ENGINE=django.db.backends.mysql
   DATABASE_NAME=assettracker_db
   DATABASE_USER=assettracker_user
   DATABASE_PASSWORD=strong-database-password
   DATABASE_HOST=localhost
   DATABASE_PORT=3306
   ```

---

## Static Files

### 1. Configure Static Files Settings

Add to `settings.py` (if not already present):

```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
```

### 2. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 3. Configure Web Server

**Nginx Example**:

```nginx
location /static/ {
    alias /path/to/your/project/staticfiles/;
}
```

---

## Email Configuration

### Gmail SMTP (Development/Small Scale)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**: Google Account → Security → App passwords
3. **Configure .env**:
   ```bash
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-16-char-app-password
   DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

### SendGrid (Production Recommended)

1. **Sign up for SendGrid** and get API key
2. **Install SendGrid**:
   ```bash
   pip install sendgrid
   ```
3. **Configure .env**:
   ```bash
   EMAIL_BACKEND=sendgrid_backend.SendgridBackend
   SENDGRID_API_KEY=your-sendgrid-api-key
   DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

### AWS SES (Enterprise)

1. **Configure AWS SES** and verify domain
2. **Install boto3**:
   ```bash
   pip install boto3
   ```
3. **Configure .env**:
   ```bash
   EMAIL_BACKEND=django_ses.SESBackend
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_SES_REGION_NAME=us-east-1
   DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

---

## Initial Data Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The requirements include `openpyxl>=3.1.2` for Excel import/export functionality.

### 2. Run Migrations

```bash
python manage.py migrate
```

This will:
- Create all database tables
- Run the initial data migration to create default roles (Admin, Manager, User)

### 3. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 4. Verify Default Roles

Log into Django admin and verify that the following roles exist:
- **Admin**: Full access to user and role management
- **Manager**: Can view users and manage assets
- **User**: Basic user access

### 5. Set Up Excel Import Template (Optional)

The system includes a sample Excel import template. Ensure the `media/templates/` directory exists:

```bash
mkdir -p media/templates
```

The sample template will be available for download from the import page.

---

## Production Server Setup

### Option 1: Gunicorn + Nginx

#### 1. Install Gunicorn

```bash
pip install gunicorn
```

#### 2. Create Gunicorn Service

Create `/etc/systemd/system/assettracker.service`:

```ini
[Unit]
Description=Asset Tracker Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/project
Environment="PATH=/path/to/your/venv/bin"
ExecStart=/path/to/your/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/path/to/your/project/assettracker.sock \
          asset_tracker.wsgi:application

[Install]
WantedBy=multi-user.target
```

#### 3. Start Gunicorn

```bash
sudo systemctl start assettracker
sudo systemctl enable assettracker
```

#### 4. Configure Nginx

Create `/etc/nginx/sites-available/assettracker`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/your/project/assettracker.sock;
    }
}
```

#### 5. Enable Site and Restart Nginx

```bash
sudo ln -s /etc/nginx/sites-available/assettracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Option 2: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "asset_tracker.wsgi:application"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: assettracker_db
      POSTGRES_USER: assettracker_user
      POSTGRES_PASSWORD: strong-database-password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: gunicorn asset_tracker.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

  nginx:
    image: nginx:latest
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
```

#### 3. Deploy

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## Post-Deployment Checklist

After deployment, verify the following:

### Security Verification

- [ ] `DEBUG=False` in production
- [ ] Unique `SECRET_KEY` set
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] HTTPS enabled and working
- [ ] SSL certificate valid
- [ ] HSTS headers present
- [ ] Session cookies secure
- [ ] CSRF cookies secure

### Functionality Verification

- [ ] Can access login page
- [ ] Can log in with superuser account
- [ ] Can create new users
- [ ] Can assign roles to users
- [ ] Password reset emails sending
- [ ] Static files loading correctly
- [ ] All pages accessible
- [ ] Permission checks working
- [ ] Excel import page accessible (admin only)
- [ ] Excel export buttons visible (all authenticated users)
- [ ] Asset filtering working correctly
- [ ] Sample import template downloadable

### Database Verification

- [ ] Database migrations applied
- [ ] Default roles created (Admin, Manager, User)
- [ ] Superuser account created
- [ ] Database backups configured

### Monitoring Setup

- [ ] Error logging configured
- [ ] Authentication failure logging working
- [ ] Server monitoring in place
- [ ] Database monitoring in place
- [ ] Backup strategy implemented

---

## Troubleshooting

### Common Issues

#### 1. Static Files Not Loading

**Problem**: CSS/JS files return 404

**Solution**:
```bash
python manage.py collectstatic --noinput
```

Verify Nginx/Apache configuration for static files.

#### 2. Database Connection Errors

**Problem**: Can't connect to database

**Solution**:
- Verify database credentials in `.env`
- Check database service is running
- Verify database user has correct permissions
- Check firewall rules

#### 3. Email Not Sending

**Problem**: Password reset emails not arriving

**Solution**:
- Verify SMTP credentials in `.env`
- Check email backend configuration
- Test with console backend first:
  ```bash
  EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
  ```
- Check spam folder
- Verify SMTP server allows connections

#### 4. Permission Denied Errors

**Problem**: 403 errors when accessing pages

**Solution**:
- Verify user has correct role assigned
- Check role has required permissions
- Review permission checks in views
- Check authentication middleware is active

#### 5. Session Issues

**Problem**: Users logged out unexpectedly

**Solution**:
- Verify `SESSION_COOKIE_AGE` setting
- Check `SESSION_EXPIRE_AT_BROWSER_CLOSE` setting
- Ensure session backend is working
- Check for session cleanup tasks

#### 6. Excel Import Not Working

**Problem**: Import page returns errors or file upload fails

**Solution**:
- Verify `openpyxl` is installed: `pip install openpyxl>=3.1.2`
- Check file size is under 10MB
- Verify file format is .xlsx or .xls
- Check `media/templates/` directory exists and is writable
- Review import error messages for specific validation issues
- Ensure Operating Systems and Teams exist before importing

#### 7. Excel Export Not Downloading

**Problem**: Export button doesn't trigger download

**Solution**:
- Verify user is authenticated
- Check browser console for JavaScript errors
- Verify export view URLs are configured correctly
- Check that `openpyxl` is installed
- Review server logs for errors during export generation

#### 8. Asset Filters Not Working

**Problem**: Filters don't narrow down results

**Solution**:
- Verify "Apply Filters" button is clicked
- Check that filter form is submitting correctly
- Review browser console for JavaScript errors
- Verify FilterService is properly configured
- Check database indexes on filtered fields

### Logs

Check application logs for errors:

```bash
# Application log
tail -f authentication.log

# Gunicorn log
sudo journalctl -u assettracker -f

# Nginx error log
sudo tail -f /var/log/nginx/error.log
```

---

## Maintenance

### Regular Tasks

1. **Database Backups**:
   ```bash
   # PostgreSQL
   pg_dump assettracker_db > backup_$(date +%Y%m%d).sql
   
   # MySQL
   mysqldump -u assettracker_user -p assettracker_db > backup_$(date +%Y%m%d).sql
   ```

2. **Clear Expired Sessions**:
   ```bash
   python manage.py clearsessions
   ```

3. **Update Dependencies**:
   ```bash
   pip install --upgrade -r requirements.txt
   python manage.py migrate
   ```

4. **Monitor Logs**:
   - Review authentication failures
   - Check for unusual activity
   - Monitor error rates

### Security Updates

- Keep Django and dependencies updated
- Monitor security advisories
- Review and rotate credentials regularly
- Audit user permissions periodically

---

## Support

For issues or questions:
- Check Django documentation: https://docs.djangoproject.com/
- Review application logs
- Contact system administrator

---

## Version History

- **v1.0** - Initial deployment guide
- Date: 2025-12-04
