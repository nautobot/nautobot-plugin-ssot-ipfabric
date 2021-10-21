"""Utility functions for Nautobot ORM."""
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from nautobot.dcim.models import DeviceRole, DeviceType, Manufacturer, Region, Site
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress
from nautobot.tenancy.models import Tenant
from netutils.ip import netmask_to_cidr


def create_site(site_name, region_obj=None, tenant_obj=None):
    """Creates a specified site in Nautobot.

    Args:
        site_name (str): Name of the site.
        region_obj (Region): Region Nautobot Object
        tenant_obj (Tenant): Tenant Nautobot Object
    """
    site_obj, _ = Site.objects.get_or_create(
        name=site_name,
        slug=slugify(site_name),
        status=Status.objects.get(name="Active"),
        region=region_obj,
        tenant=tenant_obj,
    )
    return site_obj


def create_region(region_name):
    """Creates a specified region in Nautobot.

    Args:
        region_name (str): Name of the site.
    """
    region_obj, _ = Region.objects.get_or_create(name=region_name, slug=slugify(region_name))
    return region_obj


def create_tenant(tenant_name):
    """Create a specified tenant in Nautobot.

    Args:
        tenant_name (str): The name of the tenant.
    """
    tenant_obj, _ = Tenant.objects.get_or_create(name=tenant_name, slug=slugify(tenant_name))
    return tenant_obj


def create_device_type_object(device_type, vendor_name):
    """Create a specified device type in Nautobot.

    Args:
        device_type (str): Device model gathered from DiffSync model.
        vendor_name (str): Vendor Name
    """
    mf_name = create_manufacturer(vendor_name)
    device_type_obj, _ = DeviceType.objects.get_or_create(
        manufacturer=mf_name, model=device_type, slug=slugify(device_type)
    )
    return device_type_obj


def create_manufacturer(vendor_name):
    """Create specified manufacturer in Nautobot."""
    mf_name, _ = Manufacturer.objects.get_or_create(name=vendor_name, slug=slugify(vendor_name))
    return mf_name


def create_device_role_object(role_name, role_color):
    """Create specified device role in Nautobot.

    Args:
        role_name (str): Role name.
        role_color (str): Role color.
    """
    role_obj, _ = DeviceRole.objects.get_or_create(name=role_name, slug=slugify(role_name), color=role_color)
    return role_obj


def create_status(status_name, status_color, description="", app_label="dcim", model="device"):
    """Verifies status object exists in Nautobot. If not, creates specified status. Defaults to dcim | device.

    Args:
        status_name (str): Status name.
        status_color (str): Status color.
        description (str): Description
        app_label (str): App Label ("DCIM")
        model (str): Django Model ("DEVICE")
    """
    try:
        status_obj = Status.objects.get(name=status_name)
    except Status.DoesNotExist:
        content_type = ContentType.objects.get(app_label=app_label, model=model)
        status_obj = Status.objects.create(
            name=status_name,
            slug=slugify(status_name),
            color=status_color,
            description=description,
        )
        status_obj.content_types.set([content_type])
    return status_obj


def create_ip(ip_address, subnet_mask, status="Active", object_pk=None):
    """Verifies ip address exists in Nautobot. If not, creates specified ip.

    Args:
        ip_address (str): IP address.
        subnet_mask (str): Subnet mask used for IP Address.
        status (str): Status to assign to IP Address.
        object_pk (UUID): Object to assign interface
    """
    status_obj = Status.objects.get_for_model(IPAddress).get(slug=slugify(status))
    cidr = netmask_to_cidr(subnet_mask)
    ip_obj, _ = IPAddress.objects.get_or_create(address=f"{ip_address}/{cidr}", status=status_obj)
    if object_pk:
        ip_obj.assigned_object_id = object_pk
    return ip_obj


def create_interface(interface_name, device_obj):
    """Verifies interface exists on specified device. If not, creates interface.

    Args:
        interface_name (str): Name of the interface.
        device_obj (Device): Device object to check interface against.
    """
    interface_obj, _ = device_obj.interfaces.get_or_create(name=interface_name)
    return interface_obj


def create_vlan(vlan_name: str, vlan_id: int, vlan_status: str, site_obj: Site):
    """Creates or obtains VLAN object.

    Args:
        vlan_name (str): VLAN Name
        vlan_id (int): VLAN ID
        vlan_status (str): VLAN Status
        site_obj (Site): Site Django Model

    Returns:
        (VLAN): Returns created or obtained VLAN object.
    """
    status = Status.objects.get(name=vlan_status)
    vlan_obj, _ = site_obj.vlans.get_or_create(name=vlan_name, vid=vlan_id, status=status)
    return vlan_obj