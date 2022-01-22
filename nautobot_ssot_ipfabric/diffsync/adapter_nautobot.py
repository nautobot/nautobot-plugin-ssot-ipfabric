#  pylint: disable=too-many-arguments
# Load method is packed with conditionals  #  pylint: disable=too-many-branches
"""DiffSync adapter class for Nautobot as source-of-truth."""
from typing import List
from collections import defaultdict
from diffsync import DiffSync

from diffsync.exceptions import ObjectAlreadyExists
from django.conf import settings
from django.db import transaction
from django.db.models import ProtectedError, Q
from nautobot.dcim.models import Device, Site
from nautobot.extras.models import Tag
from nautobot.ipam.models import VLAN
from netutils.mac import mac_to_format

from nautobot_ssot_ipfabric.diffsync import DiffSyncModelAdapters

CONFIG = settings.PLUGINS_CONFIG.get("nautobot_ssot_ipfabric", {})
DEFAULT_INTERFACE_TYPE = CONFIG.get("default_interface_type", "1000base-t")
DEFAULT_INTERFACE_MTU = CONFIG.get("default_interface_mtu", 1500)
DEFAULT_INTERFACE_MAC = CONFIG.get("default_interface_mac", "00:00:00:00:00:01")
DEFAULT_DEVICE_ROLE = CONFIG.get("default_device_role", "Network Device")


