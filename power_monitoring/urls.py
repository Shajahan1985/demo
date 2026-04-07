"""
URL configuration for power monitoring.
"""
from django.urls import path
from . import views

app_name = 'power_monitoring'

urlpatterns = [
    path('report/', views.power_report_view, name='report'),
    path('shutdown/<int:asset_id>/', views.shutdown_asset_view, name='shutdown'),
    path('check/', views.check_power_status_view, name='check'),
    path('help/', views.shutdown_help_view, name='help'),
    
    # Network scanner URLs (disabled)
    # path('scan/', views.scan_control_view, name='scan_control'),
    # path('scan/start/', views.scan_start_view, name='scan_start'),
    # path('scan/status/<int:job_id>/', views.scan_status_view, name='scan_status'),
    # path('scan/results/<int:job_id>/', views.scan_results_view, name='scan_results'),
    # path('scan/export/<int:job_id>/', views.scan_export_view, name='scan_export'),
    # path('scan/history/', views.scan_history_view, name='scan_history'),
]
