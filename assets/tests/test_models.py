"""
Unit tests for models.
"""
import pytest
from datetime import datetime
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from assets.models import Asset, IPAddress, IPRange, OperatingSystem


class TestAssetModel(TestCase):
    """Test cases for Asset model field constraints."""

    def setUp(self):
        """Set up test data."""
        self.os = OperatingSystem.objects.create(name="Windows 10")
        self.ip_range = IPRange.objects.create(
            range_pattern="10.0.0.x",
            network_prefix="10.0.0"
        )

    def test_manufacturer_max_length_within_limit(self):
        """Test manufacturer field accepts values within max_length=100."""
        asset = Asset.objects.create(
            asset_tag="BIDC100",
            system_type="Desktop",
            operating_system=self.os,
            manufacturer="Dell Technologies"
        )
        asset.full_clean()
        self.assertEqual(asset.manufacturer, "Dell Technologies")

    def test_manufacturer_max_length_at_boundary(self):
        """Test manufacturer field accepts exactly 100 characters."""
        value = "A" * 100
        asset = Asset.objects.create(
            asset_tag="BIDC101",
            system_type="Desktop",
            operating_system=self.os,
            manufacturer=value
        )
        asset.full_clean()
        self.assertEqual(asset.manufacturer, value)

    def test_manufacturer_max_length_exceeds_limit(self):
        """Test manufacturer field rejects values exceeding max_length=100."""
        value = "A" * 101
        asset = Asset(
            asset_tag="BIDC102",
            system_type="Desktop",
            operating_system=self.os,
            manufacturer=value
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_scrapping_reason_accepts_multiline_text(self):
        """Test scrapping_reason TextField accepts multi-line text."""
        multiline_reason = "Hardware failure.\nMotherboard burned out.\nNot economical to repair."
        asset = Asset.objects.create(
            asset_tag="BIDC103",
            system_type="Laptop",
            operating_system=self.os,
            scrapping_reason=multiline_reason
        )
        asset.refresh_from_db()
        self.assertEqual(asset.scrapping_reason, multiline_reason)

    def test_scrapping_reason_accepts_long_text(self):
        """Test scrapping_reason TextField accepts long text content."""
        long_reason = "Detailed reason. " * 200
        asset = Asset.objects.create(
            asset_tag="BIDC104",
            system_type="Desktop",
            operating_system=self.os,
            scrapping_reason=long_reason
        )
        asset.refresh_from_db()
        self.assertEqual(asset.scrapping_reason, long_reason)


class TestIPAddressModel(TestCase):
    """Test cases for IPAddress model freed_date field."""

    def setUp(self):
        """Set up test data."""
        self.ip_range = IPRange.objects.create(
            range_pattern="10.0.1.x",
            network_prefix="10.0.1"
        )

    def test_freed_date_accepts_datetime(self):
        """Test freed_date field accepts datetime values."""
        now = timezone.now()
        ip = IPAddress.objects.create(
            address="10.0.1.1",
            ip_range=self.ip_range,
            freed_date=now
        )
        ip.refresh_from_db()
        self.assertIsNotNone(ip.freed_date)
        self.assertEqual(ip.freed_date.year, now.year)
        self.assertEqual(ip.freed_date.month, now.month)
        self.assertEqual(ip.freed_date.day, now.day)

    def test_freed_date_defaults_to_none(self):
        """Test freed_date is None by default."""
        ip = IPAddress.objects.create(
            address="10.0.1.2",
            ip_range=self.ip_range
        )
        self.assertIsNone(ip.freed_date)

    def test_freed_date_accepts_specific_datetime(self):
        """Test freed_date stores a specific datetime accurately."""
        specific_time = timezone.make_aware(datetime(2024, 6, 15, 14, 30, 0))
        ip = IPAddress.objects.create(
            address="10.0.1.3",
            ip_range=self.ip_range,
            freed_date=specific_time
        )
        ip.refresh_from_db()
        self.assertEqual(ip.freed_date, specific_time)
