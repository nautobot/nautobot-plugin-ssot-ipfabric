"""Diff sync shared adapter class attritbutes to synchronize applications."""

from diffsync import DiffSync

from nautobot_ssot_ipfabric.diffsync import diffsync_models


class DiffSyncModelAdapters(DiffSync):
    """Nautobot adapter for DiffSync."""

    location = diffsync_models.Location
    device = diffsync_models.Device
    interface = diffsync_models.Interface
    vlan = diffsync_models.Vlan

    top_level = [
        "location",
    ]
