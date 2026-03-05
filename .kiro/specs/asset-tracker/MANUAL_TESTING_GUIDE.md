# Asset Tracker - Manual Testing Guide

## Overview

This guide provides comprehensive manual testing procedures for all features of the Asset Tracking System. Follow these test cases to verify that all functionality works correctly before deployment.

## Prerequisites

### 1. Environment Setup

Ensure the development environment is running:

```bash
# Start Django development server
python manage.py runserver

# In a separate terminal, start Redis (for Celery)
redis-server

# In another terminal, start Celery worker
celery -A asset_tracker worker -l info

# In another terminal, start Celery Beat (for scheduled tasks)
celery -A asset_tracker beat -l info
```

### 2. Test Users

Create test users with different permission levels:

**Admin User** (already exists):
- Username: `admin`
- Password: `admin123`
- Permissions: Full access (is_staff=True)

**Non-Admin User** (create if needed):
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
user.save()
```

### 3. Initial Data

Verify initial data exists:
- IP ranges: 192.168.10.x, 192.168.11.x, 192.168.70.x, 192.168.50.x
- At least one Operating System
- At least one Team

If missing, run:
```bash
python manage.py shell
```
```python
from assets.models import IPRange, OperatingSystem, Team

# Create IP ranges if needed
IPRange.objects.get_or_create(range_pattern='192.168.10.x', network_prefix='192.168.10')
IPRange.objects.get_or_create(range_pattern='192.168.11.x', network_prefix='192.168.11')
IPRange.objects.get_or_create(range_pattern='192.168.70.x', network_prefix='192.168.70')
IPRange.objects.get_or_create(range_pattern='192.168.50.x', network_prefix='192.168.50')

