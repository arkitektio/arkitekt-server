"""End-to-end test of the ``fakts-next`` negotiation flow against a generated server.

This drives a real client through the full device-code grant against a freshly
generated deployment. It is the strongest check that the *generated configuration*
is correct end to end: the auto-configured ``localhost`` composition must expose
working aliases for every requested service (including the ``live.arkitekt.s3``
datalayer), the rendered OAuth endpoints must be reachable, and the issued token
must validate against lok's JWKS -- otherwise the negotiation raises.

The pending device code is approved programmatically by running lok's
``validatecode`` management command inside the running container (the
``device_code_hook``), so no human interaction is required.
"""

import pytest

# Importing the mikro client registers its service builder -- and crucially its
# ``live.arkitekt.s3`` requirement -- in the default service registry that
# ``easy`` negotiates against. Without this import the client would not request
# (and therefore not exercise) the datalayer alias.
import mikro_next.api.schema as mikro

# The seeded demo identity and the composition auto-configured for it (see
# ``build_local_kommunity_partner``).
DEMO_USER = "demo"
DEMO_ORG = "arkitektio"
COMPOSITION = "localhost"


@pytest.mark.integration
def test_fakts_device_code_flow(arkitekt_server):
    """A client can negotiate via the device-code flow and run an authed mutation."""
    from arkitekt_next import easy
    from fakts_next.grants.remote import FaktsEndpoint

    srv = arkitekt_server(services=["rekuest", "mikro"], channel="next")

    with srv.setup:
        srv.setup.pull()
        srv.setup.up()
        srv.setup.check_health()

        async def device_code_hook(endpoint: FaktsEndpoint, device_code: str) -> None:
            # Approve the pending device code for the seeded demo user/org against
            # the auto-configured local composition.
            await srv.setup.arun(
                "lok",
                f"uv run python manage.py validatecode --code {device_code} "
                f"--user {DEMO_USER} --org {DEMO_ORG} --composition {COMPOSITION}",
            )

        with easy(url=srv.gateway_url, device_code_hook=device_code_hook) as app:
            # Reaching this point already proves the generated config is sound:
            # device code -> token -> JWKS validation -> alias resolution all
            # succeeded. A simple authenticated mutation confirms the mikro
            # service alias is usable.
            dataset = mikro.create_dataset(name="Fakts Flow Dataset")
            assert dataset.id, "create_dataset returned no id"
            assert dataset.name == "Fakts Flow Dataset"
