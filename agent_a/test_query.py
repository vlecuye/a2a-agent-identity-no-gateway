"""Script to test Reasoning Engine query and streamQuery endpoints."""

import json
import google.auth
import google.auth.transport.requests
import requests

def test_query():
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
            "message": "Hello, who are you and what can you do?"
        }
    }
    print(f"Sending request to {url}...")
    with requests.post(url, headers=headers, json=payload, stream=True) as resp:
        print("Status Code:", resp.status_code)
        for chunk in resp.iter_lines():
            if chunk:
                print("Chunk:", chunk.decode("utf-8"))

if __name__ == "__main__":
    test_query()
