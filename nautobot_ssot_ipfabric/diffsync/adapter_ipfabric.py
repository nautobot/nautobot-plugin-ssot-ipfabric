"""DiffSync adapter class for Ip Fabric."""

from diffsync import DiffSync

from . import tonb_models


class IPFabricDiffSync(DiffSync):
    """Nautobot adapter for DiffSync."""

    location = tonb_models.Location
    device = tonb_models.Device
    interface = tonb_models.Interface
    vlan = tonb_models.Vlan

    top_level = [
        "location",
    ]

    def __init__(self, *args, job, sync, client, **kwargs):
        """Initialize the NautobotDiffSync."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.client = client

    def load_sites(self):
        """Add IP Fabric Site objects as DiffSync Location models."""
        sites = self.client.get_sites()
        for site in sites:
            self.job.log_debug(message=f"Loading Site {site['siteName']}")
            location = self.location(diffsync=self, name=site["siteName"])
            self.add(location)

    # def load_devices(self):
    #     """Add IP Fabric Device objects as DiffSync Location models."""
    #     devices = self.client.get_device_inventory()
    #     for device in devices:
    #         self.job.log_debug(message=f"Loading Device {device['hostname']}")
    #         device = self.device(
    #             diffsync=self,
    #             name=device["hostname"],
    #             location_name=device["siteName"],
    #             model=device["model"],
    #             vendor=device["vendor"],
    #             serial_number=device["sn"],
    #         )
    #         self.location.add_child(device)
    #         self.job.log_debug(message=device)

    # def load_primary_ip_interface(self, interface_record, device_model, device_record):
    #     """Import a Nautobot primary IP interface object as a DiffSync MgmtInterface model."""
    #     pass

    def load_device_interfaces(self, device_model, interfaces, device_primary_ip):
        """Create and load DiffSync Interface model objects for a specific device."""
        device_interfaces = [iface for iface in interfaces if iface.get("hostname") == device_model.name]
        self.job.log_debug(message=f"Loading {len(device_interfaces)} interfaces for device '{device_model.name}'")

        for iface in device_interfaces:
            ip_address = iface["primaryIp"]
            ip_is_primary = ip_address == device_primary_ip
            # self.job.log_debug(message=f'{iface["hostname"]}  {device_primary_ip}, {iface["intName"]} {ip_address}')

            interface = self.interface(
                diffsync=self,
                name=iface["intName"],
                device_name=iface["hostname"],
                mac_address=iface["mac"],
                mtu=iface["mtu"],
                ip_address=iface["primaryIp"],
                subnet_mask="255.255.255.255",  # TODO: (GREG) Determine how to handle mask.
                type="1000base-t",  # TODO: (GREG) Determine how to handle type.
                ip_is_primary=ip_is_primary,
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
                self.job.log_debug(message=f"VLAN: {vlan}")
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
                )
                self.add(device_model)
                location.add_child(device_model)
                self.load_device_interfaces(device_model, interfaces, device_primary_ip)
                self.job.log_debug(message=device_model)
