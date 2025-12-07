"""Initialization commands for Arkitekt server."""

import typer
import click
from pathlib import Path
from typing import cast, Literal
from arkitekt_server.config import ArkitektServerConfig, Setup
from arkitekt_server.wizard import prompt_config
from arkitekt_server.commands import console
from arkitekt_server.utils import update_or_create_yaml_file


def create_stable_config(config: ArkitektServerConfig) -> ArkitektServerConfig:
    """Create a stable production configuration for Arkitekt server."""
    config.mikro.image = "jhnnsrs/mikro:latest"
    config.fluss.image = "jhnnsrs/fluss:latest"
    config.elektro.image = "jhnnsrs/elektro:latest"
    config.alpaka.image = "jhnnsrs/alpaka:latest"
    config.lok.image = "jhnnsrs/lok:latest"
    config.rekuest.image = "jhnnsrs/rekuest:latest"
    return config


def create_dev_config(config: ArkitektServerConfig) -> ArkitektServerConfig:
    """Create a development configuration for Arkitekt server."""
    config.rekuest.mount_github = True
    config.mikro.mount_github = True
    config.fluss.mount_github = True
    config.elektro.mount_github = True
    config.lok.mount_github = True
    config.alpaka.mount_github = True
    return config


def create_minimal_config(config: ArkitektServerConfig) -> ArkitektServerConfig:
    """Create a minimal configuration for Arkitekt server."""
    # Minimal config logic here if needed
    return config


def create_default_config(config: ArkitektServerConfig) -> ArkitektServerConfig:
    """Create a default configuration for Arkitekt server."""
    # Default config logic here if needed
    return config


def init(
    template: str = typer.Option(
        "default",
        "--template",
        "-t",
        help="The template to use (stable, dev, default, minimal)",
    ),
    wizard: bool = typer.Option(
        False, "--wizard", "-w", help="Run the configuration wizard"
    ),
    port: int | None = None,
    ssl_port: int | None = None,
    backend: str = typer.Option(
        None, help="The backend to use (docker, podman, kubernetes)"
    ),
    path: Path = typer.Argument(
        Path("."), help="The path where to initialize the server"
    ),
):
    """Create a configuration for Arkitekt server based on a template."""
    # Create a default configuration file if it doesn't exist
    config = prompt_config(console) if wizard else ArkitektServerConfig()

    if wizard and backend is None:
        backend = typer.prompt(
            "Which backend would you like to use?",
            default="docker",
            type=click.Choice(["docker", "podman", "kubernetes"]),
        )

    if port is not None:
        config.gateway.exposed_http_port = port
    if ssl_port is not None:
        config.gateway.exposed_https_port = ssl_port

    if template == "stable":
        config = create_stable_config(config)
    elif template == "dev":
        config = create_dev_config(config)
    elif template == "minimal":
        config = create_minimal_config(config)
    elif template == "default":
        config = create_default_config(config)
    else:
        console.print(f"[bold red]Unknown template: {template}[/bold red]")
        raise typer.Exit(code=1)

    setup = Setup(
        config=config,
        backend=cast(Literal["docker", "podman", "kubernetes"], backend or "docker"),
    )

    # Ensure the directory exists
    path.mkdir(parents=True, exist_ok=True)

    console.print(
        f"Creating {template} configuration file for Arkitekt server with {setup.backend} backend at {path}..."
    )
    update_or_create_yaml_file(str(path / "arkitekt_server_config.yaml"), setup)
