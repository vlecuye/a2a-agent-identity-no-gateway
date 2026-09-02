"""Agent B: Computational Specialist Agent.

Executes arithmetic expressions and formulas via the calculate_formula tool.
"""

from google.adk.agents import Agent
from google.adk.apps import App

from .models import GlobalGemini
from .tools import calculate_formula

# Specialist agent definition
root_agent = Agent(
    name="agent_b",
    model=GlobalGemini(model="gemini-3.7-flash"),
    instruction=(
        "You are Agent B, a specialized computational assistant. "
        "Your role is to solve math and calculation queries accurately using the "
        "calculate_formula tool. Always use the calculate_formula tool for calculations."
    ),
    tools=[calculate_formula],
)

# Application entrypoint for ADK / Agent Runtime
app = App(name="agent_b", root_agent=root_agent)

__all__ = [
    "GlobalGemini",
    "app",
    "calculate_formula",
    "root_agent",
]
