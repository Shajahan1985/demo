"""
Views for power monitoring.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from power_monitoring.services import PowerMonitorService, ShutdownManagerService, ExemptionService
from power_monitoring.models import MonitoringConfig, NotificationRecipient, PowerAuditLog
from assets.models import Asset


def is_staff_user(user):
    """Check if user is staff."""
    return user.is_staff


@login_required
def power_report_view(request):
    """Display power monitoring report."""
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Get online assets
    online_assets = PowerMonitorService.get_online_assets(exclude_exempt=True)
    
    # Apply search filter if provided
    if search_query:
        from django.db.models import Q
        online_assets = online_assets.filter(
            Q(asset_tag__icontains=search_query) |
            Q(assigned_to__icontains=search_query) |
            Q(ip_address__address__icontains=search_query)
        )
    
    # Get after-hours assets
    after_hours_assets = PowerMonitorService.get_after_hours_assets()
    
    # Apply search filter to after-hours assets too
    if search_query:
        after_hours_assets = after_hours_assets.filter(
            Q(asset_tag__icontains=search_query) |
            Q(assigned_to__icontains=search_query) |
            Q(ip_address__address__icontains=search_query)
        )
    
    # Get config
    config = MonitoringConfig.get_config()
    
    # Check if currently after hours
    current_time = timezone.now().time()
    is_after_hours = current_time >= config.after_hours_cutoff
    
    context = {
        'online_assets': online_assets,
        'after_hours_assets': after_hours_assets if is_after_hours else [],
        'config': config,
        'is_after_hours': is_after_hours,
        'last_check': timezone.now(),
        'search_query': search_query,
    }
    
    return render(request, 'power_monitoring/report.html', context)


@login_required
@user_passes_test(is_staff_user)
def shutdown_asset_view(request, asset_id):
    """Shutdown a specific asset."""
    try:
        asset = Asset.objects.get(pk=asset_id)
        success, message = ShutdownManagerService.shutdown_asset(asset, request.user)
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
            
    except Asset.DoesNotExist:
        messages.error(request, "Asset not found")
    
    return redirect('power_monitoring:report')


@login_required
@user_passes_test(is_staff_user)
def check_power_status_view(request):
    """Manually trigger power status check."""
    result = PowerMonitorService.check_all_assets()
    
    messages.success(
        request,
        f"Power check completed: {result['online']} online, {result['offline']} offline"
    )
    
    return redirect('power_monitoring:report')


@login_required
def shutdown_help_view(request):
    """Display help for remote shutdown setup."""
    return render(request, 'power_monitoring/shutdown_help.html')


# Network Scanner Views

from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from power_monitoring.models import ScanJob, ScanResult
from power_monitoring.services.network_scanner_service import NetworkScannerService
import threading


@login_required
def scan_start_view(request):
    """Initiate a new network scan."""
    if request.method == 'POST':
        # Check for existing running scan
        running_scan = ScanJob.objects.filter(status='running').first()
        if running_scan:
            return JsonResponse({
                'error': f'Scan already in progress (Job ID: {running_scan.id})'
            }, status=409)
        
        try:
            # Create new scan job
            scan_job = ScanJob.objects.create(status='pending')
            
            # Execute scan in background thread
            def run_scan():
                import traceback
                try:
                    NetworkScannerService.execute_scan(scan_job)
                except Exception as e:
                    print(f"Scan failed with error: {e}")
                    print(f"Traceback: {traceback.format_exc()}")
                    # Mark scan as failed
                    scan_job.status = 'failed'
                    scan_job.error_message = str(e)
                    scan_job.completed_at = timezone.now()
                    scan_job.save()
            
            thread = threading.Thread(target=run_scan)
            thread.daemon = True
            thread.start()
            
            return JsonResponse({
                'scan_job_id': scan_job.id,
                'status': 'started'
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def scan_status_view(request, job_id):
    """Get status of a scan job."""
    try:
        scan_job = ScanJob.objects.get(pk=job_id)
        
        return JsonResponse({
            'status': scan_job.status,
            'progress': {
                'total_ips': scan_job.total_ips,
                'online_count': scan_job.online_count,
                'offline_count': scan_job.offline_count,
                'tracked_count': scan_job.tracked_count,
                'discovered_count': scan_job.discovered_count,
            },
            'started_at': scan_job.started_at.isoformat() if scan_job.started_at else None,
            'completed_at': scan_job.completed_at.isoformat() if scan_job.completed_at else None,
            'error_message': scan_job.error_message
        })
        
    except ScanJob.DoesNotExist:
        return JsonResponse({'error': 'Scan job not found'}, status=404)


@login_required
def scan_results_view(request, job_id):
    """Display scan results with filtering."""
    try:
        scan_job = ScanJob.objects.get(pk=job_id)
        
        # Get filter parameter
        filter_type = request.GET.get('filter', 'all')
        
        # Query results
        results = scan_job.results.select_related('asset', 'asset__ip_address').all()
        
        # Apply filters
        if filter_type == 'tracked_only':
            results = results.filter(is_tracked=True)
        elif filter_type == 'discovered_only':
            results = results.filter(is_tracked=False, is_online=True)
        elif filter_type == 'online_only':
            results = results.filter(is_online=True)
        elif filter_type == 'offline_only':
            results = results.filter(is_online=False)
        
        # Sort by IP address (numerical)
        results = sorted(results, key=lambda r: tuple(map(int, r.ip_address.split('.'))))
        
        context = {
            'scan_job': scan_job,
            'results': results,
            'filter_type': filter_type,
        }
        
        return render(request, 'power_monitoring/scan_results.html', context)
        
    except ScanJob.DoesNotExist:
        messages.error(request, "Scan job not found")
        return redirect('power_monitoring:scan_history')


@login_required
def scan_export_view(request, job_id):
    """Export scan results as CSV."""
    try:
        scan_job = ScanJob.objects.get(pk=job_id)
        
        # Generate CSV content
        csv_content = NetworkScannerService.export_results_csv(scan_job)
        
        # Generate filename
        timestamp = scan_job.started_at.strftime('%Y-%m-%d_%H-%M-%S') if scan_job.started_at else 'unknown'
        filename = f'scan_results_{timestamp}.csv'
        
        # Return as downloadable file
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except ScanJob.DoesNotExist:
        messages.error(request, "Scan job not found")
        return redirect('power_monitoring:scan_history')


@login_required
def scan_history_view(request):
    """Display scan history with pagination."""
    scan_jobs = ScanJob.objects.all().order_by('-started_at')
    
    # Paginate results
    paginator = Paginator(scan_jobs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'power_monitoring/scan_history.html', context)


@login_required
def scan_control_view(request):
    """Display scan control interface."""
    # Get latest scan job
    latest_scan = ScanJob.objects.order_by('-created_at').first()
    
    # Check if scan is running
    running_scan = ScanJob.objects.filter(status='running').first()
    
    context = {
        'latest_scan': latest_scan,
        'running_scan': running_scan,
    }
    
    return render(request, 'power_monitoring/scan_control.html', context)
