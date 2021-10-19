"""DiffSync adapter class for Nautobot as source-of-truth."""

from diffsync import DiffSync
from diffsync.exceptions import ObjectNotFound
from nautobot.dcim.models import Device, Interface, Site
from nautobot.ipam.models import IPAddress
from netutils.ip import cidr_to_netmask

from . import tonb_models


class NautobotDiffSync(DiffSync):
    """Nautobot adapter for DiffSync."""

    location = tonb_models.Location
    device = tonb_models.Device
    interface = tonb_models.Interface
    mgmt_interface = tonb_models.MgmtInterface

    top_level = [
        "location",
    ]

    def __init__(self, *args, job, sync, **kwargs):
        """Initialize the NautobotDiffSync."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync

    def load_sites(self):
        """Add Nautobot Site objects as DiffSync Location models."""
        for site_record in Site.objects.all():
            self.job.log_debug(message=f"Loading Site {site_record.name}")
            # A Site and a Region may share the same name; if so they become part of the same Location record.
            try:
                location = self.get(self.location, site_record.name)
                location.site_pk = site_record.pk
            except ObjectNotFound:
                location = self.location(
                    diffsync=self,
                    name=site_record.name,
                    region_name=site_record.region.name,
                    container_name=site_record.tenant.name,
                    site_pk=site_record.pk,
                )
                self.add(location)

    def load_interface(self, interface_record, device_model):
        """Import a single Nautobot Interface object as a DiffSync Interface model."""
        interface = self.interface(
            diffsync=self,
            name=interface_record.name,
            device_name=device_model.name,
            description=interface_record.description,
            pk=interface_record.pk,
        )
        self.add(interface)
        device_model.add_child(interface)

    def load_primary_ip_interface(self, interface_record, device_model, device_record):
        """Import a Nautobot primary IP interface object as a DiffSync MgmtInterface model."""
        interface = self.mgmt_interface(
            diffsync=self,
            name=interface_record.name,
            device_name=device_model.name,
            ip_address=device_record.primary_ip4.host,
            subnet_mask=cidr_to_netmask(device_record.primary_ip4.prefix_length),
            description=interface_record.description,
            pk=interface_record.pk,
        )
        self.add(interface)
        device_model.add_child(interface)

    def load(self):
        """Load data from Nautobot."""
        # Import all Nautobot Site records as Locations
        self.load_sites()

        for location in self.get_all(self.location):
            if location.site_pk is None:
                continue
            for device_record in Device.objects.filter(site__pk=location.site_pk):
                device = self.device(
                    diffsync=self,
                    name=device_record.name,
                    platform=str(device_record.platform) if device_record.platform else None,
                    model=str(device_record.device_type),
                    role=str(device_record.device_role),
                    location_name=location.name,
                    vendor=str(device_record.device_type.manufacturer),
                    status=device_record.status,
                    pk=device_record.pk,
                )
                self.add(device)
                location.add_child(device)

                for interface_record in Interface.objects.filter(device=device_record):
                    try:
                        if interface_record.ip_addresses.get(host=device_record.primary_ip.host):
                            self.load_primary_ip_interface(interface_record, device, device_record)
                    except (IPAddress.DoesNotExist, AttributeError) as e:
                        print(e)
                        pass
                        # Pass for now but can uncomment to load all interfaces for a device.
                        # self.load_interface(interface_record, device)
