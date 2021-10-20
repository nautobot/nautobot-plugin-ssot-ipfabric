"""Utility functions for Nautobot ORM."""
# from nautobot.extras.models.tags import Tag
# from nautobot.extras.models.customfields import CustomField
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from nautobot.dcim.models import DeviceRole, DeviceType, Manufacturer, Region, Site
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import Interface, IPAddress
from nautobot.tenancy.models import Tenant
from netutils.ip import netmask_to_cidr


def create_site(site_name, region_obj=None, tenant_obj=None):
    """Creates a specified site in Nautobot.

    Args:
        site_name (str): Name of the site.
        region_obj (Region): Region Nautobot Object
        tenant_obj (Tenant): Tenant Nautobot Object
    """
    try:
        site_obj = Site.objects.get(slug=slugify(site_name))
    except Site.DoesNotExist:
        site_obj = Site(
            name=site_name,
            slug=slugify(site_name),
            status=Status.objects.get(name="Active"),
            region=region_obj,
            tenant=tenant_obj,
        )
        site_obj.validated_save()
    return site_obj


def create_region(region_name):
    """Creates a specified region in Nautobot.

    Args:
        region_name (str): Name of the site.
    """
    try:
        region_obj = Region.objects.get(slug=slugify(region_name))
    except Region.DoesNotExist:
        region_obj = Region(name=region_name, slug=slugify(region_name))
        region_obj.validated_save()
    return region_obj


def create_tenant(tenant_name):
    """Create a specified tenant in Nautobot.

    Args:
        tenant_name (str): The name of the tenant.
    """
    try:
        tenant_obj = Tenant.objects.get(slug=slugify(tenant_name))
    except Tenant.DoesNotExist:
        tenant_obj = Tenant(name=tenant_name, slug=slugify(tenant_name))
        tenant_obj.validated_save()
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
    try:
        role_obj = DeviceRole.objects.get(name=role_name)
    except DeviceRole.DoesNotExist:
        role_obj = DeviceRole(name=role_name, slug=role_name.lower(), color=role_color)
        role_obj.validated_save()
    return role_obj


def create_device_status(device_status, device_status_color):
    """Verifies device status object exists in Nautobot. If not, creates specified device status.

    Args:
        device_status (str): Status name.
        device_status_color (str): Status color.
    """
    try:
        status_obj = Status.objects.get(name=device_status)
    except Status.DoesNotExist:
        dcim_device = ContentType.objects.get(app_label="dcim", model="device")
        status_obj = Status(
            name=device_status,
            slug=device_status.lower(),
            color=device_status_color,
            description="Status used for ServiceNow Sync.",
        )
        status_obj.validated_save()
        status_obj.content_types.set([dcim_device])
    return status_obj


def create_ip(ip_address, subnet_mask, status="Active", object_pk=None):
    """Verifies ip address exists in Nautobot. If not, creates specified ip.

    Args:
        ip_address (str): IP address.
        subnet_mask (str): Subnet mask used for IP Address.
        status (str): Status to assign to IP Address.
        object_pk (UUID): The primary key for which to assign the IP to.
    """
    try:
        ip_obj = IPAddress.objects.get(address=ip_address)
    except IPAddress.DoesNotExist:
        cidr = netmask_to_cidr(subnet_mask)
        ip_obj = IPAddress(
            address=f"{ip_address}/{cidr}", status=Status.objects.get(name=status), assigned_object=object_pk
        )
        ip_obj.validated_save()
    return ip_obj


def create_interface(interface_name, device_obj):
    """Verifies interface exists on specified device. If not, creates interface.

    Args:
        interface_name (str): Name of the interface.
        device_obj (Device): Device object to check interface against.
    """
    try:
        interface_obj = device_obj.interfaces.get(name=interface_name)
    except Interface.DoesNotExist:
        interface_obj = device_obj.interfaces.create(name=interface_name)
        device_obj.validated_save()
    return interface_obj
