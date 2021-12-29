"""DiffSyncModel subclasses for Nautobot-to-IPFabric data sync."""
import uuid
from typing import List, Optional

from diffsync import DiffSyncModel
from django.utils.text import slugify
from django.conf import settings

# from django.conf import settings
# from requests.api import delete
from nautobot.dcim.models import Device as NautobotDevice
from nautobot.dcim.models import Site
from nautobot.ipam.models import VLAN

import nautobot_ssot_ipfabric.utilities.nbutils as tonb_nbutils

CONFIG = settings.PLUGINS_CONFIG.get("nautobot_ssot_ipfabric", {})
DEFAULT_DEVICE_ROLE = CONFIG.get("DEFAULT_DEVICE_ROLE", "Network Device")
DEFAULT_DEVICE_ROLE_COLOR = "ff0000"
DEFAULT_DEVICE_STATUS = CONFIG.get("DEFAULT_DEVICE_STATUS", "Active")
DEFAULT_DEVICE_STATUS_COLOR = "ff0000"


class Location(DiffSyncModel):
    """Location model."""

    _modelname = "location"
    _identifiers = ("name",)
    _attributes = ("site_id",)
    _children = {"device": "devices", "vlan": "vlans"}

    name: str
    site_id: str
    devices: List["Device"] = list()  # pylint: disable=use-list-literal
    vlans: List["Vlan"] = list()  # pylint: disable=use-list-literal

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Site in Nautobot."""
        tonb_nbutils.create_site(site_name=ids["name"], site_id=attrs["site_id"])

        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete Site in Nautobot."""
        site = Site.objects.get(name=self.name)
        site.delete()
        super().delete()
        return self

    def update(self, attrs):
        """Update Site Object in Nautobot."""
        site = Site.objects.get(name=self.name)
        if attrs.get("name"):
            site.object.update(name=self.name)
            site.object.update(slug=slugify(self.name))
            # site.custom_data_field.update({"ipfabric-site-id": self.site_id})
        site.validated_save()
        return super().update(attrs)


class Device(DiffSyncModel):
    """Device model."""

    _modelname = "device"
    _identifiers = ("name",)
    _attributes = ("location_name", "model", "vendor", "serial_number", "role")
    _children = {"interface": "interfaces"}

    name: str
    location_name: Optional[str]
    model: Optional[str]
    vendor: Optional[str]
    serial_number: Optional[str]
    role: Optional[str]

    # mgmt_int: List["MgmtInterface"] = list()  # pylint: disable=use-list-literal
    mgmt_address: Optional[str]

    interfaces: List["Interface"] = list()  # pylint: disable=use-list-literal

    sys_id: Optional[str] = None
    pk: Optional[uuid.UUID] = None

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

        new_device = NautobotDevice.objects.create(
            status=device_status_object,
            device_type=device_type_object,
            device_role=device_role_object,
            site=site_object,
            name=ids["name"],
            serial=attrs.get("serial_number", ""),
        )

        new_device.validated_save()

        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete device in Nautobot."""
        device = NautobotDevice.objects.get(name=self.name)
        device.delete()
        super().delete()
        return super().delete()

    def update(self, attrs):
        """Update devices in Nautbot based on Source."""
        _device = NautobotDevice.objects.get(name=self.name)

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

        device_role_object = tonb_nbutils.create_device_role_object(
            role_name=DEFAULT_DEVICE_ROLE, role_color=DEFAULT_DEVICE_ROLE_COLOR
        )
        _device.device_role = device_role_object

        device_status_object = tonb_nbutils.create_status(DEFAULT_DEVICE_STATUS, DEFAULT_DEVICE_STATUS_COLOR)
        _device.status = device_status_object

        _device.validated_save()
        # Call the super().update() method to update the in-memory DiffSyncModel instance
        return super().update(attrs)


class Interface(DiffSyncModel):
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
    _children = {}

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

    # sys_id: Optional[str] = None
    pk: Optional[uuid.UUID] = None

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create interface in Nautobot under its parent device."""
        device_obj = NautobotDevice.objects.get(name=ids["device_name"])
        if not attrs.get("mac_address"):
            attrs["mac_address"] = "00:00:00:00:00:01"
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
            device_obj.validated_save()

        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete Interface Object."""
        device = NautobotDevice.objects.get(name=self.device_name)
        interface = device.interfaces.get(name=self.name)
        interface.delete()
        return super().delete()

    def update(self, attrs):
        """Update Interface object in Nautobot."""
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
        interface.validated_save()
        return super().update(attrs)


class Vlan(DiffSyncModel):
    """VLAN model."""

    _modelname = "vlan"
    _identifiers = ("name", "site")
    _shortname = ("name",)
    _attributes = (
        "vid",
        "status",
    )
    _children = {}

    name: str
    vid: int
    status: str
    site: str

    # sys_id: Optional[str] = None
    pk: Optional[uuid.UUID] = None

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
        vlan.delete()
        return super().delete()


Location.update_forward_refs()
Device.update_forward_refs()
Interface.update_forward_refs()
Vlan.update_forward_refs()
