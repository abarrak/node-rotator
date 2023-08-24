'''
' Commandline interface for kube-rotator.
' Inteted to orchstrate flow through cluster and underlying provider.
'
' @file: cli.py
' @author: Abdullah Alotaibi
' @date: 26/03/2023
'''
from enum import Enum
import typer
from typing import Optional
from rich.progress import Progress, SpinnerColumn, TextColumn
from providers.oci import OCIProvider
from providers.self_managed import SelfManaged
from cluster_utils import KubeUtils

__version__ = "1.0.0"

app = typer.Typer(
  rich_help_panel="kube-rotator is a CLI tool to rotate kubernetes' worker nodes.",
  help="kube-rotator is a CLI tool to rotate kubernetes' worker nodes.",
  context_settings={"help_option_names": ["-h", "--help"]},
  add_completion=False
)

def version_callback(value: bool):
  if value:
    print(f"Kube Rotator CLI - Version: {__version__}")
    raise typer.Exit()


class CloudProviders(str, Enum):
  aws = "aws"
  oci = "oci"
  baba = "alibaba"
  self_managed = 'self_managed'
  k3d = "k3d"

class RotationCriteria(str, Enum):
  days = "days"


@app.command()
def rotate(
    version: Optional[bool] = typer.Option(
      None, "--version",
      help="Print the current CLI version.",
      callback=version_callback,
      is_flag=True
    ),
    dry_run: Optional[bool] = typer.Option(
      False,
      help="Run the procedure in dry mode (simulated)."
    ),
    provider: CloudProviders = typer.Option(
      CloudProviders.self_managed,
      case_sensitive=False,
      help="The targe cloud provider: oci, aws, alibaba, k3d."
    ),
    rotate_type: RotationCriteria = typer.Option(
        RotationCriteria.days,
        case_sensitive=False,
        help="The rotation criteria type. Currently only 'days' supported"
    ),
    rotate_value: int = typer.Option(
      60,
      help="The rotation value. Currently only for how long in 'days'."
    ),
    provision_time: int = typer.Option(
      60,
      help="The wait window between provider provision calls in seconds. Default: 1 minute"
    ),
    oci_compartment_id: Optional[str] = typer.Option(
      None,
      help="OCI compartment id of the cluster. Provider specific."
    ),
    oci_cluster_id: Optional[str] = typer.Option(
      None,
      help="OCI cluster ocid. Provider specific."
    ),
    cluster: str = typer.Argument(
      "default",
      help="Name of the cluster (context) to run on. Default is current context."
    )
):
  """
  Rotate the given cluster based on passed crietria.
  """
  # Process cli args.
  #
  chosen_provider = typer.style(provider.title(), fg=typer.colors.RED, bold=True)
  chosen_cluster = typer.style(cluster, fg=typer.colors.GREEN, bold=True)
  chosen_days = typer.style(rotate_value, fg=typer.colors.BRIGHT_YELLOW, bold=True)
  dry_mode = typer.style("in dry mode", fg=typer.colors.BRIGHT_BLACK, bold=True)

  typer.echo(f"The run will target cluster: {chosen_cluster} on {chosen_provider} cloud ..")
  typer.echo(f"Nodes older than {chosen_days} days will be rotated.")

  if dry_run:
    typer.echo(f"Running script {dry_mode}. No actual rotation will occur.")

  kube = KubeUtils(cluster, rotate_value, dry_run)

  # Flow (1): finding aged nodes.
  #
  progress_bar(lambda: kube.scan_nodes(), "Scanning nodes ..")

  rotatable_nodes = kube.rotatable_nodes
  rotatable_count = len(rotatable_nodes)
  if rotatable_count == 0:
    typer.echo("There's no eligiable nodes to rotate. ✅ ", color=True)
    raise typer.Exit()

  # Flow (2): communicate with provider to extend with replacements.
  #
  if provider == CloudProviders.oci:
    opts = { "oci_cluster_id": oci_cluster_id, "oci_compartment_id": oci_compartment_id }
    cloud_api = OCIProvider(rotatable_nodes, provision_time=provision_time, dry=dry_run, **opts)
  elif provider == CloudProviders.self_managed:
    cloud_api = SelfManaged(rotatable_nodes)
  else:
    raise NotImplementedError

  progress_bar(
    lambda: cloud_api.expand_cluster_for_rotation(),
    "Provisioning additional nodes 🛠 .."
  )

  # Flow (3): Run the actual rotation .. discard old and add new.
  #
  progress_bar(lambda: kube.process_nodes(), "Rotating older nodes ♻️  ..")

  # Flow (4): Deregister old nodes and possibly terminate them.
  #
  progress_bar(
    lambda: cloud_api.resize_cluster_after_rotation(), "Restoring to original cluster capacity 🪄 .."
  )

  typer.echo("Done!")
  typer.Exit(0)


def progress_bar(job, description):
  with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    transient=False
  ) as progress:
    progress.add_task(description=f"{description}", total=None)
    job()
