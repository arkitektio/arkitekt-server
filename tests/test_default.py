from pathlib import Path
from typing import Optional

import pytest
from dokker import local
from fakts_next import Fakts
from fakts_next.cache.file import FileCache
from fakts_next.fakts import Fakts
from fakts_next.grants.remote import RemoteGrant
from fakts_next.grants.remote.claimers.post import ClaimEndpointClaimer
from fakts_next.grants.remote.demanders.device_code import (
    ClientKind,
    DeviceCodeDemander,
    DeviceCodeHook,
    display_in_terminal,
)
from fakts_next.grants.remote.demanders.redeem import RedeemDemander
from fakts_next.grants.remote.demanders.static import StaticDemander
from fakts_next.grants.remote.discovery.well_known import WellKnownDiscovery
from fakts_next.models import Manifest, Requirement
from typer.testing import CliRunner

from arkitekt_server.main import app
from tests.utils import run_building_command, run_init_command


@pytest.mark.integratoin
def test_run_fakts():
    """Test that runs the building command in a temporary folder."""

    runner = CliRunner()

    manifest = Manifest(
        identifier="test-service",
        version="1.0.0",
        scopes=["read", "write"],
        requirements=[
            Requirement(key="rekuest", service="live.arkitekt.rekuest"),
        ],
    )

    # Create a temporary directory
    with runner.isolated_filesystem() as temp_dir:
        port = 4569

        run_init_command(app, runner, port=port, ssl_port=4568)
        run_building_command(app, runner)

        docker_compose_file = Path("docker-compose.yaml")
        assert docker_compose_file.exists(), (
            f"Docker Compose file not created at {docker_compose_file}"
        )

        setup = local(docker_compose_file)
        setup.down_on_exit = True

        for service in ["rekuest", "mikro", "fluss", "lok", "kabinet"]:
            setup.add_health_check(
                url=lambda spec: f"http://localhost:{setup.spec.find_service('gateway').get_port_for_internal(80).published}/{service}/ht",
                service=service,
                timeout=5,
                max_retries=10,
            )

        with setup:
            setup.inspect()

            setup.pull()

            setup.up()

            setup.check_health()

            async def device_code_hook(device_code: str):
                await setup.arun(
                    "lok",
                    f"uv run python manage.py validatecode --code {device_code} --user demo --org arkitektio --composition ",
                )

            demander = DeviceCodeDemander(
                manifest=manifest,
                open_browser=False,
                requested_client_kind=ClientKind.DEVELOPMENT,
                device_code_hook=device_code_hook,
            )

            fakts = Fakts(
                grant=RemoteGrant(
                    demander=demander,
                    discovery=WellKnownDiscovery(
                        url="url", auto_protocols=["https", "http"]
                    ),
                    claimer=ClaimEndpointClaimer(),
                ),
                manifest=manifest,
            )

            with fakts:
                t = fakts.get_alias("rekuest")
                assert t is not None, "Could not get rekueest alias"
