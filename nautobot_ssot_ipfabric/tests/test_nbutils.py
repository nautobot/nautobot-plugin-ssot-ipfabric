"""Test Nautobot Utilities."""
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils.text import slugify
from nautobot.dcim.models import DeviceRole, DeviceType, Manufacturer, Region, Site
from nautobot.dcim.models.devices import Device
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress
from nautobot.tenancy.models import Tenant
from nautobot.utilities.choices import ColorChoices

from nautobot_ssot_ipfabric.utilities import (
    create_device_role_object,
    create_device_type_object,
    create_interface,
    create_ip,
    create_manufacturer,
    create_region,
    create_site,
    create_status,
    create_tenant,
)


# pylint: disable=too-many-instance-attributes
class TestNautobotUtils(TestCase):
    """Test Nautobot Utility."""

    def setUp(self):
        """Setup."""
        self.site = Site.objects.create(
            name="Test-Site",
            slug="test-site",
            status=Status.objects.get(name="Active"),
            region=None,
            tenant=None,
        )

        self.region = Region.objects.create(name="Test-Region", slug="test-region")
        self.tenant = Tenant.objects.create(name="Test-Tenant", slug="test-tenant")
        self.manufacturer = Manufacturer.objects.create(name="Test-Manufacturer", slug="test-manufacturer")
        self.device_type = DeviceType.objects.create(
            model="Test-DeviceType", slug="test-devicetype", manufacturer=self.manufacturer
        )
        self.device_role = DeviceRole.objects.create(name="Test-Role", slug="test-role", color=ColorChoices.COLOR_RED)
        self.content_type = ContentType.objects.get(app_label="dcim", model="device")
        self.status = Status.objects.create(
            name="Test-Status",
            slug=slugify("Test-Status"),
            color=ColorChoices.COLOR_AMBER,
            description="Test-Description",
        )
        self.status.content_types.set([self.content_type])
        self.status_obj = Status.objects.get_for_model(IPAddress).get(slug=slugify("Active"))
        self.ip_address = IPAddress.objects.create(address="192.168.0.1/32", status=self.status_obj)

        self.device = Device.objects.create(
            name="Test-Device", site=self.site, device_type=self.device_type, device_role=self.device_role
        )

        self.device.interfaces.create(name="Test-Interface")
        # self.vlan_content_type = ContentType.objects.get(app_label="ipam", model="vlan")
        # self.vlan_status = Status.objects.create(
        #     name="Test-Vlan-Status",
        #     slug=slugify("Test-Vlan-Status"),
        #     color=ColorChoices.COLOR_AMBER,
        #     description="Test-Description",
        # )
        # self.vlan_status.content_types.set([self.vlan_content_type])
        # self.site.vlans.create("Test-Vlan", 100, self.vlan_status)

    def test_create_site(self):
        """Test `create_site` Utility."""
        test_site = create_site(site_name="Test-Site")
        self.assertEqual(test_site.id, self.site.id)

    def test_create_region(self):
        """Test `create_region` Utility."""
        test_region = create_region(region_name="Test-Region")
        self.assertEqual(test_region.id, self.region.id)

    def test_create_tenant(self):
        """Test `create_tenant` Utility."""
        test_tenant = create_tenant(tenant_name="Test-Tenant")
        self.assertEqual(test_tenant.id, self.tenant.id)

    def test_create_device_type_object(self):
        """Test `create_device_type_object` Utility."""
        test_device_type = create_device_type_object(device_type="Test-DeviceType", vendor_name="Test-Manufacturer")
        self.assertEqual(test_device_type.id, self.device_type.id)

    def test_create_manufacturer(self):
        """Test `create_manufacturer` Utility."""
        test_manufacturer = create_manufacturer(vendor_name="Test-Manufacturer")
        self.assertEqual(test_manufacturer.id, self.manufacturer.id)

    def test_create_device_role(self):
        """Test `create_device_role` Utility."""
        test_device_role = create_device_role_object("Test-Role", role_color=ColorChoices.COLOR_RED)
        self.assertEqual(test_device_role.id, self.device_role.id)

    def test_create_status(self):
        """Test `create_status` Utility."""
        test_status = create_status(status_name="Test-Status", status_color=ColorChoices.COLOR_AMBER)
        self.assertEqual(test_status.id, self.status.id)

    def test_create_status_doesnt_exist(self):
        """Test `create_status` Utility."""
        test_status = create_status(status_name="Test-Status-100", status_color=ColorChoices.COLOR_AMBER)
        self.assertEqual(test_status.id, Status.objects.get(name="Test-Status-100").id)

    def test_create_ip(self):
        """Test `create_ip` Utility."""
        test_ip = create_ip("192.168.0.1", "255.255.255.255")
        self.assertEqual(test_ip.id, self.ip_address.id)

    def test_create_ip_device_add(self):
        """Test `create_ip` adding to device Utility."""
        test_ip = create_ip("192.168.0.1", "255.255.255.255", object_pk=self.device.id)
        self.assertEqual(test_ip.id, self.ip_address.id)

    def test_create_interface(self):
        """Test `create_interface` Utility."""
        test_interface = create_interface("Test-Interface", self.device)
        self.assertEqual(test_interface.id, self.device.interfaces.get(name="Test-Interface").id)
