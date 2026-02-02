"""Arkitekt Server Setup Wizard.

This module provides an interactive wizard for configuring the Arkitekt server.
The wizard guides users through:
1. Selecting services to install
2. Configuring the global admin account
3. Creating users
4. Setting up organizations
5. Assigning memberships (users to organizations)
6. Configuring kommunity partners
7. Optional email setup
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.align import Align
import click
import inquirer
from .utils import safe_org_slug
from .logo import ASCI_LOGO
from .config import (
    ArkitektServerConfig,
    Organization,
    EmailConfig,
    User,
    Membership,
    KommunityPartner,
    PreconfiguredComposition,
    create_local_service_aliases,
    generate_name,
)
from .services import (
    SERVICE_REGISTRY,
    get_service_info,
)


def print_section(
    *,
    console: Console,
    title: str,
    content: str,
    border_style: str = "cyan",
) -> None:
    """Print a section header with markdown content.

    Args:
        console: Rich console instance.
        title: Section title.
        content: Markdown content to display.
        border_style: Border color style.
    """
    console.print(
        Panel(
            Markdown(content),
            title=title,
            border_style=border_style,
            expand=True,
        )
    )


def configure_services(*, console: Console, config: ArkitektServerConfig) -> None:
    """Select which services to install.

    Args:
        console: Rich console instance.
        config: Server configuration to modify.
    """
    print_section(
        console=console,
        title="🔧 Service Selection",
        content="""
Select the **services** you want to install.

**Required:**
- **Lok** - Authentication (always enabled)

**Available Services:**
- **Rekuest** - Task orchestration
- **Mikro** - Microscopy data
- **Fluss** - Workflow management
- **Kabinet** - Container deployment
- **Kraph** - Knowledge graph
- **Elektro** - Electrophysiology
- **Alpaka** - AI/ML models
- **Lovekit** - Real-time communication
        """,
        border_style="cyan",
    )

    # Build choices list from service registry
    service_choices = []
    default_enabled = ["rekuest", "mikro", "fluss", "kabinet", "kraph"]

    for identifier, service_class in SERVICE_REGISTRY.items():
        if identifier == "lok":
            continue  # Lok is always required
        info = get_service_info(identifier)
        if info:
            label = f"{info['name']} - {info['description']}"
            service_choices.append((label, identifier))

    # Prompt for service selection
    result = inquirer.prompt(
        [
            inquirer.Checkbox(
                "services",
                message="Select services to enable (Lok is always enabled)",
                choices=service_choices,
                default=[s for s in default_enabled if s != "lok"],
            )
        ]
    )

    selected = result.get("services", []) if result else default_enabled

    # Update config based on selection
    for identifier in SERVICE_REGISTRY:
        if identifier == "lok":
            continue  # Always enabled
        service_config = getattr(config, identifier, None)
        if service_config:
            service_config.enabled = identifier in selected
            info = get_service_info(identifier)
            name = info["name"] if info else identifier
            if identifier in selected:
                console.print(f"  [green]✓[/green] {name}")
            else:
                console.print(f"  [dim]✗ {name}[/dim]")


def configure_global_admin(*, console: Console) -> tuple[str, str, str | None]:
    """Configure the global admin account.

    Args:
        console: Rich console instance.

    Returns:
        Tuple of (username, password, email or None).
    """
    print_section(
        console=console,
        title="🔐 Admin Setup",
        content="""
Configure the **global admin** account.

This superuser manages server settings and has full access.
        """,
    )

    username = click.prompt("Admin username", default="admin")
    password = click.prompt("Admin password", hide_input=True)
    email = click.prompt("Admin email (optional)", default="")

    return username, password, email if email else None


def configure_users(*, console: Console) -> list[User]:
    """Create user accounts.

    Args:
        console: Rich console instance.

    Returns:
        List of User objects.
    """
    print_section(
        console=console,
        title="👤 Users",
        content="""
Create **user accounts**.

Users can later be assigned to organizations with specific roles.
        """,
        border_style="green",
    )

    users: list[User] = []

    if not click.confirm("Create users?", default=True):
        return users

    while True:
        username = click.prompt("Username", default=generate_name())
        password = click.prompt("Password", hide_input=True)
        email = click.prompt("Email (optional)", default="")

        users.append(
            User(
                username=username,
                password=password,
                email=email if email else None,
            )
        )

        console.print(f"  [green]✓[/green] Created user: {username}")

        if not click.confirm("Add another user?", default=False):
            break

    return users


def get_valid_slug(*, console: Console, prompt_text: str, default: str) -> str:
    """Prompt for a valid slug (alphanumeric + underscore, max 12 chars).

    Args:
        console: Rich console instance.
        prompt_text: Text to display in prompt.
        default: Default value.

    Returns:
        Valid slug string.
    """
    while True:
        slug = click.prompt(prompt_text, default=default)
        if len(slug) > 12:
            console.print("[red]Must be max 12 characters.[/red]")
            continue
        if slug != safe_org_slug(slug):
            console.print("[red]Must be alphanumeric and underscore only.[/red]")
            continue
        return slug


def configure_organizations(
    *, console: Console, users: list[User]
) -> list[Organization]:
    """Create organizations with optional owners.

    Args:
        console: Rich console instance.
        users: Available users to select as owners.

    Returns:
        List of Organization objects.
    """
    print_section(
        console=console,
        title="🏢 Organizations",
        content="""
