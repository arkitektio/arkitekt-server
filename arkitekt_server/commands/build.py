"""Build and deployment commands."""

from pathlib import Path
import typer
from arkitekt_server.create import create_server
from arkitekt_server.diff import run_dry_run_diff
from arkitekt_server.commands import console, load_or_create_yaml_file

app = typer.Typer(help="Build deployments for Arkitekt server")


@app.command()
def docker(
    dry_run: bool = typer.Option(
        False, help="Run a dry run to see what files would be created"
    ),
    path: Path = Path("."),
):
    """Build Docker Compose configuration."""
    console.print("Building Docker Compose configuration...")

    # Load the configuration
    config = load_or_create_yaml_file("arkitekt_server_config.yaml")

    if dry_run:
        console.print("Running dry run...")
        from pathlib import Path

        run_dry_run_diff(config, path)
    else:
        console.print("Building configuration files...")
        # TODO: Implement actual build process
        create_server(path, config)


@app.command()
def kubernetes(
    dry_run: bool = typer.Option(
        False, help="Run a dry run to see what files would be created"
    ),
):
    """Build Kubernetes configuration."""
    console.print("Building Kubernetes configuration...")
    typer.echo("Kubernetes build not yet implemented")
    # TODO: Implement Kubernetes build


@app.command()
def helm(
    dry_run: bool = typer.Option(
        False, help="Run a dry run to see what files would be created"
    ),
):
    """Build Helm chart."""
    console.print("Building Helm chart...")
    typer.echo("Helm build not yet implemented")
    # TODO: Implement Helm build
