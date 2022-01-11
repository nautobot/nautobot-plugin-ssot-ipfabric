"""IP Fabric Data Target Job."""
from diffsync.exceptions import ObjectNotCreated
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse

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
        return {
            "IP Fabric host": CONFIG.get("IPFABRIC_HOST"),
        }

    def sync_data(self):
        """Sync a device data from IP Fabric into Nautobot."""
        client = IpFabricClient(CONFIG["IPFABRIC_HOST"], CONFIG["IPFABRIC_API_TOKEN"])

        ipfabric_source = IPFabricDiffSync(job=self, sync=self.sync, client=client)
        self.log_info(message="Loading current data from IP Fabric...")
        ipfabric_source.load()

        dest = NautobotDiffSync(job=self, sync=self.sync)
        self.log_info(message="Loading current data from Nautobot.")
        dest.load()

        self.log_info(message="Calculating diffs...")
        diff = dest.diff_from(ipfabric_source)
        self.log_debug(message=f"Diff: {diff.dict()}")

        self.sync.diff = diff.dict()
        self.sync.save()
        create = diff.summary().get("create")
        update = diff.summary().get("update")
        delete = diff.summary().get("delete")
        no_change = diff.summary().get("no-change")
        self.log_info(
            message=f"DiffSync Summary: Create: {create}, Update: {update}, Delete: {delete}, No Change: {no_change}"
        )

        if not self.kwargs["dry_run"]:
            self.log_info(message="Syncing from IP Fabric to Nautobot")
            try:
                dest.sync_from(ipfabric_source)
            except ObjectNotCreated as err:
                self.log_debug(f"Unable to create object. {err}")
            self.log_success(message="Sync complete.")


jobs = [IpFabricDataSource]
