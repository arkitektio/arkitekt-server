import typer
from rich.table import Table
from arkitekt_server.commands import console
from arkitekt_server.utils import load_setup_file, update_or_create_yaml_file
from arkitekt_server.config import Organization
from pathlib import Path

app = typer.Typer(help="Manage organizations")


@app.command()
def add(
    name: str = typer.Option(..., prompt=True, help="Name of the organization"),
    identifier: str = typer.Option(None, help="Identifier for the organization"),
    description: str = typer.Option(None, help="Description of the organization"),
    path: Path = typer.Argument(Path("."), help="Path to the configuration file"),
):
    """Add a new organization."""
    config_path = path / "arkitekt_server_config.yaml"
    try:
        setup = load_setup_file(str(config_path))
    except FileNotFoundError:
        console.print(
            f"[bold red]Configuration file not found at {config_path}. Please run 'arkitekt-server init' first.[/bold red]"
        )
        raise typer.Exit(code=1)

    if identifier is None:
        identifier = name.lower().replace(" ", "_")

    # Check if organization already exists
    if any(org.identifier == identifier for org in setup.config.organizations):
        console.print(
            f"[bold red]Organization with identifier '{identifier}' already exists.[/bold red]"
        )
        raise typer.Exit(code=1)

    new_org = Organization(name=name, identifier=identifier, description=description)

    setup.config.organizations.append(new_org)
    update_or_create_yaml_file(str(config_path), setup)
    console.print(f"Organization '{name}' added successfully.")


@app.command("list")
def list_orgs(
    path: Path = typer.Argument(Path("."), help="Path to the configuration file"),
):
    """List all organizations."""
    config_path = path / "arkitekt_server_config.yaml"
    try:
        setup = load_setup_file(str(config_path))
    except FileNotFoundError:
        console.print(
            f"[bold red]Configuration file not found at {config_path}. Please run 'arkitekt-server init' first.[/bold red]"
        )
        raise typer.Exit(code=1)

    table = Table(title="Organizations")
    table.add_column("Name", style="cyan")
    table.add_column("Identifier", style="magenta")
    table.add_column("Description", style="green")

    for org in setup.config.organizations:
        table.add_row(org.name, org.identifier, org.description or "")

    console.print(table)


@app.command()
def delete(
    identifier: str = typer.Argument(
        ..., help="Identifier of the organization to delete"
    ),
    path: Path = typer.Argument(Path("."), help="Path to the configuration file"),
):
    """Delete an organization."""
    config_path = path / "arkitekt_server_config.yaml"
    try:
        setup = load_setup_file(str(config_path))
    except FileNotFoundError:
        console.print(
            f"[bold red]Configuration file not found at {config_path}. Please run 'arkitekt-server init' first.[/bold red]"
        )
        raise typer.Exit(code=1)

    # Find and remove organization
    initial_count = len(setup.config.organizations)
    setup.config.organizations = [
        o for o in setup.config.organizations if o.identifier != identifier
    ]

    if len(setup.config.organizations) == initial_count:
        console.print(f"[bold red]Organization '{identifier}' not found.[/bold red]")
        raise typer.Exit(code=1)

    update_or_create_yaml_file(str(config_path), setup)
    console.print(f"Organization '{identifier}' deleted successfully.")
