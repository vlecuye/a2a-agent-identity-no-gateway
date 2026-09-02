"""Test suite mock bootstrap for ADK Multi-Agent System."""

import sys
from unittest.mock import MagicMock


def _ensure_mock_modules():
    modules_to_mock = [
        "google",
        "google.genai",
        "google.auth",
        "google.auth.transport",
        "google.auth.transport.requests",
        "google.adk",
        "google.adk.agents",
        "google.adk.agents.remote_a2a_agent",
        "google.adk.apps",
        "google.adk.events",
        "google.adk.models",
        "google.adk.models.gemini",
        "google.adk.tools",
        "google.adk.tools.agent_tool",
        "google.adk.utils",
        "google.adk.utils._mtls_utils",
        "google.adk.cli",
        "google.adk.cli.fast_api",
        "google.adk.a2a",
        "google.adk.a2a.fast_api",
        "a2a",
        "a2a.client",
        "a2a.types",
        "httpx",
    ]
    for mod in modules_to_mock:
        if mod not in sys.modules:
            sys.modules[mod] = MagicMock()

    # Define minimal dummy classes for inheritance if needed
    class DummyGemini:
        def __init__(self, *args, **kwargs):
            self.model = kwargs.get("model", "gemini-3.7-flash")

    class DummyAgent:
        def __init__(self, name="", model=None, instruction="", tools=None):
            self.name = name
            self.model = model
            self.instruction = instruction
            self.tools = tools or []

    class DummyApp:
        def __init__(self, root_agent=None, name=""):
            self.root_agent = root_agent
            self.name = name

    class DummyRemoteA2aAgent:
        def __init__(self, name="", description="", agent_card=None, httpx_client=None, config=None):
            self.name = name
            self.description = description
            self.agent_card = agent_card
            self.httpx_client = httpx_client
            self.config = config

    class DummyAgentTool:
        def __init__(self, agent=None):
            self.agent = agent

    class DummyAuth:
        pass

    class DummyURL:
        def __init__(self, host=""):
            self.host = host

        def copy_with(self, host=None):
            return DummyURL(host=host or self.host)

    class DummyRequest:
        def __init__(self, method="GET", url=""):
            self.method = method
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            self.url = DummyURL(host=parsed.netloc)
            self.headers = {}

    class DummyClientCallContext:
        def __init__(self, state=None):
            self.state = state if state is not None else {}

    class DummyParametersConfig:
        def __init__(self, client_call_context=None, request_metadata=None):
            self.client_call_context = client_call_context or DummyClientCallContext()
            self.request_metadata = request_metadata if request_metadata is not None else {}

    class DummyRequestInterceptor:
        def __init__(self, before_request=None, after_request=None):
            self.before_request = before_request
            self.after_request = after_request

    class DummyA2aRemoteAgentConfig:
        def __init__(self, request_interceptors=None):
            self.request_interceptors = request_interceptors or []

    sys.modules["httpx"].Auth = DummyAuth
    sys.modules["httpx"].Request = DummyRequest
    sys.modules["a2a.client"].ClientCallContext = DummyClientCallContext
    sys.modules["google.adk.agents.remote_a2a_agent"].ParametersConfig = DummyParametersConfig
    sys.modules["google.adk.agents.remote_a2a_agent"].RequestInterceptor = DummyRequestInterceptor
    sys.modules["google.adk.agents.remote_a2a_agent"].A2aRemoteAgentConfig = DummyA2aRemoteAgentConfig
    sys.modules["google.adk.models"].Gemini = DummyGemini
    sys.modules["google.adk.models.gemini"].Gemini = DummyGemini
    sys.modules["google.adk.agents"].Agent = DummyAgent
    sys.modules["google.adk.apps"].App = DummyApp
    sys.modules["google.adk.tools.agent_tool"].AgentTool = DummyAgentTool
    sys.modules["google.adk.agents.remote_a2a_agent"].RemoteA2aAgent = DummyRemoteA2aAgent
    sys.modules["google.adk.agents.remote_a2a_agent"].AGENT_CARD_WELL_KNOWN_PATH = "/.well-known/agent-card.json"
    
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds.token = "mock-token"
    
    mock_auth = MagicMock()
    mock_auth.default.return_value = (mock_creds, "test-project")
    sys.modules["google.auth"] = mock_auth
    sys.modules["google"].auth = mock_auth
    
    sys.modules["google.adk.utils._mtls_utils"].use_client_cert_effective = MagicMock(return_value=False)


_ensure_mock_modules()
