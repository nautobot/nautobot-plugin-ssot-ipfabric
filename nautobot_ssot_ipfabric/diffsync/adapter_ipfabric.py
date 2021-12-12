"""DiffSync adapter class for Ip Fabric."""

from nautobot_ssot_ipfabric.diffsync import DiffSyncModelAdapters

# import logging

# logger = logging.getLogger("nautobot.jobs")


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
            # logger.log_debug(message=f"Loading Site {site['siteName']}")
            location = self.location(diffsync=self, name=site["siteName"], site_id=site["id"])
            self.add(location)

    def load_device_interfaces(self, device_model, interfaces, device_primary_ip):
        """Create and load DiffSync Interface model objects for a specific device."""
        device_interfaces = [iface for iface in interfaces if iface.get("hostname") == device_model.name]
        self.job.log_debug(message=f"Loading {len(device_interfaces)} interfaces for device '{device_model.name}'")

        pseudo_interface = pseudo_management_interface(device_model.name, device_interfaces, device_primary_ip)
        if pseudo_interface:
            device_interfaces.append(pseudo_interface)

        for iface in device_interfaces:
            ip_address = iface.get("primaryIp")
            interface = self.interface(
                diffsync=self,
                name=iface.get("intName"),
                device_name=iface.get("hostname"),
                description=iface.get("dscr"),
                enabled=not iface.get("reason") == "admin",
                mac_address=iface.get("mac"),
                mtu=iface.get("mtu"),
                # TODO: (GREG) Determine how to handle interface type.
                type=iface.get("type", "1000base-t"),
                mgmt_only=iface.get("mgmt_only", False),
                ip_address=iface.get("primaryIp"),
                # TODO: (GREG) Determine how to handle mask.
                subnet_mask="255.255.255.255",
                # TODO: (GREG) Determine how to handle type.
                ip_is_primary=ip_address == device_primary_ip,
            )
            self.add(interface)
            device_model.add_child(interface)
            # self.job.log_debug(message=interface)

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
                self.job.log_debug(message=f"Loading VLAN {vlan['vlanName']}")
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
                self.job.log_debug(message=f"Loading Device {device['hostname']}")
                device_primary_ip = device["loginIp"]
                device_model = self.device(
                    diffsync=self,
                    name=device["hostname"],
                    location_name=device["siteName"],
                    model=device["model"],
                    vendor=device["vendor"],
                    serial_number=device["sn"],
                    role="Network Device",
                )
                self.add(device_model)
                location.add_child(device_model)
                self.load_device_interfaces(device_model, interfaces, device_primary_ip)
                self.job.log_debug(message=device_model)


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
