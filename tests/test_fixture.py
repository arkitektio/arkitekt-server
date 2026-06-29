"""Tests for the reusable ``arkitekt_server`` pytest fixture."""

from pathlib import Path

import pytest
import yaml


def _compose_services(path: Path) -> dict:
    """Load the ``services`` mapping from a generated docker-compose.yaml."""
    content = yaml.safe_load((path / "docker-compose.yaml").read_text())
    return content.get("services", {})


def test_fixture_generates_temp_dir(arkitekt_server):
    """The factory writes a docker-compose.yaml into a temporary directory."""
    srv = arkitekt_server(services=["rekuest"])

    assert srv.path.exists()
    assert (srv.path / "docker-compose.yaml").exists()


def test_fixture_enables_only_selected_services(arkitekt_server):
    """Only the requested services (plus lok) end up in the compose file."""
    srv = arkitekt_server(services=["rekuest"])

    # Config-level flags
    assert srv.config.rekuest.enabled is True
    assert srv.config.lok.enabled is True  # always required
    assert srv.config.mikro.enabled is False
    assert srv.config.fluss.enabled is False
    assert set(srv.enabled_services) == {"rekuest", "lok"}

    # Generated docker-compose reflects the selection
    services = _compose_services(srv.path)
    assert "rekuest" in services
    assert "lok" in services
    assert srv.config.gateway.host in services
    assert "mikro" not in services
    assert "fluss" not in services


def test_fixture_unknown_service_raises(arkitekt_server):
    """Selecting an unknown service is a clear error."""
    with pytest.raises(ValueError):
        arkitekt_server(services=["does-not-exist"])


def test_fixture_default_channel_keeps_configured_image(arkitekt_server):
    """Without a channel the service keeps its configured image/version."""
    from arkitekt_server.config import ArkitektServerConfig

    default_image = ArkitektServerConfig().rekuest.image
    srv = arkitekt_server(services=["rekuest"])
    assert srv.config.rekuest.image == default_image


@pytest.mark.parametrize("channel", ["next", "latest"])
def test_fixture_channel_retags_images(arkitekt_server, channel):
    """The channel param switches the image tag for the Arkitekt services."""
    srv = arkitekt_server(services=["rekuest", "mikro"], channel=channel)

    assert srv.config.rekuest.image.endswith(f":{channel}")
    assert srv.config.mikro.image.endswith(f":{channel}")
    assert srv.config.lok.image.endswith(f":{channel}")


@pytest.mark.integration
def test_fixture_spins_up_deployment(arkitekt_server):
    """Integration: bring the selected services up and verify health + GraphQL."""
    import requests

    srv = arkitekt_server(services=["rekuest", "mikro"])

    with srv.setup:
        srv.setup.pull()
        srv.setup.up()
        srv.setup.check_health()

        response = requests.post(
            srv.graphql_url("mikro"),
            json={"query": "query CanRunMeQuery { canRunMeQuery }"},
        )
        assert response.status_code == 200
