"""
Property-based tests for FilterService using Hypothesis.

These tests validate the correctness properties of the FilterService
for asset filtering functionality.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase
from django.contrib.auth.models import User
from assets.models import OperatingSystem, Team, IPRange, IPAddress, Asset
from assets.services.filter_service import FilterService


@pytest.mark.django_db
class TestFilterServiceProperties(TestCase):
    """Property-based tests for FilterService."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create user
        self.user, _ = User.objects.get_or_create(
            username='admin_filter_test',
            defaults={'password': 'password'}
        )
        
        # Create OS options
        self.os1, _ = OperatingSystem.objects.get_or_create(name="Windows 10 Filter")
        self.os2, _ = OperatingSystem.objects.get_or_create(name="Windows 11 Filter")
        self.os3, _ = OperatingSystem.objects.get_or_create(name="Ubuntu 20.04 Filter")
        
        # Create Team options
        self.team1, _ = Team.objects.get_or_create(name="Engineering Filter")
        self.team2, _ = Team.objects.get_or_create(name="IT Filter")
        self.team3, _ = Team.objects.get_or_create(name="Marketing Filter")
        
        # Create IP range and addresses
        self.ip_range, _ = IPRange.objects.get_or_create(
            range_pattern="192.168.100.x",
            defaults={'network_prefix': "192.168.100"}
        )
        
        # Clean up any existing IPs and create fresh ones
        IPAddress.objects.filter(ip_range=self.ip_range).delete()
        self.ips = []
        for i in range(1, 31):  # Create 30 IPs for testing
            ip = IPAddress.objects.create(
                address=f"192.168.100.{i}",
                ip_range=self.ip_range,
                is_assigned=False
            )
            self.ips.append(ip)
        
        self.filter_service = FilterService()
    
    @given(
        count=st.integers(min_value=1, max_value=20),
        filter_type=st.sampled_from(['operating_system', 'asset_tag', 'team', 'assigned_to'])
    )
    @settings(max_examples=50, deadline=None)
    def test_property_7_filter_monotonicity(self, count, filter_type):
        """
        **Validates: Requirements 13.1, 13.2, 13.3**
        
        Property 7: Filter monotonicity
        
        For any filter operation, the size of the filtered set should be less than 
        or equal to the size of the original set. Filters can only reduce or maintain 
        the set size, never increase it.
        
        This property ensures filter correctness and data integrity.
        """
        # Ensure we have enough IPs
        assume(count <= len(self.ips))
        
        # Create diverse assets
        created_assets = []
        os_list = [self.os1, self.os2, self.os3]
        team_list = [self.team1, self.team2, self.team3, None]
        
        for i in range(count):
            asset_tag = f'BIDC_FILTER_MONO_{i}_{count}'
            
            # Assign IP if available
            ip_address = self.ips[i] if i < len(self.ips) else None
            if ip_address:
                ip_address.is_assigned = True
                ip_address.save()
            
            # Vary attributes to create diverse dataset
            os = os_list[i % len(os_list)]
            team = team_list[i % len(team_list)]
            assigned_to = f'User {i % 5}' if i % 2 == 0 else None
            
            asset = Asset.objects.create(
                asset_tag=asset_tag,
                system_type='Desktop',
                operating_system=os,
                ip_address=ip_address,
                particulars=f'Test particulars {i}',
                assigned_to=assigned_to,
                team=team,
                status='active'
            )
            if ip_address:
                ip_address.assigned_to_asset = asset
                ip_address.save()
            
            created_assets.append(asset)
        
        # Get base queryset
        base_queryset = Asset.objects.filter(
            asset_tag__startswith=f'BIDC_FILTER_MONO_'
        ).filter(asset_tag__contains=f'_{count}')
        original_count = base_queryset.count()
        
        # Apply filter based on type
        filters = {}
        if filter_type == 'operating_system':
            filters = {'operating_system': self.os1.id}
        elif filter_type == 'asset_tag':
            filters = {'asset_tag': f'BIDC_FILTER_MONO_0'}
        elif filter_type == 'team':
            filters = {'team': self.team1.id}
        elif filter_type == 'assigned_to':
            filters = {'assigned_to': 'User 0'}
        
        filtered_queryset = self.filter_service.apply_filters(base_queryset, filters)
        filtered_count = filtered_queryset.count()
        
        # Verify monotonicity: filtered_count <= original_count
        assert filtered_count <= original_count, \
            f"Filter monotonicity violated: filtered count ({filtered_count}) > original count ({original_count})"
        
        # Clean up
        for asset in created_assets:
            asset.delete()
        
        # Reset IPs
        for ip in self.ips:
            ip.is_assigned = False
            ip.assigned_to_asset = None
            ip.save()
    
    @given(
        count=st.integers(min_value=5, max_value=20),
        filter1_type=st.sampled_from(['operating_system', 'team']),
        filter2_type=st.sampled_from(['asset_tag', 'assigned_to'])
    )
    @settings(max_examples=50, deadline=None)
    def test_property_8_filter_composition(self, count, filter1_type, filter2_type):
        """
        **Validates: Requirements 13.1, 13.2, 13.3**
        
        Property 8: Filter composition
        
        For any two filters f1 and f2, applying them together should produce the 
        same result as applying them sequentially:
        apply_filters(qs, {f1, f2}) = apply_filters(apply_filters(qs, {f1}), {f2})
        
        This property ensures filter composition is associative and order-independent.
        """
        # Ensure we have enough IPs
        assume(count <= len(self.ips))
        
        # Create diverse assets
        created_assets = []
        os_list = [self.os1, self.os2, self.os3]
        team_list = [self.team1, self.team2, self.team3, None]
        
        for i in range(count):
            asset_tag = f'BIDC_FILTER_COMP_{i}_{count}'
            
            # Assign IP if available
            ip_address = self.ips[i] if i < len(self.ips) else None
            if ip_address:
                ip_address.is_assigned = True
                ip_address.save()
            
            # Vary attributes
            os = os_list[i % len(os_list)]
            team = team_list[i % len(team_list)]
            assigned_to = f'User {i % 3}' if i % 2 == 0 else None
            
            asset = Asset.objects.create(
                asset_tag=asset_tag,
                system_type='Desktop',
                operating_system=os,
                ip_address=ip_address,
                particulars=f'Test particulars {i}',
                assigned_to=assigned_to,
                team=team,
                status='active'
            )
            if ip_address:
                ip_address.assigned_to_asset = asset
                ip_address.save()
            
            created_assets.append(asset)
        
        # Get base queryset
        base_queryset = Asset.objects.filter(
            asset_tag__startswith=f'BIDC_FILTER_COMP_'
        ).filter(asset_tag__contains=f'_{count}')
        
        # Build filter1
        filter1 = {}
        if filter1_type == 'operating_system':
            filter1 = {'operating_system': self.os1.id}
        elif filter1_type == 'team':
            filter1 = {'team': self.team1.id}
        
        # Build filter2
        filter2 = {}
        if filter2_type == 'asset_tag':
            filter2 = {'asset_tag': f'BIDC_FILTER_COMP_'}
        elif filter2_type == 'assigned_to':
            filter2 = {'assigned_to': 'User'}
        
        # Method 1: Apply both filters together
        combined_filters = {**filter1, **filter2}
        result1 = self.filter_service.apply_filters(base_queryset, combined_filters)
        result1_ids = set(result1.values_list('serial_number', flat=True))
        
        # Method 2: Apply filters sequentially
        intermediate = self.filter_service.apply_filters(base_queryset, filter1)
        result2 = self.filter_service.apply_filters(intermediate, filter2)
        result2_ids = set(result2.values_list('serial_number', flat=True))
        
        # Verify composition: both methods produce same result
        assert result1_ids == result2_ids, \
            f"Filter composition violated: combined filters produced {len(result1_ids)} results, " \
            f"sequential filters produced {len(result2_ids)} results"
        
        # Clean up
        for asset in created_assets:
            asset.delete()
        
        # Reset IPs
        for ip in self.ips:
            ip.is_assigned = False
            ip.assigned_to_asset = None
            ip.save()
    
    @given(
        count=st.integers(min_value=5, max_value=20),
        filter_type=st.sampled_from(['operating_system', 'asset_tag', 'team', 'assigned_to'])
    )
    @settings(max_examples=50, deadline=None)
    def test_property_9_filter_idempotence(self, count, filter_type):
        """
        **Validates: Requirements 13.1, 13.2, 13.3**
        
        Property 9: Filter idempotence
        
        For any filter f, applying it twice should produce the same result as 
        applying it once:
        apply_filters(apply_filters(qs, f), f) = apply_filters(qs, f)
        
        This property ensures filters are idempotent and don't have side effects.
        """
        # Ensure we have enough IPs
        assume(count <= len(self.ips))
        
        # Create diverse assets
        created_assets = []
        os_list = [self.os1, self.os2, self.os3]
        team_list = [self.team1, self.team2, self.team3, None]
        
        for i in range(count):
            asset_tag = f'BIDC_FILTER_IDEMP_{i}_{count}'
            
            # Assign IP if available
            ip_address = self.ips[i] if i < len(self.ips) else None
            if ip_address:
                ip_address.is_assigned = True
                ip_address.save()
            
            # Vary attributes
            os = os_list[i % len(os_list)]
            team = team_list[i % len(team_list)]
            assigned_to = f'User {i % 4}' if i % 2 == 0 else None
            
            asset = Asset.objects.create(
                asset_tag=asset_tag,
                system_type='Desktop',
                operating_system=os,
                ip_address=ip_address,
                particulars=f'Test particulars {i}',
                assigned_to=assigned_to,
                team=team,
                status='active'
            )
            if ip_address:
                ip_address.assigned_to_asset = asset
                ip_address.save()
            
            created_assets.append(asset)
        
        # Get base queryset
        base_queryset = Asset.objects.filter(
            asset_tag__startswith=f'BIDC_FILTER_IDEMP_'
        ).filter(asset_tag__contains=f'_{count}')
        
        # Build filter
        filters = {}
        if filter_type == 'operating_system':
            filters = {'operating_system': self.os1.id}
        elif filter_type == 'asset_tag':
            filters = {'asset_tag': f'BIDC_FILTER_IDEMP_'}
        elif filter_type == 'team':
            filters = {'team': self.team1.id}
        elif filter_type == 'assigned_to':
            filters = {'assigned_to': 'User'}
        
        # Apply filter once
        result1 = self.filter_service.apply_filters(base_queryset, filters)
        result1_ids = set(result1.values_list('serial_number', flat=True))
        
        # Apply filter twice (idempotence test)
        result2 = self.filter_service.apply_filters(result1, filters)
        result2_ids = set(result2.values_list('serial_number', flat=True))
        
        # Verify idempotence: applying filter twice produces same result as once
        assert result1_ids == result2_ids, \
            f"Filter idempotence violated: first application produced {len(result1_ids)} results, " \
            f"second application produced {len(result2_ids)} results"
        
        # Also verify counts match
        assert result1.count() == result2.count(), \
            f"Filter idempotence violated: counts differ ({result1.count()} vs {result2.count()})"
        
        # Clean up
        for asset in created_assets:
            asset.delete()
        
        # Reset IPs
        for ip in self.ips:
            ip.is_assigned = False
            ip.assigned_to_asset = None
            ip.save()
