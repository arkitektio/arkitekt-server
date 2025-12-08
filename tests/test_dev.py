from arkitekt_server.dev import temp_deployment


def test_temp_deployment():
    with temp_deployment() as deployment:
        assert deployment.config is not None
        assert deployment.deployment is not None

        # Check if services are present in the deployment spec
        assert deployment.deployment.spec.find_service("gateway") is not None
        assert deployment.deployment.spec.find_service("rekuest") is not None

        # Test helper methods
        gateway_url = deployment.gateway_url
        assert gateway_url.startswith("http://localhost:")

        # Gateway exposes port 80 (internal)
        gateway_url_explicit = deployment.get_service_url("gateway", 80)
        assert gateway_url_explicit == gateway_url
