# Celery and Email Configuration Guide

This document explains how to configure and run Celery for background tasks, specifically for the warranty expiration alert system.

## Prerequisites

- Redis server installed and running
- Python dependencies installed from `requirements.txt`

## Installing Redis

### Windows
1. Download Redis from: https://github.com/microsoftarchive/redis/releases
2. Install and run Redis server
3. Default port: 6379

### Linux/Mac
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Mac (using Homebrew)
brew install redis
brew services start redis
```

## Configuration

### 1. Environment Variables

Update your `.env` file with the following settings:

```env
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration (Development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@assettracker.com

# Email Configuration (Production - SMTP)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
# DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### 2. Email Backend Options

#### Console Backend (Development)
Prints emails to the console. Already configured by default.

#### SMTP Backend (Production)
Configure SMTP settings in `.env` file. Examples:

**Gmail:**
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Note:** For Gmail, you need to use an App Password, not your regular password.

**Other SMTP Providers:**
- Outlook: `smtp.office365.com:587`
- Yahoo: `smtp.mail.yahoo.com:587`
- SendGrid: `smtp.sendgrid.net:587`

## Running Celery

### 1. Start Redis Server

Make sure Redis is running:
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG
```

### 2. Start Celery Worker

Open a terminal and run:
```bash
# Windows
celery -A asset_tracker worker -l info --pool=solo

# Linux/Mac
celery -A asset_tracker worker -l info
```

### 3. Start Celery Beat (Scheduler)

Open another terminal and run:
```bash
# Windows
celery -A asset_tracker beat -l info

# Linux/Mac
celery -A asset_tracker beat -l info
```

### 4. Combined Command (Development)

You can run both worker and beat in one command:
```bash
# Windows
celery -A asset_tracker worker --beat -l info --pool=solo

# Linux/Mac
celery -A asset_tracker worker --beat -l info
```

## Warranty Alert Schedule

The warranty check task is scheduled to run daily at 9:00 AM (server time). This is configured in `asset_tracker/settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'check-warranty-expiration-daily': {
        'task': 'assets.tasks.run_daily_warranty_check',
        'schedule': crontab(hour=9, minute=0),  # Run daily at 9:00 AM
    },
}
```

To change the schedule, modify the `hour` and `minute` parameters in the `crontab()` function.

## Testing Email Functionality

### Manual Test

Run the management command to test email sending:

```bash
# Create test data and send test email
python manage.py test_warranty_email --create-test-data

# Just check and send alerts for existing data
python manage.py test_warranty_email
```

### Automated Tests

Run the test suite:
```bash
pytest assets/tests/test_warranty_email.py -v
```

## Troubleshooting

### Redis Connection Error
```
Error: Error 10061 connecting to localhost:6379. No connection could be made...
```
**Solution:** Make sure Redis server is running.

### Celery Worker Not Starting
**Solution:** 
- On Windows, use `--pool=solo` flag
- Check that all dependencies are installed
- Verify Redis is accessible

### Emails Not Sending
**Solution:**
- Check email backend configuration in `.env`
- Verify SMTP credentials are correct
- For Gmail, ensure App Password is used
- Check that admin users have email addresses set

### Task Not Running on Schedule
**Solution:**
- Ensure Celery Beat is running
- Check timezone settings in `settings.py`
- Verify the schedule in `CELERY_BEAT_SCHEDULE`

## Production Deployment

For production, consider using:

1. **Supervisor** or **systemd** to manage Celery processes
2. **Flower** for monitoring Celery tasks
3. **Redis Sentinel** or **Redis Cluster** for high availability
4. **Proper SMTP service** (SendGrid, Mailgun, AWS SES)

Example systemd service files:

**celery-worker.service:**
```ini
[Unit]
Description=Celery Worker
After=network.target redis.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/asset_tracker
ExecStart=/path/to/venv/bin/celery -A asset_tracker worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

**celery-beat.service:**
```ini
[Unit]
Description=Celery Beat
After=network.target redis.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/asset_tracker
ExecStart=/path/to/venv/bin/celery -A asset_tracker beat -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

## Monitoring

Install Flower for web-based monitoring:
```bash
pip install flower
celery -A asset_tracker flower
```

Access at: http://localhost:5555

## Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- [Redis Documentation](https://redis.io/documentation)
