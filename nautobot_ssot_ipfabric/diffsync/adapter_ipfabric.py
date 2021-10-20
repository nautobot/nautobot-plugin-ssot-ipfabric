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

    # def load_interface(self, interface_record, device_model):
    #     """Import a single Nautobot Interface object as a DiffSync Interface model."""
    #     pass

    # def load_primary_ip_interface(self, interface_record, device_model, device_record):
    #     """Import a Nautobot primary IP interface object as a DiffSync MgmtInterface model."""
    #     pass

    def load(self):
        """Load data from IP Fabric."""
        self.load_sites()
        devices = self.client.get_device_inventory()

        for location in self.get_all(self.location):
            if location.name is None:
                continue
            location_devices = [device for device in devices if device["siteName"] == location.name]
            for device in location_devices:
                self.job.log_debug(message=f"Loading Device {device['hostname']}")
                device = self.device(
                    diffsync=self,
                    name=device["hostname"],
                    location_name=device["siteName"],
                    model=device["model"],
                    vendor=device["vendor"],
                    serial_number=device["sn"],
                )
                self.add(device)
                location.add_child(device)
                self.job.log_debug(message=device)
