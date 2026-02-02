"""Tests for the services module."""

import pytest
from arkitekt_server.services import (
    SERVICE_REGISTRY,
    get_service_class,
    get_available_services,
    get_service_info,
    get_all_roles,
    get_all_scopes,
    get_enabled_service_scopes,
    ServiceRole,
    ServiceScope,
    RekuestConfig,
    MikroConfig,
    LokConfig,
    FlussConfig,
    KabinetConfig,
    KraphConfig,
    ElektroConfig,
    AlpakaConfig,
    LovekitConfig,
)


class TestServiceRegistry:
    """Tests for the service registry."""

    def test_registry_contains_all_services(self):
        """Test that registry contains all expected services."""
        expected = [
            "rekuest",
            "mikro",
            "fluss",
            "kabinet",
            "lok",
            "kraph",
            "elektro",
            "alpaka",
            "lovekit",
        ]
        assert set(SERVICE_REGISTRY.keys()) == set(expected)

    def test_get_service_class(self):
        """Test getting service class by identifier."""
        assert get_service_class("rekuest") == RekuestConfig
        assert get_service_class("mikro") == MikroConfig
        assert get_service_class("lok") == LokConfig
        assert get_service_class("nonexistent") is None

    def test_get_available_services(self):
        """Test getting list of available services."""
        services = get_available_services()
        assert len(services) == 9
        assert "rekuest" in services
        assert "lok" in services


class TestServiceInfo:
    """Tests for service info retrieval."""

    def test_get_service_info_rekuest(self):
        """Test getting info for Rekuest service."""
        info = get_service_info("rekuest")
        assert info is not None
        assert info["identifier"] == "rekuest"
        assert info["name"] == "Rekuest"
        assert "Task orchestration" in info["description"]
        assert len(info["roles"]) > 0
        assert len(info["scopes"]) > 0

    def test_get_service_info_nonexistent(self):
        """Test getting info for nonexistent service."""
        info = get_service_info("nonexistent")
        assert info is None


class TestServiceRolesAndScopes:
    """Tests for service roles and scopes."""

    def test_get_all_roles(self):
        """Test getting all roles from all services."""
        roles = get_all_roles()
        assert len(roles) > 0
        role_keys = [r.key for r in roles]
        assert "admin" in role_keys
        assert "user" in role_keys

    def test_get_all_scopes(self):
        """Test getting all scopes from all services."""
        scopes = get_all_scopes()
        assert len(scopes) > 0
        assert "read" in scopes
        assert "write" in scopes
        assert "rekuest_agent" in scopes
        assert "mikro_read" in scopes

    def test_get_enabled_service_scopes_all_enabled(self):
        """Test getting scopes with all services enabled."""
        scopes = get_enabled_service_scopes(
            rekuest_enabled=True,
            mikro_enabled=True,
            fluss_enabled=True,
            kabinet_enabled=True,
            lok_enabled=True,
            kraph_enabled=True,
            elektro_enabled=True,
            alpaka_enabled=True,
            lovekit_enabled=True,
        )
        assert "rekuest_agent" in scopes
        assert "mikro_read" in scopes
        assert "elektro_read" in scopes
        assert "alpaka_infer" in scopes

    def test_get_enabled_service_scopes_partial(self):
        """Test getting scopes with only some services enabled."""
        scopes = get_enabled_service_scopes(
            rekuest_enabled=True,
            mikro_enabled=True,
            fluss_enabled=False,
            kabinet_enabled=False,
            lok_enabled=True,
            kraph_enabled=False,
            elektro_enabled=False,
            alpaka_enabled=False,
            lovekit_enabled=False,
        )
        assert "rekuest_agent" in scopes
        assert "mikro_read" in scopes
        # These should NOT be present
        assert "fluss_read" not in scopes
        assert "kabinet_deploy" not in scopes


class TestServiceConfigs:
    """Tests for individual service configurations."""

    def test_rekuest_config(self):
        """Test Rekuest service configuration."""
        assert RekuestConfig.get_identifier() == "rekuest"
        assert RekuestConfig.get_name() == "Rekuest"
        roles = RekuestConfig.get_roles()
        assert len(roles) > 0
        scopes = RekuestConfig.get_scopes()
        assert any(s.key == "rekuest_agent" for s in scopes)

    def test_mikro_config(self):
        """Test Mikro service configuration."""
        assert MikroConfig.get_identifier() == "mikro"
        config = MikroConfig()
        buckets = config.get_buckets()
        assert "zarr" in buckets
        assert "parquet" in buckets
        assert "media" in buckets

    def test_lok_config(self):
        """Test Lok service configuration."""
        assert LokConfig.get_identifier() == "lok"
        roles = LokConfig.get_roles()
        role_keys = [r.key for r in roles]
        assert "admin" in role_keys
        assert "user" in role_keys
        assert "bot" in role_keys

    def test_kabinet_config(self):
        """Test Kabinet service configuration."""
        config = KabinetConfig()
        assert config.host == "kabinet"
        assert len(config.ensured_repositories) > 0
        scopes = KabinetConfig.get_scopes()
        assert any(s.key == "kabinet_deploy" for s in scopes)

    def test_service_config_defaults(self):
        """Test that service configs have sensible defaults."""
        for identifier, service_class in SERVICE_REGISTRY.items():
            config = service_class()
            assert config.internal_port == 80
            assert config.debug is False
            assert len(config.allowed_hosts) > 0
            assert config.secret_key  # Should be generated


class TestServiceProtocol:
    """Tests for service protocol compliance."""

    def test_all_services_have_identifier(self):
        """Test that all services have an identifier."""
        for identifier, service_class in SERVICE_REGISTRY.items():
            assert service_class.get_identifier() == identifier

    def test_all_services_have_name(self):
        """Test that all services have a display name."""
        for service_class in SERVICE_REGISTRY.values():
            name = service_class.get_name()
            assert name
            assert len(name) > 0

    def test_all_services_have_description(self):
        """Test that all services have a description."""
        for service_class in SERVICE_REGISTRY.values():
            desc = service_class.get_description()
            assert desc
            assert len(desc) > 0

    def test_all_services_have_roles(self):
        """Test that all services define roles."""
        for service_class in SERVICE_REGISTRY.values():
            roles = service_class.get_roles()
            assert len(roles) > 0
            for role in roles:
                assert isinstance(role, ServiceRole)
                assert role.key
                assert role.description

    def test_all_services_have_scopes(self):
        """Test that all services define scopes."""
        for service_class in SERVICE_REGISTRY.values():
            scopes = service_class.get_scopes()
            assert len(scopes) > 0
            for scope in scopes:
                assert isinstance(scope, ServiceScope)
                assert scope.key
                assert scope.description

    def test_all_services_can_build_run_command(self):
        """Test that all services can build a run command."""
        for service_class in SERVICE_REGISTRY.values():
            config = service_class()
            cmd = config.build_run_command()
            assert cmd in ["bash run.sh", "bash run-debug.sh"]
