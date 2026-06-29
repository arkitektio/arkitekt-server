"""Tests for the new wizard flow and config generation."""

import pytest
from pathlib import Path
import yaml
from arkitekt_server.config import (
    ArkitektServerConfig,
    Organization,
    User,
    Membership,
    KommunityPartner,
    PreconfiguredComposition,
    ServiceInstance,
    ServiceAlias,
    ServiceManifest,
    create_local_service_aliases,
    create_default_kommunity_partners,
    generate_name,
)
from arkitekt_server.diff import write_virtual_config_files


class TestOrganizationModel:
    """Tests for the Organization model with owner field."""

    def test_organization_with_owner(self):
        """Test creating an organization with an owner."""
        org = Organization(
            name="Test Org",
            identifier="test_org",
            description="A test organization",
            owner="testuser",
            auto_configure=True,
        )
        assert org.name == "Test Org"
        assert org.identifier == "test_org"
        assert org.owner == "testuser"
        assert org.auto_configure is True
        assert org.bot_name == "Test Org_bot"

    def test_organization_without_owner(self):
        """Test creating an organization without an owner."""
        org = Organization(
            name="No Owner Org",
            identifier="no_owner",
            description="An organization without owner",
        )
        assert org.owner is None
        assert org.auto_configure is True  # default

    def test_organization_auto_configure_default(self):
        """Test that auto_configure defaults to True."""
        org = Organization(name="Test", identifier="test")
        assert org.auto_configure is True


class TestUserMembership:
    """Tests for User and Membership models (now separate)."""

    def test_user_creation(self):
        """Test creating a user (simple model without memberships)."""
        user = User(
            username="testuser",
            password="testpass",
            email="test@example.com",
        )
        assert user.username == "testuser"
        assert user.password == "testpass"
        assert user.email == "test@example.com"

    def test_user_without_email(self):
        """Test creating a user without email."""
        user = User(
            username="nomail",
            password="pass",
        )
        assert user.email is None

    def test_membership_with_user(self):
        """Test creating a membership with user field."""
        membership = Membership(
            user="testuser",
            organization="org1",
            roles=["admin"],
        )
        assert membership.user == "testuser"
        assert membership.organization == "org1"
        assert membership.roles == ["admin"]

    def test_multiple_memberships(self):
        """Test creating multiple memberships for different users."""
        memberships = [
            Membership(user="user1", organization="org1", roles=["admin"]),
            Membership(user="user1", organization="org2", roles=["user", "viewer"]),
            Membership(user="user2", organization="org1", roles=["user"]),
        ]
        assert len(memberships) == 3
        user1_memberships = [m for m in memberships if m.user == "user1"]
        assert len(user1_memberships) == 2


class TestKommunityPartnerModel:
    """Tests for KommunityPartner and related models."""

    def test_service_alias_creation(self):
        """Test creating a ServiceAlias."""
        alias = ServiceAlias(
            challenge="ht",
            host="rekuest",
            id="local_rekuest",
            port=80,
            kind="relative",
            name="Rekuest Service",
            scope="public",
            ssl=False,
        )
        assert alias.host == "rekuest"
        assert alias.kind == "relative"
        assert alias.ssl is False

    def test_service_manifest_creation(self):
        """Test creating a ServiceManifest."""
        manifest = ServiceManifest(
            description="Test service",
            identifier="test.service",
            name="Test Service",
            public_sources=[{"kind": "github", "url": "https://github.com/test"}],
            roles=[{"key": "user", "description": "User role"}],
            scopes=[{"key": "read", "description": "Read access"}],
        )
        assert manifest.identifier == "test.service"
        assert len(manifest.roles) == 1
        assert manifest.version == "1.0.0"

    def test_service_instance_creation(self):
        """Test creating a ServiceInstance."""
        instance = ServiceInstance(
            identifier="rekuest",
            aliases=[
                ServiceAlias(
                    challenge="ht",
                    host="rekuest",
                    id="local_rekuest",
                    port=80,
                    kind="relative",
                    name="Rekuest",
                    scope="public",
                    ssl=False,
                )
            ],
            manifest=ServiceManifest(
                description="Rekuest Service",
                identifier="live.arkitekt.rekuest",
                name="Rekuest",
            ),
        )
        assert instance.identifier == "rekuest"
        assert len(instance.aliases) == 1

    def test_kommunity_partner_preauthorized(self):
        """Test creating a preauthorized KommunityPartner."""
        partner = KommunityPartner(
            identifier="test_partner",
            name="Test Partner",
            website_url="localhost",
            partner_kind="preauthorized",
            auto_configure=True,
            preconfigured_composition=PreconfiguredComposition(
                identifier="localhost",
                instances=[],
            ),
        )
        assert partner.partner_kind == "preauthorized"
        assert partner.auto_configure is True

    def test_kommunity_partner_autoconfigured(self):
        """Test creating an autoconfigured KommunityPartner."""
        partner = KommunityPartner(
            identifier="auto_partner",
            name="Auto Partner",
            website_url="localhost",
            partner_kind="autoconfigured",
            auto_configure=True,
        )
        assert partner.partner_kind == "autoconfigured"


