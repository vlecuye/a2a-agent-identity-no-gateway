#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Deploy Agent B (Specialist) to Agent Runtime with Agent Identity enabled
# ==============================================================================

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${PROJECT_ID:-}}"
LOCATION="${GOOGLE_CLOUD_LOCATION:-${LOCATION:-us-central1}}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Error: PROJECT_ID or GOOGLE_CLOUD_PROJECT environment variable must be set." >&2
  echo "Usage: PROJECT_ID=my-gcp-project LOCATION=us-central1 ./scripts/deploy_agent_b.sh" >&2
  exit 1
fi

echo "=========================================================="
echo "Deploying Agent B (Specialist) to Agent Runtime"
echo "Project:  ${PROJECT_ID}"
echo "Location: ${LOCATION}"
echo "Identity: AGENT_IDENTITY"
echo "=========================================================="

# Ensure required APIs are enabled
gcloud services enable \
  agentidentity.googleapis.com \
  agentregistry.googleapis.com \
  aiplatform.googleapis.com \
  apphub.googleapis.com \
  cloudbuild.googleapis.com \
  --project="${PROJECT_ID}"

# Verify Agent Identity configuration exists
if [[ ! -f "agent_b/.agent_engine_config.json" ]]; then
  echo '{ "identity_type": "AGENT_IDENTITY" }' > agent_b/.agent_engine_config.json
fi

# Deploy Agent B to Agent Runtime (Reasoning Engine)
cd agent_b
uv run adk deploy agent_engine agent_b \
  --project="${PROJECT_ID}" \
  --region="${LOCATION}"
cd ..

echo ""
echo "=========================================================="
echo "Agent B Deployment Triggered."
echo ""
echo "Next Steps:"
echo "1. Retrieve Agent B's Reasoning Engine ID (ENGINE_ID_B) and SPIFFE ID:"
echo "   gcloud logging or GCP Console -> Agent Platform -> Deployments"
echo "2. Formulate the A2A Endpoint URL for Agent B:"
echo "   export AGENT_B_A2A_URL=\"https://${LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/projects/${PROJECT_ID}/locations/${LOCATION}/reasoningEngines/\${ENGINE_ID_B}/api/a2a/agent_b\""
echo "3. Run ./scripts/deploy_agent_a.sh with AGENT_B_A2A_URL set."
echo "=========================================================="