Create **organizations**.

Each organization can have an **owner** who gets admin access automatically.
        """,
        border_style="magenta",
    )

    organizations: list[Organization] = []
    user_names = [u.username for u in users]

    if not user_names:
        console.print(
            "[yellow]No users available. Creating default organization.[/yellow]"
        )
        organizations.append(
            Organization(
                name="default",
                identifier="default",
                description="Default organization",
            )
        )
        return organizations

    while True:
        name = click.prompt("Organization name", default=generate_name())
        identifier = get_valid_slug(
            console=console,
            prompt_text="Organization identifier (slug)",
            default=safe_org_slug(name.lower()),
        )
        description = click.prompt("Description", default="")

        # Select owner
        owner_choices = ["(no owner)"] + user_names
        result = inquirer.prompt(
            [
                inquirer.List(
                    "owner",
                    message="Select owner",
                    choices=owner_choices,
                    default=user_names[0] if user_names else "(no owner)",
                )
            ]
        )

        owner = result.get("owner") if result else None
        if owner == "(no owner)":
            owner = None

        organizations.append(
            Organization(
                name=name,
                identifier=identifier,
                description=description if description else None,
                owner=owner,
                auto_configure=True,
            )
        )

        console.print(
            f"  [green]✓[/green] Created: {name}"
            + (f" (owner: {owner})" if owner else "")
        )

        if not click.confirm("Add another organization?", default=False):
            break

    return organizations


def configure_memberships(
    *,
    console: Console,
    users: list[User],
    organizations: list[Organization],
) -> list[Membership]:
    """Assign users to organizations with roles.

    Args:
        console: Rich console instance.
        users: Available users.
        organizations: Available organizations.

    Returns:
        List of Membership objects.
    """
    print_section(
        console=console,
        title="🔗 Memberships",
        content="""
Assign **users to organizations** with roles.

Available roles: admin, user, bot, viewer, editor

Organization owners are automatically added as admins.
        """,
        border_style="blue",
    )

    memberships: list[Membership] = []

    if not users or not organizations:
        console.print("[yellow]No users or organizations to configure.[/yellow]")
        return memberships

    org_ids = [o.identifier for o in organizations]
    role_choices = ["admin", "user", "bot", "viewer", "editor"]

    # Auto-add owners as admins
    for org in organizations:
        if org.owner:
            memberships.append(
                Membership(
                    user=org.owner,
                    organization=org.identifier,
                    roles=["admin"],
                )
            )
            console.print(
                f"  [cyan]Auto-added:[/cyan] {org.owner} → {org.identifier} (admin)"
            )

    if not click.confirm("Configure additional memberships?", default=True):
        return memberships

    while True:
        # Select user
        user_result = inquirer.prompt(
            [
                inquirer.List(
                    "user",
                    message="Select user",
                    choices=[u.username for u in users],
                )
            ]
        )
        if not user_result:
            break
        username = user_result.get("user")

        # Select organization
        org_result = inquirer.prompt(
            [
                inquirer.List(
                    "organization",
                    message="Select organization",
                    choices=org_ids,
                )
            ]
        )
        if not org_result:
            break
        org_id = org_result.get("organization")

        # Select roles
        roles_result = inquirer.prompt(
            [
                inquirer.Checkbox(
                    "roles",
                    message="Select roles",
                    choices=role_choices,
                    default=["user"],
                )
            ]
        )
        roles = roles_result.get("roles", ["user"]) if roles_result else ["user"]

        # Check for existing membership
        existing = next(
            (m for m in memberships if m.user == username and m.organization == org_id),
            None,
        )
        if existing:
            memberships.remove(existing)
            console.print(f"  [yellow]Updated:[/yellow] {username} → {org_id}")

        memberships.append(
            Membership(
                user=username,
                organization=org_id,
                roles=roles,
            )
        )
        console.print(f"  [green]✓[/green] {username} → {org_id} ({', '.join(roles)})")

        if not click.confirm("Add another membership?", default=False):
            break

    return memberships


def configure_kommunity_partners(
    *,
    console: Console,
    config: ArkitektServerConfig,
) -> list[KommunityPartner]:
    """Configure kommunity partners for external integrations.

    Args:
        console: Rich console instance.
        config: Server configuration.

    Returns:
        List of KommunityPartner objects.
    """
    print_section(
        console=console,
        title="🌐 Kommunity Partners",
        content="""
Configure **kommunity partners** for external service access.

- **autoconfigured**: Auto-discovered by clients
- **preauthorized**: Pre-approved for immediate connection
        """,
        border_style="cyan",
    )

    partners: list[KommunityPartner] = []

    # Build list of enabled services
    local_services = []
    if config.rekuest.enabled:
        local_services.append(("rekuest", "Rekuest", 80, "live.arkitekt.rekuest"))
    if config.mikro.enabled:
        local_services.append(("mikro", "Mikro", 80, "live.arkitekt.mikro"))
    if config.fluss.enabled:
        local_services.append(("fluss", "Fluss", 80, "live.arkitekt.fluss"))
    if config.kabinet.enabled:
        local_services.append(("kabinet", "Kabinet", 80, "live.arkitekt.kabinet"))
    if config.lok.enabled:
        local_services.append(("lok", "Lok", 80, "live.arkitekt.lok"))
    if config.kraph.enabled:
        local_services.append(("kraph", "Kraph", 80, "live.arkitekt.kraph"))

    if not click.confirm("Set up default local partners?", default=True):
        return partners

    # Create both partner types
    for kind in ["autoconfigured", "preauthorized"]:
        partners.append(
            KommunityPartner(
                identifier=f"local_{kind}",
                name=f"Local Arkitekt ({kind.title()})",
                website_url="localhost",
                partner_kind=kind,
                auto_configure=True,
                preconfigured_composition=PreconfiguredComposition(
                    identifier="localhost",
                    instances=create_local_service_aliases(local_services),
                ),
            )
        )
        console.print(f"  [green]✓[/green] Added {kind} partner")

    if click.confirm("Add custom partners?", default=False):
        while True:
            identifier = click.prompt("Partner identifier", default=generate_name())
            name = click.prompt("Partner name", default=f"{identifier} Partner")

            kind_result = inquirer.prompt(
                [
                    inquirer.List(
                        "kind",
                        message="Partner kind",
                        choices=["preauthorized", "autoconfigured"],
                    )
                ]
            )
            kind = (
                kind_result.get("kind", "preauthorized")
                if kind_result
                else "preauthorized"
            )

            partners.append(
                KommunityPartner(
                    identifier=identifier,
                    name=name,
                    website_url="localhost",
                    partner_kind=kind,
                    auto_configure=True,
                    preconfigured_composition=PreconfiguredComposition(
                        identifier="localhost",
                        instances=create_local_service_aliases(local_services),
                    ),
                )
            )
            console.print(f"  [green]✓[/green] Added {name}")

            if not click.confirm("Add another?", default=False):
                break

    return partners


def configure_email(*, console: Console) -> EmailConfig | None:
    """Configure email support (optional).

    Args:
        console: Rich console instance.

    Returns:
        EmailConfig or None if skipped.
    """
    print_section(
        console=console,
        title="📧 Email",
        content="""
Configure **SMTP email** for notifications (optional).
        """,
        border_style="blue",
    )

    if not click.confirm("Enable email?", default=False):
        return None

    return EmailConfig(
        host=click.prompt("SMTP host", default="smtp.example.com"),
        port=click.prompt("SMTP port", type=int, default=587),
        username=click.prompt("SMTP username", default=""),
        password=click.prompt("SMTP password", hide_input=True, default=""),
        email=click.prompt("Sender email", default="noreply@example.com"),
    )


def prompt_config(console: Console) -> ArkitektServerConfig:
    """Run the interactive configuration wizard.

    Args:
        console: Rich console instance.

    Returns:
        Configured ArkitektServerConfig.
    """
    # Welcome banner
    console.print(
        Panel(
            Align.center(Text(ASCI_LOGO, style="bold cyan")),
            border_style="cyan",
            expand=True,
            subtitle=Text("Arkitekt Server Setup", style="bold cyan"),
        )
    )

    config = ArkitektServerConfig()

    # Step 1: Select services
    configure_services(console=console, config=config)

    # Step 2: Global admin
    admin, password, email = configure_global_admin(console=console)
    config.global_admin = admin
    config.global_admin_password = password
    config.global_admin_email = email

    # Step 3: Users
    users = configure_users(console=console)
    config.users = users

    # Step 4: Organizations
    organizations = configure_organizations(console=console, users=users)
    config.organizations = organizations

    # Step 5: Memberships
    memberships = configure_memberships(
        console=console,
        users=users,
        organizations=organizations,
    )
    config.memberships = memberships

    # Step 6: Kommunity partners
    partners = configure_kommunity_partners(console=console, config=config)
    config.kommunity_partners = partners

    # Step 7: Email (optional)
    config.email = configure_email(console=console)

    # Done
    console.print(
        Panel(
            Align.center(Text("✓ Configuration complete!", style="bold green")),
            border_style="green",
            expand=True,
        )
    )

    return config