class TestCreateLocalServiceAliases:
    """Tests for the create_local_service_aliases helper function."""

    def test_create_single_service_alias(self):
        """Test creating aliases for a single service."""
        services = [("rekuest", "Rekuest Service", 80, "live.arkitekt.rekuest")]
        instances = create_local_service_aliases(services)

        assert len(instances) == 1
        assert instances[0].identifier == "Rekuest Service"
        assert len(instances[0].aliases) == 1
        assert instances[0].aliases[0].host == "rekuest"
        assert instances[0].aliases[0].kind == "relative"

    def test_create_multiple_service_aliases(self):
        """Test creating aliases for multiple services."""
        services = [
            ("rekuest", "Rekuest Service", 80, "live.arkitekt.rekuest"),
            ("mikro", "Mikro Service", 80, "live.arkitekt.mikro"),
            ("fluss", "Fluss Service", 80, "live.arkitekt.fluss"),
        ]
        instances = create_local_service_aliases(services)

        assert len(instances) == 3
        assert instances[0].manifest.identifier == "live.arkitekt.rekuest"
        assert instances[1].manifest.identifier == "live.arkitekt.mikro"
        assert instances[2].manifest.identifier == "live.arkitekt.fluss"

    def test_service_aliases_have_correct_structure(self):
        """Test that service aliases have the correct structure for lok config."""
        services = [("lok", "Lok Service", 80, "live.arkitekt.lok")]
        instances = create_local_service_aliases(services)

        instance = instances[0]
        alias = instance.aliases[0]

        assert alias.challenge == "ht"
        assert alias.id == "local_lok"
        assert alias.port == 80
        assert alias.scope == "public"
        assert alias.ssl is False


class TestArkitektServerConfigWithKommunityPartners:
    """Tests for ArkitektServerConfig with kommunity_partners field."""

    def test_config_with_kommunity_partners(self):
        """Test creating a config with kommunity partners."""
        config = ArkitektServerConfig(
            kommunity_partners=[
                KommunityPartner(
                    identifier="test",
                    name="Test Partner",
                    partner_kind="preauthorized",
                )
            ]
        )
        assert len(config.kommunity_partners) == 1
        assert config.kommunity_partners[0].identifier == "test"

    def test_config_empty_kommunity_partners(self):
        """Test that kommunity_partners defaults to empty list."""
        config = ArkitektServerConfig()
        assert config.kommunity_partners == []


