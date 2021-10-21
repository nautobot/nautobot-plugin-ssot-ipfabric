"""Unit tests for the IPFabric DiffSync adapter class."""
import json
import uuid
from unittest.mock import MagicMock

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from nautobot.extras.models import Job, JobResult

from nautobot_ssot_ipfabric.diffsync.adapter_ipfabric import IPFabricDiffSync
from nautobot_ssot_ipfabric.jobs import IpFabricDataSource


def load_json(path):
    """Load a json file."""
    with open(path, encoding="utf-8") as file:
        return json.loads(file.read())


SITE_FIXTURE = load_json("./nautobot_ssot_ipfabric/tests/fixtures/get_sites.json")
DEVICE_INVENTORY_FIXTURE = load_json("./nautobot_ssot_ipfabric/tests/fixtures/get_device_inventory.json")


class IPFabricDiffSyncTestCase(TestCase):
    """Test the IPFabricDiffSync adapter class."""

    def test_data_loading(self):
        """Test the load() function."""

        # Create a mock client
        ipfabric_client = MagicMock()
        ipfabric_client.get_sites.return_value = SITE_FIXTURE
        ipfabric_client.get_device_inventory.return_value = DEVICE_INVENTORY_FIXTURE

        job = IpFabricDataSource()
        job.job_result = JobResult.objects.create(
            name=job.class_path, obj_type=ContentType.objects.get_for_model(Job), user=None, job_id=uuid.uuid4()
        )
        ipfabric = IPFabricDiffSync(job=job, sync=None, client=ipfabric_client)
        ipfabric.load()
        self.assertEqual(
            {site["siteName"] for site in SITE_FIXTURE},
            {site.get_unique_id() for site in ipfabric.get_all("location")},
        )
        self.assertEqual(
            {dev["hostname"] for dev in DEVICE_INVENTORY_FIXTURE},
            {dev.get_unique_id() for dev in ipfabric.get_all("device")},
        )

        # Assert each site has a device tied to it.
        for site in ipfabric.get_all("location"):
            self.assertEqual(len(site.devices), 1, f"{site} does not have the expected single device tied to it.")

        # Assert each device has the necessary attributes
        for device in ipfabric.get_all("device"):
            self.assertTrue(hasattr(device, "location_name"))
            self.assertTrue(hasattr(device, "model"))
            self.assertTrue(hasattr(device, "vendor"))
            self.assertTrue(hasattr(device, "serial_number"))

        # Assert each vlan has the necessary attributes
        for vlan in ipfabric.get_all("vlan"):
            self.assertTrue(hasattr(vlan, "name"))
            self.assertTrue(hasattr(vlan, "vid"))
            self.assertTrue(hasattr(vlan, "status"))
            self.assertTrue(hasattr(vlan, "site"))

        # TODO: Add testing for any new models we add
