"""Extending IP Fabric connection from IP Fabric ChatOps."""
import logging

from nautobot_chatops_ipfabric.ipfabric import IpFabric

logger = logging.getLogger("ipfabric")


class IpFabricClient(IpFabric):
    """Class for interfacing with IP Fabric API."""

    def __init__(self, host_url, token):  # pylint: disable=W0235
        """Instantiates init from parent class to create connection."""
        super().__init__(
            host_url,
            token,
        )

    def get_sites(self, snapshot_id="$last"):
        """Return Site info."""
        payload = {
            "columns": [
                "id",
                "siteName",
                "siteKey",
                "devicesCount",
                "usersCount",
                "stpDCount",
                "switchesCount",
                "vlanCount",
                "rDCount",
                "routersCount",
                "networksCount",
            ],
            "snapshot": snapshot_id,
            "sort": {"column": "siteName", "order": "asc"},
        }

        return self.get_response("/api/v1/tables/inventory/sites", payload)

    # pylint: disable=arguments-differ
    def get_device_inventory(
        self,
        search_key=None,
        filters=None,
        snapshot_id="$last",
    ):
        """Return Device info."""
        logger.debug("Received device inventory request")
        if search_key:
            pass

        # columns and snapshot required
        payload = {
            "columns": [
                "hostname",
                "siteName",
                "vendor",
                "platform",
                "model",
                "memoryUtilization",
                "version",
                "sn",
                "loginIp",
            ],
            "filters": filters if filters else {},
            "snapshot": snapshot_id,
        }

        logger.debug("Requesting inventory with payload: %s", payload)
        return self.get_response("/api/v1/tables/inventory/devices", payload)

    # pylint: disable=arguments-renamed
    def get_interface_inventory(
        self,
        search_key=None,
        filters=None,
        device=None,
        snapshot_id="$last",
    ):
        """Return Interface info."""
        logger.debug("Received interface inventory request")
        if search_key:
            pass

        filters = filters if filters else {}
        if device:
            filters["hostname"] = ["eq", device]

        payload = {
            "columns": [
                "id",
                "hostname",
                "intName",
                "reason",
                "dscr",
                "mac",
                "duplex",
                "speed",
                "media",
                "mtu",
                "primaryIp",
                # "hasTransceiver",
            ],
            "filters": filters,
            "snapshot": snapshot_id,
        }

        logger.debug("Requesting interface inventory with payload: %s", payload)
        return self.get_response("/api/v1/tables/inventory/interfaces", payload)

    # pylint: disable=arguments-renamed
    def get_vlans(
        self,
        filters=None,
        snapshot_id="$last",
    ):
        """Return VLAN info."""
        logger.debug("Received VLAN inventory request")

        # columns and snapshot required
        payload = {
            "columns": ["siteName", "vlanName", "vlanId", "dscr"],
            "filters": filters if filters else {},
            "snapshot": snapshot_id,
        }

        logger.debug("Requesting VLAN information with payload: %s", payload)
        return self.get_response("/api/v1/tables/vlan/site-summary", payload)
