# Production Deployment Guide - Asset Tracking System

## Recommended Approach: Waitress + NSSM (Windows Service)

This guide will help you deploy the Asset Tracking System as a production-ready Windows service that starts automatically.

---

## Prerequisites

- Windows Server or Windows 10/11
- Python 3.10+ installed
- Administrator access
- Your project located at: `D:\Asset tracker`

---

## Step 1: Install Waitress

Waitress is a production-ready WSGI server for Python applications.

```bash
pip install waitress
```

---

## Step 2: Update Django Settings for Production

### 2.1 Update `.env` file

```env
# Django Settings
SECRET_KEY=your-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=192.168.11.213,localhost,127.0.0.1,your-domain.com

# Database Configuration
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3

# Security Settings (IMPORTANT for production)
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0

# Session Configuration
SESSION_COOKIE_AGE=1209600
SESSION_EXPIRE_AT_BROWSER_CLOSE=False

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=shajahan.t@benzyinfotech.com
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=shajahan.t@benzyinfotech.com

# Password Reset
PASSWORD_RESET_TIMEOUT=3600

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 2.2 Collect Static Files

```bash
python manage.py collectstatic --noinput
```

This copies all static files to the `staticfiles` folder.

---

## Step 3: Test Waitress Locally

Before setting up as a service, test that Waitress works:

```bash
waitress-serve --listen=*:8000 asset_tracker.wsgi:application
```

Open browser and test: `http://localhost:8000/assets/`

If it works, press `Ctrl+C` to stop and proceed to Step 4.

---

## Step 4: Install NSSM (Non-Sucking Service Manager)

NSSM allows you to run any program as a Windows Service.

### 4.1 Download NSSM

1. Go to: https://nssm.cc/download
2. Download the latest version (e.g., nssm-2.24.zip)
3. Extract to `C:\nssm\`

### 4.2 Add NSSM to PATH (Optional)

Or use the full path: `C:\nssm\win64\nssm.exe`

---

## Step 5: Create Windows Service for Django

### 5.1 Open Command Prompt as Administrator

Press `Win + X` → Select "Command Prompt (Admin)" or "Terminal (Admin)"

### 5.2 Install the Service

```bash
C:\nssm\win64\nssm.exe install AssetTracker
```

This opens the NSSM GUI. Fill in:

**Application Tab:**
- Path: `C:\Python310\Scripts\waitress-serve.exe` (adjust Python version)
- Startup directory: `D:\Asset tracker`
- Arguments: `--listen=*:8000 asset_tracker.wsgi:application`

**Details Tab:**
- Display name: `Asset Tracking System`
- Description: `Django-based IT Asset Management System`
- Startup type: `Automatic`

**I/O Tab:**
- Output (stdout): `D:\Asset tracker\logs\service_output.log`
- Error (stderr): `D:\Asset tracker\logs\service_error.log`

**Environment Tab:**
Add these environment variables:
```
DJANGO_SETTINGS_MODULE=asset_tracker.settings
PYTHONPATH=D:\Asset tracker
```

Click "Install service"

### 5.3 Create Logs Directory

```bash
mkdir "D:\Asset tracker\logs"
```

---

## Step 6: Start the Service

```bash
C:\nssm\win64\nssm.exe start AssetTracker
```

Or use Windows Services:
1. Press `Win + R`, type `services.msc`, press Enter
2. Find "Asset Tracking System"
3. Right-click → Start

---

## Step 7: Configure Firewall

Allow incoming connections on port 8000:

```powershell
New-NetFirewallRule -DisplayName "Asset Tracker" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

---

## Step 8: Set Up Celery for Warranty Alerts (Optional)

### 8.1 Install Redis

Download and install Redis for Windows:
- https://github.com/microsoftarchive/redis/releases
- Or use Memurai: https://www.memurai.com/

### 8.2 Create Celery Worker Service

```bash
C:\nssm\win64\nssm.exe install AssetTrackerCelery
```

**Application Tab:**
- Path: `C:\Python310\python.exe`
- Startup directory: `D:\Asset tracker`
- Arguments: `-m celery -A asset_tracker worker -l info`

