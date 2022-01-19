"""DiffSync adapter class for Ip Fabric."""

import logging

from django.conf import settings
from netutils.mac import mac_to_format

from nautobot_ssot_ipfabric.diffsync import DiffSyncModelAdapters

logger = logging.getLogger("nautobot.jobs")

CONFIG = settings.PLUGINS_CONFIG.get("nautobot_ssot_ipfabric", {})
DEFAULT_INTERFACE_TYPE = CONFIG.get("default_interface_type", "1000base-t")
DEFAULT_INTERFACE_MTU = CONFIG.get("default_interface_mtu", 1500)
DEFAULT_INTERFACE_MAC = CONFIG.get("default_interface_mac", "00:00:00:00:00:01")
DEFAULT_DEVICE_ROLE = CONFIG.get("default_device_role", "Network Device")
DEFAULT_DEVICE_STATUS = CONFIG.get("default_device_status", "Active")


class IPFabricDiffSync(DiffSyncModelAdapters):
    """Nautobot adapter for DiffSync."""

    def __init__(self, job, sync, client, *args, **kwargs):
        """Initialize the NautobotDiffSync."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.client = client

    def load_sites(self):
        """Add IP Fabric Site objects as DiffSync Location models."""
        sites = self.client.get_sites()
        for site in sites:
            location = self.location(diffsync=self, name=site["siteName"], site_id=site["id"])
            self.add(location)

    def load_device_interfaces(self, device_model, interfaces, device_primary_ip):
        """Create and load DiffSync Interface model objects for a specific device."""
        device_interfaces = [iface for iface in interfaces if iface.get("hostname") == device_model.name]
        pseudo_interface = pseudo_management_interface(device_model.name, device_interfaces, device_primary_ip)

        if pseudo_interface:
            device_interfaces.append(pseudo_interface)
            logger.info("Pseudo MGMT Interface: %s", pseudo_interface)

        for iface in device_interfaces:
            ip_address = iface.get("primaryIp")
            interface = self.interface(
                diffsync=self,
                name=iface.get("intName"),
                device_name=iface.get("hostname"),
                description=iface.get("dscr"),
                enabled=True,
                mac_address=mac_to_format(iface.get("mac"), "MAC_COLON_TWO").upper()
                if iface.get("mac")
                else DEFAULT_INTERFACE_MAC,
                mtu=iface.get("mtu") if iface.get("mtu") else DEFAULT_INTERFACE_MTU,
                type=DEFAULT_INTERFACE_TYPE,
                mgmt_only=iface.get("mgmt_only", False),
                ip_address=ip_address,
                subnet_mask="255.255.255.255",
                ip_is_primary=ip_address == device_primary_ip,
            )
            self.add(interface)
            device_model.add_child(interface)

    def load(self):
        """Load data from IP Fabric."""
        self.load_sites()
        devices = self.client.get_device_inventory()
        interfaces = self.client.get_interface_inventory()
        vlans = self.client.get_vlans()
        for location in self.get_all(self.location):
            if location.name is None:
                continue
            location_vlans = [vlan for vlan in vlans if vlan["siteName"] == location.name]
            for vlan in location_vlans:
                vlan = self.vlan(
                    diffsync=self,
                    name=vlan["vlanName"],
                    site=vlan["siteName"],
                    vid=vlan["vlanId"],
                    status=vlan["status"],
                )
                self.add(vlan)
                location.add_child(vlan)
            location_devices = [device for device in devices if device["siteName"] == location.name]
            for device in location_devices:
                device_primary_ip = device["loginIp"]
                device_model = self.device(
                    diffsync=self,
                    name=device["hostname"],
                    location_name=device["siteName"],
                    model=device.get("model") if device.get("model") else f"general-{device.get('vendor')}",
                    vendor=device.get("vendor"),
                    serial_number=device["sn"],
                    role=DEFAULT_DEVICE_ROLE,
                    status=DEFAULT_DEVICE_STATUS,
                )
                self.add(device_model)
                location.add_child(device_model)
                self.load_device_interfaces(device_model, interfaces, device_primary_ip)


def pseudo_management_interface(hostname, device_interfaces, device_primary_ip):
    """Return a dict for an non-existing interface for NAT management addresses."""
    if any(iface for iface in device_interfaces if iface.get("primaryIp", "") == device_primary_ip):
        return None
    return {
        "hostname": hostname,
        "intName": "pseudo_mgmt",
        "dscr": "pseudo interface for NAT IP address",
        "primaryIp": device_primary_ip,
        "type": "virtual",
        "mgmt_only": True,
    }
