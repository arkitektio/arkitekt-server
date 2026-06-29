import re

from typer.testing import CliRunner
from arkitekt_server.main import app
from arkitekt_server.config import ArkitektServerConfig, Setup
from arkitekt_server.utils import update_or_create_yaml_file

runner = CliRunner()

# Rich wraps interpolated values in ANSI color codes (e.g. ``'Test Org'`` becomes
# ``\x1b[32m'Test Org'\x1b[0m``), which breaks naive substring checks. Strip the
# escape sequences so assertions match on message content, not exact formatting.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def clean(text: str) -> str:
    """Return ``text`` with ANSI color/style escape sequences removed."""
    return _ANSI_RE.sub("", text)


def test_user_commands():
    """Test user management commands including edge cases."""
    with runner.isolated_filesystem():
        # 1. Test commands without config file
        result = runner.invoke(app, ["user", "list"])
        assert result.exit_code == 1
        assert "Configuration file not found" in clean(result.stdout)

        result = runner.invoke(app, ["user", "add", "--username", "testuser"])
        assert result.exit_code == 1
        assert "Configuration file not found" in clean(result.stdout)

        # Initialize config
        setup = Setup(config=ArkitektServerConfig())
        update_or_create_yaml_file("arkitekt_server_config.yaml", setup)

        # 2. Test adding a user
        result = runner.invoke(
            app, ["user", "add", "--username", "testuser", "--password", "password123"]
        )
        assert result.exit_code == 0
        assert "User 'testuser' added successfully" in clean(result.stdout)

        # 3. Test adding duplicate user
        result = runner.invoke(app, ["user", "add", "--username", "testuser"])
        assert result.exit_code == 1
        assert "User 'testuser' already exists" in clean(result.stdout)

        # 4. Test listing users
        result = runner.invoke(app, ["user", "list"])
        assert result.exit_code == 0
        assert "testuser" in clean(result.stdout)

        # 5. Test deleting user
        result = runner.invoke(app, ["user", "delete", "testuser"])
        assert result.exit_code == 0
        assert "User 'testuser' deleted successfully" in clean(result.stdout)

        # 6. Test deleting non-existent user
        result = runner.invoke(app, ["user", "delete", "nonexistent"])
        assert result.exit_code == 1
        assert "User 'nonexistent' not found" in clean(result.stdout)


def test_organization_commands():
    """Test organization management commands including edge cases."""
    with runner.isolated_filesystem():
        # 1. Test commands without config file
        result = runner.invoke(app, ["organization", "list"])
        assert result.exit_code == 1
        assert "Configuration file not found" in clean(result.stdout)

        # Initialize config
        setup = Setup(config=ArkitektServerConfig())
        update_or_create_yaml_file("arkitekt_server_config.yaml", setup)

        # 2. Test adding an organization
        result = runner.invoke(
            app,
            ["organization", "add", "--name", "Test Org", "--identifier", "test_org"],
        )
        assert result.exit_code == 0
        assert "Organization 'Test Org' added successfully" in clean(result.stdout)

        # 3. Test adding duplicate organization
        result = runner.invoke(
            app,
            ["organization", "add", "--name", "Test Org", "--identifier", "test_org"],
        )
        assert result.exit_code == 1
        assert "Organization with identifier 'test_org' already exists" in clean(result.stdout)

        # 4. Test listing organizations
        result = runner.invoke(app, ["organization", "list"])
        assert result.exit_code == 0
        assert "Test Org" in clean(result.stdout)
        assert "test_org" in clean(result.stdout)

        # 5. Test deleting organization
        result = runner.invoke(app, ["organization", "delete", "test_org"])
        assert result.exit_code == 0
        assert "Organization 'test_org' deleted successfully" in clean(result.stdout)

        # 6. Test deleting non-existent organization
        result = runner.invoke(app, ["organization", "delete", "nonexistent"])
        assert result.exit_code == 1
        assert "Organization 'nonexistent' not found" in clean(result.stdout)


def test_inspect_commands():
    """Test inspect commands including edge cases."""
    with runner.isolated_filesystem():
        # 1. Test inspect without config
        result = runner.invoke(app, ["inspect", "config"])
        assert result.exit_code == 1
        assert "Configuration file not found" in clean(result.stdout)

        # Initialize config
        setup = Setup(config=ArkitektServerConfig())
        update_or_create_yaml_file("arkitekt_server_config.yaml", setup)

        # 2. Test inspect config
        result = runner.invoke(app, ["inspect", "config"])
        assert result.exit_code == 0
        assert "Configuration loaded from" in clean(result.stdout)
        assert "Enabled Services" in clean(result.stdout)

        # 3. Test inspect services
        result = runner.invoke(app, ["inspect", "services"])
        assert result.exit_code == 0
        assert "Service Status Overview" in clean(result.stdout)