Click "Install service" and start it.

### 8.3 Create Celery Beat Service (Scheduler)

```bash
C:\nssm\win64\nssm.exe install AssetTrackerCeleryBeat
```

**Application Tab:**
- Path: `C:\Python310\python.exe`
- Startup directory: `D:\Asset tracker`
- Arguments: `-m celery -A asset_tracker beat -l info`

Click "Install service" and start it.

---

## Step 9: Verify Deployment

### 9.1 Check Service Status

```bash
C:\nssm\win64\nssm.exe status AssetTracker
```

### 9.2 Access the Application

- From server: `http://localhost:8000/assets/`
- From network: `http://192.168.11.213:8000/assets/`

### 9.3 Check Logs

```bash
type "D:\Asset tracker\logs\service_output.log"
type "D:\Asset tracker\logs\service_error.log"
```

---

## Step 10: Service Management Commands

### Start Service
```bash
C:\nssm\win64\nssm.exe start AssetTracker
```

### Stop Service
```bash
C:\nssm\win64\nssm.exe stop AssetTracker
```

### Restart Service
```bash
C:\nssm\win64\nssm.exe restart AssetTracker
```

### Remove Service
```bash
C:\nssm\win64\nssm.exe remove AssetTracker confirm
```

### View Service Status
```bash
C:\nssm\win64\nssm.exe status AssetTracker
```

---

## Troubleshooting

### Service won't start

1. Check logs: `D:\Asset tracker\logs\service_error.log`
2. Verify Python path is correct
3. Ensure all dependencies are installed: `pip install -r requirements.txt`
4. Test manually: `waitress-serve --listen=*:8000 asset_tracker.wsgi:application`

### Can't access from network

1. Check firewall: `Get-NetFirewallRule -DisplayName "Asset Tracker"`
2. Verify ALLOWED_HOSTS in .env includes your server IP
3. Check if service is running: `C:\nssm\win64\nssm.exe status AssetTracker`

### Static files not loading

1. Run: `python manage.py collectstatic --noinput`
2. Check STATIC_ROOT in settings.py
3. Verify staticfiles folder exists

### Database locked errors

1. Ensure only one instance is running
2. Check file permissions on db.sqlite3
3. Consider upgrading to PostgreSQL for production

---

## Production Checklist

- [ ] DEBUG=False in .env
- [ ] SECRET_KEY changed to a secure random value
- [ ] ALLOWED_HOSTS configured with your domain/IP
- [ ] Static files collected
- [ ] Database backed up
- [ ] Firewall configured
- [ ] Service starts automatically on boot
- [ ] Logs directory created
- [ ] Email settings configured
- [ ] Celery services running (for warranty alerts)
- [ ] Regular database backups scheduled

---

## Backup Strategy

### Database Backup Script

Create `backup_database.bat`:

```batch
@echo off
set BACKUP_DIR=D:\Asset tracker\backups
set DATE=%date:~-4,4%%date:~-10,2%%date:~-7,2%
set TIME=%time:~0,2%%time:~3,2%%time:~6,2%
set TIME=%TIME: =0%

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

copy "D:\Asset tracker\db.sqlite3" "%BACKUP_DIR%\db_backup_%DATE%_%TIME%.sqlite3"

echo Backup completed: %BACKUP_DIR%\db_backup_%DATE%_%TIME%.sqlite3
```

Schedule this with Windows Task Scheduler to run daily.

---

## Upgrading to PostgreSQL (Recommended for Production)

For better performance and concurrent access, consider PostgreSQL:

1. Install PostgreSQL
2. Update .env:
```env
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=asset_tracker
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
```
3. Install: `pip install psycopg2`
4. Migrate: `python manage.py migrate`

---

## Support

For issues or questions:
- Check logs in `D:\Asset tracker\logs\`
- Review Django documentation: https://docs.djangoproject.com/
- Check Waitress documentation: https://docs.pylonsproject.org/projects/waitress/

---

**Deployment Complete!**

Your Asset Tracking System is now running as a production Windows service and will start automatically on system boot.
