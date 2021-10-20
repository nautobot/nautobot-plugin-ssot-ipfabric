"""Test additional IP-Fabric Client Calls."""
import os
import unittest

import responses

from nautobot_ssot_ipfabric.tests.fixtures import real_path
from nautobot_ssot_ipfabric.utilities import json_fixture
from nautobot_ssot_ipfabric.utilities.ipfabric_client import IpFabricClient

FIXTURES = os.environ.get("FIXTURE_DIR", real_path)


class TestIpFabricClient(unittest.TestCase):
    """Test IP Fabric Client"""

    def setUp(self):
        """Setup."""
        self.uri = "https://ip-fabric-host.com"
        self.client = IpFabricClient(self.uri, "CrazyTrainToken")

    @responses.activate
    def test_get_sites(self):
        """Test `get_sites` API Call."""
        endpoint = f"{self.uri}/api/v1/tables/inventory/sites"
        json_response = json_fixture(f"{FIXTURES}/get_sites.json")
        # IP Fabric Responses are wrapped inside 'data' key.
        response = {"data": json_response}
        responses.add(
            responses.POST,
            endpoint,
            json=response,
            status=200,
        )
        sites = self.client.get_sites()

        self.assertEqual(sites[0]["siteName"], "JCY-RTR-01_1")
        self.assertEqual(len(sites), 6)

    @responses.activate
    def test_get_device_inventory(self):
        """Test `get_device_inventory` API Call."""
        endpoint = f"{self.uri}/api/v1/tables/inventory/devices"
        json_response = json_fixture(f"{FIXTURES}/get_device_inventory.json")
        # IP Fabric Responses are wrapped inside 'data' key.
        response = {"data": json_response}
        responses.add(
            responses.POST,
            endpoint,
            json=response,
            status=200,
        )
        sites = self.client.get_device_inventory()

        self.assertEqual(sites[0]["hostname"], "nyc-spine-02")
        self.assertEqual(sites[0]["platform"], "veos")
        self.assertEqual(len(sites), 6)
