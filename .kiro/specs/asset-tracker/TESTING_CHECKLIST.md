# Asset Tracker - Quick Testing Checklist

## Pre-Testing Setup

```bash
# 1. Start development server
python manage.py runserver

# 2. Start Redis (in separate terminal)
redis-server

# 3. Start Celery worker (in separate terminal)
celery -A asset_tracker worker -l info

# 4. Start Celery Beat (in separate terminal)
celery -A asset_tracker beat -l info
```

## Quick Test URLs

- **Active Assets**: http://localhost:8000/assets/
- **Create Asset**: http://localhost:8000/assets/create/
- **Free Systems**: http://localhost:8000/assets/freed/
- **Scrapped Items**: http://localhost:8000/assets/scrapped/
- **Free IPs**: http://localhost:8000/assets/ips/free/
- **Warranty**: http://localhost:8000/assets/warranty/
- **Django Admin**: http://localhost:8000/admin/

## Test Credentials

**Admin User**:
- Username: `admin`
- Password: `admin123`

**Non-Admin User** (create if needed):
- Username: `testuser`
- Password: `testpass123`

## Critical Test Scenarios

### 1. Asset CRUD Operations (Admin)
- [ ] Create asset with all fields → Success
- [ ] Create duplicate asset tag → Rejected
- [ ] Edit asset → Changes saved
- [ ] Change asset IP → Old IP freed, new IP assigned
- [ ] View asset list → All active assets shown

### 2. Permission Tests (Non-Admin)
- [ ] Try to create asset → 403 Forbidden
- [ ] Try to edit asset → 403 Forbidden
- [ ] Try to free asset → 403 Forbidden
- [ ] Try to scrap asset → 403 Forbidden
- [ ] View asset list → Success (read-only)

### 3. Asset Lifecycle
- [ ] Free asset with correct password → Moved to freed
- [ ] Free asset with wrong password → Rejected
- [ ] Scrap freed asset → Moved to scrapped
- [ ] Try to scrap active asset → Rejected

### 4. IP Management
- [ ] Assign IP to new asset → IP marked as used
- [ ] Free asset → IP released to free pool
- [ ] Change asset IP → Old freed, new assigned
- [ ] View free IPs → Grouped by range

### 5. Warranty Alerts
- [ ] Create asset with warranty in 3 days → Shows on warranty page
- [ ] Run warranty check → Email sent (console)
- [ ] View warranty page → Expiring assets highlighted

### 6. File Attachments
- [ ] Upload file to asset → File saved
- [ ] Download attachment → File retrieved
- [ ] Delete attachment → File removed
- [ ] Update asset → Attachments preserved

## Quick Verification Commands

```bash
# Check database state
python manage.py shell < verify_db_state.py

# Check warranty status
python manage.py shell < check_warranty_status.py

# Test warranty email
python manage.py shell < test_warranty_email.py
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Can't create asset | Check if logged in as admin |
| IP not showing as free | Verify asset was freed properly |
| Email not sending | Check Celery worker is running |
| 403 errors | Verify user has admin permissions |
| File upload fails | Check MEDIA_ROOT permissions |

## Test Data Setup

```python
# Run in Django shell: python manage.py shell

from assets.models import *
from django.utils import timezone
from datetime import timedelta

# Create test OS
os1 = OperatingSystem.objects.get_or_create(name='Windows 11')[0]
os2 = OperatingSystem.objects.get_or_create(name='Ubuntu 22.04')[0]

# Create test teams
team1 = Team.objects.get_or_create(name='IT Department')[0]
team2 = Team.objects.get_or_create(name='Engineering')[0]

# Get a free IP
free_ip = IPAddress.objects.filter(is_assigned=False).first()

# Create test asset
if free_ip:
    asset = Asset.objects.create(
        asset_tag='BIDC999',
        system_type='Desktop',
        operating_system=os1,
        ip_address=free_ip,
        assigned_to='Test User',
        team=team1,
        warranty_expiration=timezone.now().date() + timedelta(days=3),
        status='active'
    )
    free_ip.is_assigned = True
    free_ip.assigned_to_asset = asset
    free_ip.save()
    print(f"Created test asset: {asset.asset_tag}")
```

## Sign-Off

**Date**: _______________

**Tester**: _______________

**Result**: [ ] PASS  [ ] FAIL

**Notes**:
