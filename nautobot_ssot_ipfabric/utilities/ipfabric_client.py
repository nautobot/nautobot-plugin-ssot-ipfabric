"""Extending IP Fabric connection from IP Fabric ChatOps."""
from nautobot_chatops_ipfabric.ipfabric import IpFabric


class IpFabricClient(IpFabric):
    """Class for interfacing with IP Fabric API."""

    def __init__(self, host_url, token):  # pylint: disable=W0235
        """Instantiates init from parent class to create connection."""
        super().__init__(host_url, token)

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
