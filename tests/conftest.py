"""Pytest configuration for the arkitekt-server test suite.

The reusable fixtures (``arkitekt_server``, ``arkitekt_server_config``) live in
``arkitekt_server.pytest_plugin`` and are loaded automatically via the ``pytest11``
entry point declared in ``pyproject.toml`` -- so nothing needs to be registered
here. Downstream projects that do not install this package as a distribution can
opt in explicitly with ``pytest_plugins = ["arkitekt_server.pytest_plugin"]``.
"""
