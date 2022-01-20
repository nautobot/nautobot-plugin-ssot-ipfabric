# Ignore return statements for updates and deletes, #  pylint:disable=R1710
"""DiffSyncModel subclasses for Nautobot-to-IPFabric data sync."""
from typing import Any, ClassVar, List, Optional

from diffsync import DiffSyncModel
from django.conf import settings
from django.db.models import Q
from nautobot.dcim.models import Device as NautobotDevice
from nautobot.dcim.models import Site
from nautobot.extras.models import Tag
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import VLAN

import nautobot_ssot_ipfabric.utilities.nbutils as tonb_nbutils

CONFIG = settings.PLUGINS_CONFIG.get("nautobot_ssot_ipfabric", {})
DEFAULT_DEVICE_ROLE = CONFIG.get("default_device_role", "Network Device")
DEFAULT_DEVICE_ROLE_COLOR = CONFIG.get("default_device_role_color", "ff0000")
DEFAULT_DEVICE_STATUS = CONFIG.get("default_device_status", "Active")
DEFAULT_DEVICE_STATUS_COLOR = CONFIG.get("default_device_status_color", "ff0000")
DEFAULT_INTERFACE_MAC = CONFIG.get("default_interface_mac", "00:00:00:00:00:01")
SAFE_DELETE_SITE_STATUS = CONFIG.get("safe_delete_site_status", "Decommissioning")
SAFE_DELETE_INTERFACE_STATUS = CONFIG.get("safe_delete_interface_status", "Inventory")
SAFE_DELETE_DEVICE_STATUS = CONFIG.get("safe_delete_device_status", "Offline")
SAFE_DELETE_IPADDRESS_STATUS = CONFIG.get("safe_ipaddress_interfaces_status", "Deprecated")
SAFE_DELETE_VLAN_STATUS = CONFIG.get("safe_delete_vlan_status", "Deprecated")


class DiffSyncExtras(DiffSyncModel):
    """Additional components to mix and subclass from with `DiffSyncModel`."""

    safe_delete_mode: ClassVar[bool] = True

    def safe_delete(self, nautobot_object: Any, safe_mode: bool, safe_delete_status: str):
        """Safe delete an object, by adding tags or changing it's default status.

        Args:
            nautobot_object (Any): Any type of Nautobot object
            safe_mode (bool): Safe mode or not
            safe_delete_status (str): Desired status to change to
        """
        safe_delete_status = Status.objects.get(name=safe_delete_status.capitalize())

        if not safe_mode:
            self.diffsync.job.log_warning(
                message=f"{nautobot_object} will be deleted as safe delete mode is not enabled."
            )
            nautobot_object.delete()
            super().delete()

        else:
            if hasattr(nautobot_object, "status"):
                if not nautobot_object.status == safe_delete_status:
                    nautobot_object.status = safe_delete_status
                    self.diffsync.job.log_warning(
                        message=f"{nautobot_object} status has changed to {safe_delete_status}."
                    )
            if hasattr(nautobot_object, "tags"):
                tag, _ = Tag.objects.get_or_create(name="SSoT Safe Delete")
                nautobot_object.tags.add(tag)

            tonb_nbutils.tag_object(nautobot_object=nautobot_object, custom_field="ssot-synced-from-ipfabric")
            nautobot_object.validated_save()

        return self


class Location(DiffSyncExtras):
    """Location model."""

    _modelname = "location"
    _identifiers = ("name",)
    _attributes = ("site_id", "status")
    _children = {"device": "devices", "vlan": "vlans"}

    name: str
    site_id: Optional[str]
    status: str
    devices: List["Device"] = list()  # pylint: disable=use-list-literal
    vlans: List["Vlan"] = list()  # pylint: disable=use-list-literal

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Site in Nautobot."""
        tonb_nbutils.create_site(site_name=ids["name"], site_id=attrs["site_id"])
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete Site in Nautobot."""
        site_object = Site.objects.get(name=self.name)
        self.safe_delete(
            site_object,
            self.safe_delete_mode,
            SAFE_DELETE_SITE_STATUS,
        )
        return self

    def update(self, attrs):
        """Update Site Object in Nautobot."""
        site = Site.objects.get(name=self.name)
        if attrs.get("site_id"):
            site.custom_field_data["ipfabric-site-id"] = attrs.get("site_id")
        if attrs.get("status") == "Active":
            site.status = Status.objects.get(name="Active")
        tonb_nbutils.tag_object(nautobot_object=site, custom_field="ssot-synced-from-ipfabric")
        site.validated_save()
        return super().update(attrs)


