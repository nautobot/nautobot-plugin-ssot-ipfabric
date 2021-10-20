"""Test IPFabric Jobs."""
from django.test import TestCase, override_settings
from django.urls import reverse

from nautobot_ssot_ipfabric import jobs


class IPFabricJobTest(TestCase):
    """Test the IPFabric job."""

    def test_metadata(self):
        """Verify correctness of the Job Meta attributes."""
        self.assertEqual("IP Fabric", jobs.IpFabricDataSource.name)
        self.assertEqual("IP Fabric", jobs.IpFabricDataSource.Meta.name)
        self.assertEqual("IP Fabric", jobs.IpFabricDataSource.Meta.data_source)
        self.assertEqual("Synchronize data from IP Fabric into Nautobot.", jobs.IpFabricDataSource.Meta.description)

    def test_data_mapping(self):
        """Verify correctness of the data_mappings() API."""
        mappings = jobs.IpFabricDataSource.data_mappings()

        self.assertEqual("Device", mappings[0].source_name)
        self.assertIsNone(mappings[0].source_url)
        self.assertEqual("Device", mappings[0].target_name)
        self.assertEqual(reverse("dcim:device_list"), mappings[0].target_url)

        self.assertEqual("Site", mappings[1].source_name)
        self.assertIsNone(mappings[1].source_url)
        self.assertEqual("Site", mappings[1].target_name)
        self.assertEqual(reverse("dcim:site_list"), mappings[1].target_url)

    @override_settings(
        PLUGINS_CONFIG={
            "nautobot_ssot_ipfabric": {
                "IPFABRIC_HOST": "https://ipfabric.networktocode.com",
                "IPFABRIC_API_TOKEN": "1234",
            }
        }
    )
    def test_config_information(self):
        """Verify the config_information() API."""
        config_information = jobs.IpFabricDataSource.config_information()
        self.assertEqual(
            config_information,
            {
                "IP Fabric host": "https://ipfabric.networktocode.com",
            },
        )
