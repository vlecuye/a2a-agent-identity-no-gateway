"""Agent A: Root Coordinator Agent.

Coordinates multi-agent workflows and delegates mathematical calculations to Agent B
over the A2A protocol using Agent Identity and Entra ID RBAC authorization.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence

from google.adk.agents import Agent, BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App

from .auth import (
    AdcAuth,
    GCPAuth,
    effective_googleapis_endpoint,
    mtls_context,
)
from .auth_entra import (
    EntraTokenValidationError,
    validate_entra_id_token,
)
from .models import GlobalGemini
from .remote_agents import (
    a2a_httpx_client,
    create_remote_a2a_agent,
    remote_agent_b,
)

logger = logging.getLogger(__name__)


@dataclass
class SubAgentRegistration:
    """Registry entry mapping an A2A sub-agent to required Entra ID security groups."""

    agent: BaseAgent
    required_groups: Sequence[str] = ()
    description: str = ""


# Sub-agent registry defining required security groups (matching A2A capability extensions)
SUBAGENT_REGISTRY: list[SubAgentRegistration] = [
    SubAgentRegistration(
        agent=remote_agent_b,
        required_groups=["math-users", "admin"],
        description="Mathematical calculation specialist agent",
    ),
]


def extract_token_from_state(state: Any) -> str | None:
    """Extract Entra ID OAuth token from ADK / Gemini Enterprise session state."""
    if state is None:
        return None
    state_dict = state.to_dict() if hasattr(state, "to_dict") else (dict(state) if isinstance(state, dict) else {})

    # 1. Exact candidate keys (matching auth ID 'entra_oauth_auth' / 'entra_oauth_auth_v2' and common conventions)
    candidate_keys = (
        "user:entra_oauth_auth_v2",
        "entra_oauth_auth_v2",
        "user:entra_oauth_auth",
        "entra_oauth_auth",
        "user:entra-oauth-auth",
        "entra-oauth-auth",
        "user:entra_oauth_auth:token",
        "user:entra_oauth_auth:access_token",
        "oauth_token",
        "user:oauth_token",
        "user:access_token",
        "access_token",
        "user:entra_id_token",
        "bearer_token",
    )
    for key in candidate_keys:
        val = state_dict.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()

    # 2. Check nested authorizations structure if present
    auths = state_dict.get("authorizations")
    if isinstance(auths, dict):
        for sub_key in ("entra_oauth_auth", "entra-oauth-auth", "default"):
            sub_val = auths.get(sub_key)
            if isinstance(sub_val, str) and sub_val.strip():
                return sub_val.strip()
            if isinstance(sub_val, dict):
                for k in ("token", "access_token", "oauth_token"):
                    if isinstance(sub_val.get(k), str) and sub_val[k].strip():
                        return sub_val[k].strip()

    # 3. Dynamic scan for any user:* key or JWT-shaped string
    for k, v in state_dict.items():
        if isinstance(v, str):
            v_stripped = v.strip()
            if (k.startswith("user:") or "token" in k or "auth" in k) and v_stripped:
                if v_stripped.startswith("ey") and v_stripped.count(".") == 2:
                    return v_stripped
            elif v_stripped.startswith("ey") and v_stripped.count(".") == 2:
                return v_stripped

    return None


async def authorize_and_bind_subagents(callback_context: CallbackContext) -> None:
    """ADK before_agent_callback: validates Entra ID OAuth token and dynamically binds authorized sub-agents.

    Extracts the token from session state, validates it offline against public keys
    loaded from GCP (GCS/Secret Manager/local fallback), and dynamically assigns only
    the authorized sub-agents to root_agent.sub_agents for this turn.
    """
    state = callback_context.state
    token = extract_token_from_state(state)

    user_groups: list[str] = []
    if token:
        try:
            claims = validate_entra_id_token(token)
            user_groups = claims.groups
            state["user_groups"] = user_groups
            state["user_email"] = claims.email
            state["auth_status"] = "authenticated"
            logger.info("Authenticated Entra user: %s with groups: %s", claims.email, user_groups)
        except EntraTokenValidationError as e:
            state["user_groups"] = []
            state["auth_status"] = f"invalid_token: {e}"
            logger.warning("Entra ID token validation failed: %s", e)
    else:
        # No token provided
        state["user_groups"] = []
        state["auth_status"] = "unauthenticated"

    # Dynamically filter candidate sub-agents
    authorized_agents = [
        reg.agent
        for reg in SUBAGENT_REGISTRY
        if not reg.required_groups or any(g in user_groups for g in reg.required_groups)
    ]
    root_agent.sub_agents = authorized_agents


# Coordinator root agent definition with dynamic RBAC callback
root_agent = Agent(
    name="agent_a",
    model=GlobalGemini(model="gemini-3.7-flash"),
    instruction=(
        "You are Agent A, a helpful coordinator agent. When the user asks for math calculations, "
        "evaluations, or data formulas, check if you have access to agent_b. "
        "If agent_b is available in your sub-agents, delegate the work to agent_b and summarize the result. "
        "If agent_b is NOT available (or if authorization is missing), politely inform the user "
        "that they do not have authorization to access calculation services (required group: math-users) "
        "and advise them to contact their administrator."
    ),
    before_agent_callback=authorize_and_bind_subagents,
    sub_agents=[reg.agent for reg in SUBAGENT_REGISTRY],
)

# Application entrypoint for ADK / Agent Runtime
app = App(name="agent_a", root_agent=root_agent)

__all__ = [
    "SUBAGENT_REGISTRY",
    "AdcAuth",
    "GCPAuth",
    "GlobalGemini",
    "SubAgentRegistration",
    "a2a_httpx_client",
    "app",
    "authorize_and_bind_subagents",
    "create_remote_a2a_agent",
    "effective_googleapis_endpoint",
    "mtls_context",
    "remote_agent_b",
    "root_agent",
]
