# Disable dispatcher from chatops unused. # pylint: disable=unused-argument
"""Chat Ops Worker."""
import uuid

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django_rq import job
from nautobot.core.settings_funcs import is_truthy
from nautobot.extras.models import JobResult
from nautobot_chatops.choices import CommandStatusChoices
from nautobot_chatops.workers import handle_subcommands, subcommand_of

from nautobot_ssot_ipfabric.jobs import IpFabricDataSource

configs = settings.PLUGINS_CONFIG.get("nautobot_ssot_ipfabric", {})
BASE_CMD = "ipfabric"
IPFABRIC_LOGO_PATH = "nautobot_ssot_ipfabric/ipfabric_logo.png"
IPFABRIC_LOGO_ALT = "IPFabric Logo"


def prompt_for_dry_run(dispatcher, action_id, help_text):
    """Prompt the user to select a Network name."""
    choices = [("Yes", "True"), ("No", "False")]
    return dispatcher.prompt_from_menu(action_id, help_text, choices, default=("Yes", "True"))


def ipfabric_logo(dispatcher):
    """Construct an image_element containing the locally hosted IP Fabric logo."""
    return dispatcher.image_element(dispatcher.static_url(IPFABRIC_LOGO_PATH), alt_text=IPFABRIC_LOGO_ALT)


@job("default")
def ipfabric(subcommand, **kwargs):
    """Interact with ipfabric plugin."""
    return handle_subcommands("ipfabric", subcommand, **kwargs)


@subcommand_of("ipfabric")
def ssot_sync_to_nautobot(dispatcher, dry_run=None):
    """Start an SSoT sync from IPFabric to Nautobot."""
    if not dry_run:
        prompt_for_dry_run(dispatcher, f"{BASE_CMD} ssot-sync-to-nautobot", "Do you want to run a dry run?")
        return False

    dry_run = is_truthy(dry_run)
    data = {"dry_run": dry_run}
    sync_job = IpFabricDataSource()
    sync_job.job_result = JobResult(
        name=sync_job.class_path,
        obj_type=ContentType.objects.get(
            app_label="extras",
            model="job",
        ),
        job_id=uuid.uuid4(),
    )
    sync_job.job_result.validated_save()

    dispatcher.send_markdown(
        f"Stand by {dispatcher.user_mention()}, I'm running your sync with dry run set to {dry_run}.",
        ephemeral=True,
    )

    sync_job.run(data, commit=True)
    sync_job.post_run()
    sync_job.job_result.status = "completed" if not sync_job.failed else "failed"
    sync_job.job_result.save()
    blocks = [
        *dispatcher.command_response_header(
            "ipfabric",
            "ssot-sync-to-nautobot",
            [("Dry Run", str(dry_run))],
            "sync job",
            ipfabric_logo(dispatcher),
        ),
    ]
    dispatcher.send_blocks(blocks)
    if sync_job.job_result.status == "completed":
        dispatcher.send_markdown(
            f"Sync completed succesfully. Here is the link to your job: {configs['NAUTOBOT_HOST']}{sync_job.sync.get_absolute_url()}."
        )
    else:
        dispatcher.send_warning(
            f"Sync failed. Here is the link to your job: {configs['NAUTOBOT_HOST']}{sync_job.sync.get_absolute_url()}"
        )
    return CommandStatusChoices.STATUS_SUCCEEDED
    # To get the url of JOB:
    # sync_job.job_result.get_absolute_url()
