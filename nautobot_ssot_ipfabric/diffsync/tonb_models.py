"""DiffSyncModel subclasses for Nautobot-to-IPFabric data sync."""
import uuid
from typing import List, Optional

from diffsync import DiffSyncModel

# from django.conf import settings
# from requests.api import delete
from nautobot.dcim.models import Device as NautobotDevice
from nautobot.dcim.models import Site

import nautobot_ssot_ipfabric.utilities.nbutils as tonb_nbutils

DEFAULT_DEVICE_ROLE = "leaf"
DEFAULT_DEVICE_ROLE_COLOR = "ff0000"
DEFAULT_DEVICE_STATUS = "Active"
DEFAULT_DEVICE_STATUS_COLOR = "ff0000"


class Location(DiffSyncModel):
    """Location model."""

    _modelname = "location"
    _identifiers = ("name",)
    _attributes = (
        "region_name",
        "container_name",
    )
    _children = {"device": "devices"}

    name: str
    devices: List["Device"] = list()

    sys_id: Optional[str] = None
    region_pk: Optional[uuid.UUID] = None
    site_pk: Optional[uuid.UUID] = None

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Site in Nautobot."""
        region_obj = tonb_nbutils.create_region(region_name=attrs["region_name"])
        tenant_obj = tonb_nbutils.create_tenant(tenant_name=attrs["container_name"])
        tonb_nbutils.create_site(site_name=ids["name"], region_obj=region_obj, tenant_obj=tenant_obj)

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
    _children = {"mgmt_interface": "mgmt_int"}

    name: str
    location_name: Optional[str]
    model: Optional[str]
    vendor: Optional[str]

    mgmt_int: List["MgmtInterface"] = list()
    mgmt_address: Optional[str]
    # interfaces: List["Interface"] = list()

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
        device_status_object = tonb_nbutils.create_device_status(DEFAULT_DEVICE_STATUS, DEFAULT_DEVICE_STATUS_COLOR)
        site_object = tonb_nbutils.create_site(attrs["location_name"])

        new_device = NautobotDevice(
            status=device_status_object,
            device_type=device_type_object,
            device_role=device_role_object,
            site=site_object,
            name=ids["name"],
        )

        new_device.validated_save()

        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete device in Nautobot."""
        device = NautobotDevice.objects.get(name=self.name)
        device.delete()
        super().delete()
        return super().delete()


class MgmtInterface(DiffSyncModel):
    """Mgmt Interface model."""

    _modelname = "mgmt_interface"
    _identifiers = (
        "device_name",
        "name",
    )
    _shortname = ("name",)
    _attributes = (
        "ip_address",
        "subnet_mask",
    )
    _children = {}

    name: Optional[str]
    device_name: Optional[str]
    ip_address: Optional[str]
    subnet_mask: Optional[str]

    sys_id: Optional[str] = None
    pk: Optional[uuid.UUID] = None

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create management interface in Nautobot under its parent device."""
        device_obj = NautobotDevice.objects.get(name=ids["device_name"])
        new_interface = tonb_nbutils.create_interface(interface_name=ids["name"], device_obj=device_obj)
        ipam_ip = tonb_nbutils.create_ip(
            ip_address=attrs["ip_address"],
            subnet_mask=attrs["subnet_mask"],
            status="Active",
            object=new_interface,
        )

        device_obj.primary_ip4 = ipam_ip
        device_obj.validated_save()

        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete."""
        device = NautobotDevice.objects.get(name=self.device_name)
        interface = device.interfaces.get(name=self.name)
        interface.delete()
        return super().delete()


Location.update_forward_refs()
Device.update_forward_refs()
