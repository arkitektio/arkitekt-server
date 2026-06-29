from pathlib import Path
from typer.testing import CliRunner
from typer.main import Typer


def run_init_command(
    app: Typer,
    runner: CliRunner,
    port: int = 80,
    ssl_port: int = 443,
    coord_server: str = "local",
):
    # Run the arkitekt init stable command. The integration tests spin up a full local
    # stack, so default the coordination server to "local" (which provisions Lok).
    result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "stable",
            "--port",
            str(port),
            "--ssl-port",
            str(ssl_port),
            "--coord_server",
            coord_server,
        ],
    )

    # Check that the command succeeded
    assert result.exit_code == 0, (
        f"Command failed with exit code {result.exit_code}. Output: {result.stderr + result.stdout}"
    )


def run_building_command(app: Typer, runner: CliRunner):
    # Run the arkitekt build command
    result = runner.invoke(app, ["build"])

    # Check that the command succeeded
    assert result.exit_code == 0, (
        f"Command failed with exit code {result.exit_code}. Output: {result.stderr + result.stdout}"
    )

    # Check that the config file was created
    config_file = Path("docker-compose.yaml")
    assert config_file.exists(), f"Docker Compose file not created at {config_file}"
