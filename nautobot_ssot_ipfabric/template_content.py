"""Template Content for other models."""
from nautobot.extras.plugins import PluginTemplateExtension


# pylint: disable=abstract-method
class SiteDiagram(PluginTemplateExtension):
    """Attempt to inject content in."""

    model = "dcim.site"

    def full_width_page(self):
        """Implement cool topology from IPFabric based on site."""
        return self.render(
            "nautobot_ssot_ipfabric/inc/diagram.html",
        )


template_extensions = [SiteDiagram]
