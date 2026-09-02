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

"""Microsoft Entra ID (Azure AD) OAuth token validation with GCP key storage.

Validates incoming Entra ID JWT tokens offline against public JWKS signing keys
loaded dynamically from Google Cloud Storage, Secret Manager, or local storage.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

import jwt
from jwt import PyJWKSet

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "config", "microsoft_entra_jwks.json"
)

# In-memory cached JWKS storage: (jwks_dict, timestamp_fetched)
_CACHED_JWKS: tuple[dict[str, Any], float] | None = None
_CACHE_TTL_SECONDS = int(os.getenv("ENTRA_JWKS_CACHE_TTL_SECONDS", "3600"))


@dataclass
class EntraUserClaims:
    """Parsed claims from a validated Microsoft Entra ID token."""

    subject: str
    groups: list[str] = field(default_factory=list)
    username: str | None = None
    email: str | None = None
    name: str | None = None
    issuer: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


class EntraTokenValidationError(Exception):
    """Raised when an Entra ID token fails signature, expiration, or claims validation."""
    pass


def load_jwks_from_gcs(gcs_uri: str) -> dict[str, Any]:
    """Load JWKS public keys from Google Cloud Storage."""
    from google.cloud import storage

    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI: {gcs_uri}")

    parts = gcs_uri[5:].split("/", 1)
    bucket_name = parts[0]
    blob_name = parts[1] if len(parts) > 1 else "microsoft_entra_jwks.json"

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    content = blob.download_as_text()
    return json.loads(content)


def load_jwks_from_secret_manager(secret_name: str, project_id: str | None = None) -> dict[str, Any]:
    """Load JWKS public keys from Google Cloud Secret Manager."""
    from google.cloud import secretmanager

    project = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise ValueError("GCP project ID is required to read from Secret Manager.")

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    content = response.payload.data.decode("utf-8")
    return json.loads(content)


def load_jwks_from_file(file_path: str) -> dict[str, Any]:
    """Load JWKS public keys from a local JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_entra_jwks(force_refresh: bool = False) -> dict[str, Any]:
    """Retrieve Microsoft Entra ID public JWKS keys from GCP or local file.

    Lookup priority:
    1. In-memory cache (if not expired and not force_refresh).
    2. Google Cloud Storage (`ENTRA_JWKS_GCS_URI` env var).
    3. Google Cloud Secret Manager (`ENTRA_JWKS_SECRET_NAME` env var).
    4. Local file path (`ENTRA_JWKS_FILE_PATH` env var or bundled config).
    """
    global _CACHED_JWKS
    now = time.time()

    if not force_refresh and _CACHED_JWKS is not None:
        cached_data, cached_time = _CACHED_JWKS
        if (now - cached_time) < _CACHE_TTL_SECONDS:
            return cached_data

    # 1. Check GCS URI
    if gcs_uri := os.getenv("ENTRA_JWKS_GCS_URI"):
        try:
            jwks_data = load_jwks_from_gcs(gcs_uri)
            _CACHED_JWKS = (jwks_data, now)
            logger.info("Loaded Entra ID JWKS from GCS: %s", gcs_uri)
            return jwks_data
        except Exception as e:
            logger.warning("Failed to load JWKS from GCS (%s): %s", gcs_uri, e)

    # 2. Check Secret Manager
    if secret_name := os.getenv("ENTRA_JWKS_SECRET_NAME"):
        try:
            jwks_data = load_jwks_from_secret_manager(secret_name)
            _CACHED_JWKS = (jwks_data, now)
            logger.info("Loaded Entra ID JWKS from Secret Manager: %s", secret_name)
            return jwks_data
        except Exception as e:
            logger.warning("Failed to load JWKS from Secret Manager (%s): %s", secret_name, e)

    # 3. Fall back to local file
    file_path = os.getenv("ENTRA_JWKS_FILE_PATH", _DEFAULT_CONFIG_PATH)
    if os.path.exists(file_path):
        jwks_data = load_jwks_from_file(file_path)
        _CACHED_JWKS = (jwks_data, now)
        logger.info("Loaded Entra ID JWKS from local file: %s", file_path)
        return jwks_data

    raise RuntimeError(
        f"Could not load Entra ID public JWKS. No valid source found (checked GCS, Secret Manager, and file '{file_path}')."
    )


def validate_entra_id_token(
    token: str,
    jwks_data: dict[str, Any] | None = None,
    audience: str | list[str] | None = None,
    verify_aud: bool = False,
) -> EntraUserClaims:
    """Validate an Entra ID JWT token offline using Microsoft's public keys.

    Args:
        token: The raw JWT string (e.g. from Authorization: Bearer <token>).
        jwks_data: Optional pre-loaded JWKS dictionary. If None, dynamically fetched.
        audience: Optional expected audience claim (aud).
        verify_aud: Whether to strictly enforce audience verification.

    Returns:
        EntraUserClaims with extracted subject, groups, username, and email.

    Raises:
        EntraTokenValidationError: If validation fails for any reason.
    """
    token_str = token.strip()
    if token_str.lower().startswith("bearer "):
        token_str = token_str[7:].strip()

    if not token_str:
        raise EntraTokenValidationError("Empty OAuth token provided.")

    keys_dict = jwks_data if jwks_data is not None else get_entra_jwks()

    try:
        header = jwt.get_unverified_header(token_str)
    except Exception as e:
        raise EntraTokenValidationError(f"Invalid JWT header: {e}") from e

    kid = header.get("kid")
    if not kid:
        raise EntraTokenValidationError("JWT header is missing required 'kid' (key ID).")

    try:
        jwk_set = PyJWKSet.from_dict(keys_dict)
        signing_key = jwk_set[kid]
    except KeyError:
        # Try a force refresh once in case a new signing key was added
        if jwks_data is None:
            keys_dict = get_entra_jwks(force_refresh=True)
            jwk_set = PyJWKSet.from_dict(keys_dict)
            if kid not in jwk_set:
                raise EntraTokenValidationError(
                    f"Signing key ID '{kid}' not found in Microsoft JWKS."
                )
            signing_key = jwk_set[kid]
        else:
            raise EntraTokenValidationError(
                f"Signing key ID '{kid}' not found in provided JWKS."
            )
    except Exception as e:
        raise EntraTokenValidationError(f"Failed to resolve signing key: {e}") from e

    decode_options = {
        "verify_signature": True,
        "verify_exp": True,
        "verify_aud": verify_aud,
    }

    try:
        payload = jwt.decode(
            token_str,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            options=decode_options,
        )
    except jwt.ExpiredSignatureError as e:
        raise EntraTokenValidationError(f"Entra ID token has expired: {e}") from e
    except jwt.InvalidSignatureError as e:
        raise EntraTokenValidationError(f"Invalid Entra ID token signature: {e}") from e
    except jwt.InvalidTokenError as e:
        raise EntraTokenValidationError(f"Invalid Entra ID token: {e}") from e

    # Extract groups (can be in 'groups', 'roles', or 'wids')
    raw_groups = payload.get("groups") or payload.get("roles") or []
    if isinstance(raw_groups, str):
        groups = [raw_groups]
    elif isinstance(raw_groups, list):
        groups = [str(g) for g in raw_groups]
    else:
        groups = []

    return EntraUserClaims(
        subject=payload.get("sub", ""),
        groups=groups,
        username=payload.get("preferred_username") or payload.get("upn"),
        email=payload.get("email") or payload.get("preferred_username"),
        name=payload.get("name"),
        issuer=payload.get("iss"),
        raw_payload=payload,
    )
