"""IP Fabric Data Target Job."""
from diffsync.enum import DiffSyncFlags
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse

# from nautobot.dcim.models import Device, Interface, Region, Site
from nautobot.extras.jobs import BooleanVar, Job
from nautobot_ssot.jobs.base import DataMapping, DataSource

from nautobot_ssot_ipfabric.diffsync.adapter_ipfabric import IPFabricDiffSync
from nautobot_ssot_ipfabric.diffsync.adapter_nautobot import NautobotDiffSync
from nautobot_ssot_ipfabric.utilities.ipfabric_client import IpFabricClient

CONFIG = settings.PLUGINS_CONFIG.get("nautobot_ssot_ipfabric", {})


# pylint:disable=too-few-public-methods
class IpFabricDataSource(DataSource, Job):
    """Job syncing data from IP Fabric to Nautobot."""

    debug = BooleanVar(description="Enable for more verbose debug logging")

    class Meta:
        """Metadata about this Job."""

        name = "IP Fabric"
        data_source = "IP Fabric"
        data_source_icon = static("nautobot_ssot_ipfabric/ipfabric.png")
        description = "Synchronize data from IP Fabric into Nautobot."

    @classmethod
    def data_mappings(cls):
        """List describing the data mappings involved in this DataSource."""
        # configs = settings.PLUGINS_CONFIG.get("nautobot_ssot_ipfabric", {})

        return (
            DataMapping("Device", None, "Device", reverse("dcim:device_list")),
            DataMapping("Site", None, "Site", reverse("dcim:site_list")),
            DataMapping("Interfaces", None, "Interfaces", reverse("dcim:interface_list")),
            DataMapping("IP Addresses", None, "IP Addresses", reverse("ipam:ipaddress_list")),
            DataMapping("VLANs", None, "VLANs", reverse("ipam:vlan_list")),
            DataMapping("Network Diagram", None, "Graph", f"{CONFIG['IPFABRIC_HOST']}/graph"),
        )

    @classmethod
    def config_information(cls):
        """Dictionary describing the configuration of this DataSource."""
        # configs = settings.PLUGINS_CONFIG.get("nautobot_ssot_ipfabric", {})
        return {
            "IP Fabric host": CONFIG.get("IPFABRIC_HOST"),
        }

    def sync_data(self):
        """Sync a device data from IP Fabric into Nautobot."""
        # configs = settings.PLUGINS_CONFIG.get("nautobot_ssot_ipfabric", {})

        client = IpFabricClient(CONFIG["IPFABRIC_HOST"], CONFIG["IPFABRIC_API_TOKEN"])

        ipfabric_source = IPFabricDiffSync(job=self, sync=self.sync, client=client)

        self.log_info(message="Loading current data from IP Fabric...")
        ipfabric_source.load()

        dest = NautobotDiffSync(job=self, sync=self.sync)

        self.log_info(message="Loading current data from Nautobot.")
        dest.load()

        diffsync_flags = DiffSyncFlags.CONTINUE_ON_FAILURE

        self.log_info(message="Calculating diffs...")
        diff = dest.diff_from(ipfabric_source)
        self.log_info(message=f"Diff: {diff.dict()}")

        self.sync.diff = diff.dict()
        self.sync.save()

        if not self.kwargs["dry_run"]:
            self.log_info(message="Syncing from IP Fabric to Nautobot")
            dest.sync_from(ipfabric_source, flags=diffsync_flags)
            self.log_info(message="Sync complete")


jobs = [IpFabricDataSource]
