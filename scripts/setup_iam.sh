#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Setup IAM Permissions for Agent A's SPIFFE Identity to invoke Agent B
# ==============================================================================

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${PROJECT_ID:-}}"
PRINCIPAL_A="${PRINCIPAL_A:-}"

if [[ -z "${PROJECT_ID}" || -z "${PRINCIPAL_A}" ]]; then
  echo "Error: PROJECT_ID and PRINCIPAL_A must be set." >&2
  echo "" >&2
  echo "Usage:" >&2
  echo "  PROJECT_ID=\"my-project\" \\" >&2
  echo "  PRINCIPAL_A=\"principal://agents.global.org-ORGANIZATION_ID.system.id.goog/resources/aiplatform/projects/PROJECT_NUMBER/locations/LOCATION/reasoningEngines/ENGINE_ID_A\" \\" >&2
  echo "  ./scripts/setup_iam.sh" >&2
  exit 1
fi

echo "=========================================================="
echo "Configuring IAM Policy Binding for Agent Identity"
echo "Project:   ${PROJECT_ID}"
echo "Principal: ${PRINCIPAL_A}"
echo "Role:      roles/aiplatform.user"
echo "=========================================================="

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="${PRINCIPAL_A}" \
  --role="roles/aiplatform.user"

echo ""
echo "IAM Policy binding successfully applied."
echo "Agent A's SPIFFE Identity is now authorized to call Agent B on Agent Runtime."
