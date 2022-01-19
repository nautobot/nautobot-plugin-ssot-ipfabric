"""IP Fabric Data Target Job."""
from diffsync.enum import DiffSyncFlags
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
IPFABRIC_HOST = CONFIG["ipfabric_host"]
IPFABRIC_API_TOKEN = CONFIG["ipfabric_api_token"]

name = "Nautobot SSoT IPFabric"  # pylint: disable=invalid-name


# pylint:disable=too-few-public-methods
class IpFabricDataSource(DataSource, Job):
    """Job syncing data from IP Fabric to Nautobot."""

    debug = BooleanVar(description="Enable for more verbose debug logging")
    safe_delete_mode = BooleanVar(
        description="Records are not deleted. Status fields are updated as necessary.",
        default=True,
        label="Safe Delete Mode",
    )
    sync_ipfabric_tagged_only = BooleanVar(
        default=True,
        label="Sync Tagged Only",
        description="Only sync objects that have the 'ssot-synced-from-ipfabric' tag.",
    )

    class Meta:
        """Metadata about this Job."""

        name = "IP Fabric SSoT Sync"
        data_source = "IP Fabric"
        data_source_icon = static("nautobot_ssot_ipfabric/ipfabric.png")
        description = "Synchronize data from IP Fabric into Nautobot."
        field_order = (
            "debug",
            "safe_delete_mode",
            "sync_ipfabric_tagged_only",
            "dry_run",
        )

    @classmethod
    def data_mappings(cls):
        """List describing the data mappings involved in this DataSource."""
        return (
            DataMapping("Device", None, "Device", reverse("dcim:device_list")),
            DataMapping("Site", None, "Site", reverse("dcim:site_list")),
            DataMapping("Interfaces", None, "Interfaces", reverse("dcim:interface_list")),
            DataMapping("IP Addresses", None, "IP Addresses", reverse("ipam:ipaddress_list")),
            DataMapping("VLANs", None, "VLANs", reverse("ipam:vlan_list")),
        )

    @classmethod
    def config_information(cls):
        """Dictionary describing the configuration of this DataSource."""
        return {
            "IP Fabric host": CONFIG["ipfabric_host"],
            "Default MAC Address": CONFIG.get("default_interface_mac", "00:00:00:00:00:01"),
            "Default Device Role": CONFIG.get("default_device_role", "Network Device"),
            "Default Interface Type": CONFIG.get("default_interface_type", "1000base-t"),
            "Default Device Status": CONFIG.get("default_device_status", "Active"),
            "Allow Duplicate Addresses": CONFIG.get("allow_duplicate_addresses", True),
            "Default MTU": CONFIG.get("default_interface_mtu", 1500),
            "Nautobot Host URL": CONFIG.get("nautobot_host"),
            "Safe Delete Interface Status": CONFIG.get("safe_delete_interface_status", "Inventory"),
            "Safe Delete Device Status": CONFIG.get("safe_delete_device_status", "Deprecated"),
            "Safe Delete Site Status": CONFIG.get("safe_delete_site_status", "Decommissioning"),
            "Safe Delete IPAddress Status": CONFIG.get("safe_ipaddress_interfaces_status", "Deprecated"),
            "Safe Delete VLAN status": CONFIG.get("safe_delete_vlan_status", "Inventory"),
        }

    def sync_data(self):
        """Sync a device data from IP Fabric into Nautobot."""
        client = IpFabricClient(IPFABRIC_HOST, IPFABRIC_API_TOKEN)

        ipfabric_source = IPFabricDiffSync(job=self, sync=self.sync, client=client)
        self.log_info(message="Loading current data from IP Fabric...")
        ipfabric_source.load()

        dest = NautobotDiffSync(
            job=self,
            sync=self.sync,
            safe_delete_mode=self.kwargs["safe_delete_mode"],
            sync_ipfabric_tagged_only=self.kwargs["sync_ipfabric_tagged_only"],
        )
        self.log_info(message="Loading current data from Nautobot.")
        dest.load()

        self.log_info(message="Calculating diffs...")
        flags = DiffSyncFlags.CONTINUE_ON_FAILURE

        diff = dest.diff_from(ipfabric_source, flags=flags)
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