# Create test OS and Team
OperatingSystem.objects.get_or_create(name='Windows 11')
OperatingSystem.objects.get_or_create(name='Ubuntu 22.04')
Team.objects.get_or_create(name='IT Department')
Team.objects.get_or_create(name='Engineering')
```

---

## Test Cases

### Section 1: Asset Creation (Admin User)

**Test Case 1.1: Create Asset with All Fields**

**Validates**: Requirements 1.1, 1.2, 1.3, 1.4

**Steps**:
1. Log in as admin user (admin/admin123)
2. Navigate to http://localhost:8000/assets/
3. Click "Add New Asset" button
4. Fill in the form:
   - Asset Tag: `BIDC001`
   - System Type: `Desktop`
   - Operating System: Select from dropdown
   - IP Address: Select any available IP
   - Particulars: `Test asset for manual testing`
   - Assigned To: `John Doe`
   - Team: Select from dropdown
   - Warranty Expiration: Set to 30 days from today
5. Click "Save" or "Create Asset"

**Expected Results**:
- ✅ Asset is created successfully
- ✅ Success message displayed: "Asset BIDC001 created successfully"
- ✅ Redirected to asset list page
- ✅ New asset appears in the list with serial number 1 (or next sequential number)
- ✅ Selected IP address is marked as in use

**Verification**:
- Check asset list shows the new asset
- Navigate to Free IPs page - selected IP should NOT appear there
- Note the serial number for next test

---

**Test Case 1.2: Duplicate Asset Tag Rejection**

**Validates**: Requirement 1.2

**Steps**:
1. Still logged in as admin
2. Click "Add New Asset" again
3. Fill in the form with the SAME asset tag: `BIDC001`
4. Fill other fields with different values
5. Click "Save"

**Expected Results**:
- ✅ Asset creation is rejected
- ✅ Error message displayed: "Asset tag already exists" or similar
- ✅ Form is redisplayed with error
- ✅ No new asset is created

**Verification**:
- Check asset list - should still show only one BIDC001

---

**Test Case 1.3: Sequential Serial Number Assignment**

**Validates**: Requirement 1.3

**Steps**:
1. Create another asset with tag `BIDC002`
2. Fill in all required fields
3. Save the asset

**Expected Results**:
- ✅ Asset is created with serial number = previous serial + 1
- ✅ Serial numbers are sequential

**Verification**:
- Check asset list - BIDC002 should have serial number one higher than BIDC001

---

### Section 2: Permission Enforcement (Non-Admin User)

**Test Case 2.1: Non-Admin Cannot Create Assets**

**Validates**: Requirement 1.5

**Steps**:
1. Log out from admin account
2. Log in as non-admin user (testuser/testpass123)
3. Try to navigate to http://localhost:8000/assets/create/

**Expected Results**:
- ✅ Access is denied
- ✅ HTTP 403 Forbidden error or redirect to login
- ✅ Error message: "Admin access required" or similar

---

**Test Case 2.2: Non-Admin Cannot Edit Assets**

**Validates**: Requirement 2.4

**Steps**:
1. Still logged in as non-admin user
2. Navigate to asset list: http://localhost:8000/assets/
3. Try to access edit URL directly: http://localhost:8000/assets/1/edit/

**Expected Results**:
- ✅ Access is denied
- ✅ HTTP 403 Forbidden error
- ✅ Edit buttons should not be visible on asset list (if implemented)

---

**Test Case 2.3: Non-Admin Cannot Free Assets**

**Validates**: Requirement 3.6

**Steps**:
1. Still logged in as non-admin user
2. Try to access free URL directly: http://localhost:8000/assets/1/free/

**Expected Results**:
- ✅ Access is denied
- ✅ HTTP 403 Forbidden error

---

**Test Case 2.4: Non-Admin Cannot Scrap Assets**

**Validates**: Requirement 6.4

**Steps**:
1. Still logged in as non-admin user
2. Try to access scrap URL directly: http://localhost:8000/assets/1/scrap/

**Expected Results**:
- ✅ Access is denied
- ✅ HTTP 403 Forbidden error

---

**Test Case 2.5: Non-Admin Can View Assets**

**Validates**: Requirements 4.1, 5.1, 7.1, 8.1

**Steps**:
1. Still logged in as non-admin user
2. Navigate to each view page:
   - Active Assets: http://localhost:8000/assets/
   - Free Systems: http://localhost:8000/assets/freed/
   - Scrapped Items: http://localhost:8000/assets/scrapped/
   - Free IPs: http://localhost:8000/assets/ips/free/
   - Warranty: http://localhost:8000/assets/warranty/

**Expected Results**:
- ✅ All view pages are accessible
- ✅ Data is displayed correctly
- ✅ No edit/delete/free/scrap buttons visible (admin-only actions)

---

### Section 3: Asset Updates (Admin User)

**Test Case 3.1: Update Asset Information**

**Validates**: Requirement 2.1

**Steps**:
1. Log out and log back in as admin
2. Navigate to asset list
3. Click "Edit" on BIDC001
4. Update the following fields:
   - Assigned To: Change to `Jane Smith`
   - Particulars: Add more text
5. Leave other fields unchanged
6. Click "Save"

**Expected Results**:
- ✅ Asset is updated successfully
- ✅ Success message displayed
- ✅ Changed fields are updated
- ✅ Unchanged fields remain the same (data integrity preserved)

**Verification**:
- View asset details - verify Assigned To is now "Jane Smith"
- Verify other fields (asset tag, system type, OS) are unchanged

---

**Test Case 3.2: Change Asset IP Address**

**Validates**: Requirement 2.2

**Steps**:
1. Note the current IP address of BIDC001
2. Navigate to Free IPs page and note a free IP address
3. Edit BIDC001
4. Change IP address to the noted free IP
5. Save the asset

**Expected Results**:
- ✅ Asset IP is updated successfully
- ✅ Old IP is now marked as free
- ✅ New IP is marked as in use

**Verification**:
- Check Free IPs page - old IP should now appear there
- Check Free IPs page - new IP should NOT appear there
- Asset list shows new IP for BIDC001

---

### Section 4: Asset Lifecycle (Free and Scrap)

**Test Case 4.1: Free an Asset with Correct Password**

**Validates**: Requirements 3.1, 3.2, 3.3, 3.4, 3.5

**Steps**:
1. Logged in as admin
2. Navigate to asset list
3. Click "Free" button on BIDC001
4. Confirmation dialog appears: "Do you want to free this system?"
5. Enter admin password: `admin123`
6. Click "Confirm" or "Free Asset"

**Expected Results**:
- ✅ Confirmation message displayed
- ✅ Password prompt appears
- ✅ Asset is freed successfully
- ✅ Success message: "Asset BIDC001 has been freed successfully"
- ✅ Redirected to Free Systems page
- ✅ BIDC001 appears on Free Systems page
- ✅ BIDC001 no longer appears on Active Assets page
- ✅ Assigned To and Team fields are cleared
- ✅ IP address is released and appears on Free IPs page

**Verification**:
- Navigate to Active Assets - BIDC001 should NOT be there
- Navigate to Free Systems - BIDC001 should be there
- Navigate to Free IPs - BIDC001's IP should be listed as free
- Check database or admin panel - freed_date should be set

---

**Test Case 4.2: Free Asset with Incorrect Password**

**Validates**: Requirement 3.2

**Steps**:
1. Create another asset BIDC003 (or use BIDC002)
2. Try to free it
3. Enter incorrect password: `wrongpassword`
4. Click "Confirm"

**Expected Results**:
- ✅ Operation is rejected
- ✅ Error message: "Incorrect password"
- ✅ Asset remains active
- ✅ Form is redisplayed

**Verification**:
- Asset should still be on Active Assets page
- Asset should NOT be on Free Systems page

---

**Test Case 4.3: Scrap a Freed Asset**

**Validates**: Requirements 6.1, 6.2, 6.3

**Steps**:
1. Navigate to Free Systems page
2. Click "Scrap" or "Delete" button on BIDC001
3. Confirmation dialog appears
4. Click "Confirm"

**Expected Results**:
- ✅ Asset is scrapped successfully
- ✅ Success message: "Asset BIDC001 has been scrapped successfully"
- ✅ Redirected to Scrapped Items page
- ✅ BIDC001 appears on Scrapped Items page with:
  - Asset tag
  - IP address (retained)
  - Date of deletion (scrapped_date)
- ✅ BIDC001 no longer appears on Free Systems page

**Verification**:
- Navigate to Free Systems - BIDC001 should NOT be there
- Navigate to Scrapped Items - BIDC001 should be there with scrapped date
- Check that asset tag and IP are retained

---

**Test Case 4.4: Cannot Scrap Active Asset**

**Validates**: Requirement 6.1

**Steps**:
1. Try to access scrap URL for an active asset directly
2. Example: http://localhost:8000/assets/2/scrap/ (assuming asset 2 is active)

**Expected Results**:
- ✅ Operation is rejected
- ✅ Error message: "Only freed assets can be scrapped"
- ✅ Asset remains active

---

### Section 5: View Functionality

**Test Case 5.1: Active Assets View**

**Validates**: Requirements 4.1, 4.2, 4.3

**Steps**:
1. Create at least 3 active assets with different serial numbers
2. Navigate to Active Assets page

**Expected Results**:
- ✅ All active assets are displayed
- ✅ Freed and scrapped assets are NOT displayed
- ✅ Assets are ordered by serial number (ascending)
- ✅ Columns displayed: serial number, asset tag, system type, OS, IP address, assigned to, team
- ✅ Edit and Free buttons visible (admin only)

**Verification**:
- Check that serial numbers are in ascending order
- Verify all expected columns are present
- Confirm freed/scrapped assets don't appear

---

**Test Case 5.2: Free Systems View**

**Validates**: Requirements 5.1, 5.3

**Steps**:
1. Ensure at least one asset is freed (from previous tests)
2. Navigate to Free Systems page

**Expected Results**:
- ✅ All freed assets are displayed
- ✅ Active and scrapped assets are NOT displayed
- ✅ IP address and asset tag are visible
- ✅ Scrap/Delete button visible for each asset (admin only)

---

**Test Case 5.3: Scrapped Items View**

**Validates**: Requirements 7.1, 7.2

**Steps**:
1. Ensure at least 2 assets are scrapped at different times
2. Navigate to Scrapped Items page

**Expected Results**:
- ✅ All scrapped assets are displayed
- ✅ Active and freed assets are NOT displayed
- ✅ Columns displayed: asset tag, IP address, date of deletion
- ✅ Assets are ordered by scrapped_date in descending order (most recent first)

**Verification**:
- Check that most recently scrapped asset appears first
- Verify scrapped dates are in descending order

---

**Test Case 5.4: Free IPs View**

**Validates**: Requirements 8.1, 8.2

**Steps**:
1. Navigate to Free IPs page

**Expected Results**:
- ✅ All unassigned IP addresses are displayed
- ✅ IPs are grouped by range with headers:
  - 192.168.10.x
  - 192.168.11.x
  - 192.168.70.x
  - 192.168.50.x
- ✅ IPs assigned to active assets do NOT appear
- ✅ IPs from freed assets DO appear

**Verification**:
- Check that each range section has a header
- Verify IPs are properly grouped under their ranges
- Confirm assigned IPs are not listed

---

### Section 6: File Attachments

**Test Case 6.1: Upload Attachment to Asset**

**Validates**: Requirements 12.1, 12.2

**Steps**:
1. Create a test file (e.g., test_document.pdf or test_image.jpg)
2. Navigate to edit page for an active asset
3. Look for file upload section
4. Select the test file
5. Upload the file
6. Save the asset

**Expected Results**:
- ✅ File is uploaded successfully
- ✅ File is stored in media/asset_attachments/
- ✅ Attachment is associated with the asset
- ✅ Attachment appears in asset details with download link

**Verification**:
- Check media/asset_attachments/ directory - file should be there
- View asset details - attachment should be listed
- Click download link - file should download correctly

---

**Test Case 6.2: Delete Attachment**

**Validates**: Requirement 12.3

**Steps**:
1. On the asset edit page with an attachment
2. Click "Delete" or remove button next to the attachment
3. Confirm deletion
4. Save the asset

**Expected Results**:
- ✅ Attachment is removed from asset record
- ✅ File is deleted from storage
- ✅ Attachment no longer appears in asset details

**Verification**:
- Check media/asset_attachments/ - file should be deleted
- View asset details - attachment should not be listed

---

**Test Case 6.3: Attachments Preserved During Updates**

**Validates**: Requirement 2.3

**Steps**:
1. Upload an attachment to an asset
2. Edit the asset and change non-attachment fields (e.g., Assigned To)
3. Save without touching the attachment
4. View asset details

**Expected Results**:
- ✅ Attachment is preserved
- ✅ Attachment still appears in asset details
- ✅ File still exists in storage

---

**Test Case 6.4: Attachments Preserved When Scrapping**

**Validates**: Requirement 12.4

**Steps**:
1. Create an asset with an attachment
2. Free the asset
3. Scrap the asset
4. Check scrapped asset details (if viewable)

**Expected Results**:
- ✅ Attachment is retained for historical reference
- ✅ File still exists in storage
- ✅ Attachment record still associated with scrapped asset

**Verification**:
- Check database - attachment record should still exist
- Check media/asset_attachments/ - file should still be there

---

### Section 7: Warranty Management

**Test Case 7.1: Warranty Page Display**

**Validates**: Requirements 13.4, 13.6

**Steps**:
1. Create several assets with different warranty expiration dates:
   - Asset A: Warranty expires in 3 days
   - Asset B: Warranty expires in 10 days
   - Asset C: Warranty expires in 30 days
   - Asset D: Warranty expired 5 days ago
2. Navigate to Warranty page

**Expected Results**:
- ✅ All assets with warranty dates are displayed
- ✅ Assets are ordered by warranty_expiration in ascending order
- ✅ Columns show: asset details and warranty expiration date
- ✅ Assets expiring within 7 days are highlighted (Asset A)
- ✅ Expired warranties are marked as expired (Asset D)

**Verification**:
- Check that Asset A (3 days) appears before Asset B (10 days)
- Verify Asset A is highlighted or marked as "expiring soon"
- Verify Asset D is marked as "expired"

---

**Test Case 7.2: Warranty Expiration Identification**

**Validates**: Requirement 13.2

**Steps**:
1. Ensure assets with various warranty dates exist (from previous test)
2. Run the warranty check manually:
```bash
python manage.py shell
```
```python
from assets.services.warranty_service import WarrantyService
expiring = WarrantyService.check_expiring_warranties()
print(f"Found {expiring.count()} assets expiring within 7 days")
for asset in expiring:
    print(f"- {asset.asset_tag}: {asset.warranty_expiration}")
