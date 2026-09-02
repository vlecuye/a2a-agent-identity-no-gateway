#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Register Agent A and Agent B in Google Cloud Agent Registry as A2A Agents
# ==============================================================================

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${PROJECT_ID:-}}"
LOCATION="${GOOGLE_CLOUD_LOCATION:-${LOCATION:-us-central1}}"
ENGINE_ID_A="${ENGINE_ID_A:-}"
ENGINE_ID_B="${ENGINE_ID_B:-}"

if [[ -z "${PROJECT_ID}" || -z "${ENGINE_ID_A}" || -z "${ENGINE_ID_B}" ]]; then
  echo "Error: PROJECT_ID, ENGINE_ID_A, and ENGINE_ID_B must be set." >&2
  echo "" >&2
  echo "Usage:" >&2
  echo "  PROJECT_ID=\"my-project\" \\" >&2
  echo "  LOCATION=\"us-central1\" \\" >&2
  echo "  ENGINE_ID_A=\"123456\" \\" >&2
  echo "  ENGINE_ID_B=\"789012\" \\" >&2
  echo "  ./scripts/register_agent_registry.sh" >&2
  exit 1
fi

AGENT_A_URL="https://${LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/projects/${PROJECT_ID}/locations/${LOCATION}/reasoningEngines/${ENGINE_ID_A}/api/a2a/agent_a"
AGENT_B_URL="https://${LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/projects/${PROJECT_ID}/locations/${LOCATION}/reasoningEngines/${ENGINE_ID_B}/api/a2a/agent_b"

echo "=========================================================="
echo "Registering Agents in Google Cloud Agent Registry"
echo "Project:   ${PROJECT_ID}"
echo "Location:  ${LOCATION}"
echo "=========================================================="

echo "1. Registering Agent B (Calculator Specialist)..."
gcloud agent-registry services update agent_b \
  --project="${PROJECT_ID}" \
  --location="${LOCATION}" \
  --display-name="Agent B (Calculator Specialist)" \
  --description="Specialist calculation agent exposed via A2A protocol" \
  --agent-spec-type=a2a-agent-card \
  --agent-spec-content=@agent_b/agent_card.json \
  --interfaces="url=${AGENT_B_URL},protocolBinding=http-json"

echo "2. Registering Agent A (Coordinator)..."
gcloud agent-registry services update agent_a \
  --project="${PROJECT_ID}" \
  --location="${LOCATION}" \
  --display-name="Agent A (Coordinator)" \
  --description="Coordinator agent communicating with sub-agents via A2A" \
  --agent-spec-type=a2a-agent-card \
  --agent-spec-content=@agent_a/agent_card.json \
  --interfaces="url=${AGENT_A_URL},protocolBinding=http-json"

echo ""
echo "=========================================================="
echo "Agent Registry registration completed successfully."
echo "Both agents are cataloged and identified as A2A services."
echo "=========================================================="
