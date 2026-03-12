# Deployment Checklist: Import/Export/Filter Features

## Pre-Deployment Checklist

### Dependencies
- [ ] Verify `openpyxl>=3.1.2` is in requirements.txt
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify openpyxl installation: `python -c "import openpyxl; print(openpyxl.__version__)"`

### Database
- [ ] Run migrations: `python manage.py migrate`
- [ ] Verify no pending migrations: `python manage.py showmigrations`
- [ ] Check database has Operating Systems configured
- [ ] Check database has Teams configured
- [ ] Check database has IP addresses configured

### File System
- [ ] Create media directory: `mkdir -p media/templates`
- [ ] Set proper permissions on media directory (writable by web server)
- [ ] Verify sample import template exists or can be created
- [ ] Check disk space for uploaded files (10MB max per file)

### Code Verification
- [ ] Run Django system check: `python manage.py check`
- [ ] Verify no syntax errors: `python -m py_compile assets/services/import_service.py`
- [ ] Verify no syntax errors: `python -m py_compile assets/services/export_service.py`
- [ ] Verify no syntax errors: `python -m py_compile assets/services/filter_service.py`

### URL Configuration
- [ ] Verify import URL: `/assets/import/`
- [ ] Verify export URLs: `/assets/export/active/`, `/assets/export/freed/`, `/assets/export/scrapped/`
- [ ] Verify free IPs export URL: `/assets/ips/export/free/`
- [ ] Test URL routing: `python manage.py show_urls` (if django-extensions installed)

## Testing Checklist

### Import Functionality
- [ ] Access import page as admin user
- [ ] Verify non-admin users cannot access import page
- [ ] Download sample template
- [ ] Upload valid Excel file with 5-10 test assets
- [ ] Verify success message and asset count
- [ ] Upload Excel file with validation errors
- [ ] Verify error messages are clear and specific
- [ ] Verify partial import works (valid rows imported, invalid rows skipped)
- [ ] Test file size limit (try uploading >10MB file)
- [ ] Test invalid file format (try uploading .csv or .txt)
- [ ] Verify imported assets appear in asset list
- [ ] Verify IP addresses are marked as assigned after import

### Export Functionality
- [ ] Test export active assets
- [ ] Verify Excel file downloads correctly
- [ ] Open exported file and verify all columns present
- [ ] Verify data matches database records
- [ ] Test export freed assets
- [ ] Test export scrapped assets
- [ ] Test export free IPs
- [ ] Verify exports work with empty datasets (headers only)
- [ ] Test export with large dataset (100+ records)
- [ ] Verify export buttons visible to all authenticated users
- [ ] Verify non-authenticated users cannot access export URLs

### Filter Functionality
- [ ] Test Operating System filter
- [ ] Test Asset Tag filter (partial match)
- [ ] Test Team filter
- [ ] Test Assigned To filter (partial match)
- [ ] Test multiple filters combined (AND logic)
- [ ] Test "Clear Filters" button
- [ ] Verify filter values persist in URL
- [ ] Verify "No assets found" message when no matches
- [ ] Test filter with special characters in search
- [ ] Test case-insensitive search

### Integration Testing
- [ ] Import assets → Verify in asset list → Export → Compare data
- [ ] Apply filters → Export filtered results → Verify Excel matches filtered view
- [ ] Import assets → Free one → Verify in freed list → Export freed list
- [ ] Import assets → Scrap one → Verify in scrapped list → Export scrapped list
- [ ] Import with IP → Verify IP marked as assigned → Check free IPs list

### Performance Testing
- [ ] Import 100 rows - measure time
- [ ] Import 500 rows - measure time
- [ ] Export 100 assets - measure time
- [ ] Export 500 assets - measure time
- [ ] Apply filters on 500+ assets - measure response time
- [ ] Test concurrent imports (if applicable)
- [ ] Monitor memory usage during large imports/exports

## Security Checklist

### Access Control
- [ ] Verify import is admin-only (AdminRequiredMixin)
- [ ] Verify export requires authentication (LoginRequiredMixin)
- [ ] Verify filters require authentication
- [ ] Test unauthorized access returns proper error (403/redirect)
- [ ] Verify CSRF protection on import form
- [ ] Test file upload security (reject non-Excel files)

### Data Validation
- [ ] Verify asset_tag uniqueness enforced
- [ ] Verify IP address validation works
- [ ] Verify foreign key validation (OS, Team)
- [ ] Verify date format validation
- [ ] Verify system_type validation
- [ ] Test SQL injection prevention in filters
- [ ] Test XSS prevention in error messages

### File Security
- [ ] Verify file size limit enforced (10MB)
- [ ] Verify file type validation (.xlsx, .xls only)
- [ ] Test malicious file upload (corrupted Excel)
- [ ] Verify uploaded files are not executable
- [ ] Check file permissions on media directory

## Production Deployment Steps

### 1. Backup
- [ ] Backup database before deployment
- [ ] Backup current codebase
- [ ] Document current system state

### 2. Deploy Code
- [ ] Pull latest code from repository
- [ ] Install/update dependencies: `pip install -r requirements.txt`
- [ ] Collect static files: `python manage.py collectstatic --noinput`
- [ ] Run migrations: `python manage.py migrate`

