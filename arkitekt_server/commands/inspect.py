"""Inspect and analyze Arkitekt server configuration."""

import typer
from pathlib import Path
from arkitekt_server.commands import console
from arkitekt_server.utils import load_setup_file, show_important_information

app = typer.Typer(help="Inspect the Arkitekt server configuration")


@app.command()
def config(
    path: Path = typer.Argument(Path("."), help="Path to the configuration file"),
):
    """Inspect the current configuration."""
    config_path = path / "arkitekt_server_config.yaml"
    if not config_path.exists():
        console.print(
            f"[bold red]Configuration file not found at {config_path}.[/bold red]"
        )
        raise typer.Exit(1)

    try:
        setup = load_setup_file(str(config_path))
        config = setup.config
        console.print(f"📋 Configuration loaded from: {config_path}", style="blue")
        show_important_information(config)

        # Show enabled services
        console.print("\n🔧 Enabled Services:", style="bold blue")
        services = [
            ("Rekuest", config.rekuest.enabled),
            ("Kabinet", config.kabinet.enabled),
            ("Mikro", config.mikro.enabled),
            ("Fluss", config.fluss.enabled),
            ("Elektro", config.elektro.enabled),
            ("Lok", config.lok.enabled),
            ("Alpaka", config.alpaka.enabled),
            ("Kraph", config.kraph.enabled),
        ]

        for service_name, enabled in services:
            status = "✅" if enabled else "❌"
            console.print(f"  {status} {service_name}")

        # Show gateway configuration
        console.print("\n🌐 Gateway Configuration:", style="bold blue")
        console.print(f"  • HTTP Port: {config.gateway.exposed_http_port}")
        if config.gateway.ssl:
            console.print(f"  • HTTPS Port: {config.gateway.exposed_https_port}")
            console.print("  • SSL: Enabled")
        else:
            console.print("  • SSL: Disabled")

    except Exception as e:
        console.print(f"❌ Error loading configuration: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def services(
    path: Path = typer.Argument(Path("."), help="Path to the configuration file"),
):
    """List all available services and their status."""
    config_path = path / "arkitekt_server_config.yaml"
    if not config_path.exists():
        console.print(
            f"[bold red]Configuration file not found at {config_path}.[/bold red]"
        )
        raise typer.Exit(1)

    try:
        setup = load_setup_file(str(config_path))
        config = setup.config
        console.print("🔧 Service Status Overview:", style="bold blue")

        services = {
            "Database": {"enabled": True, "type": "PostgreSQL"},
            "Redis": {"enabled": True, "type": "Redis"},
            "MinIO": {"enabled": True, "type": "S3 Storage"},
            "Gateway": {
                "enabled": config.gateway.enabled,
                "type": "Caddy Reverse Proxy",
            },
            "Rekuest": {"enabled": config.rekuest.enabled, "type": "Task Management"},
            "Kabinet": {"enabled": config.kabinet.enabled, "type": "App Management"},
            "Mikro": {"enabled": config.mikro.enabled, "type": "Microscopy"},
            "Fluss": {"enabled": config.fluss.enabled, "type": "Workflow"},
            "Elektro": {"enabled": config.elektro.enabled, "type": "Electronics"},
            "Lok": {"enabled": config.lok.enabled, "type": "Authentication"},
            "Alpaka": {"enabled": config.alpaka.enabled, "type": "Alpaka Service"},
            "Kraph": {"enabled": config.kraph.enabled, "type": "Graph Database"},
        }

        for name, info in services.items():
            status = "✅" if info["enabled"] else "❌"
            console.print(f"  {status} {name:<12} - {info['type']}")

    except Exception as e:
        console.print(f"❌ Error loading configuration: {e}", style="red")
        raise typer.Exit(1)
