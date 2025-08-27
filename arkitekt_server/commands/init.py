"""Initialization commands for Arkitekt server."""

import typer
from arkitekt_server.config import ArkitektServerConfig
from arkitekt_server.wizard import prompt_config
from arkitekt_server.commands import console, update_or_create_yaml_file

app = typer.Typer(help="Initialize an Arkitekt deployment configuration")


@app.command()
def stable(
    defaults: bool = False, port: int | None = None, ssl_port: int | None = None
):
    """Create a stable production configuration for Arkitekt server."""
    # Create a default configuration file if it doesn't exist
    config = ArkitektServerConfig() if defaults else prompt_config(console)
    if port is not None:
        config.gateway.exposed_http_port = port
    if ssl_port is not None:
        config.gateway.exposed_https_port = ssl_port

    config.mikro.image = "jhnnsrs/mikro:latest"
    config.fluss.image = "jhnnsrs/fluss:latest"
    config.elektro.image = "jhnnsrs/elektro:latest"
    config.alpaka.image = "jhnnsrs/alpaka:latest"
    config.lok.image = "jhnnsrs/lok:latest"
    config.rekuest.image = "jhnnsrs/rekuest:latest"

    console.print("Creating stable configuration file for Arkitekt server...")
    update_or_create_yaml_file("arkitekt_server_config.yaml", config)


@app.command()
def default(defaults: bool = False, port: int | None = None):
    """Create a default configuration for Arkitekt server."""
    # Create a default configuration file if it doesn't exist
    config = ArkitektServerConfig() if defaults else prompt_config(console)
    if port is not None:
        config.gateway.exposed_http_port = port

    console.print("Creating default configuration file for Arkitekt server...")
    update_or_create_yaml_file("arkitekt_server_config.yaml", config)


@app.command()
def dev(defaults: bool = False, port: int | None = None):
    """Create a development configuration for Arkitekt server."""
    # Create a default configuration file if it doesn't exist
    config = ArkitektServerConfig() if defaults else prompt_config(console)
    if port is not None:
        config.gateway.exposed_http_port = port

    config.rekuest.mount_github = True
    config.mikro.mount_github = True
    config.fluss.mount_github = True
    config.elektro.mount_github = True
    config.lok.mount_github = True
    config.alpaka.mount_github = True

    console.print("Creating development configuration file for Arkitekt server...")
    update_or_create_yaml_file("arkitekt_server_config.yaml", config)
