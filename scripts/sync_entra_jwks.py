#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Helper script to sync Microsoft Entra ID (Azure AD) public JWKS keys to GCP.

Downloads Microsoft's signing keys and uploads them to Google Cloud Storage (GCS)
and/or Secret Manager, with an optional local file output for offline/testing use.

Usage examples:
    # Save locally:
    python scripts/sync_entra_jwks.py --output-file agent_a/app/config/microsoft_entra_jwks.json

    # Upload to GCS:
    python scripts/sync_entra_jwks.py --gcs-uri gs://my-agent-bucket/config/microsoft_entra_jwks.json

    # Upload to Secret Manager:
    python scripts/sync_entra_jwks.py --secret-name entra-id-public-jwks --project all-in-demo
"""

import argparse
import json
import os
import sys
import urllib.request


DEFAULT_ENTRA_KEYS_URL = "https://login.microsoftonline.com/common/discovery/v2.0/keys"


def fetch_microsoft_jwks(tenant_id: str | None = None) -> dict:
    """Fetch the latest JWKS public keys from Microsoft Entra ID."""
    url = (
        f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        if tenant_id
        else DEFAULT_ENTRA_KEYS_URL
    )
    print(f"Fetching Microsoft Entra ID public JWKS from: {url}")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ADK-EntraID-Sync/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP error {response.status} fetching keys from {url}")
        data = json.loads(response.read().decode("utf-8"))
    
    keys_count = len(data.get("keys", []))
    print(f"Successfully retrieved {keys_count} public key(s).")
    return data


def save_to_local_file(jwks_data: dict, file_path: str) -> None:
    """Save JWKS data to a local JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(jwks_data, f, indent=2)
    print(f"Saved JWKS to local file: {file_path}")


def upload_to_gcs(jwks_data: dict, gcs_uri: str) -> None:
    """Upload JWKS JSON data to Google Cloud Storage."""
    from google.cloud import storage

    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI (must start with gs://): {gcs_uri}")

    parts = gcs_uri[5:].split("/", 1)
    bucket_name = parts[0]
    blob_name = parts[1] if len(parts) > 1 else "microsoft_entra_jwks.json"

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        json.dumps(jwks_data, indent=2),
        content_type="application/json",
    )
    print(f"Uploaded JWKS to GCS: {gcs_uri}")


def upload_to_secret_manager(jwks_data: dict, secret_name: str, project_id: str) -> None:
    """Upload JWKS JSON data as a new version in Secret Manager."""
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project_id}"
    secret_path = f"{parent}/secrets/{secret_name}"

    payload_bytes = json.dumps(jwks_data, indent=2).encode("utf-8")

    # Create secret if it does not exist
    try:
        client.get_secret(request={"name": secret_path})
    except Exception:
        print(f"Secret '{secret_name}' does not exist in project '{project_id}'. Creating it...")
        client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_name,
                "secret": {
                    "replication": {"automatic": {}},
                    "labels": {"managed-by": "adk-auth"},
                },
            }
        )

    response = client.add_secret_version(
        request={
            "parent": secret_path,
            "payload": {"data": payload_bytes},
        }
    )
    print(f"Added new secret version to Secret Manager: {response.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Sync Microsoft Entra ID public JWKS keys to GCP (GCS/Secret Manager) or local storage."
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        default=None,
        help="Optional Entra ID tenant ID (defaults to 'common').",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Local file path to save JWKS JSON (e.g., agent_a/app/config/microsoft_entra_jwks.json).",
    )
    parser.add_argument(
        "--gcs-uri",
        type=str,
        default=None,
        help="Google Cloud Storage URI to upload JWKS to (e.g., gs://my-bucket/config/microsoft_entra_jwks.json).",
    )
    parser.add_argument(
        "--secret-name",
        type=str,
        default=None,
        help="Secret Manager secret name (e.g., entra-id-public-jwks).",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=os.getenv("GOOGLE_CLOUD_PROJECT"),
        help="GCP Project ID for Secret Manager (defaults to GOOGLE_CLOUD_PROJECT env var).",
    )

    args = parser.parse_args()

    if not (args.output_file or args.gcs-uri or args.secret_name):
        parser.print_help()
        print("\nError: Specify at least one destination (--output-file, --gcs-uri, or --secret-name).")
        sys.exit(1)

    try:
        jwks_data = fetch_microsoft_jwks(tenant_id=args.tenant_id)
    except Exception as e:
        print(f"Failed to fetch Microsoft JWKS: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output_file:
        save_to_local_file(jwks_data, args.output_file)

    if args.gcs_uri:
        upload_to_gcs(jwks_data, args.gcs_uri)

    if args.secret_name:
        if not args.project:
            print("Error: --project or GOOGLE_CLOUD_PROJECT env var is required for Secret Manager.", file=sys.stderr)
            sys.exit(1)
        upload_to_secret_manager(jwks_data, args.secret_name, args.project)

    print("JWKS sync completed successfully.")


if __name__ == "__main__":
    main()