### 3. Configuration
- [ ] Verify environment variables set correctly
- [ ] Check file upload settings in Django settings
- [ ] Verify media directory permissions
- [ ] Check max upload size in web server config (Nginx/Apache)

### 4. Restart Services
- [ ] Restart Django application (Gunicorn/uWSGI)
- [ ] Restart web server (Nginx/Apache)
- [ ] Restart Celery workers (if applicable)
- [ ] Clear application cache (if applicable)

### 5. Smoke Tests
- [ ] Access application homepage
- [ ] Log in as admin
- [ ] Access import page
- [ ] Access export buttons
- [ ] Test one import with sample data
- [ ] Test one export
- [ ] Test one filter
- [ ] Verify no errors in logs

## Post-Deployment Verification

### Functionality Verification
- [ ] Import page accessible at `/assets/import/`
- [ ] Export buttons visible on asset list page
- [ ] Export buttons visible on freed systems page
- [ ] Export buttons visible on scrapped items page
- [ ] Export button visible on free IPs page
- [ ] Filters visible on asset list page
- [ ] Sample template downloadable
- [ ] All features work as expected

### Monitoring
- [ ] Check application logs for errors
- [ ] Monitor server resource usage
- [ ] Check database query performance
- [ ] Monitor file system usage (media directory)
- [ ] Set up alerts for import/export failures

### Documentation
- [ ] Update user documentation with new features
- [ ] Update admin documentation
- [ ] Document any configuration changes
- [ ] Update API documentation (if applicable)

## Rollback Plan

If issues are encountered:

### Immediate Rollback
1. [ ] Revert code to previous version
2. [ ] Restore database backup (if migrations were run)
3. [ ] Restart services
4. [ ] Verify system is stable

### Partial Rollback
1. [ ] Disable import feature (remove URL or add maintenance flag)
2. [ ] Disable export features
3. [ ] Keep existing functionality working
4. [ ] Investigate and fix issues
5. [ ] Re-deploy when ready

## Troubleshooting Guide

### Import Issues

**Issue**: Import page returns 500 error
- Check: openpyxl installed
- Check: media directory exists and is writable
- Check: Application logs for specific error
- Check: Database connection

**Issue**: All imports fail validation
- Check: Operating Systems exist in database
- Check: Teams exist in database
- Check: IP addresses exist in IP management
- Check: Excel file format matches template

**Issue**: File upload fails
- Check: File size under 10MB
- Check: File format is .xlsx or .xls
- Check: Web server max upload size setting
- Check: Django FILE_UPLOAD_MAX_MEMORY_SIZE setting

### Export Issues

**Issue**: Export returns empty file
- Check: Data exists in database for export type
- Check: User has permission to view data
- Check: Filters not excluding all results

**Issue**: Export fails with error
- Check: openpyxl installed
- Check: Database query succeeds
- Check: Application logs for specific error

### Filter Issues

**Issue**: Filters don't work
- Check: Form submission working
- Check: FilterService properly configured
- Check: Database indexes exist
- Check: JavaScript errors in browser console

## Performance Optimization

### Database
- [ ] Add indexes on filtered columns (asset_tag, status)
- [ ] Optimize queries with select_related/prefetch_related
- [ ] Monitor slow query log

### File Handling
- [ ] Consider chunking for large imports
- [ ] Implement progress indicators for long operations
- [ ] Add caching for frequently exported data

### Web Server
- [ ] Increase max upload size if needed
- [ ] Configure timeout for long-running imports
- [ ] Enable gzip compression for exports

## Maintenance Tasks

### Regular Tasks
- [ ] Monitor import success/failure rates
- [ ] Review import error logs weekly
- [ ] Clean up old uploaded files (if stored)
- [ ] Monitor disk space in media directory
- [ ] Review export usage patterns

### Monthly Tasks
- [ ] Review and optimize database queries
- [ ] Check for openpyxl security updates
- [ ] Review user feedback on import/export features
- [ ] Analyze performance metrics

## Support Resources

### Documentation
- README.md - General system documentation
- ASSET_MANAGEMENT_GUIDE.md - User guide for import/export/filter
- EXCEL_IMPORT_FORMAT.md - Detailed Excel format specification
- DEPLOYMENT.md - General deployment guide

### Logs
- Application log: `authentication.log`
- Web server log: `/var/log/nginx/error.log` or `/var/log/apache2/error.log`
- Django debug log: Check DEBUG setting and log configuration

### Testing
- Run test suite: `pytest assets/tests/`
- Run property tests: `pytest assets/tests/ -v`
- Run specific test: `pytest assets/tests/test_import_service.py -v`

## Sign-Off

### Deployment Team
- [ ] Developer sign-off: _______________
- [ ] QA sign-off: _______________
- [ ] DevOps sign-off: _______________
- [ ] Product Owner sign-off: _______________

### Deployment Details
- Deployment Date: _______________
- Deployed By: _______________
- Version/Commit: _______________
- Environment: _______________

### Notes
_Add any deployment-specific notes here_

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**For**: Asset Tracker - Import/Export/Filter Features