class Device(DiffSyncExtras):
    """Device model."""

    _modelname = "device"
    _identifiers = ("name",)
    _attributes = ("location_name", "model", "vendor", "serial_number", "role", "status")
    _children = {"interface": "interfaces"}

    name: str
    location_name: Optional[str]
    model: Optional[str]
    vendor: Optional[str]
    serial_number: Optional[str]
    role: Optional[str]
    status: Optional[str]

    mgmt_address: Optional[str]

    interfaces: List["Interface"] = list()  # pylint: disable=use-list-literal

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Nautobot under its parent site."""
        device_type_object = tonb_nbutils.create_device_type_object(
            device_type=attrs["model"], vendor_name=attrs["vendor"]
        )
        device_role_object = tonb_nbutils.create_device_role_object(
            role_name=DEFAULT_DEVICE_ROLE, role_color=DEFAULT_DEVICE_ROLE_COLOR
        )
        device_status_object = tonb_nbutils.create_status(DEFAULT_DEVICE_STATUS, DEFAULT_DEVICE_STATUS_COLOR)

        site_object = tonb_nbutils.create_site(attrs["location_name"])

        new_device, _ = NautobotDevice.objects.get_or_create(
            status=device_status_object,
            device_type=device_type_object,
            device_role=device_role_object,
            site=site_object,
            name=ids["name"],
            serial=attrs.get("serial_number", ""),
        )
        tonb_nbutils.tag_object(nautobot_object=new_device, custom_field="ssot-synced-from-ipfabric")
        new_device.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete device in Nautobot."""
        try:
            device_object = NautobotDevice.objects.get(name=self.name)
            self.safe_delete(
                device_object,
                self.safe_delete_mode,
                SAFE_DELETE_DEVICE_STATUS,
            )
            return self
        except NautobotDevice.DoesNotExist:
            self.diffsync.job.log_warning(f"Unable to match device by name, {self.name}")

    def update(self, attrs):
        """Update devices in Nautbot based on Source."""
        try:
            _device = NautobotDevice.objects.get(name=self.name)
            if attrs.get("status") == "Active":
                safe_delete_tag = Tag.objects.get(name="SSoT Safe Delete")
                _device.status = Status.objects.get(name="Active")
                device_tags = _device.tags.all()
                for tag in device_tags:
                    if safe_delete_tag == tag:
                        _device.tags.remove(safe_delete_tag)

            if attrs.get("model"):
                device_type_object = tonb_nbutils.create_device_type_object(
                    device_type=attrs["model"], vendor_name=attrs["vendor"]
                )
                _device.type = device_type_object
            if attrs.get("location_name"):
                site_object = tonb_nbutils.create_site(attrs["location_name"])
                _device.site = site_object
            if attrs.get("serial_number"):
                _device.serial = attrs.get("serial_number")
            if attrs.get("role"):
                device_role_object = tonb_nbutils.create_device_role_object(
                    role_name=attrs.get("role", DEFAULT_DEVICE_ROLE), role_color=DEFAULT_DEVICE_ROLE_COLOR
                )
                _device.device_role = device_role_object
            tonb_nbutils.tag_object(nautobot_object=_device, custom_field="ssot-synced-from-ipfabric")
            _device.validated_save()
            # Call the super().update() method to update the in-memory DiffSyncModel instance
            return super().update(attrs)
        except NautobotDevice.DoesNotExist:
            self.diffsync.job.log_warning(f"Unable to match device by name, {self.name}")


