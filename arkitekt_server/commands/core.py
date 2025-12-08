"""Core server management commands."""

import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from rich.console import Console

from arkitekt_server.config import DatenConfig, GatewayConfig, MinioConfig

from arkitekt_server.utils import load_yaml_file

console = Console()


def run_command_in_directory(command: str, directory: Path):
    """Run a shell command in a specific directory."""
    result = subprocess.run(command, shell=True, cwd=directory, check=True)
    return result


def migrate():
    """Migrate the server to the latest version."""
    console.print("[blue]Starting server migration...[/blue]")

    try:
        load_yaml_file("arkitekt_server_config.yaml")
        console.print("[green]Migration completed successfully![/green]")
    except FileNotFoundError:
        console.print(
            "[red]No configuration file found. Please run 'arkitekt init' first.[/red]"
        )
        return


def start():
    """Start the Arkitekt server."""
    console.print("[blue]Starting Arkitekt server...[/blue]")

    try:
        # Use subprocess directly since we simplified the command
        subprocess.run("docker compose up -d", shell=True, check=True)
        console.print("[green]Arkitekt server started successfully![/green]")

    except subprocess.CalledProcessError:
        console.print(
            "[red]Failed to start the server. Make sure Docker is running and you have a docker-compose.yaml file.[/red]"
        )
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")


def update():
    """Update the Arkitekt server."""
    console.print("[blue]Updating Arkitekt server...[/blue]")

    try:
        # Pull latest images and restart
        subprocess.run("docker compose pull", shell=True, check=True)
        subprocess.run("docker compose up -d", shell=True, check=True)
        console.print("[green]Arkitekt server updated successfully![/green]")

    except subprocess.CalledProcessError:
        console.print(
            "[red]Failed to update the server. Make sure Docker is running.[/red]"
        )
    except Exception as e:
        console.print(f"[red]Error updating server: {e}[/red]")


def ephemeral(
    port: int | None = None, https_port: int | None = None, defaults: bool = False
):
    """Create and start a temporary Arkitekt server instance."""
    from ..dev import create_server
    from ..config import ArkitektServerConfig

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="arkitekt_ephemeral_"))
    console.print(f"[blue]Creating ephemeral server in: {temp_dir}[/blue]")

    cleanup_performed = False

    def cleanup():
        """Clean up resources when the server is stopped."""
        nonlocal cleanup_performed
        if cleanup_performed:
            return
        cleanup_performed = True

        console.print("\n[yellow]Stopping ephemeral server...[/yellow]")

        # Stop Docker Compose services
        try:
            run_command_in_directory("docker compose down", temp_dir)
            console.print("[green]Docker services stopped.[/green]")
        except Exception as e:
            console.print(f"[red]Warning: Error stopping Docker services: {e}[/red]")

        # Remove temporary directory
        try:
            import shutil

            shutil.rmtree(temp_dir)
            console.print(f"[green]Cleaned up temporary directory: {temp_dir}[/green]")
        except Exception as e:
            console.print(f"[red]Warning: Error cleaning up directory: {e}[/red]")

    def signal_handler(signum, frame):
        """Handle interrupt signals."""
        cleanup()
        sys.exit(0)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Create ephemeral configuration
        config = ArkitektServerConfig(
            global_admin="admin",
            global_admin_password="admin123",  # Simple password for ephemeral
            db=DatenConfig(mount=None),
            minio=MinioConfig(mount=None),
            gateway=GatewayConfig(
                exposed_http_port=port or 24891, exposed_https_port=https_port
            ),
        )

        # Create server in temporary directory
        create_server(temp_dir, config)

        # Start the server
        console.print("[blue]Starting ephemeral server with Docker Compose...[/blue]")
        run_command_in_directory("docker compose up -d", temp_dir)

        # Display connection info
        access_url = f"http://localhost:{config.gateway.exposed_http_port}"
        console.print("\n[green]✅ Ephemeral Arkitekt server is running![/green]")
        console.print(f"[blue]Access URL: {access_url}[/blue]")
        console.print(f"[blue]Admin user: {config.global_admin}[/blue]")
        console.print(f"[blue]Admin password: {config.global_admin_password}[/blue]")

        for user in config.users:
            console.print("\n[green]Additional user created:[/green]")
            console.print(f"[blue]User: {user.username}[/blue]")
            console.print(f"[blue]Password: {user.password}[/blue]")
        console.print(f"[yellow]Temporary directory: {temp_dir}[/yellow]")
        console.print(
            "\n[yellow]Press Ctrl+C to stop the server and clean up resources.[/yellow]"
        )

        # Keep the process running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    except Exception as e:
        console.print(f"[red]Error running ephemeral server: {e}[/red]")
    finally:
        cleanup()
