"""Test Nautobot Utilities."""
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from nautobot.dcim.models import DeviceRole, DeviceType, Manufacturer, Region, Site
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import Interface, IPAddress
from nautobot.tenancy.models import Tenant
from netutils.ip import netmask_to_cidr
from django.test import TestCase

from nautobot_ssot_ipfabric.utilities import create_site


class TestNautobotUtils(TestCase):
    """Test Nautobot Utility."""

    def setUp(self):
        """Setup."""
        self.site = Site.objects.create(name="Test-Site")

    def test_create_site(self):
        """Test Create Site Fixture/Utility."""
        test_site = create_site(site_name="Test-Site")
        self.assertEqual(test_site.id, self.site.id)
