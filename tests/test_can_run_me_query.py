from pathlib import Path
from typer.testing import CliRunner
from arkitekt_server.main import app
from tests.utils import run_building_command, run_init_command
from dokker import testing
import requests
import pytest


@pytest.mark.integration
def test_vitality():
    """Test that runs the building command in a temporary folder."""

    runner = CliRunner()
    # Create a temporary directory
    with runner.isolated_filesystem() as temp_dir:
        port = 4569

        run_init_command(app, runner, port=port, ssl_port=4568)
        run_building_command(app, runner)

        docker_compose_file = Path("docker-compose.yaml")
        assert docker_compose_file.exists(), (
            f"Docker Compose file not created at {docker_compose_file}"
        )

        setup = testing(docker_compose_file)

        mikro_watcher = setup.create_watcher("mikro")

        for service in ["rekuest", "mikro", "fluss", "lok", "kabinet"]:
            # Bind ``service`` via default arg: the lambda is evaluated later during
            # ``check_health()``, and without this every health check would close over
            # the loop's final value and only ever probe the last service.
            setup.add_health_check(
                url=lambda spec, service=service: (
                    f"http://localhost:{setup.spec.find_service('gateway').get_port_for_internal(80).published}/{service}/ht"
                ),
                service=service,
                # First boot runs database migrations, which can take a while.
                timeout=10,
                max_retries=60,
            )

        with setup:
            setup.inspect()

            assert (
                setup.spec.find_service("gateway").get_port_for_internal(80).published
                == 4569
            ), "Gateway service is not exposed on the expected port"

            setup.down()
            setup.pull()
            setup.up()

            setup.check_health()

            service = "mikro"

            graphl_api = f"http://localhost:{setup.spec.find_service('gateway').get_port_for_internal(80).published}/{service}/graphql"

            with mikro_watcher:
                answer = requests.post(
                    graphl_api,
                    json={
                        "query": """
                        query CanRunMeQuery {
                            canRunMeQuery
                        }
                        """
                    },
                )

                assert answer.status_code == 200, "Needs to return a"
