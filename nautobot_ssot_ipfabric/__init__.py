"""Plugin declaration for nautobot_ssot_ipfabric."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
try:
    from importlib import metadata
except ImportError:
    # Python version < 3.8
    import importlib_metadata as metadata

__version__ = metadata.version(__name__)

from nautobot.extras.plugins import PluginConfig


class NautobotSSoTIPFabricConfig(PluginConfig):
    """Plugin configuration for the nautobot_ssot_ipfabric plugin."""

    name = "nautobot_ssot_ipfabric"
    verbose_name = "Nautobot SSoT IPFabric"
    version = __version__
    author = "Network to Code, LLC"
    description = "Nautobot SSoT IPFabric."
    base_url = "ssot-ipfabric"
    required_settings = ["ipfabric_host", "ipfabric_api_token"]
    min_version = "1.1.0"
    max_version = "1.9999"
    default_settings = {}
    caching_config = {}


config = NautobotSSoTIPFabricConfig  # pylint:disable=invalid-name
