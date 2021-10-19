"""ServiceNow Data Target Job."""
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse

from diffsync.enum import DiffSyncFlags

from nautobot.dcim.models import Device, Interface, Region, Site
from nautobot.extras.jobs import Job, BooleanVar

from nautobot_ssot.jobs.base import DataMapping, DataTarget, DataSource


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


jobs = [IpFabricDataSource]
