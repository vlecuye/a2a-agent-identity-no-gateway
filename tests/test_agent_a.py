import unittest

import tests
tests._ensure_mock_modules()

from agent_a.app.agent import root_agent, app
from agent_a.app.remote_agents import remote_agent_b, a2a_httpx_client
from agent_a.app.auth import (
    AdcAuth,
    effective_googleapis_endpoint,
    mtls_context,
)


class TestAgentA(unittest.TestCase):
    def test_agent_and_app_configuration(self):
        self.assertEqual(root_agent.name, "agent_a")
        self.assertEqual(app.name, "agent_a")
        self.assertEqual(len(root_agent.tools), 1)

    def test_remote_a2a_tool(self):
        self.assertEqual(remote_agent_b.name, "agent_b")
        self.assertIn(".well-known/agent-card.json", remote_agent_b.agent_card)

    def test_adc_auth_host_rewriting(self):
        auth = AdcAuth()
        import httpx
        req = httpx.Request("GET", "https://us-central1-aiplatform.googleapis.com/test")
        flow = list(auth.auth_flow(req))
        self.assertEqual(flow[0].url.host, "us-central1-aiplatform.mtls.googleapis.com")

    def test_effective_googleapis_endpoint(self):
        standard_url = "https://us-central1-aiplatform.googleapis.com/v1/projects/123/locations/us-central1/reasoningEngines/456:query"
        mtls_url = effective_googleapis_endpoint(standard_url)
        self.assertIn("us-central1-aiplatform.mtls.googleapis.com", mtls_url)

    def test_mtls_context_callable(self):
        # mtls_context returns SSLContext when certs exist or None in local dev
        ssl_ctx = mtls_context()
        self.assertTrue(ssl_ctx is None or hasattr(ssl_ctx, "load_cert_chain"))


if __name__ == "__main__":
    unittest.main()

