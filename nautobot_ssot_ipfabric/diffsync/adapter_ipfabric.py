"""DiffSync adapter class for Ip Fabric."""

from diffsync import DiffSync
from . import tonb_models


class IPFabricDiffSync(DiffSync):
    """Nautobot adapter for DiffSync."""

    location = tonb_models.Location
    device = tonb_models.Device
    mgmt_interface = tonb_models.MgmtInterface

    top_level = [
        "location",
    ]

    def __init__(self, *args, job, sync, client, **kwargs):
        """Initialize the NautobotDiffSync."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.client = client

    def load_sites(self):
        """Add IP Fabric Site objects as DiffSync Location models."""
        sites = self.client.get_sites()
        for site in sites:
            self.job.log_debug(message=f"Loading Site {site['siteName']}")
            location = self.location(diffsync=self, name=site["siteName"])
            self.add(location)

    def load_interface(self, interface_record, device_model):
        """Import a single Nautobot Interface object as a DiffSync Interface model."""
        pass

    def load_primary_ip_interface(self, interface_record, device_model, device_record):
        """Import a Nautobot primary IP interface object as a DiffSync MgmtInterface model."""
        pass

    def load(self):
        """Load data from IP Fabric."""
        # Import all Nautobot Site records as Locations
        self.load_sites()
