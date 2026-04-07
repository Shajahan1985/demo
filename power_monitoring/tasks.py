"""
Celery tasks for power monitoring background processing.
"""
import logging
from celery import shared_task
from power_monitoring.services.power_monitor_service import PowerMonitorService


logger = logging.getLogger(__name__)


@shared_task
def check_power_status_task():
    """
    Periodic task to check power status of all assets.
    Runs at configured interval.
    """
    result = PowerMonitorService.check_all_assets()
    logger.info(f"Power status check completed: {result}")
    return result


@shared_task
def send_daily_notification_task():
    """
    Task to send daily power monitoring notification.
    Runs at configured notification time.
    """
    from power_monitoring.services.notification_service import NotificationService
    
    success = NotificationService.send_daily_notification()
    return {'success': success}


@shared_task
def send_after_hours_notification_task():
    """
    Task to send after-hours notification.
    Runs shortly after configured after-hours cutoff.
    """
    from power_monitoring.services.notification_service import NotificationService
    
    success = NotificationService.send_after_hours_notification()
    return {'success': success}
