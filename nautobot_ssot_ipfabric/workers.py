# Disable dispatcher from chatops unused. # pylint: disable=unused-argument
"""Chat Ops Worker."""
import uuid

from django.contrib.contenttypes.models import ContentType
from django_rq import job
from nautobot.extras.models import JobResult
from nautobot_chatops.workers import handle_subcommands, subcommand_of

from nautobot_ssot_ipfabric.jobs import IpFabricDataSource


@job("default")
def ipfabric(subcommand, **kwargs):
    """Interact with ipfabric plugin."""
    return handle_subcommands("ipfabric", subcommand, **kwargs)


@subcommand_of("ipfabric")
def ssot_sync_to_nautobot(dispatcher, dry_run=True):
    """Start an SSoT sync from IPFabric to Nautobot."""
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
    sync_job.run(data, commit=True)
    # To get the url of JOB:
    # sync_job.job_result.get_absolute_url()
