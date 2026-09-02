"""Test script to test query with auth token injected."""

import json
import time
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
import google.auth
import google.auth.transport.requests
import requests

def generate_mock_entra_token():
    # Load private key used for mock tests if needed, or inspect behavior
    payload = {
        "iss": "https://login.microsoftonline.com/f7ed2580-354f-41c6-8363-8929bcab9347/v2.0",
        "aud": "55884d39-1177-4adf-b2c0-ea520cd495ee",
        "sub": "user_test_123",
        "roles": ["math-users"],
        "groups": ["math-users", "admin"],
        "exp": int(time.time()) + 3600,
        "nbf": int(time.time()) - 10,
        "iat": int(time.time()) - 10,
    }
    return payload

def run_test():
    creds, project = google.auth.default()
    req = google.auth.transport.requests.Request()
    creds.refresh(req)

    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }

    url = "https://us-central1-aiplatform.googleapis.com/v1/projects/816122473048/locations/us-central1/reasoningEngines/4334879018332454912:streamQuery"

    payload = {
        "input": {
            "message": "What is 42 * 100?",
        }
    }
    print("Testing streamQuery...")
    with requests.post(url, headers=headers, json=payload, stream=True) as resp:
        print("Status Code:", resp.status_code)
        for chunk in resp.iter_lines():
            if chunk:
                print("Chunk:", chunk.decode("utf-8")[:200])

if __name__ == "__main__":
    run_test()
