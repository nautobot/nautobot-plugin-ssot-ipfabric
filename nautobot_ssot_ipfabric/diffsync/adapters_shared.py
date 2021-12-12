"""Diff sync shared adapter class attritbutes to synchronize applications."""

from diffsync import DiffSync

from nautobot_ssot_ipfabric.diffsync import tonb_models


class DiffSyncModelAdapters(DiffSync):
    """Nautobot adapter for DiffSync."""

    location = tonb_models.Location
    device = tonb_models.Device
    interface = tonb_models.Interface
    vlan = tonb_models.Vlan

    top_level = [
        "location",
    ]
