import logging
import os
from typing import Any
import httpx

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

from .auth import (
    AdcAuth,
    mtls_context,
)

logger = logging.getLogger(__name__)

# Default URL pointing to Agent B's Reasoning Engine on Agent Runtime (us-central1)
DEFAULT_AGENT_B_A2A_URL = (
    "https://us-central1-aiplatform.mtls.googleapis.com/reasoningEngines/v1"
    "/projects/816122473048/locations/us-central1/reasoningEngines/5622908511760416768"
    "/api/a2a/agent_b/.well-known/agent-card.json"
)

AGENT_B_A2A_URL = os.environ.get("AGENT_B_A2A_URL", DEFAULT_AGENT_B_A2A_URL)

# Authenticated HTTP client presenting ADC token and mTLS client certificates
tls = mtls_context()
a2a_httpx_client = httpx.AsyncClient(
    auth=AdcAuth(),
    verify=tls if tls else True,
    timeout=120.0,
)

# Remote A2A wrapper for Agent B
remote_agent_b = RemoteA2aAgent(
    name="agent_b",
    agent_card=AGENT_B_A2A_URL,
    description=(
        "Specialist calculation agent that performs accurate arithmetic calculations "
        "and formula evaluations via A2A protocol."
    ),
    httpx_client=a2a_httpx_client,
)


def create_remote_a2a_agent(
    name: str,
    agent_card_url: str,
    description: str = "",
    agent_card_dict: dict[str, Any] | None = None,
) -> RemoteA2aAgent:
    """Factory helper to create a RemoteA2aAgent with mTLS and Agent Identity authentication."""
    return RemoteA2aAgent(
        name=name,
        agent_card=agent_card_url,
        description=description,
        httpx_client=a2a_httpx_client,
    )

