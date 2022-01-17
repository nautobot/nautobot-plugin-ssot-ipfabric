"""Testing."""
from nautobot.extras.plugins import PluginTemplateExtension


# pylint: disable=abstract-method
class SiteDiagram(PluginTemplateExtension):
    """Attempt to inject content in."""

    model = "dcim.site"

    def full_width_page(self):
        """Implement cool topology from IPFabric based on site."""
        return self.render(
            "nautobot_ssot_ipfabric/inc/diagram.html",
            extra_context={
                "ipfabric_site": "{{ settings.PLUGINS_CONFIG.nautobot_ssot_ipfabric.ipfabric_host }}/graph?urls=domains%3Fad%3DvSite%252F55467784%2Btransit%3Fad%3DvSite%252F55467784"
            },
        )


template_extensions = [SiteDiagram]
