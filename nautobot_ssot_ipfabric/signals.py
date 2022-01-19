"""Signal handlers for nautobot_ssot_ipfabric."""

from typing import List

from nautobot.extras.choices import CustomFieldTypeChoices
from nautobot.utilities.choices import ColorChoices


def create_custom_field(field_name: str, label: str, models: List, apps):
    """Create custom field on a given model instance type.

    Args:
        field_name (str): Field Name
        label (str): Label description
        models (List): List of Django Models
        apps: Django Apps
    """
    ContentType = apps.get_model("contenttypes", "ContentType")  # pylint:disable=invalid-name
    CustomField = apps.get_model("extras", "CustomField")  # pylint:disable=invalid-name
    custom_field, _ = CustomField.objects.get_or_create(
        type=CustomFieldTypeChoices.TYPE_TEXT,
        name=field_name,
        defaults={
            "label": label,
        },
    )
    for model in models:
        custom_field.content_types.add(ContentType.objects.get_for_model(model))


def nautobot_database_ready_callback(sender, *, apps, **kwargs):  # pylint: disable=unused-argument
    """Callback function triggered by the nautobot_database_ready signal when the Nautobot database is fully ready."""
    # pylint: disable=invalid-name
    Device = apps.get_model("dcim", "Device")
    DeviceType = apps.get_model("dcim", "DeviceType")
    DeviceRole = apps.get_model("dcim", "DeviceRole")
    Interface = apps.get_model("dcim", "Interface")
    IPAddress = apps.get_model("ipam", "IPAddress")
    Manufacturer = apps.get_model("dcim", "Manufacturer")
    Site = apps.get_model("dcim", "Site")
    VLAN = apps.get_model("ipam", "VLAN")
    Tag = apps.get_model("extras", "Tag")

    Tag.objects.get_or_create(
        slug="ssot-synced-from-ipfabric",
        name="SSoT Synced from IPFabric",
        defaults={
            "description": "Object synced at some point from IPFabric to Nautobot",
            "color": ColorChoices.COLOR_LIGHT_GREEN,
        },
    )
    Tag.objects.get_or_create(
        slug="ssot-safe-delete",
        name="SSoT Safe Delete",
        defaults={
            "description": "Safe Delete Mode tag to flag an object, but not delete from Nautobot.",
            "color": ColorChoices.COLOR_RED,
        },
    )
    # Ensure that the "ssot-synced-from-ipfabric" custom field is present; as above, it *should* already exist.
    synced_from_models = [Device, DeviceType, Interface, Manufacturer, Site, VLAN, DeviceRole, IPAddress]
    create_custom_field("ssot-synced-from-ipfabric", "Last synced from IPFabric on", synced_from_models, apps=apps)
    site_model = [Site]
    create_custom_field("ipfabric-site-id", "IPFabric Site ID", site_model, apps=apps)
