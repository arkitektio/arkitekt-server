import typer
from rich.table import Table
from arkitekt_server.commands import console
from arkitekt_server.utils import load_setup_file, update_or_create_yaml_file
from arkitekt_server.config import User
from pathlib import Path

app = typer.Typer(help="Manage users")


@app.command()
def add(
    username: str = typer.Option(..., prompt=True, help="Username"),
    email: str = typer.Option(None, help="Email address"),
    password: str = typer.Option(
        None, help="Password (leave empty to generate automatically)"
    ),
    path: Path = typer.Argument(Path("."), help="Path to the configuration file"),
):
    """Add a new user."""
    config_path = path / "arkitekt_server_config.yaml"
    try:
        setup = load_setup_file(str(config_path))
    except FileNotFoundError:
        console.print(
            f"[bold red]Configuration file not found at {config_path}. Please run 'arkitekt-server init' first.[/bold red]"
        )
        raise typer.Exit(code=1)

    # Check if user already exists
    if any(user.username == username for user in setup.config.users):
        console.print(f"[bold red]User '{username}' already exists.[/bold red]")
        raise typer.Exit(code=1)

    user_data = {
        "username": username,
        "email": email,
    }
    if password:
        user_data["password"] = password

    new_user = User(**user_data)

    setup.config.users.append(new_user)
    update_or_create_yaml_file(str(config_path), setup)
    console.print(f"User '{username}' added successfully.")
    if not password:
        console.print(
            f"Generated password: [bold green]{new_user.password}[/bold green]"
        )


@app.command("list")
def list_users(
    path: Path = typer.Argument(Path("."), help="Path to the configuration file"),
):
    """List all users."""
    config_path = path / "arkitekt_server_config.yaml"
    try:
        setup = load_setup_file(str(config_path))
    except FileNotFoundError:
        console.print(
            f"[bold red]Configuration file not found at {config_path}. Please run 'arkitekt-server init' first.[/bold red]"
        )
        raise typer.Exit(code=1)

    table = Table(title="Users")
    table.add_column("Username", style="cyan")
    table.add_column("Email", style="magenta")
    table.add_column("Active Organization", style="green")

    for user in setup.config.users:
        table.add_row(user.username, user.email or "", user.active_organization)

    console.print(table)


@app.command()
def delete(
    username: str = typer.Argument(..., help="Username to delete"),
    path: Path = typer.Argument(Path("."), help="Path to the configuration file"),
):
    """Delete a user."""
    config_path = path / "arkitekt_server_config.yaml"
    try:
        setup = load_setup_file(str(config_path))
    except FileNotFoundError:
        console.print(
            f"[bold red]Configuration file not found at {config_path}. Please run 'arkitekt-server init' first.[/bold red]"
        )
        raise typer.Exit(code=1)

    # Find and remove user
    initial_count = len(setup.config.users)
    setup.config.users = [u for u in setup.config.users if u.username != username]

    if len(setup.config.users) == initial_count:
        console.print(f"[bold red]User '{username}' not found.[/bold red]")
        raise typer.Exit(code=1)

    update_or_create_yaml_file(str(config_path), setup)
    console.print(f"User '{username}' deleted successfully.")
