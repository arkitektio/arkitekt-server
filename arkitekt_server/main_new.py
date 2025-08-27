"""Main entry point for the Arkitekt server CLI."""

import sys
import typer
import rich_click as click
from .logo import ASCI_LOGO

# Import command modules
from .commands import init, auth, build, inspect, service, core

app = typer.Typer(
    rich_markup_mode="rich",
    help="Arkitekt server CLI for managing your local Arkitekt server deployment.",
)

# Add command groups
app.add_typer(
    init.app, name="init", help="Initialize an Arkitekt deployment configuration"
)
app.add_typer(
    auth.app, name="auth", help="Authentication related settings and commands"
)
app.add_typer(
    inspect.app, name="inspect", help="Inspect the Arkitekt server configuration"
)
app.add_typer(build.app, name="build", help="Build deployments for Arkitekt server")
app.add_typer(service.app, name="service", help="Service management commands")

# Add core commands directly to main app
app.command()(core.migrate)
app.command()(core.start)
app.command()(core.update)


@app.command()
def ephemeral(
    port: int | None = typer.Option(
        None, help="HTTP port to expose (will be auto-assigned if not specified)"
    ),
    https_port: int | None = typer.Option(
        None, help="HTTPS port to expose (disabled by default for ephemeral)"
    ),
    defaults: bool = typer.Option(
        False, help="Use default configuration without prompts"
    ),
):
    """Create and start a temporary Arkitekt server instance."""
    core.ephemeral(port, https_port, defaults)


def main():
    """Main entry point for the Arkitekt server CLI."""
    if "--help" in sys.argv or len(sys.argv) == 1:
        click.secho(ASCI_LOGO, fg="cyan", bold=True)
    app()


if __name__ == "__main__":
    main()
