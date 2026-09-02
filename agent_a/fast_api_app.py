"""FastAPI application for Agent A (ADK Coordinator Agent)."""

from google.adk.cli.fast_api import get_fast_api_app
from agent_a.agent import app as agent_app

# Build the base FastAPI application for the ADK agent
app = get_fast_api_app(agent_app=agent_app, web=True, a2a=False)
