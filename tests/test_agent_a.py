import asyncio
import base64
import json
import unittest
from unittest.mock import MagicMock

import tests
tests._ensure_mock_modules()

from agent_a.app.agent import root_agent, app
from agent_a.app.remote_agents import remote_agent_b, entra_id_request_interceptor
from agent_a.app.auth import (
    AdcAuth,
    decode_jwt_payload,
    get_user_group_ids_from_token,
    extract_token_from_context,
    is_agent_authorized_for_user,
    effective_googleapis_endpoint,
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

    def test_jwt_decode_and_group_extraction(self):
        payload = {
            "sub": "user-guid-12345",
            "groups": ["group-alpha", "group-beta"],
            "roles": ["Admin"],
        }
        b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        mock_jwt = f"eyJhbGciOiJSUzI1NiJ9.{b64}.signature"

        decoded = decode_jwt_payload(mock_jwt)
        self.assertEqual(decoded.get("sub"), "user-guid-12345")

        groups = get_user_group_ids_from_token(mock_jwt)
        self.assertIn("group-alpha", groups)
        self.assertIn("group-beta", groups)
        self.assertIn("Admin", groups)

    def test_extract_token_from_context(self):
        # 1. Dict context
        self.assertEqual(
            extract_token_from_context({"microsoft-entra-id": "token-123"}),
            "token-123"
        )
        self.assertEqual(
            extract_token_from_context({"authorization": "Bearer token-456"}),
            "token-456"
        )

        # 2. ToolContext / InvocationContext mock
        ctx = MagicMock()
        ctx.state = {"microsoft_entra_id": "token-789"}
        self.assertEqual(extract_token_from_context(ctx), "token-789")

    def test_is_agent_authorized_for_user(self):
        agent_card = {
            "name": "secure_agent",
            "capabilities": {
                "extensions": {
                    "security": {
                        "type": "microsoft_entra_id",
                        "required_group_ids": ["group-alpha"],
                    }
                }
            }
        }
        
        # Valid token with matching group
        payload = {"groups": ["group-alpha", "other-group"]}
        b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        authorized_jwt = f"header.{b64}.sig"
        self.assertTrue(is_agent_authorized_for_user(agent_card, authorized_jwt))

        # Token with non-matching group
        payload_denied = {"groups": ["unrelated-group"]}
        b64_denied = base64.urlsafe_b64encode(json.dumps(payload_denied).encode()).decode().rstrip("=")
        denied_jwt = f"header.{b64_denied}.sig"
        self.assertFalse(is_agent_authorized_for_user(agent_card, denied_jwt))

        # No token
        self.assertFalse(is_agent_authorized_for_user(agent_card, None))

    def test_entra_id_request_interceptor(self):
        ctx = MagicMock()
        ctx.state = {"microsoft-entra-id": "mock-token-xyz"}
        message = MagicMock()
        params = None

        msg_out, params_out = asyncio.run(entra_id_request_interceptor(ctx, message, params))
        self.assertEqual(params_out.client_call_context.state.get("microsoft-entra-id"), "mock-token-xyz")
        self.assertEqual(params_out.request_metadata.get("microsoft-entra-id"), "mock-token-xyz")


if __name__ == "__main__":
    unittest.main()
