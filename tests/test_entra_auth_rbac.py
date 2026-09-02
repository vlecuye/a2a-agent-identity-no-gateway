# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for Microsoft Entra ID token validation and dynamic A2A RBAC binding."""

import json
import time
import unittest
from unittest.mock import MagicMock, patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from agent_a.app.agent import (
    SUBAGENT_REGISTRY,
    authorize_and_bind_subagents,
    remote_agent_b,
    root_agent,
)
from agent_a.app.auth_entra import (
    EntraTokenValidationError,
    get_entra_jwks,
    load_jwks_from_file,
    load_jwks_from_gcs,
    load_jwks_from_secret_manager,
    validate_entra_id_token,
)
from agent_b.app.app_utils.a2a import (
    ACCESS_CONTROL_EXTENSION_URI,
    _default_capabilities,
)


class TestEntraAuthAndRBAC(unittest.IsolatedAsyncioTestCase):
    """Test suite for Entra ID JWT verification and dynamic subagent authorization."""

    @classmethod
    def setUpClass(cls):
        # Generate an RSA keypair for testing tokens
        cls.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        cls.public_key = cls.private_key.public_key()
        cls.kid = "test-entra-key-1"

        jwk_json = jwt.algorithms.RSAAlgorithm.to_jwk(cls.public_key)
        jwk_dict = json.loads(jwk_json)
        jwk_dict["kid"] = cls.kid
        cls.test_jwks = {"keys": [jwk_dict]}

    def _mint_token(self, payload: dict, kid: str | None = None, private_key=None) -> str:
        key = private_key or self.private_key
        headers = {"kid": kid or self.kid}
        return jwt.encode(payload, key, algorithm="RS256", headers=headers)

    def test_validate_valid_entra_token(self):
        payload = {
            "sub": "user-guid-12345",
            "preferred_username": "alice@contoso.com",
            "name": "Alice Developer",
            "groups": ["math-users", "dev-team"],
            "iss": "https://login.microsoftonline.com/tenant-123/v2.0",
            "aud": "api://gemini-enterprise-agent",
            "exp": int(time.time()) + 3600,
        }
        token = self._mint_token(payload)

        claims = validate_entra_id_token(token, jwks_data=self.test_jwks)
        self.assertEqual(claims.subject, "user-guid-12345")
        self.assertEqual(claims.username, "alice@contoso.com")
        self.assertIn("math-users", claims.groups)
        self.assertIn("dev-team", claims.groups)

    def test_validate_bearer_prefix_handling(self):
        payload = {
            "sub": "user-bearer",
            "groups": ["math-users"],
            "exp": int(time.time()) + 3600,
        }
        token = "Bearer " + self._mint_token(payload)

        claims = validate_entra_id_token(token, jwks_data=self.test_jwks)
        self.assertEqual(claims.subject, "user-bearer")
        self.assertEqual(claims.groups, ["math-users"])

    def test_validate_expired_token(self):
        payload = {
            "sub": "user-expired",
            "groups": ["math-users"],
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
        }
        token = self._mint_token(payload)

        with self.assertRaises(EntraTokenValidationError) as ctx:
            validate_entra_id_token(token, jwks_data=self.test_jwks)
        self.assertIn("expired", str(ctx.exception).lower())

    def test_validate_invalid_signature(self):
        # Mint token with a different private key
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        payload = {
            "sub": "attacker",
            "groups": ["admin", "math-users"],
            "exp": int(time.time()) + 3600,
        }
        forged_token = self._mint_token(payload, private_key=other_key)

        with self.assertRaises(EntraTokenValidationError) as ctx:
            validate_entra_id_token(forged_token, jwks_data=self.test_jwks)
        self.assertIn("signature", str(ctx.exception).lower())

    def test_validate_missing_kid(self):
        token = jwt.encode(
            {"sub": "no-kid", "exp": int(time.time()) + 3600},
            self.private_key,
            algorithm="RS256",
        )
        with self.assertRaises(EntraTokenValidationError) as ctx:
            validate_entra_id_token(token, jwks_data=self.test_jwks)
        self.assertIn("missing required 'kid'", str(ctx.exception).lower())

    @patch("google.cloud.storage.Client")
    def test_load_jwks_from_gcs(self, mock_storage_client):
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.download_as_text.return_value = json.dumps(self.test_jwks)
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        data = load_jwks_from_gcs("gs://test-bucket/config/microsoft_entra_jwks.json")
        self.assertEqual(data, self.test_jwks)

    @patch("google.cloud.secretmanager.SecretManagerServiceClient")
    def test_load_jwks_from_secret_manager(self, mock_sm_client):
        mock_response = MagicMock()
        mock_response.payload.data = json.dumps(self.test_jwks).encode("utf-8")
        mock_sm_client.return_value.access_secret_version.return_value = mock_response

        data = load_jwks_from_secret_manager("test-secret", project_id="all-in-demo")
        self.assertEqual(data, self.test_jwks)

    async def test_dynamic_binding_authorized_user(self):
        payload = {
            "sub": "authorized-user",
            "preferred_username": "bob@contoso.com",
            "groups": ["math-users"],
            "exp": int(time.time()) + 3600,
        }
        token = self._mint_token(payload)

        # Mock CallbackContext
        class MockCallbackContext:
            def __init__(self):
                self.state = {"oauth_token": token}

        ctx = MockCallbackContext()
        with patch("agent_a.app.agent.validate_entra_id_token") as mock_val:
            from agent_a.app.auth_entra import EntraUserClaims

            mock_val.return_value = EntraUserClaims(
                subject="authorized-user",
                groups=["math-users"],
                username="bob@contoso.com",
            )
            await authorize_and_bind_subagents(ctx)

        self.assertEqual(ctx.state["auth_status"], "authenticated")
        self.assertEqual(ctx.state["user_groups"], ["math-users"])
        self.assertEqual(len(root_agent.sub_agents), 1)
        self.assertEqual(root_agent.sub_agents[0].name, "agent_b")

    async def test_dynamic_binding_unauthorized_user(self):
        payload = {
            "sub": "unauthorized-user",
            "preferred_username": "charlie@contoso.com",
            "groups": ["hr-only-group"],
            "exp": int(time.time()) + 3600,
        }
        token = self._mint_token(payload)

        class MockCallbackContext:
            def __init__(self):
                self.state = {"oauth_token": token}

        ctx = MockCallbackContext()
        with patch("agent_a.app.agent.validate_entra_id_token") as mock_val:
            from agent_a.app.auth_entra import EntraUserClaims

            mock_val.return_value = EntraUserClaims(
                subject="unauthorized-user",
                groups=["hr-only-group"],
                username="charlie@contoso.com",
            )
            await authorize_and_bind_subagents(ctx)

        self.assertEqual(ctx.state["auth_status"], "authenticated")
        self.assertEqual(ctx.state["user_groups"], ["hr-only-group"])
        self.assertEqual(len(root_agent.sub_agents), 0)

    async def test_dynamic_binding_unauthenticated(self):
        class MockCallbackContext:
            def __init__(self):
                self.state = {}

        ctx = MockCallbackContext()
        await authorize_and_bind_subagents(ctx)

        self.assertEqual(ctx.state["auth_status"], "unauthenticated")
        self.assertEqual(len(root_agent.sub_agents), 0)

    def test_agent_b_a2a_capability_extension(self):
        caps = _default_capabilities()
        self.assertTrue(caps.streaming)
        ext_uris = [e.uri for e in caps.extensions]
        self.assertIn(ACCESS_CONTROL_EXTENSION_URI, ext_uris)

    def test_extract_token_from_state_variations(self):
        from agent_a.app.agent import extract_token_from_state

        dummy_jwt = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMifQ.signature"

        # Auth ID specific key
        self.assertEqual(
            extract_token_from_state({"user:entra_oauth_auth": dummy_jwt}),
            dummy_jwt,
        )
        self.assertEqual(
            extract_token_from_state({"entra_oauth_auth": dummy_jwt}),
            dummy_jwt,
        )
        self.assertEqual(
            extract_token_from_state({"user:entra-oauth-auth": dummy_jwt}),
            dummy_jwt,
        )
        # Nested auth dict
        self.assertEqual(
            extract_token_from_state({"authorizations": {"entra_oauth_auth": {"token": dummy_jwt}}}),
            dummy_jwt,
        )
        # Dynamic JWT pattern fallback
        self.assertEqual(
            extract_token_from_state({"some_custom_gemini_key": dummy_jwt}),
            dummy_jwt,
        )
        # Empty state
        self.assertIsNone(extract_token_from_state({}))


if __name__ == "__main__":
    unittest.main()
