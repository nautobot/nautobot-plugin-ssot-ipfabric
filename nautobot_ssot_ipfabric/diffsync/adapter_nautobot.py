"""DiffSync adapter class for Nautobot as source-of-truth."""
# import logging

from diffsync.exceptions import ObjectNotFound
from django.conf import settings
from nautobot.dcim.models import Device, Site
from nautobot.ipam.models import VLAN
from netutils.mac import mac_to_format

from nautobot_ssot_ipfabric.diffsync import DiffSyncModelAdapters

# from netutils.ip import cidr_to_netmask


# from django.utils.text import slugify

# logger = logging.getLogger("nautobot.jobs")
CONFIG = settings.PLUGINS_CONFIG.get("nautobot_ssot_ipfabric", {})
DEFAULT_INTERFACE_TYPE = CONFIG.get("DEFAULT_INTERFACE_TYPE", "1000base-t")
DEFAULT_INTERFACE_MTU = CONFIG.get("DEFAULT_INTERFACE_MTU", 1500)
DEFAULT_INTERFACE_MAC = CONFIG.get("DEFAULT_INTERFACE_MAC", "00:00:00:00:00:01")
DEFAULT_DEVICE_ROLE = CONFIG.get("DEFAULT_DEVICE_ROLE", "Network Device")


class NautobotDiffSync(DiffSyncModelAdapters):
    """Nautobot adapter for DiffSync."""

    def __init__(self, job, sync, *args, **kwargs):
        """Initialize the NautobotDiffSync."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync

    def load_sites(self):
        """Add Nautobot Site objects as DiffSync Location models."""
        for site_record in Site.objects.all():
            # logger.log_debug(message=f"Loading Site {site_record.name}")
            # A Site and a Region may share the same name; if so they become part of the same Location record.
            try:
                location = self.get(self.location, site_record.name)
                location.site_pk = site_record.pk
            except ObjectNotFound:
                location = self.location(
                    diffsync=self,
                    name=site_record.name,
                    region_name=site_record.region.name if site_record.region else None,
                    container_name=site_record.tenant.name if site_record.tenant else None,
                    site_id=site_record.facility if site_record.facility else "",
                    site_pk=site_record.pk,
                )
                self.add(location)

    def load_interface(self):
        """Import a single Nautobot Interface object as a DiffSync Interface model."""
        for device_record in Device.objects.all():
            device = self.get(self.device, device_record.name)
            for interface_record in device_record.interfaces.all():
                try:
                    interface = self.get(self.interface, self.name)
                    interface.pk = interface_record.pk
                except ObjectNotFound:
                    interface = self.interface(
                        diffsync=self,
                        name=interface_record.name,
                        device_name=device_record.name,
                        description=interface_record.description if interface_record.description else None,
                        enabled=True,
                        mac_address=mac_to_format(str(interface_record.mac_address), "MAC_COLON_TWO").upper()
                        if str(interface_record.mac_address)
                        else DEFAULT_INTERFACE_MAC,
                        subnet_mask="255.255.255.255",
                        mtu=interface_record.mtu if interface_record.mtu else DEFAULT_INTERFACE_MTU,
                        type=DEFAULT_INTERFACE_TYPE,
                        mgmt_only=interface_record.mgmt_only if interface_record.mgmt_only else False,
                        pk=interface_record.pk,
                    )
                    self.add(interface)
                    device.add_child(interface)

    def load_devices(self):
        """Add Nautobot Device objects as DiffSync Device models."""
        for device_record in Device.objects.all():
            # self.job.log_debug(message=f"Loading Device {device_record.name}")
            location = self.get(self.location, device_record.site.name)
            try:
                device = self.get(self.device, device_record.name)
                device.pk = device_record.pk
            except ObjectNotFound:
                device = self.device(
                    diffsync=self,
                    name=device_record.name,
                    # platform=str(device_record.platform) if device_record.platform else None,
                    model=str(device_record.device_type),
                    role=str(device_record.device_role) if str(device_record.device_role) else DEFAULT_DEVICE_ROLE,
                    location_name=device_record.site.name,
                    vendor=str(device_record.device_type.manufacturer),
                    # status=device_record.status,
                    pk=device_record.pk,
                    serial_number=device_record.serial if device_record.serial else "",
                )

                self.add(device)
                location.add_child(device)

    def load_vlans(self):
        """Add Nautobot VLAN objects as DiffSync VLAN models."""
        for vlan_record in VLAN.objects.all():
            self.job.log_debug(message=f"Loading VLAN {vlan_record.name}")
            location = self.get(self.location, vlan_record.site.name)
            try:
                vlan = self.get(self.vlan, vlan_record.name)
                vlan.pk = vlan_record.pk
            except ObjectNotFound:
                vlan = self.vlan(
                    diffsync=self,
                    name=vlan_record.name,
                    site=vlan_record.site.name,
                    status=vlan_record.status.slug,
                    pk=vlan_record.pk,
                    vid=vlan_record.vid,
                )

                self.add(vlan)
                location.add_child(vlan)

    def load(self):
        """Load data from Nautobot."""
        self.load_sites()
        self.load_devices()
        self.load_vlans()
        self.load_interface()


#                for interface_record in Interface.objects.filter(device=device_record):
#                    try:
#                        if interface_record.ip_addresses.get(host=device_record.primary_ip.host):
#                            self.load_primary_ip_interface(interface_record, device, device_record)
#                    except (IPAddress.DoesNotExist, AttributeError) as e:
#                        print(e)
#                        pass
#                        # Pass for now but can uncomment to load all interfaces for a device.
#                        # self.load_interface(interface_record, device)


# def load_primary_ip_interface(self):
#     """Import a Nautobot primary IP interface object as a DiffSync MgmtInterface model."""
#     for device_record in Device.objects.all():
#         device_model = self.get(self.device, device_record.name)
#         for interface_record in device_record.interfaces.all():
#             interface = self.mgmt_int(
#                 diffsync=self,
#                 name=interface_record.name,
#                 device_name=device_model.name,
#                 ip_address=device_record.primary_ip4.host,
#                 subnet_mask=cidr_to_netmask(device_record.primary_ip4.prefix_length),
#                 description=interface_record.description,
#                 pk=interface_record.pk,
#             )
#             self.add(interface)
#             device_model.add_child(interface)
