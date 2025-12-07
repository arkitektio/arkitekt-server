from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.align import Align
import click
import inquirer
from .utils import safe_org_slug
from .logo import ASCI_LOGO
from .config import ArkitektServerConfig, Organization, EmailConfig, User, Membership
from .config import generate_name

console = Console()


def print_section_header(
    console: Console, title: str, content: str, border_style: str = "cyan"
) -> None:
    """Helper to print consistent section headers with Markdown content."""
    console.print(
        Panel(
            Markdown(content),
            title=title,
            border_style=border_style,
            expand=True,
        )
    )


def configure_global_admin(console: Console) -> tuple[str, str]:
    """Handles the configuration of the global admin account."""
    print_section_header(
        console,
        "",
        """
This wizard will guide you through setting up your **Arkitekt Server**.

Arkitekt is a multi-tenant server designed to manage data and workflows for various labs, institutions, or projects.
As such, it supports multiple organizations, users, and roles.

You will configure:
- A **global admin** account to manage server settings
- One or more **organizations** (e.g. `openuc2`, `anatlab`)
- **Users** who can access the server, each belonging to an organization
- Optional **email support** for notifications (experimental)

🔐 First, you'll configure the global admin — the account that manages the server settings.
        """,
    )
    username = click.prompt("Enter the global admin username", default="admin")
    password = click.prompt("Enter the global admin password", hide_input=True)
    return username, password


def get_valid_org_slug(console: Console, default_slug: str) -> str:
    """Prompts for and validates an organization slug."""
    while True:
        org_slug = click.prompt(
            "Enter the organization slug (max 8 characters)",
            default=default_slug,
        )
        if len(org_slug) > 12:
            console.print(
                "[bold red]⚠️ Organization slug must be max 12 characters.[/bold red]"
            )
            continue
        if org_slug != safe_org_slug(org_slug):
            console.print(
                "[bold red]⚠️ Organization slug must be alphanumeric and _[/bold red]"
            )
            continue
        return org_slug


def configure_organizations(console: Console) -> list[Organization]:
    """Handles the configuration of organizations."""
    print_section_header(
        console,
        "🔧 Organization Setup",
        """
### Organizations

Lets configure the organizations that will use twith this Arkitekt server.

You can define:
- A **single global organization**, or
- **Multiple named organizations** (e.g. `openuc2`, `anatlab`)

Users ca belong to multiple organizations, and each organization can specify its own roles 
which will be used to manage permissions and access control. Some common roles include:

- `admin`: Full access to manage the organization
- `user`: Regular user with limited permissions
- `bot`: Automated processes or services that interact with the organization

You can define custom organizations here, or use a single global organization.
        """,
        border_style="magenta",
    )

    organizations: list[Organization] = []

    if click.confirm("Would you like to define custom organizations?", default=True):
        while True:
            org_name = click.prompt(
                "Enter the organization name (max 8 characters)",
                default=generate_name(),
            )
            org_slug = get_valid_org_slug(console, safe_org_slug(org_name.lower()))
            org_description = click.prompt(
                "Enter a short description",
                default="This is a sample organization for the Arkitekt server.",
            )

            organizations.append(
                Organization(
                    name=org_name, description=org_description, identifier=org_slug
                )
            )

            if not click.confirm("Add another organization?"):
                break
    else:
        console.print("[yellow]Using a single global organization.[/yellow]")
        organizations.append(
            Organization(
                name="global",
                description="This is the global organization for the Arkitekt server.",
                identifier="global",
            )
        )
    return organizations


def configure_email(console: Console) -> EmailConfig | None:
    """Handles the configuration of email support."""
    print_section_header(
        console,
        "📧 Email Setup",
        """
### Email Support (Experimental)

You can enable email notifications (e.g. for password resets or invites) via an SMTP server.

This is optional and can be skipped if you're running locally or without email features.
        """,
        border_style="blue",
    )

    if click.confirm("Would you like to enable email support?", default=False):
        return EmailConfig(
            host=click.prompt("SMTP host", default="smtp.example.com"),
            port=click.prompt("SMTP port", type=int, default=587),
            username=click.prompt("SMTP username", default=""),
            password=click.prompt("SMTP password", hide_input=True, default=""),
            email=click.prompt("Sender email address", default="noreply@example.com"),
        )
    return None