class NautobotDiffSync(DiffSyncModelAdapters):
    """Nautobot adapter for DiffSync."""

    objects_to_delete = defaultdict(list)

    nb_vlan = VLAN
    nb_device = Device
    nb_site = Site

    def __init__(
        self,
        job,
        sync,
        safe_delete_mode: bool,
        sync_ipfabric_tagged_only: bool,
        site_filter: Site,
        *args,
        **kwargs,
    ):
        """Initialize the NautobotDiffSync."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.safe_delete_mode = safe_delete_mode
        self.sync_ipfabric_tagged_only = sync_ipfabric_tagged_only
        self.site_filter = site_filter

    def sync_complete(self, source: DiffSync, *args, **kwargs):
        """Clean up function for DiffSync sync.

        Once the sync is complete, this function runs deleting any objects
        from Nautobot that need to be deleted in a specific order.

        Args:
            source (DiffSync): DiffSync
        """
        for grouping in (
            "nb_vlan",
            "nb_device",
            "nb_site",
        ):
            for nautobot_object in self.objects_to_delete[grouping]:
                try:
                    nautobot_object.delete()
                except ProtectedError:
                    self.job.log_failure(obj=nautobot_object, message="Deletion failed protected object")
            self.objects_to_delete[grouping] = []

        return super().sync_complete(source, *args, **kwargs)

    def load_interfaces(self, device_record: Device, diffsync_device):
        """Import a single Nautobot Interface object as a DiffSync Interface model."""
        # Get MGMT IP
        mgmt_int_qset = device_record.interfaces.filter(mgmt_only=True)
        for interface_record in device_record.interfaces.all():
            interface = self.interface(
                diffsync=self,
                status=device_record.status.name,
                name=interface_record.name,
                device_name=device_record.name,
                description=interface_record.description if interface_record.description else None,
                enabled=True,
                mac_address=mac_to_format(str(interface_record.mac_address), "MAC_COLON_TWO").upper()
                if interface_record.mac_address
                else DEFAULT_INTERFACE_MAC,
                subnet_mask="255.255.255.255",
                mtu=interface_record.mtu if interface_record.mtu else DEFAULT_INTERFACE_MTU,
                type=DEFAULT_INTERFACE_TYPE,
                mgmt_only=interface_record.mgmt_only if interface_record.mgmt_only else False,
                pk=interface_record.pk,
                ip_is_primary=bool(
                    any(interface for interface in mgmt_int_qset if interface.name == interface_record.name)
                ),
                ip_address=str(interface_record.ip_addresses.first().host)
                if interface_record.ip_addresses.first()
                else None,
            )
            if not self.safe_delete_mode:
                self.interface.safe_delete_mode = self.safe_delete_mode
            self.add(interface)
            diffsync_device.add_child(interface)

    def load_device(self, filtered_devices: List, location):
        """Load Devices from Nautobot."""
        for device_record in filtered_devices:
            device = self.device(
                diffsync=self,
                name=device_record.name,
                model=str(device_record.device_type),
                role=str(device_record.device_role) if str(device_record.device_role) else DEFAULT_DEVICE_ROLE,
                location_name=device_record.site.name,
                vendor=str(device_record.device_type.manufacturer),
                status=device_record.status.name,
                serial_number=device_record.serial if device_record.serial else "",
            )
            if not self.safe_delete_mode:
                self.device.safe_delete_mode = self.safe_delete_mode
            try:
                self.add(device)
            except ObjectAlreadyExists:
                self.job.log_debug(message=f"Duplicate device discovered, {device_record.name}")
                continue

            location.add_child(device)
            self.load_interfaces(device_record=device_record, diffsync_device=device)

    def load_vlans(self, filtered_vlans: List, location):
        """Add Nautobot VLAN objects as DiffSync VLAN models."""
        for vlan_record in filtered_vlans:
            if not vlan_record:
                continue
            vlan = self.vlan(
                diffsync=self,
                name=vlan_record.name,
                site=vlan_record.site.name,
                status=vlan_record.status.name if vlan_record.status else "Active",
                vid=vlan_record.vid,
            )
            if not self.safe_delete_mode:
                self.vlan.safe_delete_mode = self.safe_delete_mode
            try:
                self.add(vlan)
            except ObjectAlreadyExists:
                self.job.log_debug(message=f"Duplicate VLAN discovered, {vlan_record.name}")
                continue
            location.add_child(vlan)

    def get_initial_site(self, ssot_tag):
        """Identify the site objects based on user defined job inputs.

        Args:
            ssot_tag ([type]): Tag used for filtering
        """
        # Simple check / validate Tag is present.
        if self.sync_ipfabric_tagged_only:
            site_objects = Site.objects.filter(tags__slug=ssot_tag.slug)
            if self.site_filter:
                site_objects = Site.objects.filter(Q(name=self.site_filter.name) & Q(tags__slug=ssot_tag.slug))
                if not site_objects:
                    self.job.log_warning(
                        message=f"{self.site_filter.name} was used to filter, alongside SSoT Tag. {self.site_filter.name} is not tagged."
                    )
        elif not self.sync_ipfabric_tagged_only:
            if self.site_filter:
                site_objects = Site.objects.filter(name=self.site_filter.name)
            else:
                site_objects = Site.objects.all()
        return site_objects

    @transaction.atomic
    def load_data(self):
        """Add Nautobot Site objects as DiffSync Location models."""
        ssot_tag, _ = Tag.objects.get_or_create(name="SSoT Synced from IPFabric")
        site_objects = self.get_initial_site(ssot_tag)
        # The parent object that stores all children, is the Site.
        if site_objects:
            for site_record in site_objects:
                location = self.location(
                    diffsync=self,
                    name=site_record.name,
                    site_id=site_record.custom_field_data.get("ipfabric-site-id"),
                    status=site_record.status.name,
                )
                if not self.safe_delete_mode:
                    self.location.safe_delete_mode = self.safe_delete_mode
                self.add(location)
                try:
                    # Load Site's Children - Devices with Interfaces, if any.
                    if self.sync_ipfabric_tagged_only:
                        nautobot_site_devices = Device.objects.filter(Q(site=site_record) & Q(tags__slug=ssot_tag.slug))
                    else:
                        nautobot_site_devices = Device.objects.filter(site=site_record)
                    if nautobot_site_devices.exists():
                        self.load_device(nautobot_site_devices, location)

                    # Load Site Children - Vlans, if any.
                    nautobot_site_vlans = VLAN.objects.filter(site=site_record)
                    if not nautobot_site_vlans.exists():
                        continue
                    self.load_vlans(nautobot_site_vlans, location)
                except Site.DoesNotExist:
                    self.job.log_info(message=f"Unable to find Site, {site_record}.")
        else:
            self.job.log_warning(message="No Nautobot records to load.")

    def load(self):
        """Load data from Nautobot."""
        self.load_data()