class TestConfigGeneration:
    """Tests for config file generation with kommunity_partners."""

    def test_lok_config_includes_kommunity_partners(self, tmp_path: Path):
        """Test that generated lok.yaml includes kommunity_partners."""
        config = ArkitektServerConfig(
            organizations=[
                Organization(
                    name="demo",
                    identifier="demo",
                    owner="demo_user",
                    auto_configure=True,
                )
            ],
            users=[
                User(
                    username="demo_user",
                    password="demo",
                )
            ],
            memberships=[
                Membership(user="demo_user", organization="demo", roles=["admin"]),
            ],
            kommunity_partners=[
                KommunityPartner(
                    identifier="local_partner",
                    name="Local Partner",
                    website_url="localhost",
                    partner_kind="preauthorized",
                    auto_configure=True,
                    preconfigured_composition=PreconfiguredComposition(
                        identifier="localhost",
                        instances=create_local_service_aliases(
                            [
                                ("rekuest", "Rekuest", 80, "live.arkitekt.rekuest"),
                            ]
                        ),
                    ),
                ),
            ],
        )

        write_virtual_config_files(tmp_path, config)

        lok_config_path = tmp_path / "configs" / "lok.yaml"
        assert lok_config_path.exists()

        with open(lok_config_path) as f:
            lok_config = yaml.safe_load(f)

        assert "kommunity_partners" in lok_config
        by_id = {p["identifier"]: p for p in lok_config["kommunity_partners"]}
        # The generator always injects a "local_arkitekt" partner alongside any
        # explicitly configured ones.
        assert "local_arkitekt" in by_id
        assert "local_partner" in by_id
        assert by_id["local_partner"]["partner_kind"] == "preauthorized"

    def test_lok_config_includes_memberships(self, tmp_path: Path):
        """Test that generated lok.yaml includes memberships."""
        config = ArkitektServerConfig(
            organizations=[
                Organization(name="org1", identifier="org1"),
                Organization(name="org2", identifier="org2"),
            ],
            users=[
                User(
                    username="user1",
                    password="pass",
                )
            ],
            memberships=[
                Membership(user="user1", organization="org1", roles=["admin"]),
                Membership(user="user1", organization="org2", roles=["user"]),
            ],
        )

        write_virtual_config_files(tmp_path, config)

        lok_config_path = tmp_path / "configs" / "lok.yaml"
        with open(lok_config_path) as f:
            lok_config = yaml.safe_load(f)

        assert "memberships" in lok_config
        # Note: The config generation adds bot users, so we need to account for that
        memberships = [m for m in lok_config["memberships"] if m["user"] == "user1"]
        assert len(memberships) == 2

    def test_lok_config_includes_organization_owner(self, tmp_path: Path):
        """Test that organizations include owner field in config."""
        config = ArkitektServerConfig(
            organizations=[
                Organization(
                    name="owned_org",
                    identifier="owned",
                    owner="owner_user",
                    auto_configure=True,
                )
            ],
            users=[
                User(
                    username="owner_user",
                    password="pass",
                )
            ],
            memberships=[
                Membership(user="owner_user", organization="owned", roles=["admin"]),
            ],
        )

        write_virtual_config_files(tmp_path, config)

        lok_config_path = tmp_path / "configs" / "lok.yaml"
        with open(lok_config_path) as f:
            lok_config = yaml.safe_load(f)

        assert "organizations" in lok_config
        owned_org = next(
            (o for o in lok_config["organizations"] if o["identifier"] == "owned"), None
        )
        assert owned_org is not None
        assert owned_org["owner"] == "owner_user"
        assert owned_org["auto_configure"] is True

    def test_kommunity_partner_preconfigured_composition(self, tmp_path: Path):
        """Test that preconfigured_composition is correctly serialized."""
        services = [
            ("rekuest", "Rekuest Service", 80, "live.arkitekt.rekuest"),
            ("mikro", "Mikro Service", 80, "live.arkitekt.mikro"),
        ]

        config = ArkitektServerConfig(
            kommunity_partners=[
                KommunityPartner(
                    identifier="full_partner",
                    name="Full Partner",
                    partner_kind="autoconfigured",
                    preconfigured_composition=PreconfiguredComposition(
                        identifier="localhost",
                        instances=create_local_service_aliases(services),
                    ),
                ),
            ],
        )

        write_virtual_config_files(tmp_path, config)

        lok_config_path = tmp_path / "configs" / "lok.yaml"
        with open(lok_config_path) as f:
            lok_config = yaml.safe_load(f)

        partner = next(
            p
            for p in lok_config["kommunity_partners"]
            if p["identifier"] == "full_partner"
        )
        assert "preconfigured_composition" in partner
        composition = partner["preconfigured_composition"]
        assert composition["identifier"] == "localhost"
        assert len(composition["instances"]) == 2

        # Check instance structure
        instance = composition["instances"][0]
        assert "aliases" in instance
        assert "manifest" in instance

        alias = instance["aliases"][0]
        assert alias["kind"] == "relative"
        assert alias["scope"] == "public"


class TestWizardHelpers:
    """Tests for wizard helper functions."""

    def test_safe_org_slug(self):
        """Test safe_org_slug function."""
        from arkitekt_server.utils import safe_org_slug

        assert safe_org_slug("test") == "test"
        assert safe_org_slug("Test Org") == "test_org"
        assert safe_org_slug("test-org") == "test_org"
        assert safe_org_slug("TEST_ORG") == "test_org"


