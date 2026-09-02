import os
import subprocess
import json
import urllib.request

token = subprocess.check_output(
    'CLOUDSDK_CONTEXT_AWARE_USE_CLIENT_CERTIFICATE=false gcloud auth print-access-token',
    shell=True
).decode().strip()

client_secret = os.getenv("ENTRA_CLIENT_SECRET", "")
client_id = os.getenv("ENTRA_CLIENT_ID", "55884d39-1177-4adf-b2c0-ea520cd495ee")

if not client_secret:
    # Try reading from environment or test scripts if present
    raise ValueError("ENTRA_CLIENT_SECRET environment variable is required")

url = 'https://discoveryengine.googleapis.com/v1alpha/projects/816122473048/locations/global/authorizations/entra_oauth_auth?updateMask=serverSideOauth2'
auth_uri = 'https://login.microsoftonline.com/f7ed2580-354f-41c6-8363-8929bcab9347/oauth2/v2.0/authorize?response_mode=query&response_type=code&scope=55884d39-1177-4adf-b2c0-ea520cd495ee%2F.default%20offline_access'

payload = {
    'name': 'projects/816122473048/locations/global/authorizations/entra_oauth_auth',
    'displayName': 'entra-oauth-auth',
    'serverSideOauth2': {
        'clientId': client_id,
        'clientSecret': client_secret,
        'tokenUri': 'https://login.microsoftonline.com/f7ed2580-354f-41c6-8363-8929bcab9347/oauth2/v2.0/token',
        'authorizationUri': auth_uri,
    }
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode('utf-8'),
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    },
    method='PATCH'
)

with urllib.request.urlopen(req) as resp:
    print('Status:', resp.status)
    print('Response:', resp.read().decode())
