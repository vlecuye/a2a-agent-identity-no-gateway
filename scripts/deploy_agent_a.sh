#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Deploy Agent A (Coordinator) to Agent Runtime with Agent Identity & Agent B URL
# ==============================================================================

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${PROJECT_ID:-}}"
LOCATION="${GOOGLE_CLOUD_LOCATION:-${LOCATION:-us-central1}}"
AGENT_B_A2A_URL="${AGENT_B_A2A_URL:-}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Error: PROJECT_ID or GOOGLE_CLOUD_PROJECT must be set." >&2
  exit 1
fi

if [[ -z "${AGENT_B_A2A_URL}" ]]; then
  echo "Error: AGENT_B_A2A_URL must be provided so Agent A knows how to reach Agent B." >&2
  echo "Example: AGENT_B_A2A_URL=\"https://${LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/projects/${PROJECT_ID}/locations/${LOCATION}/reasoningEngines/12345/api/a2a/agent_b\"" >&2
  exit 1
fi

echo "=========================================================="
echo "Deploying Agent A (Coordinator) to Agent Runtime"
echo "Project:     ${PROJECT_ID}"
echo "Location:    ${LOCATION}"
echo "Identity:    AGENT_IDENTITY"
echo "Agent B URL: ${AGENT_B_A2A_URL}"
echo "=========================================================="

# Verify Agent Identity configuration exists
if [[ ! -f "agent_a/.agent_engine_config.json" ]]; then
  echo '{ "identity_type": "AGENT_IDENTITY" }' > agent_a/.agent_engine_config.json
fi

# Deploy Agent A with environment variable pointing to Agent B's A2A URL
cd agent_a
uv run adk deploy agent_engine agent_a \
  --project="${PROJECT_ID}" \
  --region="${LOCATION}" \
  --update-env-vars="AGENT_B_A2A_URL=${AGENT_B_A2A_URL}"
cd ..

echo ""
echo "=========================================================="
echo "Agent A Deployment Triggered."
echo ""
echo "Next Steps:"
echo "1. Retrieve Agent A's SPIFFE ID (PRINCIPAL_A) from GCP Console -> Deployments."
echo "2. Run ./scripts/setup_iam.sh to grant Agent A permission to invoke Agent B."
echo "3. Run ./scripts/register_agent_registry.sh to catalog both agents."
echo "=========================================================="
