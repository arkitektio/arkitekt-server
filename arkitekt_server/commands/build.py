"""Build and deployment commands."""

from pathlib import Path
import typer
from arkitekt_server.dev import create_server
from arkitekt_server.diff import run_dry_run_diff
from arkitekt_server.commands import console
from arkitekt_server.utils import load_setup_file


def build(
    dry_run: bool = typer.Option(
        False, help="Run a dry run to see what files would be created"
    ),
    path: Path = typer.Argument(Path("."), help="Path to the configuration file"),
):
    """Build the deployment configuration based on the selected backend."""
    config_path = path / "arkitekt_server_config.yaml"

    try:
        setup = load_setup_file(str(config_path))
    except FileNotFoundError:
        console.print(
            f"[bold red]Configuration file not found at {config_path}. Please run 'arkitekt-server init' first.[/bold red]"
        )
        raise typer.Exit(code=1)

    console.print(
        f"Building configuration for backend: [bold green]{setup.backend}[/bold green]"
    )

    if setup.backend in ["docker", "podman"]:
        if dry_run:
            console.print("Running dry run...")
            run_dry_run_diff(setup.config, path)
        else:
            console.print("Building configuration files...")
            create_server(path, setup.config)
            console.print("[bold green]Build complete![/bold green]")

    elif setup.backend == "kubernetes":
        console.print("[bold yellow]Kubernetes build not yet implemented[/bold yellow]")
    else:
        console.print(f"[bold red]Unknown backend: {setup.backend}[/bold red]")
        raise typer.Exit(code=1)
