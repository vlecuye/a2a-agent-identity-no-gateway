"""Authentication and mTLS security helpers for Agent Identity and A2A.

Provides:
- `mtls_context`: Extracts SPIFFE client certificates for mutual TLS.
- `AdcAuth` / `GCPAuth`: Injects Application Default Credentials (ADC) tokens
  and automatically routes requests to mTLS endpoints (*.mtls.googleapis.com).
- `effective_googleapis_endpoint`: Rewrites standard Google APIs endpoints to mTLS.
"""

import logging
import ssl
from typing import Generator

import google.auth
from google.auth.transport.requests import Request as GoogleAuthRequest
import httpx
from google.adk.utils._mtls_utils import (
    MtlsClientCerts,
    use_client_cert_effective,
)

logger = logging.getLogger(__name__)

_CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


def effective_googleapis_endpoint(raw_url: str) -> str:
    """Transforms a standard googleapis.com URL into an mTLS endpoint if applicable."""
    if "-aiplatform.googleapis.com" in raw_url:
        return raw_url.replace("-aiplatform.googleapis.com", "-aiplatform.mtls.googleapis.com")
    return raw_url


def mtls_context() -> ssl.SSLContext | None:
    """Creates an SSLContext presenting this agent's Agent Identity certificate.

    When Agent Identity is enabled on Agent Runtime, SPIFFE workload credentials
    are mounted into `/var/run/secrets/google/`. Frontends require mTLS to validate
    certificate-bound access tokens.
    """
    if not use_client_cert_effective():
        logger.info("No client certificate in this environment; using bearer auth only.")
        return None

    try:
        certs = MtlsClientCerts()
        cert_path, key_path, passphrase = certs.get_certs()
        if not (cert_path and key_path):
            logger.warning(
                "mTLS is indicated but no client certificate could be extracted; "
                "a certificate-bound token will be rejected by the ingress."
            )
            return None

        context = ssl.create_default_context()
        context.load_cert_chain(cert_path, key_path, passphrase)
        certs.close()

        logger.info("Presenting Agent Identity client certificate on outbound calls.")
        return context
    except Exception as e:
        logger.warning(
            "mTLS certificate extraction failed (%s); falling back to standard TLS.", e
        )
        return None


class AdcAuth(httpx.Auth):
    """Attach an Application Default Credentials bearer token to each request."""

    def __init__(self) -> None:
        self._credentials, _ = google.auth.default(scopes=[_CLOUD_PLATFORM_SCOPE])

    def token(self) -> str:
        if not self._credentials.valid:
            self._credentials.refresh(GoogleAuthRequest())
        return str(self._credentials.token)

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        # Automatically rewrite standard AI Platform host to mTLS host
        if "-aiplatform.googleapis.com" in request.url.host:
            new_host = request.url.host.replace(
                "-aiplatform.googleapis.com", "-aiplatform.mtls.googleapis.com"
            )
            request.url = request.url.copy_with(host=new_host)

        request.headers["Authorization"] = f"Bearer {self.token()}"
        yield request


# GCPAuth alias for backwards compatibility and clarity
GCPAuth = AdcAuth

