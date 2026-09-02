"""Model configuration for Agent A.

Forces the Vertex AI client to use enterprise mode in the global region.
"""

from functools import cached_property
from google.adk.models import Gemini
from google.genai import Client


class GlobalGemini(Gemini):
    """Subclass of Gemini model forcing the Vertex AI API client to the global region."""

    @cached_property
    def api_client(self) -> Client:
        return Client(enterprise=True, location="global")
