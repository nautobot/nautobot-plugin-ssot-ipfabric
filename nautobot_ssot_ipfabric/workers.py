from nautobot_chatops.workers import subcommand_of, handle_subcommands
from django_rq import job
from nautobot_ssot_ipfabric.jobs import IpFabricDataSource
from nautobot.extras.models import JobResult


@job("default")
def ipfabric(subcommand, **kwargs):
    """Interact with ipfabric plugin."""
    return handle_subcommands("ipfabric", subcommand, **kwargs)


@subcommand_of("ipfabric")
def ssot_sync_to_nautobot(dispatcher, dry_run="True"):
    """Start an SSoT sync from IPFabric to Nautobot."""
    data = {"dry_run": dry_run}
    job = IpFabricDataSource()
    job.job_result = JobResult()
    job.run(data, commit=True)