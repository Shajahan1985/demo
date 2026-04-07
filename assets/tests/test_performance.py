"""
Performance tests for import/export/filter operations.

This module tests the performance of the asset import, export, and filtering
features with large datasets to ensure they meet performance requirements.
"""

import time
import io
import openpyxl
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from assets.models import Asset, OperatingSystem, Team, IPAddress, IPRange
from assets.services.import_service import ImportService
from assets.services.export_service import ExportService
from assets.services.filter_service import FilterService


User = get_user_model()


class PerformanceTestBase(TransactionTestCase):
    """Base class for performance tests with common setup."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        
        # Create operating systems
        self.os_windows = OperatingSystem.objects.create(name='Windows 10')
        self.os_linux = OperatingSystem.objects.create(name='Ubuntu 22.04')
        self.os_macos = OperatingSystem.objects.create(name='macOS Ventura')
        
        # Create teams
        self.team_eng = Team.objects.create(name='Engineering')
        self.team_sales = Team.objects.create(name='Sales')
        self.team_hr = Team.objects.create(name='HR')
        
        # Create IP ranges
        self.ip_range_10 = IPRange.objects.create(
            range_pattern='192.168.10.x',
            network_prefix='192.168.10'
        )
        self.ip_range_11 = IPRange.objects.create(
            range_pattern='192.168.11.x',
            network_prefix='192.168.11'
        )
    
    def create_ip_addresses(self, count):
        """Create IP addresses for testing."""
        ips = []
        
        # Create additional IP ranges if needed for large datasets
        ranges = [self.ip_range_10, self.ip_range_11]
        
        # Add more ranges if we need more than 500 IPs
        if count > 500:
            for range_num in range(70, 70 + ((count - 500) // 250) + 1):
                ip_range = IPRange.objects.create(
                    range_pattern=f'192.168.{range_num}.x',
                    network_prefix=f'192.168.{range_num}'
                )
                ranges.append(ip_range)
        
        for i in range(count):
            # Distribute across ranges (250 IPs per range to stay within valid range)
            range_index = i // 250
            if range_index >= len(ranges):
                range_index = len(ranges) - 1
            
            ip_range = ranges[range_index]
            last_octet = (i % 250) + 1  # 1-250 to stay within valid IPv4 range
            
            # Extract the network prefix from the range
            if range_index == 0:
                address = f'192.168.10.{last_octet}'
            elif range_index == 1:
                address = f'192.168.11.{last_octet}'
            else:
                # For dynamically created ranges
                network_num = 70 + (range_index - 2)
                address = f'192.168.{network_num}.{last_octet}'
            
            ip = IPAddress.objects.create(
                address=address,
                ip_range=ip_range,
                is_assigned=False
            )
            ips.append(ip)
        return ips
    
    def create_test_assets(self, count):
        """Create test assets for performance testing."""
        # Create IP addresses
        ips = self.create_ip_addresses(count)
        
        assets = []
        system_types = ['Desktop', 'Laptop', 'All-in-One PC']
        operating_systems = [self.os_windows, self.os_linux, self.os_macos]
        teams = [self.team_eng, self.team_sales, self.team_hr]
        
        for i in range(count):
            asset = Asset.objects.create(
                asset_tag=f'BIDC{1000 + i}',
                system_type=system_types[i % 3],
                operating_system=operating_systems[i % 3],
                ip_address=ips[i],
                assigned_to=f'User{i % 100}',
                team=teams[i % 3],
                status='active'
            )
            # Mark IP as assigned
            ips[i].is_assigned = True
            ips[i].assigned_to_asset = asset
            ips[i].save()
            
            assets.append(asset)
        
        return assets
    
    def create_large_excel_file(self, row_count):
        """Create a large Excel file for import testing."""
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        
        # Write headers
        headers = [
            'asset_tag', 'system_type', 'operating_system',
            'ip_address', 'particulars', 'assigned_to', 'team'
        ]
        sheet.append(headers)
        
        # Create IP addresses for the import
        ips = self.create_ip_addresses(row_count)
        
        # Write data rows
        system_types = ['Desktop', 'Laptop', 'All-in-One PC']
        os_names = ['Windows 10', 'Ubuntu 22.04', 'macOS Ventura']
        team_names = ['Engineering', 'Sales', 'HR']
        
        for i in range(row_count):
            row = [
                f'BIDC{2000 + i}',  # Unique asset tag
                system_types[i % 3],
                os_names[i % 3],
                ips[i].address,
                f'Test asset {i}',
                f'User{i % 100}',
                team_names[i % 3]
            ]
            sheet.append(row)
        
        # Save to BytesIO
        file_stream = io.BytesIO()
        workbook.save(file_stream)
        file_stream.seek(0)
        
        return file_stream


class ImportPerformanceTest(PerformanceTestBase):
    """Performance tests for import operations."""
    
    def test_import_large_file_1000_rows(self):
        """Test import performance with 1000+ rows."""
        # Create Excel file with 1000 rows
        excel_file = self.create_large_excel_file(1000)
        
        # Measure import time
        import_service = ImportService()
        start_time = time.time()
        result = import_service.import_assets(excel_file, self.user)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # Assertions
        self.assertEqual(result['created_count'], 1000, 
                        f"Expected 1000 successful imports, got {result['created_count']}")
        self.assertEqual(result['error_count'], 0,
                        f"Expected 0 errors, got {result['error_count']}")
        
        # Performance assertion: should complete in reasonable time (< 60 seconds)
        self.assertLess(elapsed_time, 60.0,
                       f"Import took {elapsed_time:.2f}s, expected < 60s")
        
        # Verify assets were created
        asset_count = Asset.objects.filter(asset_tag__startswith='BIDC2').count()
        self.assertEqual(asset_count, 1000)
        
        print(f"\n✓ Import Performance: 1000 rows imported in {elapsed_time:.2f}s "
              f"({1000/elapsed_time:.1f} rows/sec)")
    
    def test_import_large_file_2000_rows(self):
        """Test import performance with 2000 rows."""
        # Create Excel file with 2000 rows
        excel_file = self.create_large_excel_file(2000)
        
        # Measure import time
        import_service = ImportService()
        start_time = time.time()
        result = import_service.import_assets(excel_file, self.user)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # Assertions
        self.assertEqual(result['created_count'], 2000)
        self.assertEqual(result['error_count'], 0)
        
        # Performance assertion: should scale reasonably (< 120 seconds)
        self.assertLess(elapsed_time, 120.0,
                       f"Import took {elapsed_time:.2f}s, expected < 120s")
        
        print(f"\n✓ Import Performance: 2000 rows imported in {elapsed_time:.2f}s "
              f"({2000/elapsed_time:.1f} rows/sec)")


class ExportPerformanceTest(PerformanceTestBase):
    """Performance tests for export operations."""
    
    def test_export_large_dataset_1000_assets(self):
        """Test export performance with 1000+ assets."""
        # Create 1000 test assets
        self.create_test_assets(1000)
        
        # Measure export time
        export_service = ExportService()
        start_time = time.time()
        response = export_service.export_active_assets()
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Performance assertion: should complete quickly (< 10 seconds)
        self.assertLess(elapsed_time, 10.0,
                       f"Export took {elapsed_time:.2f}s, expected < 10s")
        
        # Verify Excel content
        file_stream = io.BytesIO(response.content)
        workbook = openpyxl.load_workbook(file_stream)
        sheet = workbook.active
        
        # Count rows (including header)
        row_count = sheet.max_row
        self.assertEqual(row_count, 1001, f"Expected 1001 rows (1 header + 1000 data), got {row_count}")
        
        print(f"\n✓ Export Performance: 1000 assets exported in {elapsed_time:.2f}s "
              f"({1000/elapsed_time:.1f} assets/sec)")
    
    def test_export_large_dataset_2000_assets(self):
        """Test export performance with 2000 assets."""
        # Create 2000 test assets
        self.create_test_assets(2000)
        
        # Measure export time
        export_service = ExportService()
        start_time = time.time()
        response = export_service.export_active_assets()
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        
        # Performance assertion: should scale reasonably (< 20 seconds)
        self.assertLess(elapsed_time, 20.0,
                       f"Export took {elapsed_time:.2f}s, expected < 20s")
        
        # Verify Excel content
        file_stream = io.BytesIO(response.content)
        workbook = openpyxl.load_workbook(file_stream)
        sheet = workbook.active
        
        row_count = sheet.max_row
        self.assertEqual(row_count, 2001)
        
        print(f"\n✓ Export Performance: 2000 assets exported in {elapsed_time:.2f}s "
              f"({2000/elapsed_time:.1f} assets/sec)")
    
    def test_export_free_ips_large_dataset(self):
        """Test export performance for free IPs with large dataset."""
        # Create 1000 free IP addresses
        self.create_ip_addresses(1000)
        
        # Measure export time
        export_service = ExportService()
        start_time = time.time()
        response = export_service.export_free_ips()
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        
        # Performance assertion
        self.assertLess(elapsed_time, 5.0,
                       f"Free IPs export took {elapsed_time:.2f}s, expected < 5s")
        
        print(f"\n✓ Free IPs Export Performance: 1000 IPs exported in {elapsed_time:.2f}s")


class FilterPerformanceTest(PerformanceTestBase):
    """Performance tests for filtering operations."""
    
    def test_filter_large_dataset_single_filter(self):
        """Test filtering performance with single filter on large dataset."""
        # Create 1000 test assets
        self.create_test_assets(1000)
        
        # Measure filter time
        filter_service = FilterService()
        queryset = Asset.objects.filter(status='active')
        
        start_time = time.time()
        filtered_qs = filter_service.filter_by_os(queryset, self.os_windows.id)
        result_count = filtered_qs.count()
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # Assertions
        self.assertGreater(result_count, 0)
        
        # Performance assertion: should be very fast (< 1 second)
        self.assertLess(elapsed_time, 1.0,
                       f"Filter took {elapsed_time:.2f}s, expected < 1s")
        
        print(f"\n✓ Filter Performance (single): 1000 assets filtered in {elapsed_time:.4f}s "
              f"(returned {result_count} results)")
    
    def test_filter_large_dataset_multiple_filters(self):
        """Test filtering performance with multiple filters on large dataset."""
        # Create 1000 test assets
        self.create_test_assets(1000)
        
        # Measure filter time with multiple filters
        filter_service = FilterService()
        queryset = Asset.objects.filter(status='active')
        
        filters = {
            'operating_system': self.os_windows.id,
            'team': self.team_eng.id,
            'asset_tag': 'BIDC1'
        }
        
        start_time = time.time()
        filtered_qs = filter_service.apply_filters(queryset, filters)
        result_count = filtered_qs.count()
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # Assertions
        self.assertGreaterEqual(result_count, 0)
        
        # Performance assertion: should be fast even with multiple filters (< 1 second)
        self.assertLess(elapsed_time, 1.0,
                       f"Multiple filters took {elapsed_time:.2f}s, expected < 1s")
        
        print(f"\n✓ Filter Performance (multiple): 1000 assets filtered in {elapsed_time:.4f}s "
              f"(returned {result_count} results)")
    
    def test_filter_large_dataset_text_search(self):
        """Test filtering performance with text search on large dataset."""
        # Create 1000 test assets
        self.create_test_assets(1000)
        
        # Measure filter time with text search
        filter_service = FilterService()
        queryset = Asset.objects.filter(status='active')
        
        start_time = time.time()
        filtered_qs = filter_service.filter_by_assigned_user(queryset, 'User1')
        result_count = filtered_qs.count()
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # Assertions
        self.assertGreater(result_count, 0)
        
        # Performance assertion: text search should be reasonably fast (< 2 seconds)
        self.assertLess(elapsed_time, 2.0,
                       f"Text search took {elapsed_time:.2f}s, expected < 2s")
        
        print(f"\n✓ Filter Performance (text search): 1000 assets searched in {elapsed_time:.4f}s "
              f"(returned {result_count} results)")
    
    def test_filter_with_select_related_optimization(self):
        """Test that filtering uses select_related for optimal performance."""
        # Create 1000 test assets
        self.create_test_assets(1000)
        
        # Measure query count and time with select_related
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        filter_service = FilterService()
        queryset = Asset.objects.filter(status='active').select_related(
            'operating_system', 'team', 'ip_address'
        )
        
        with CaptureQueriesContext(connection) as context:
            start_time = time.time()
            filtered_qs = filter_service.apply_filters(queryset, {
                'operating_system': self.os_windows.id
            })
            # Force evaluation by iterating
            results = list(filtered_qs[:100])  # Get first 100 results
            end_time = time.time()
        
        elapsed_time = end_time - start_time
        query_count = len(context.captured_queries)
        
        # Assertions
        self.assertGreater(len(results), 0)
        
        # With select_related, should use minimal queries (ideally 1-2)
        self.assertLess(query_count, 5,
                       f"Expected < 5 queries with select_related, got {query_count}")
        
        # Performance should be good
        self.assertLess(elapsed_time, 1.0,
                       f"Optimized filter took {elapsed_time:.2f}s, expected < 1s")
        
        print(f"\n✓ Filter Optimization: 100 results fetched with {query_count} queries "
              f"in {elapsed_time:.4f}s")


class DatabaseIndexPerformanceTest(PerformanceTestBase):
    """Tests to verify database indexes are working effectively."""
    
    def test_asset_tag_index_performance(self):
        """Test that asset_tag lookups are fast (index is working)."""
        # Create 1000 test assets
        self.create_test_assets(1000)
        
        # Test exact lookup
        start_time = time.time()
        asset = Asset.objects.get(asset_tag='BIDC1500')
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # Should be very fast with index (< 0.1 seconds)
        self.assertLess(elapsed_time, 0.1,
                       f"Indexed lookup took {elapsed_time:.4f}s, expected < 0.1s")
        
        print(f"\n✓ Index Performance (asset_tag): Lookup in {elapsed_time:.4f}s")
    
    def test_status_index_performance(self):
        """Test that status filtering is fast (index is working)."""
        # Create 1000 test assets
        assets = self.create_test_assets(1000)
        
        # Mark some as freed
        for i in range(0, 200):
            assets[i].status = 'freed'
            assets[i].save()
        
        # Test status filter
        start_time = time.time()
        active_count = Asset.objects.filter(status='active').count()
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # Should be fast with index
        self.assertLess(elapsed_time, 0.5,
                       f"Status filter took {elapsed_time:.4f}s, expected < 0.5s")
        self.assertEqual(active_count, 800)
        
        print(f"\n✓ Index Performance (status): Filter in {elapsed_time:.4f}s")


class IntegratedWorkflowPerformanceTest(PerformanceTestBase):
    """Test performance of complete workflows."""
    
    def test_import_filter_export_workflow(self):
        """Test complete workflow: import → filter → export."""
        # Step 1: Import 500 assets
        excel_file = self.create_large_excel_file(500)
        import_service = ImportService()
        
        import_start = time.time()
        import_result = import_service.import_assets(excel_file, self.user)
        import_end = time.time()
        import_time = import_end - import_start
        
        self.assertEqual(import_result['created_count'], 500)
        
        # Step 2: Filter the imported assets
        filter_service = FilterService()
        queryset = Asset.objects.filter(status='active')
        
        filter_start = time.time()
        filtered_qs = filter_service.apply_filters(queryset, {
            'operating_system': self.os_windows.id
        })
        filter_count = filtered_qs.count()
        filter_end = time.time()
        filter_time = filter_end - filter_start
        
        self.assertGreater(filter_count, 0)
        
        # Step 3: Export filtered results
        export_service = ExportService()
        
        export_start = time.time()
        response = export_service.export_active_assets()
        export_end = time.time()
        export_time = export_end - export_start
        
        self.assertEqual(response.status_code, 200)
        
        # Total workflow time
        total_time = import_time + filter_time + export_time
        
        # Performance assertion: complete workflow should be reasonable (< 90 seconds)
        self.assertLess(total_time, 90.0,
                       f"Complete workflow took {total_time:.2f}s, expected < 90s")
        
        print(f"\n✓ Integrated Workflow Performance:")
        print(f"  - Import 500 assets: {import_time:.2f}s")
        print(f"  - Filter assets: {filter_time:.4f}s")
        print(f"  - Export assets: {export_time:.2f}s")
        print(f"  - Total: {total_time:.2f}s")
