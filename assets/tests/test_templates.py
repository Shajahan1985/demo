"""Template tests for the scrapped items page.

Tests that the scrapped_items.html template correctly renders all required fields,
handles IP reassignment indicators, and gracefully handles missing data.

Requirements: 1.3, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.1, 7.2
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assets.models import Asset, IPAddress, IPRange, OperatingSystem


class TestScrappedItemsTemplateFields(TestCase):
    """Test that all required fields are displayed on the scrapped items page."""

    def setUp(self):
        self.user = User.objects.create_user(username="tpluser", password="testpass123")
        self.client.login(username="tpluser", password="testpass123")

        self.os = OperatingSystem.objects.create(name="Windows 11")
        self.ip_range = IPRange.objects.create(
            range_pattern="10.0.1.x",
            network_prefix="10.0.1",
        )
        self.ip = IPAddress.objects.create(
            address="10.0.1.50",
            ip_range=self.ip_range,
            is_assigned=False,
        )
        self.scrapped_date = timezone.now() - timedelta(days=3)
        self.asset = Asset.objects.create(
            asset_tag="BIDC100",
            system_type="Desktop",
            operating_system=self.os,
            ip_address=self.ip,
            manufacturer="Dell",
            scrapping_reason="Hardware failure",
            status="scrapped",
            scrapped_date=self.scrapped_date,
        )

    def test_displays_ip_address(self):
        """Requirement 3.1: IP address is displayed for scrapped asset."""
        response = self.client.get(reverse("scrapped_items"))
        self.assertContains(response, "10.0.1.50")

    def test_displays_asset_tag(self):
        """Requirement 3.2: Asset tag (BIDC number) is displayed."""
        response = self.client.get(reverse("scrapped_items"))
        self.assertContains(response, "BIDC100")

    def test_displays_system_type(self):
        """Requirement 3.3: System type is displayed."""
        response = self.client.get(reverse("scrapped_items"))
        self.assertContains(response, "Desktop")

    def test_displays_manufacturer(self):
        """Requirements 1.3, 3.4: System make (manufacturer) is displayed."""
        response = self.client.get(reverse("scrapped_items"))
        self.assertContains(response, "Dell")

    def test_displays_scrapped_date(self):
        """Requirement 3.5: Scrapped date is displayed."""
        response = self.client.get(reverse("scrapped_items"))
        formatted_date = self.scrapped_date.strftime("%Y-%m-%d")
        self.assertContains(response, formatted_date)

    def test_displays_scrapping_reason(self):
        """Requirements 2.3, 3.6: Scrapping reason is displayed."""
        response = self.client.get(reverse("scrapped_items"))
        self.assertContains(response, "Hardware failure")


class TestScrappedItemsTemplateReassignedIP(TestCase):
    """Test IP reassignment indicators on the scrapped items page."""

    def setUp(self):
        self.user = User.objects.create_user(username="tpluser2", password="testpass123")
        self.client.login(username="tpluser2", password="testpass123")

        self.os = OperatingSystem.objects.create(name="Windows 11")
        self.ip_range = IPRange.objects.create(
            range_pattern="10.0.2.x",
            network_prefix="10.0.2",
        )
        # IP that has been reassigned to another asset
        self.reassigned_ip = IPAddress.objects.create(
            address="10.0.2.10",
            ip_range=self.ip_range,
            is_assigned=True,
        )
        # IP that is still free
        self.free_ip = IPAddress.objects.create(
            address="10.0.2.20",
            ip_range=self.ip_range,
            is_assigned=False,
        )
        now = timezone.now()
        self.scrapped_reassigned = Asset.objects.create(
            asset_tag="BIDC200",
            system_type="Laptop",
            operating_system=self.os,
            ip_address=self.reassigned_ip,
            manufacturer="HP",
            scrapping_reason="End of life",
            status="scrapped",
            scrapped_date=now - timedelta(days=5),
        )
        self.scrapped_free = Asset.objects.create(
            asset_tag="BIDC201",
            system_type="Desktop",
            operating_system=self.os,
            ip_address=self.free_ip,
            manufacturer="Lenovo",
            scrapping_reason="Damaged",
            status="scrapped",
            scrapped_date=now - timedelta(days=2),
        )

    def test_reassigned_ip_shows_label(self):
        """Requirement 7.1: Reassigned IPs show '(Reassigned)' label."""
        response = self.client.get(reverse("scrapped_items"))
        self.assertContains(response, "(Reassigned)")

    def test_reassigned_ip_has_red_styling(self):
        """Requirement 7.2: Reassigned IPs are displayed in red."""
        response = self.client.get(reverse("scrapped_items"))
        content = response.content.decode()
        self.assertIn('style="color: red;"', content)
        # Verify the red-styled span contains the reassigned IP
        self.assertIn(
            '<span style="color: red;">10.0.2.10 (Reassigned)</span>',
            content,
        )

    def test_free_ip_no_reassigned_label(self):
        """Free IPs should not show the '(Reassigned)' label."""
        response = self.client.get(reverse("scrapped_items"))
        content = response.content.decode()
        # The free IP should appear without the reassigned label
        self.assertIn("10.0.2.20", content)
        self.assertNotIn("10.0.2.20 (Reassigned)", content)


class TestScrappedItemsTemplateMissingData(TestCase):
    """Test graceful handling of missing data on the scrapped items page."""

    def setUp(self):
        self.user = User.objects.create_user(username="tpluser3", password="testpass123")
        self.client.login(username="tpluser3", password="testpass123")
        self.os = OperatingSystem.objects.create(name="Ubuntu 22.04")

    def test_missing_manufacturer_displays_na(self):
        """Requirement 3.4: Missing manufacturer displays 'N/A'."""
        Asset.objects.create(
            asset_tag="BIDC300",
            system_type="Desktop",
            operating_system=self.os,
            manufacturer=None,
            scrapping_reason="Obsolete",
            status="scrapped",
            scrapped_date=timezone.now(),
        )
        response = self.client.get(reverse("scrapped_items"))
        content = response.content.decode()
        self.assertIn("N/A", content)

    def test_missing_ip_displays_na(self):
        """Requirement 3.1: Missing IP address displays 'N/A'."""
        Asset.objects.create(
            asset_tag="BIDC301",
            system_type="Laptop",
            operating_system=self.os,
            ip_address=None,
            manufacturer="Dell",
            scrapping_reason="Broken screen",
            status="scrapped",
            scrapped_date=timezone.now(),
        )
        response = self.client.get(reverse("scrapped_items"))
        content = response.content.decode()
        self.assertIn("N/A", content)


class TestFreeIPsTemplateFreedDate(TestCase):
    """Test freed_date display on the free IPs page.

    Requirements: 5.2, 5.3, 6.1, 6.2
    """

    def setUp(self):
        self.user = User.objects.create_user(username="freeipuser", password="testpass123")
        self.client.login(username="freeipuser", password="testpass123")

        self.ip_range = IPRange.objects.create(
            range_pattern="10.0.5.x",
            network_prefix="10.0.5",
        )
        self.freed_time = timezone.now() - timedelta(days=7)
        self.ip_with_freed_date = IPAddress.objects.create(
            address="10.0.5.10",
            ip_range=self.ip_range,
            is_assigned=False,
            freed_date=self.freed_time,
        )
        self.ip_without_freed_date = IPAddress.objects.create(
            address="10.0.5.20",
            ip_range=self.ip_range,
            is_assigned=False,
            freed_date=None,
        )

    def test_freed_date_displayed_when_present(self):
        """Requirement 5.3: freed_date is shown for IPs that have been released."""
        response = self.client.get(reverse("free_ips"))
        formatted_date = self.freed_time.strftime("%Y-%m-%d")
        self.assertContains(response, f"Freed: {formatted_date}")

    def test_freed_date_format_is_correct(self):
        """Requirement 5.3: freed_date is formatted as 'Freed: YYYY-MM-DD'."""
        response = self.client.get(reverse("free_ips"))
        content = response.content.decode()
        formatted_date = self.freed_time.strftime("%Y-%m-%d")
        self.assertIn(f"Freed: {formatted_date}", content)

    def test_freed_date_not_shown_when_absent(self):
        """IPs without a freed_date should not display a 'Freed:' label."""
        # Remove the IP that has a freed_date so only the one without remains
        self.ip_with_freed_date.delete()
        response = self.client.get(reverse("free_ips"))
        content = response.content.decode()
        self.assertNotIn("Freed:", content)


class TestFreeIPsTemplateReassignedStyling(TestCase):
    """Test red color styling and availability status for reassigned IPs.

    Requirements: 5.2, 6.1, 6.2
    """

    def setUp(self):
        self.user = User.objects.create_user(username="freeipuser2", password="testpass123")
        self.client.login(username="freeipuser2", password="testpass123")

        self.ip_range = IPRange.objects.create(
            range_pattern="10.0.6.x",
            network_prefix="10.0.6",
        )
        # Occupied/reassigned IP
        self.occupied_ip = IPAddress.objects.create(
            address="10.0.6.10",
            ip_range=self.ip_range,
            is_assigned=True,
            freed_date=timezone.now() - timedelta(days=5),
        )
        # Free IP
        self.free_ip = IPAddress.objects.create(
            address="10.0.6.20",
            ip_range=self.ip_range,
            is_assigned=False,
            freed_date=timezone.now() - timedelta(days=3),
        )

    def test_reassigned_ip_has_occupied_css_class(self):
        """Requirement 6.1: Reassigned IPs are styled with 'occupied' CSS class (red)."""
        response = self.client.get(reverse("free_ips"))
        content = response.content.decode()
        # The occupied class applies red background/border styling
        self.assertIn('class="ip-item occupied"', content)

    def test_free_ip_has_free_css_class(self):
        """Requirement 5.2: Free IPs are styled with 'free' CSS class."""
        response = self.client.get(reverse("free_ips"))
        content = response.content.decode()
        self.assertIn('class="ip-item free"', content)

    def test_occupied_ip_title_shows_occupied(self):
        """Requirement 6.2: Occupied IPs have title indicating 'Occupied' status."""
        response = self.client.get(reverse("free_ips"))
        content = response.content.decode()
        self.assertIn('title="Occupied"', content)

    def test_free_ip_title_shows_free(self):
        """Requirement 5.2: Free IPs have title indicating 'Free' status."""
        response = self.client.get(reverse("free_ips"))
        content = response.content.decode()
        self.assertIn('title="Free', content)

    def test_freed_date_not_shown_for_occupied_ip(self):
        """Freed date label should not appear for occupied/reassigned IPs."""
        response = self.client.get(reverse("free_ips"))
        content = response.content.decode()
        # The freed_date small tag should only appear for free IPs, not occupied ones
        freed_date_str = self.occupied_ip.freed_date.strftime("%Y-%m-%d")
        # The freed date text in the small tag should not appear for occupied IPs
        self.assertNotIn(
            f'<small class="freed-date">Freed: {freed_date_str}</small>',
            content.split('occupied')[1].split('</div>')[0]
            if 'occupied' in content
            else "",
        )