```

**Expected Results**:
- ✅ Only assets expiring within 7 days are returned
- ✅ Asset A (3 days) is included
- ✅ Asset B (10 days) is NOT included
- ✅ Asset C (30 days) is NOT included
- ✅ Asset D (expired) is NOT included

---

**Test Case 7.3: Warranty Alert Email**

**Validates**: Requirement 13.3

**Steps**:
1. Ensure at least one asset has warranty expiring within 7 days
2. Trigger the warranty check task manually:
```bash
python manage.py shell
```
```python
from assets.tasks import run_daily_warranty_check
run_daily_warranty_check()
```
3. Check console output (since EMAIL_BACKEND is console in development)

**Expected Results**:
- ✅ Email is generated and printed to console
- ✅ Email contains list of assets with expiring warranties
- ✅ Email includes asset details and days until expiration
- ✅ Email is addressed to admin users

**Verification**:
- Check console output for email content
- Verify email lists correct assets
- Verify email formatting is clear and readable

---

**Test Case 7.4: Scheduled Warranty Check (Celery)**

**Validates**: Requirement 13.2, 13.3

**Prerequisites**:
- Redis must be running
- Celery worker must be running
- Celery beat must be running

**Steps**:
1. Verify Celery beat schedule in settings:
```python
# Should be configured to run daily at 9:00 AM
CELERY_BEAT_SCHEDULE = {
    'check-warranty-expiration': {
        'task': 'assets.tasks.run_daily_warranty_check',
        'schedule': crontab(hour=9, minute=0),
    },
}
```
2. For testing, modify schedule to run every minute:
```python
'schedule': crontab(minute='*'),
```
3. Restart Celery beat
4. Wait for task to execute
5. Check Celery worker logs

**Expected Results**:
- ✅ Task executes automatically on schedule
- ✅ Warranty check runs successfully
- ✅ Email is sent (visible in console)
- ✅ No errors in Celery logs

**Verification**:
- Check Celery beat logs for task scheduling
- Check Celery worker logs for task execution
- Check console for email output

---

### Section 8: IP Management

**Test Case 8.1: IP Assignment on Asset Creation**

**Validates**: Requirement 1.4, 8.3

**Steps**:
1. Note a free IP from Free IPs page (e.g., 192.168.10.50)
2. Create a new asset and assign that IP
3. Save the asset
4. Navigate to Free IPs page

**Expected Results**:
- ✅ IP is assigned to the asset
- ✅ IP is marked as in use
- ✅ IP no longer appears on Free IPs page

---

**Test Case 8.2: IP Release on Asset Freeing**

**Validates**: Requirement 3.4, 8.4

**Steps**:
1. Note the IP address of an active asset
2. Free that asset
3. Navigate to Free IPs page

**Expected Results**:
- ✅ IP is released when asset is freed
- ✅ IP appears on Free IPs page under appropriate range
- ✅ IP is available for reassignment

---

**Test Case 8.3: IP Change Management**

**Validates**: Requirement 2.2

**Steps**:
1. Asset has IP 192.168.10.50
2. Edit asset and change IP to 192.168.11.75
3. Save asset
4. Check Free IPs page

**Expected Results**:
- ✅ Old IP (192.168.10.50) is now free
- ✅ New IP (192.168.11.75) is now in use
- ✅ Old IP appears on Free IPs page
- ✅ New IP does NOT appear on Free IPs page

---

### Section 9: Data Management (Django Admin)

**Test Case 9.1: Manage Operating Systems**

**Validates**: Requirements 9.1, 9.3

**Steps**:
1. Log in to Django admin: http://localhost:8000/admin/
2. Navigate to Operating Systems
3. Add a new OS: "macOS Sonoma"
4. Save
5. Try to add duplicate: "macOS Sonoma" again

**Expected Results**:
- ✅ New OS is created successfully
- ✅ OS appears in dropdown when creating/editing assets
- ✅ Duplicate OS is rejected with error message

---

**Test Case 9.2: Manage Teams**

**Validates**: Requirements 10.1, 10.3

**Steps**:
1. In Django admin, navigate to Teams
2. Add a new team: "Marketing"
3. Save
4. Try to add duplicate: "Marketing" again

**Expected Results**:
- ✅ New team is created successfully
- ✅ Team appears in dropdown when creating/editing assets
- ✅ Duplicate team is rejected with error message

---

**Test Case 9.3: Manage IP Ranges**

**Validates**: Requirements 11.1, 11.3

**Steps**:
1. In Django admin, navigate to IP Ranges
2. Add a new range: "192.168.100.x" with prefix "192.168.100"
3. Save
4. Try to add duplicate: "192.168.100.x" again

**Expected Results**:
- ✅ New IP range is created successfully
- ✅ IPs from new range become available for assignment
- ✅ Duplicate range is rejected with error message

---

## Automated Verification Scripts

### Script 1: Verify Database State

```python
# Run: python manage.py shell < verify_db.py

