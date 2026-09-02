"""FastAPI application for Agent A.

Exposes ADK endpoints, Agent-to-Agent (A2A) protocol endpoints,
and Reasoning Engine contract routes for Agent Runtime.
"""

from google.adk.cli.fast_api import get_fast_api_app
from google.adk.a2a.fast_api import attach_a2a_routes
from agent_a.agent import app as agent_app

# Build the base FastAPI application for the ADK agent
app = get_fast_api_app(agent_app=agent_app, web=True)

# Attach A2A routes (/a2a/agent_a/.well-known/agent-card.json and JSON-RPC message handlers)
try:
    attach_a2a_routes(app, agent_app=agent_app)
except Exception:
    pass
