"""
Unit tests for management commands.
"""
import pytest
from django.core.management import call_command
from django.test import TestCase
from io import StringIO
from assets.models import IPRange, IPAddress


class TestInitializeIPRangesCommand(TestCase):
    """Test cases for initialize_ip_ranges management command."""
    
    def test_initialize_ip_ranges_creates_ranges_and_addresses(self):
        """Test that the command creates all IP ranges and addresses."""
        # Ensure database is clean
        IPAddress.objects.all().delete()
        IPRange.objects.all().delete()
        
        # Run the command
        out = StringIO()
        call_command('initialize_ip_ranges', stdout=out)
        
        # Verify IP ranges were created
        assert IPRange.objects.count() == 4
        
        # Verify all expected ranges exist
        expected_ranges = ['192.168.10.x', '192.168.11.x', '192.168.70.x', '192.168.50.x']
        for range_pattern in expected_ranges:
            assert IPRange.objects.filter(range_pattern=range_pattern).exists()
        
        # Verify IP addresses were created (254 per range * 4 ranges = 1016)
        assert IPAddress.objects.count() == 1016
        
        # Verify all IPs are marked as free
        assert IPAddress.objects.filter(is_assigned=False).count() == 1016
        assert IPAddress.objects.filter(is_assigned=True).count() == 0
        
        # Verify each range has 254 addresses
        for ip_range in IPRange.objects.all():
            assert ip_range.ip_addresses.count() == 254
    
    def test_initialize_ip_ranges_generates_correct_ip_addresses(self):
        """Test that IP addresses are generated from 1 to 254."""
        # Ensure database is clean
        IPAddress.objects.all().delete()
        IPRange.objects.all().delete()
        
        # Run the command
        call_command('initialize_ip_ranges', stdout=StringIO())
        
        # Check one range in detail
        ip_range = IPRange.objects.get(range_pattern='192.168.10.x')
        
        # Verify first and last IPs
        assert IPAddress.objects.filter(address='192.168.10.1').exists()
        assert IPAddress.objects.filter(address='192.168.10.254').exists()
        
        # Verify 0 and 255 are not created
        assert not IPAddress.objects.filter(address='192.168.10.0').exists()
        assert not IPAddress.objects.filter(address='192.168.10.255').exists()
        
        # Verify all IPs from 1 to 254 exist
        for i in range(1, 255):
            assert IPAddress.objects.filter(address=f'192.168.10.{i}').exists()
    
    def test_initialize_ip_ranges_idempotent_without_force(self):
        """Test that running the command twice without --force doesn't duplicate data."""
        # Ensure database is clean
        IPAddress.objects.all().delete()
        IPRange.objects.all().delete()
        
        # Run the command first time
        call_command('initialize_ip_ranges', stdout=StringIO())
        first_count = IPAddress.objects.count()
        
        # Run the command second time
        out = StringIO()
        call_command('initialize_ip_ranges', stdout=out)
        second_count = IPAddress.objects.count()
        
        # Verify counts are the same
        assert first_count == second_count == 1016
        
        # Verify warning message
        assert 'already exist' in out.getvalue()
    
    def test_initialize_ip_ranges_force_flag_recreates_data(self):
        """Test that --force flag recreates IP ranges and addresses."""
        # Ensure database is clean
        IPAddress.objects.all().delete()
        IPRange.objects.all().delete()
        
        # Run the command first time
        call_command('initialize_ip_ranges', stdout=StringIO())
        
        # Modify an IP to test recreation
        ip = IPAddress.objects.first()
        ip.is_assigned = True
        ip.save()
        
        # Run with --force
        out = StringIO()
        call_command('initialize_ip_ranges', '--force', stdout=out)
        
        # Verify all IPs are free again
        assert IPAddress.objects.filter(is_assigned=True).count() == 0
        assert IPAddress.objects.filter(is_assigned=False).count() == 1016
        
        # Verify force message
        assert 'Force flag detected' in out.getvalue()
    
    def test_ip_addresses_linked_to_correct_ranges(self):
        """Test that IP addresses are correctly linked to their ranges."""
        # Ensure database is clean
        IPAddress.objects.all().delete()
        IPRange.objects.all().delete()
        
        # Run the command
        call_command('initialize_ip_ranges', stdout=StringIO())
        
        # Verify each IP is linked to the correct range
        for range_pattern, network_prefix in [
            ('192.168.10.x', '192.168.10'),
            ('192.168.11.x', '192.168.11'),
            ('192.168.70.x', '192.168.70'),
            ('192.168.50.x', '192.168.50'),
        ]:
            ip_range = IPRange.objects.get(range_pattern=range_pattern)
            
            # Check that all IPs in this range are linked to this IPRange
            ips_in_range = IPAddress.objects.filter(address__startswith=network_prefix)
            assert ips_in_range.count() == 254
            
            for ip in ips_in_range:
                assert ip.ip_range == ip_range
