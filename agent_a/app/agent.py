"""Agent A: Root Coordinator Agent.

Coordinates multi-agent workflows and delegates mathematical calculations to Agent B
over the A2A protocol using Agent Identity.
"""

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.tools.agent_tool import AgentTool

from .auth import (
    AdcAuth,
    GCPAuth,
    effective_googleapis_endpoint,
    mtls_context,
)
from .models import GlobalGemini
from .remote_agents import (
    a2a_httpx_client,
    create_remote_a2a_agent,
    remote_agent_b,
)

# Coordinator root agent definition
root_agent = Agent(
    name="agent_a",
    model=GlobalGemini(model="gemini-3.7-flash"),
    instruction=(
        "You are Agent A, a coordinator agent. When the user asks for math calculations, "
        "evaluations, or data formulas, you must delegate the work to Agent B using the agent_b tool. "
        "Summarize the result clearly and explain what Agent B computed."
    ),
    tools=[AgentTool(agent=remote_agent_b)],
)

# Application entrypoint for ADK / Agent Runtime
app = App(name="agent_a", root_agent=root_agent)

__all__ = [
    "AdcAuth",
    "GCPAuth",
    "GlobalGemini",
    "a2a_httpx_client",
    "app",
    "create_remote_a2a_agent",
    "effective_googleapis_endpoint",
    "mtls_context",
    "remote_agent_b",
    "root_agent",
]
