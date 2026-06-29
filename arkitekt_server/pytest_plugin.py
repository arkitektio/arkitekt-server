"""Pytest plugin exposing reusable fixtures for testing Arkitekt deployments.

This module is registered as a ``pytest11`` entry point (see ``pyproject.toml``),
so the fixtures below are available automatically to any project that has
``arkitekt-server`` installed. Downstream projects can also load it explicitly via
``pytest_plugins = ["arkitekt_server.pytest_plugin"]`` in their ``conftest.py``.

Example::

    @pytest.mark.integration
    def test_rekuest(arkitekt_server):
        srv = arkitekt_server(services=["rekuest", "mikro"])
        with srv.setup:
            srv.setup.up()
            srv.setup.check_health()
            ...
"""

from contextlib import ExitStack
from typing import Callable

import pytest

from arkitekt_server.config import ArkitektServerConfig
from arkitekt_server.dev import (
    ArkitektServer,
    Channel,
    create_test_config,
    temp_setup,
)


def pytest_configure(config: pytest.Config) -> None:
    """Register the ``integration`` marker so the plugin is self-contained."""
    config.addinivalue_line(
        "markers",
        "integration: requires Docker / spins up a real Arkitekt deployment",
    )


@pytest.fixture
def arkitekt_server() -> Callable[..., ArkitektServer]:
    """Factory fixture that generates temporary Arkitekt deployments.

    Call the returned factory with the services you want enabled::

        srv = arkitekt_server(services=["rekuest", "mikro"])

    Each call generates a fresh deployment in a temporary directory and returns an
    :class:`~arkitekt_server.dev.ArkitektServer` handle whose ``setup`` is a
    not-yet-started ``dokker`` deployment with health checks pre-registered. The
    test controls the docker lifecycle (``up()``/``down()``). Every deployment
    created during the test (and its temp directory) is cleaned up on teardown.
    """
    stack = ExitStack()

    def _factory(
        services: list[str] | None = None,
        *,
        config: ArkitektServerConfig | None = None,
        channel: Channel | None = None,
    ) -> ArkitektServer:
        return stack.enter_context(
            temp_setup(services, config=config, channel=channel)
        )

    try:
        yield _factory
    finally:
        stack.close()


@pytest.fixture
def arkitekt_server_config() -> Callable[..., ArkitektServerConfig]:
    """Factory fixture returning :func:`create_test_config` for config-only tests."""
    return create_test_config