from assets.models import Asset, IPAddress, OperatingSystem, Team, IPRange

print("=== Database State Verification ===\n")

# Count assets by status
active_count = Asset.objects.filter(status='active').count()
freed_count = Asset.objects.filter(status='freed').count()
scrapped_count = Asset.objects.filter(status='scrapped').count()

print(f"Active Assets: {active_count}")
print(f"Freed Assets: {freed_count}")
print(f"Scrapped Assets: {scrapped_count}")
print(f"Total Assets: {active_count + freed_count + scrapped_count}\n")

# Count IPs
total_ips = IPAddress.objects.count()
assigned_ips = IPAddress.objects.filter(is_assigned=True).count()
free_ips = IPAddress.objects.filter(is_assigned=False).count()

print(f"Total IPs: {total_ips}")
print(f"Assigned IPs: {assigned_ips}")
print(f"Free IPs: {free_ips}\n")

# List IP ranges
print("IP Ranges:")
for ip_range in IPRange.objects.all():
    range_ips = IPAddress.objects.filter(ip_range=ip_range)
    free_in_range = range_ips.filter(is_assigned=False).count()
    print(f"  {ip_range.range_pattern}: {range_ips.count()} total, {free_in_range} free")

print("\nOperating Systems:")
for os in OperatingSystem.objects.all():
    print(f"  - {os.name}")

