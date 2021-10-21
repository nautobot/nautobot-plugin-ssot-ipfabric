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

    @responses.activate
    def test_get_vlans(self):
        """Test `get_vlans` API Call."""
        endpoint = f"{self.uri}/api/v1/tables/vlan/device"
        json_response = json_fixture(f"{FIXTURES}/get_vlans.json")
        # IP Fabric Responses are wrapped inside 'data' key.
        response = {"data": json_response}
        responses.add(
            responses.POST,
            endpoint,
            json=response,
            status=200,
        )
        vlans = self.client.get_vlans()

        self.assertEqual(vlans[0]["siteName"], "JCY-SPINE-01.INFRA.NTC.COM_1")
        self.assertEqual(len(vlans), 13)

    @responses.activate
    def test_get_interface_inventory(self):
        """Test `get_interface_inventory` API Call."""
        endpoint = f"{self.uri}/api/v1/tables/inventory/interfaces"
        json_response = json_fixture(f"{FIXTURES}/get_interface_inventory.json")
        # IP Fabric Responses are wrapped inside 'data' key.
        response = {"data": json_response}
        responses.add(
            responses.POST,
            endpoint,
            json=response,
            status=200,
        )
        interfaces = self.client.get_interface_inventory()

        self.assertEqual(interfaces[0]["id"], "19941192")
        self.assertEqual(interfaces[2]["primaryIp"], "10.10.0.10")
        self.assertEqual(len(interfaces), 4)

    @responses.activate
    def test_get_interface_inventory_filter(self):
        """Test `get_interface_inventory` with filter applied API Call."""
        endpoint = f"{self.uri}/api/v1/tables/inventory/interfaces"
        json_response = json_fixture(f"{FIXTURES}/get_interface_inventory.json")
        # IP Fabric Responses are wrapped inside 'data' key.
        response = {"data": json_response}
        responses.add(
            responses.POST,
            endpoint,
            json=response,
            status=200,
        )
        interfaces = self.client.get_interface_inventory(device="nyc-rtr-01")

        self.assertEqual(interfaces[0]["hostname"], "nyc-rtr-01")
