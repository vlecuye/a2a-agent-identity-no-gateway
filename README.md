# ADK Multi-Agent System with A2A, Agent Identity, and Agent Registry

This project implements a multi-agent system built using the **Google Agent Development Kit (ADK)**. Both agents are exposed as **Agent-to-Agent (A2A)** services, deployed to **Agent Runtime** (Vertex AI Reasoning Engine), cataloged in **Google Cloud Agent Registry**, and secured using **Agent Identity** (SPIFFE-based workload identity).

## Architecture

- **Agent A (`agent_a`)**: Coordinator agent. Receives user requests and delegates calculation tasks to Agent B via the A2A protocol (`RemoteA2aAgent`). Uses `gemini-3.7-flash` with the `global` region explicitly forced via `GlobalGemini`.
- **Agent B (`agent_b`)**: Specialist calculation agent. Evaluates arithmetic expressions and returns structured results. Also uses `gemini-3.7-flash` with the `global` region forced.
- **Agent Identity**: Both agents configure `.agent_engine_config.json` with `identity_type: AGENT_IDENTITY`. Google Cloud assigns a secure SPIFFE ID to each agent at deployment.
- **IAM Authorization**: Agent A's SPIFFE principal is granted `roles/aiplatform.user` to authorize requests made to Agent B's Reasoning Engine `/api` HTTP passthrough endpoint.
- **Agent Registry**: Both agents are registered as `a2a-agent-card` services in Agent Registry.

---

## Directory Structure

```
.
├── .agents-cli-spec.md               # Full specification document
├── README.md                         # Project documentation and deployment guide
├── scripts/
│   ├── deploy_agent_b.sh             # Deploy Agent B to Agent Runtime
│   ├── deploy_agent_a.sh             # Deploy Agent A with Agent B's A2A URL
│   ├── setup_iam.sh                  # Grant IAM permissions to Agent A's SPIFFE principal
│   └── register_agent_registry.sh    # Register both agents in Agent Registry
├── agent_b/                          # Specialist Agent (Calculator)
│   ├── .agent_engine_config.json     # Agent Identity config ({ "identity_type": "AGENT_IDENTITY" })
│   ├── agent.py                      # Specialist logic & GlobalGemini(model="gemini-3.7-flash")
│   ├── fast_api_app.py               # FastAPI app mounting A2A routes
│   ├── agent_card.json               # A2A Agent Card specification
│   ├── requirements.txt              # Dependencies
│   └── pyproject.toml                # Package configuration
├── agent_a/                          # Coordinator Agent
│   ├── .agent_engine_config.json     # Agent Identity config ({ "identity_type": "AGENT_IDENTITY" })
│   ├── agent.py                      # Coordinator logic, RemoteA2aAgent & GlobalGemini
│   ├── fast_api_app.py               # FastAPI app mounting A2A routes
│   ├── agent_card.json               # A2A Agent Card specification
│   ├── requirements.txt              # Dependencies
│   └── pyproject.toml                # Package configuration
└── tests/                            # Unit and integration tests
    ├── __init__.py
    ├── test_agent_a.py
    ├── test_agent_b.py
    ├── test_global_gemini.py
    └── test_agent_cards_and_configs.py
```

---

## Global Region Forcing Pattern

In both `agent_a/agent.py` and `agent_b/agent.py`, `GlobalGemini` overrides `api_client` to force `location="global"`:

```python
from functools import cached_property
from google.genai import Client
from google.adk.models.gemini import Gemini

class GlobalGemini(Gemini):
    @cached_property
    def api_client(self) -> Client:
        return Client(enterprise=True, location="global")

root_agent = Agent(
    name="...",
    model=GlobalGemini(model="gemini-3.7-flash"),
    ...
)
```

---

## Deployment & Setup Guide

### 1. Prerequisites & APIs
Ensure required APIs are enabled in your Google Cloud Project:
```bash
gcloud services enable \
  agentidentity.googleapis.com \
  agentregistry.googleapis.com \
  aiplatform.googleapis.com \
  apphub.googleapis.com \
  cloudbuild.googleapis.com \
  --project="YOUR_PROJECT_ID"
```

### 2. Deploy Agent B (Specialist)
```bash
PROJECT_ID="YOUR_PROJECT_ID" LOCATION="us-central1" ./scripts/deploy_agent_b.sh
```
Retrieve Agent B's Reasoning Engine ID (`ENGINE_ID_B`) from the console or CLI output.

### 3. Deploy Agent A (Coordinator)
Set the `AGENT_B_A2A_URL` referencing Agent B's `/api` passthrough URL and deploy Agent A:
```bash
export AGENT_B_A2A_URL="https://us-central1-aiplatform.googleapis.com/reasoningEngines/v1/projects/YOUR_PROJECT_ID/locations/us-central1/reasoningEngines/ENGINE_ID_B/api/a2a/agent_b"

PROJECT_ID="YOUR_PROJECT_ID" LOCATION="us-central1" ./scripts/deploy_agent_a.sh
```

### 4. Configure IAM Permissions for Agent Identity
Retrieve Agent A's SPIFFE ID (`PRINCIPAL_A`) from Google Cloud Console -> **Agent Platform** -> **Deployments**:
```bash
PROJECT_ID="YOUR_PROJECT_ID" \
PRINCIPAL_A="principal://agents.global.org-ORGANIZATION_ID.system.id.goog/resources/aiplatform/projects/PROJECT_NUMBER/locations/us-central1/reasoningEngines/ENGINE_ID_A" \
./scripts/setup_iam.sh
```

### 5. Register in Agent Registry
Catalog both agents in Google Cloud Agent Registry:
```bash
PROJECT_ID="YOUR_PROJECT_ID" \
LOCATION="us-central1" \
ENGINE_ID_A="ENGINE_ID_A" \
ENGINE_ID_B="ENGINE_ID_B" \
./scripts/register_agent_registry.sh
```

---

## Running Tests

Run the test suite locally:
```bash
python3 -m unittest discover tests
```