class TestConfigWithMultiplePartnerKinds:
    """Tests for configs with both autoconfigured and preauthorized partners."""

    def test_multiple_partner_kinds(self, tmp_path: Path):
        """Test config with both autoconfigured and preauthorized partners."""
        services = [("rekuest", "Rekuest", 80, "live.arkitekt.rekuest")]

        config = ArkitektServerConfig(
            kommunity_partners=[
                KommunityPartner(
                    identifier="auto_partner",
                    name="Auto Partner",
                    partner_kind="autoconfigured",
                    auto_configure=True,
                    preconfigured_composition=PreconfiguredComposition(
                        identifier="localhost",
                        instances=create_local_service_aliases(services),
                    ),
                ),
                KommunityPartner(
                    identifier="preauth_partner",
                    name="Preauth Partner",
                    partner_kind="preauthorized",
                    auto_configure=True,
                    preconfigured_composition=PreconfiguredComposition(
                        identifier="localhost",
                        instances=create_local_service_aliases(services),
                    ),
                ),
            ],
        )

        write_virtual_config_files(tmp_path, config)

        lok_config_path = tmp_path / "configs" / "lok.yaml"
        with open(lok_config_path) as f:
            lok_config = yaml.safe_load(f)

        by_id = {p["identifier"]: p for p in lok_config["kommunity_partners"]}

        assert by_id["auto_partner"]["partner_kind"] == "autoconfigured"
        assert by_id["preauth_partner"]["partner_kind"] == "preauthorized"


class TestEndToEndConfigGeneration:
    """End-to-end tests for complete config generation."""

    def test_complete_config_generation(self, tmp_path: Path):
        """Test complete config generation with all features."""
        config = ArkitektServerConfig(
            global_admin="superadmin",
            global_admin_password="superpass",
            global_admin_email="admin@example.com",
            organizations=[
                Organization(
                    name="Demo Lab",
                    identifier="demo",
                    description="A demo laboratory",
                    owner="demo_admin",
                    auto_configure=True,
                ),
                Organization(
                    name="Research Lab",
                    identifier="research",
                    description="A research laboratory",
                    owner=None,
                    auto_configure=True,
                ),
            ],
            users=[
                User(
                    username="demo_admin",
                    password="demo",
                    email="demo@example.com",
                ),
                User(
                    username="researcher",
                    password="research",
                ),
            ],
            memberships=[
                Membership(user="demo_admin", organization="demo", roles=["admin"]),
                Membership(user="researcher", organization="demo", roles=["user"]),
                Membership(
                    user="researcher", organization="research", roles=["admin", "user"]
                ),
            ],
            kommunity_partners=[
                KommunityPartner(
                    identifier="local_services",
                    name="Local Arkitekt Services",
                    website_url="localhost",
                    partner_kind="autoconfigured",
                    auto_configure=True,
                    preconfigured_composition=PreconfiguredComposition(
                        identifier="localhost",
                        instances=create_local_service_aliases(
                            [
                                ("rekuest", "Rekuest", 80, "live.arkitekt.rekuest"),
                                ("mikro", "Mikro", 80, "live.arkitekt.mikro"),
                                ("fluss", "Fluss", 80, "live.arkitekt.fluss"),
                            ]
                        ),
                    ),
                ),
            ],
        )

        write_virtual_config_files(tmp_path, config)

        # Check all expected files exist
        assert (tmp_path / "docker-compose.yaml").exists()
        assert (tmp_path / "configs" / "lok.yaml").exists()
        assert (tmp_path / "configs" / "rekuest.yaml").exists()
        assert (tmp_path / "configs" / "mikro.yaml").exists()
        assert (tmp_path / "configs" / "fluss.yaml").exists()
        assert (tmp_path / "configs" / "Caddyfile").exists()

        # Check lok.yaml content
        with open(tmp_path / "configs" / "lok.yaml") as f:
            lok_config = yaml.safe_load(f)

        # Verify organizations
        assert (
            len(
                [
                    o
                    for o in lok_config["organizations"]
                    if o["identifier"] in ["demo", "research"]
                ]
            )
            == 2
        )

        # Verify users (including bot users)
        user_names = [u["username"] for u in lok_config["users"]]
        assert "demo_admin" in user_names
        assert "researcher" in user_names

        # Verify kommunity partners (the generator also injects "local_arkitekt")
        by_id = {p["identifier"]: p for p in lok_config["kommunity_partners"]}
        assert "local_services" in by_id
        partner = by_id["local_services"]
        assert len(partner["preconfigured_composition"]["instances"]) == 3

        # Verify memberships
        researcher_memberships = [
            m for m in lok_config["memberships"] if m["user"] == "researcher"
        ]
        assert len(researcher_memberships) == 2
