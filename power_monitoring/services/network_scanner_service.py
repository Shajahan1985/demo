"""
Network scanner service for discovering online systems across IP ranges.
"""
import ipaddress
import socket
import subprocess
import platform
from typing import List, Tuple, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.utils import timezone
from django.db import transaction
from power_monitoring.models import ScanConfiguration, ScanJob, ScanResult
from assets.models import Asset


class NetworkScannerService:
    """Service for scanning network IP ranges and discovering online systems."""
    
    @staticmethod
    def expand_cidr_range(cidr: str) -> List[str]:
        """
        Expand CIDR notation to list of IP addresses.
        Excludes network and broadcast addresses.
        
        Args:
            cidr: IP range in CIDR notation (e.g., "192.168.10.0/24")
            
        Returns:
            List of IP address strings
            
        Raises:
            ValueError: If CIDR notation is invalid
        """
        try:
            network = ipaddress.IPv4Network(cidr, strict=False)
            # Exclude network and broadcast addresses
            hosts = list(network.hosts())
            return [str(ip) for ip in hosts]
        except (ValueError, ipaddress.AddressValueError, ipaddress.NetmaskValueError) as e:
            raise ValueError(f"Invalid CIDR notation: {cidr}") from e
    
    @staticmethod
    def check_tcp_port(ip: str, port: int, timeout: int = 2) -> bool:
        """
        Check if a TCP port is open on the target IP.
        
        Args:
            ip: IP address to check
            port: TCP port number
            timeout: Connection timeout in seconds
            
        Returns:
            bool: True if port is open, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    @staticmethod
    def check_ip_status(ip: str, timeout: int = 2) -> Tuple[bool, str]:
        """
        Check if IP is online using multi-method detection.
        First tries ICMP ping, then falls back to TCP port checks.
        
        Args:
            ip: IP address to check
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (is_online, detection_method)
        """
        # Method 1: Try ICMP ping first
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', '-w' if platform.system().lower() == 'windows' else '-W', 
                      str(timeout * 1000) if platform.system().lower() == 'windows' else str(timeout),
                      ip]
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 1
            )
            
            if result.returncode == 0:
                return (True, 'icmp')
                
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
        
        # Method 2: Fallback to TCP port checks
        common_ports = [(22, 'tcp_22'), (80, 'tcp_80'), (443, 'tcp_443')]
        
        for port, method in common_ports:
            if NetworkScannerService.check_tcp_port(ip, port, timeout=timeout):
                return (True, method)
        
        return (False, 'none')
    
    @staticmethod
    def find_tracked_asset(ip: str) -> Optional[Asset]:
        """
        Find asset with matching IP address.
        
        Args:
            ip: IP address to lookup
            
        Returns:
            Asset instance or None
        """
        try:
            # Query assets with matching IP address
            asset = Asset.objects.filter(
                ip_address__address=ip,
                status='active'
            ).select_related('ip_address').first()
            return asset
        except Exception:
            return None
    
    @staticmethod
    def execute_scan(scan_job: ScanJob) -> Dict[str, Any]:
        """
        Execute network scan for configured IP ranges.
        
        Args:
            scan_job: ScanJob instance to execute
            
        Returns:
            Summary dictionary with counts and statistics
        """
        try:
            # Load active configuration
            config = ScanConfiguration.objects.filter(is_active=True).first()
            if not config or not config.ip_ranges:
                raise ValueError("No active scan configuration with IP ranges found")
            
            # Expand all CIDR ranges to individual IPs
            all_ips = []
            for cidr in config.ip_ranges:
                try:
                    ips = NetworkScannerService.expand_cidr_range(cidr)
                    all_ips.extend(ips)
                except ValueError as e:
                    print(f"Skipping invalid CIDR {cidr}: {e}")
            
            if not all_ips:
                raise ValueError("No valid IP addresses to scan")
            
            # Update scan job to running
            scan_job.status = 'running'
            scan_job.started_at = timezone.now()
            scan_job.total_ips = len(all_ips)
            scan_job.save()
            
            # Parallel scanning
            results_batch = []
            online_count = 0
            offline_count = 0
            tracked_count = 0
            discovered_count = 0
            
            with ThreadPoolExecutor(max_workers=config.concurrent_checks) as executor:
                # Submit all IP checks
                future_to_ip = {
                    executor.submit(NetworkScannerService.check_ip_status, ip, config.timeout_seconds): ip
                    for ip in all_ips
                }
                
                # Process results as they complete
                for future in as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    try:
                        is_online, detection_method = future.result()
                        
                        # Find if this IP is tracked
                        asset = None
                        is_tracked = False
                        if is_online:
                            asset = NetworkScannerService.find_tracked_asset(ip)
                            is_tracked = asset is not None
                        
                        # Create scan result
                        result = ScanResult(
                            scan_job=scan_job,
                            ip_address=ip,
                            is_online=is_online,
                            detection_method=detection_method,
                            is_tracked=is_tracked,
                            asset=asset
                        )
                        results_batch.append(result)
                        
                        # Update counts
                        if is_online:
                            online_count += 1
                            if is_tracked:
                                tracked_count += 1
                            else:
                                discovered_count += 1
                        else:
                            offline_count += 1
                        
                        # Bulk create in batches of 100
                        if len(results_batch) >= 100:
                            ScanResult.objects.bulk_create(results_batch)
                            results_batch = []
                            
                    except Exception as e:
                        print(f"Error checking {ip}: {e}")
            
            # Create any remaining results
            if results_batch:
                ScanResult.objects.bulk_create(results_batch)
            
            # Update scan job with final counts
            scan_job.status = 'completed'
            scan_job.completed_at = timezone.now()
            scan_job.online_count = online_count
            scan_job.offline_count = offline_count
            scan_job.tracked_count = tracked_count
            scan_job.discovered_count = discovered_count
            scan_job.save()
            
            return {
                'total_ips': scan_job.total_ips,
                'online': online_count,
                'offline': offline_count,
                'tracked': tracked_count,
                'discovered': discovered_count,
                'timestamp': scan_job.completed_at.isoformat()
            }
            
        except Exception as e:
            # Mark scan as failed
            scan_job.status = 'failed'
            scan_job.error_message = str(e)
            scan_job.completed_at = timezone.now()
            scan_job.save()
            raise
    
    @staticmethod
    def export_results_csv(scan_job: ScanJob) -> str:
        """
        Export scan results to CSV format.
        
        Args:
            scan_job: ScanJob to export
            
        Returns:
            CSV content as string
        """
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ip_address', 'is_online', 'is_tracked', 'asset_tag', 
            'hostname', 'detection_method', 'checked_at'
        ])
        
        # Write data rows
        results = scan_job.results.select_related('asset').all()
        for result in results:
            writer.writerow([
                result.ip_address,
                'Yes' if result.is_online else 'No',
                'Yes' if result.is_tracked else 'No',
                result.asset.asset_tag if result.asset else '',
                result.asset.hostname if result.asset else '',
                result.get_detection_method_display(),
                result.checked_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return output.getvalue()
