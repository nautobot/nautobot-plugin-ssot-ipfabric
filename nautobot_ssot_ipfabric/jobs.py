"""IP Fabric Data Target Job."""
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse

# from nautobot.dcim.models import Device, Interface, Region, Site
from nautobot.extras.jobs import BooleanVar, Job
from nautobot_ssot.jobs.base import DataMapping, DataSource

from nautobot_ssot_ipfabric.diffsync.adapter_ipfabric import IPFabricDiffSync
from nautobot_ssot_ipfabric.diffsync.adapter_nautobot import NautobotDiffSync

# from diffsync.enum import DiffSyncFlags
from nautobot_ssot_ipfabric.utilities.ipfabric_client import IpFabricClient


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
        return (
            DataMapping("Device", None, "Device", reverse("dcim:device_list")),
            DataMapping("Site", None, "Site", reverse("dcim:site_list")),
        )

    @classmethod
    def config_information(cls):
        """Dictionary describing the configuration of this DataSource."""
        configs = settings.PLUGINS_CONFIG.get("nautobot_ssot_ipfabric", {})
        return {
            "IP Fabric host": configs.get("IPFABRIC_HOST"),
        }

    def sync_data(self):
        """Sync a device data from IP Fabric into Nautobot."""
        # TODO Add sync job
        configs = settings.PLUGINS_CONFIG.get("nautobot_ssot_ipfabric", {})
        ipfabric_conn = IpFabricClient(configs["IPFABRIC_HOST"], configs["IPFABRIC_API_TOKEN"])

        self.log_info(message="Loading current data from IP Fabric...")
        ipfabric_diffsync = IPFabricDiffSync(job=self, sync=self.sync, client=ipfabric_conn)
        ipfabric_diffsync.load()
        self.log_info(message=ipfabric_diffsync.dict())

        self.log_info(message="Loading current data from Nautobot.")
        nautobot_diffsync = NautobotDiffSync(job=self, sync=self.sync)
        nautobot_diffsync.load()
        self.log_info(message=nautobot_diffsync.dict())

        self.log_info(message="Calculating diffs...")
        diff = nautobot_diffsync.diff_from(ipfabric_diffsync)
        self.log_info(message=diff.dict())
        self.sync.diff = diff.dict()
        self.sync.save()

        if not self.kwargs["dry_run"]:
            self.log_info(message="Syncing from IP Fabric to Nautobot")
            nautobot_diffsync.sync_from(ipfabric_diffsync)
            self.log_info(message="Sync complete")


jobs = [IpFabricDataSource]
