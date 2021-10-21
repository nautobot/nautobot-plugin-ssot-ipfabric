"""DiffSyncModel subclasses for Nautobot-to-IPFabric data sync."""
from functools import lru_cache
from typing import List, Optional
import uuid

from diffsync import DiffSyncModel

# from django.conf import settings
# from requests.api import delete
from nautobot.dcim.models import Device as NautobotDevice
from nautobot.dcim.models import Site

import nautobot_ssot_ipfabric.utilities.nbutils as tonb_nbutils

DEFAULT_DEVICE_ROLE = "leaf"  # TODO: (HUGO) Do something about this
DEFAULT_DEVICE_ROLE_COLOR = "ff0000"
DEFAULT_DEVICE_STATUS = "Active"
DEFAULT_DEVICE_STATUS_COLOR = "ff0000"


class Location(DiffSyncModel):
    """Location model."""

    _modelname = "location"
    _identifiers = ("name",)
    _attributes = ()
    _children = {"device": "devices"}

    name: str
    devices: List["Device"] = list()  # pylint: disable=use-list-literal

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Site in Nautobot."""
        tonb_nbutils.create_site(site_name=ids["name"])

        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete Site in Nautobot."""
        site = Site.objects.get(name=self.name)
        site.delete()
        super().delete()
        return self


class Device(DiffSyncModel):
    """Device model."""

    _modelname = "device"
    _identifiers = ("name",)
    _attributes = ("location_name", "model", "vendor")
    _children = {"interface": "interfaces"}

    name: str
    location_name: Optional[str]
    model: Optional[str]
    vendor: Optional[str]
    serial_number: Optional[str]

    mgmt_int: List["MgmtInterface"] = list()  # pylint: disable=use-list-literal
    mgmt_address: Optional[str]

    interfaces: List["Interface"] = list()  # pylint: disable=use-list-literal

    sys_id: Optional[str] = None
    pk: Optional[uuid.UUID] = None

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Nautobot under its parent site."""
        # TODO: Update creation of device role to be dynamic somehow.
        device_type_object = tonb_nbutils.create_device_type_object(
            device_type=attrs["model"], vendor_name=attrs["vendor"]
        )
        device_role_object = tonb_nbutils.create_device_role_object(
            role_name=DEFAULT_DEVICE_ROLE, role_color=DEFAULT_DEVICE_ROLE_COLOR
        )
        device_status_object = tonb_nbutils.create_status(DEFAULT_DEVICE_STATUS, DEFAULT_DEVICE_STATUS_COLOR)
        site_object = tonb_nbutils.create_site(attrs["location_name"])

        new_device = NautobotDevice(
            status=device_status_object,
            device_type=device_type_object,
            device_role=device_role_object,
            site=site_object,
            name=ids["name"],
            serial=ids.get("serial_number", ""),
        )

        new_device.validated_save()

        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete device in Nautobot."""
        device = NautobotDevice.objects.get(name=self.name)
        device.delete()
        super().delete()
        return super().delete()


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
        "mac_address",
        "mtu",
        "type",
        "ip_address",
        "subnet_mask",
        "ip_is_primary",
    )
    _children = {}

    name: str
    device_name: str
    description: Optional[str]
    mac_address: Optional[str]
    mtu: Optional[str]
    type: Optional[str]
    ip_address: Optional[str]
    subnet_mask: Optional[str]
    ip_is_primary: Optional[bool]

    # sys_id: Optional[str] = None
    pk: Optional[uuid.UUID] = None

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create interface in Nautobot under its parent device."""
        device_obj = NautobotDevice.objects.get(name=ids["device_name"])
        interface_obj = tonb_nbutils.create_interface(interface_name=ids["name"], device_obj=device_obj)

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
                if ip.family == 4:
                    device_obj.primary_ip4 = ip
                if ip.family == 6:
                    device_obj.primary_ip6 = ip
                device_obj.validated_save()

        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    # def delete(self) -> Optional["DiffSyncModel"]:
    #     """Delete."""
    #     device = NautobotDevice.objects.get(name=self.device_name)
    #     interface = device.interfaces.get(name=self.name)
    #     interface.delete()
    #     return super().delete()


class MgmtInterface(Interface):
    """
    MgmtInterface class renamed to Interface.
    For compatibility until references are removed.
    """

    _modelname = "mgmt_interface"


Location.update_forward_refs()
Device.update_forward_refs()