def select_user_organizations(
    console: Console, available_orgs: list[Organization]
) -> list[str]:
    """Prompts the user to select organizations."""
    while True:
        org_choice = inquirer.prompt(
            [
                inquirer.Checkbox(
                    "organizations",
                    message="Select the organizations this user belongs to",
                    choices=[o.identifier for o in available_orgs],
                    default=[available_orgs[0].identifier],
                )
            ]
        )

        if not org_choice or not org_choice.get("organizations"):
            console.print(
                "[bold red]⚠️ No organization selected, please select at least one organization.[/bold red]"
            )
            continue

        return org_choice["organizations"]


def select_user_roles(console: Console, org_name: str) -> list[str]:
    """Prompts the user to select roles for a specific organization."""
    role_choices = ["admin", "user", "bot", "viewer", "editor"]
    while True:
        inquisition = inquirer.prompt(
            [
                inquirer.Checkbox(
                    "roles",
                    message=f"Select the roles for this user within the {org_name} organization",
                    choices=role_choices,
                    default=[role_choices[0]],
                )
            ]
        )

        roles = inquisition.get("roles", []) if inquisition else []
        if not roles:
            console.print(
                "[bold red]⚠️ No roles selected, please select at least one role.[/bold red]"
            )
            continue
        return roles


def configure_users(console: Console, organizations: list[Organization]) -> list[User]:
    """Handles the configuration of users."""
    print_section_header(
        console,
        "👤 Users",
        """
### User Setup

Now you can define users who can access the Arkitekt services.

Each user:
- Belongs to one organization
- Has one or more roles (`admin`, `user`) in that organization

The **global admin** you defined earlier is not included here — these are standard users.

Attention: We will autogenerate a Bot user for you for some arkitekt internal services, which will be used for automated tasks and 
background processes. This user will have the `bot` role in all organizations.
        """,
        border_style="green",
    )

    users: list[User] = []
    while True:
        username = click.prompt("Enter the username")
        password = click.prompt("Enter the password", hide_input=True)
        email = click.prompt("Enter the email (optional)", default="")

        selected_orgs = select_user_organizations(console, organizations)
        memberships = []

        for org in selected_orgs:
            roles = select_user_roles(console, org)
            memberships.append(Membership(organization=org, roles=roles))

        active_org_choice = inquirer.prompt(
            [
                inquirer.List(
                    "organization",
                    message="Select the active organization for this user",
                    choices=selected_orgs,
                    default=selected_orgs[0],
                )
            ]
        )

        active_org = (
            active_org_choice.get("organization", selected_orgs[0])
            if active_org_choice
            else selected_orgs[0]
        )

        users.append(
            User(
                username=username,
                password=password,
                email=email or None,
                active_organization=active_org,
                memberships=memberships,
            )
        )

        console.print(f"Added user: {username}")

        if not click.confirm("Add another user?", default=False):
            break
    return users


def prompt_config(console: Console) -> ArkitektServerConfig:
    """Main function to prompt for server configuration."""
    # Welcome
    console.print(
        Panel(
            Align.center(Text(ASCI_LOGO, style="bold cyan")),
            title="",
            border_style="cyan",
            expand=True,
            subtitle=Text(
                "Welcome to the Arkitekt Server Setup Wizard", style="bold cyan"
            ),
        )
    )

    config = ArkitektServerConfig()

    config.global_admin, config.global_admin_password = configure_global_admin(console)
    config.organizations = configure_organizations(console)
    config.email = configure_email(console)
    config.users = configure_users(console, config.organizations)

    # Final message
    console.print(
        Panel(
            Align.center(
                Text("✔️ Arkitekt configuration complete!", style="bold green")
            ),
            border_style="green",
            expand=True,
        )
    )

    return config