print("\nTeams:")
for team in Team.objects.all():
    print(f"  - {team.name}")
```

### Script 2: Check Warranty Status

```python
# Run: python manage.py shell < check_warranties.py

from assets.models import Asset
from assets.services.warranty_service import WarrantyService
from django.utils import timezone

print("=== Warranty Status Check ===\n")

# Get all assets with warranties
assets_with_warranty = Asset.objects.filter(warranty_expiration__isnull=False)
print(f"Total assets with warranty: {assets_with_warranty.count()}\n")

# Check expiring soon
expiring_soon = WarrantyService.check_expiring_warranties()
print(f"Assets expiring within 7 days: {expiring_soon.count()}")
for asset in expiring_soon:
    days_left = (asset.warranty_expiration - timezone.now().date()).days
    print(f"  - {asset.asset_tag}: {days_left} days left")

# Check expired
today = timezone.now().date()
expired = assets_with_warranty.filter(warranty_expiration__lt=today)
print(f"\nExpired warranties: {expired.count()}")
for asset in expired:
    days_ago = (today - asset.warranty_expiration).days
    print(f"  - {asset.asset_tag}: expired {days_ago} days ago")
```

---

## Test Results Checklist

Use this checklist to track test completion:

### Asset Creation
- [ ] 1.1: Create asset with all fields
- [ ] 1.2: Duplicate asset tag rejection
- [ ] 1.3: Sequential serial numbers

### Permission Enforcement
- [ ] 2.1: Non-admin cannot create
- [ ] 2.2: Non-admin cannot edit
- [ ] 2.3: Non-admin cannot free
- [ ] 2.4: Non-admin cannot scrap
- [ ] 2.5: Non-admin can view

### Asset Updates
- [ ] 3.1: Update asset information
- [ ] 3.2: Change IP address

### Asset Lifecycle
- [ ] 4.1: Free asset with correct password
- [ ] 4.2: Free asset with incorrect password
- [ ] 4.3: Scrap freed asset
- [ ] 4.4: Cannot scrap active asset

### View Functionality
- [ ] 5.1: Active assets view
- [ ] 5.2: Free systems view
- [ ] 5.3: Scrapped items view
- [ ] 5.4: Free IPs view

### File Attachments
- [ ] 6.1: Upload attachment
- [ ] 6.2: Delete attachment
- [ ] 6.3: Attachments preserved during updates
- [ ] 6.4: Attachments preserved when scrapping

### Warranty Management
- [ ] 7.1: Warranty page display
- [ ] 7.2: Warranty expiration identification
- [ ] 7.3: Warranty alert email
- [ ] 7.4: Scheduled warranty check

### IP Management
- [ ] 8.1: IP assignment on creation
- [ ] 8.2: IP release on freeing
- [ ] 8.3: IP change management

### Data Management
- [ ] 9.1: Manage operating systems
- [ ] 9.2: Manage teams
- [ ] 9.3: Manage IP ranges

---

## Known Issues and Notes

Document any issues found during testing:

| Test Case | Issue Description | Severity | Status |
|-----------|------------------|----------|--------|
| Example: 6.1 | File upload button not visible | Medium | Open |
|  |  |  |  |

---

## Sign-Off

**Tester Name**: ___________________________

**Date**: ___________________________

**Overall Result**: [ ] PASS  [ ] FAIL  [ ] PASS WITH ISSUES

**Notes**:
