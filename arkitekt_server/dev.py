from contextlib import contextmanager
from typing import Generator
from arkitekt_server.diff import write_virtual_config_files
from .config import ArkitektServerConfig
from pathlib import Path
import random
from dokker import Deployment, local
from dataclasses import dataclass


def create_server(path: Path | str, config: ArkitektServerConfig | None = None):
    """
    Create a server configuration at the specified path using the provided config.

    Args:
        path (str): The path where the server configuration will be created.
        config (ArkitektServerConfig): The configuration for the server.

    Returns:
        None
    """
    if isinstance(path, str):
        path = Path(path)

    # Ensure the directory exists
    path.mkdir(parents=True, exist_ok=True)

    if config is None:
        config = ArkitektServerConfig()

    # Write the configuration to a file
    write_virtual_config_files(path, config)


@contextmanager
def temp_server(
    config: ArkitektServerConfig | None = None,
) -> Generator[Path, None, None]:
    """
    Create a temporary server configuration using the provided config.

    This is a context manager that yields the path to the temporary server configuration.
    The server directory is created and cleaned up automatically.

    Attention: The docker compose project that was created will not be cleaned up automatically.
                If you want to clean it up, you have to call `down` on the project manually.
                Or use the `local` function from the `dokker` package to create a local deployment.

    Args:
        config (ArkitektServerConfig): The configuration for the server.

    Yield:
        Path: The path to the temporary server configuration.
    """
    import tempfile

    if not config:
        config = ArkitektServerConfig()

    # Make sure we are creating volumes not bind mounts
    config.minio.mount = None
    config.db.mount = None
    config.gateway.exposed_http_port = random.randint(8000, 9000)
    config.gateway.exposed_https_port = random.randint(9000, 10000)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_server(temp_path, config)
        yield temp_path


@dataclass
class TempDeployment:
    config: ArkitektServerConfig
    deployment: Deployment

    def get_service_url(
        self, service_name: str, internal_port: int = 80, protocol: str = "http"
    ) -> str:
        """Get the URL for a service."""
        service = self.deployment.spec.find_service(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found")

        port = service.get_port_for_internal(internal_port)
        if not port:
            raise ValueError(
                f"Service {service_name} does not expose internal port {internal_port}"
            )

        return f"{protocol}://localhost:{port.published}"

    @property
    def gateway_url(self) -> str:
        """Get the URL for the gateway service."""
        return self.get_service_url("gateway", 80)


@contextmanager
def temp_deployment(
    config: ArkitektServerConfig | None = None,
) -> Generator[TempDeployment, None, None]:
    """
    Create a temporary deployment configuration using the provided config.

    This is a context manager that yields the path to the temporary deployment configuration.
    The deployment directory is created and cleaned up automatically.

    Args:
        config (ArkitektServerConfig): The configuration for the deployment.
    Yield:

    """

    config = config or ArkitektServerConfig()

    with temp_server(config) as temp_path:
        with local(temp_path / "docker-compose.yaml") as setup:
            # Check that the setup can be initialized
            assert setup is not None, "Setup could not be initialized"

            # Check that the services are correctly set up
            assert setup.spec.find_service("gateway") is not None, (
                "Gateway service not found"
            )
            assert setup.spec.find_service("rekuest") is not None, (
                "Rekuest service not found"
            )
            assert setup.spec.find_service("mikro") is not None, (
                "Mikro service not found"
            )
            assert setup.spec.find_service("fluss") is not None, (
                "Fluss service not found"
            )

            yield TempDeployment(config=config, deployment=setup)

            setup.down()
