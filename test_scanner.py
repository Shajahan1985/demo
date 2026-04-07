import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from power_monitoring.models import ScanJob
from power_monitoring.services.network_scanner_service import NetworkScannerService

# Create a test scan job
scan_job = ScanJob.objects.create(status='pending')
print(f"Created scan job {scan_job.id}")

try:
    result = NetworkScannerService.execute_scan(scan_job)
    print(f"Scan completed successfully: {result}")
except Exception as e:
    print(f"Scan failed with error: {e}")
    import traceback
    traceback.print_exc()
