"""
Celery tasks for background processing.
"""
from celery import shared_task
from assets.services.warranty_service import WarrantyService


@shared_task
def run_daily_warranty_check():
    """
    Scheduled task to check for expiring warranties and send alerts.
    Runs daily at 9:00 AM.
    """
    expiring_assets = WarrantyService.check_expiring_warranties()
    if expiring_assets.exists():
        WarrantyService.send_warranty_alerts(expiring_assets)