class Interface(DiffSyncExtras):
    """Interface model."""

    _modelname = "interface"
    _identifiers = (
        "name",
        "device_name",
    )
    _shortname = ("name",)
    _attributes = (
        "description",
        "enabled",
        "mac_address",
        "mtu",
        "type",
        "mgmt_only",
        "ip_address",
        "subnet_mask",
        "ip_is_primary",
    )

    name: str
    device_name: str
    description: Optional[str]
    enabled: Optional[bool]
    mac_address: Optional[str]
    mtu: Optional[int]
    type: Optional[str]
    mgmt_only: Optional[bool]
    ip_address: Optional[str]
    subnet_mask: Optional[str]
    ip_is_primary: Optional[bool]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create interface in Nautobot under its parent device."""
        try:
            device_obj = NautobotDevice.objects.get(name=ids["device_name"])
        except NautobotDevice.MultipleObjectsReturned:
            tag, _ = Tag.objects.get_or_create(name="SSoT Synced from IPFabric")
            device_obj = NautobotDevice.objects.filter(Q(name=ids["device_name"]) & Q(tags__slug=tag.slug)).first()

        if not attrs.get("mac_address"):
            attrs["mac_address"] = DEFAULT_INTERFACE_MAC
        interface_obj = tonb_nbutils.create_interface(
            device_obj=device_obj,
            interface_details=dict(**ids, **attrs),
        )
        ip_address = attrs["ip_address"]
        if ip_address:
            ip_address_obj = tonb_nbutils.create_ip(
                ip_address=attrs["ip_address"],
                subnet_mask=attrs["subnet_mask"],
                status="Active",
                object_pk=interface_obj,
            )
            interface_obj.ip_addresses.add(ip_address_obj)
            if attrs["ip_is_primary"]:
                if ip_address_obj.family == 4:
                    device_obj.primary_ip4 = ip_address_obj
                if ip_address_obj.family == 6:
                    device_obj.primary_ip6 = ip_address_obj
        tonb_nbutils.tag_object(nautobot_object=interface_obj, custom_field="ssot-synced-from-ipfabric")
        interface_obj.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete Interface Object."""
        try:
            device = NautobotDevice.objects.get(name=self.device_name)
            interface = device.interfaces.get(name=self.name)
            # Access the addr within an interface, change the status if necessary
            if interface.ip_addresses.first():
                self.safe_delete(interface.ip_addresses.first(), self.safe_delete_mode, SAFE_DELETE_IPADDRESS_STATUS)
            # Then do the parent interface
            self.safe_delete(
                interface,
                self.safe_delete_mode,
                SAFE_DELETE_DEVICE_STATUS,
            )

            return self
        except NautobotDevice.DoesNotExist:
            self.diffsync.job.log_warning(f"Unable to match device by name, {self.name}")

    def update(self, attrs):
        """Update Interface object in Nautobot."""
        try:
            device = NautobotDevice.objects.get(name=self.device_name)
            interface = device.interfaces.get(name=self.name)
            if attrs.get("description"):
                interface.description = attrs["description"]
            if attrs.get("enabled"):
                interface.enabled = attrs["enabled"]
            if attrs.get("mac_address"):
                interface.mac_address = attrs["mac_address"]
            if attrs.get("mtu"):
                interface.mtu = attrs["mtu"]
            if attrs.get("mode"):
                interface.mode = attrs["mode"]
            if attrs.get("lag"):
                interface.lag = attrs["lag"]
            if attrs.get("type"):
                interface.type = attrs["type"]
            if attrs.get("mgmt_only"):
                interface.mgmt_only = attrs["mgmt_only"]
            if attrs.get("ip_address"):
                interface.ip_addresses.all().delete()
                ip_address_obj = tonb_nbutils.create_ip(
                    ip_address=attrs.get("ip_address"),
                    subnet_mask=attrs.get("subnet_mask") if attrs.get("subnet_mask") else "255.255.255.255",
                    status="Active",
                    object_pk=interface,
                )
                interface.ip_addresses.add(ip_address_obj)
            tonb_nbutils.tag_object(nautobot_object=interface, custom_field="ssot-synced-from-ipfabric")
            interface.validated_save()
            return super().update(attrs)
        except NautobotDevice.DoesNotExist:
            self.diffsync.job.log_warning(f"Unable to match device by name, {self.name}")


class Vlan(DiffSyncExtras):
    """VLAN model."""

    _modelname = "vlan"
    _identifiers = ("name", "site")
    _shortname = ("name",)
    _attributes = (
        "vid",
        "status",
    )

    name: str
    vid: int
    status: str
    site: str

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create VLANs in Nautobot under the site."""
        status = attrs["status"].lower().capitalize()
        site = Site.objects.get(name=ids["site"])
        name = ids["name"] if ids["name"] else f"VLAN{attrs['vid']}"
        new_vlan = tonb_nbutils.create_vlan(vlan_name=name, vlan_id=attrs["vid"], vlan_status=status, site_obj=site)
        new_vlan.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete."""
        vlan = VLAN.objects.get(name=self.name)
        self.safe_delete(
            vlan,
            self.safe_delete_mode,
            SAFE_DELETE_VLAN_STATUS,
        )
        return self


# TODO: If necessary add an update, don't see a need at this momemt.

Location.update_forward_refs()
Device.update_forward_refs()
Interface.update_forward_refs()
Vlan.update_forward_refs()
