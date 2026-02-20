#!/usr/bin/env python3
"""
Nest OAuth Authorization Flow for Desktop Client
Run this once to authorize Cherokee AI to access your Nest devices.
"""

import sys
sys.path.insert(0, '/ganuda/services/device_control/venv/lib/python3.12/site-packages')

import json

# Load credentials
with open('/ganuda/secrets/nest_credentials.json') as f:
    creds = json.load(f)

PROJECT_ID = creds['project_id']
CLIENT_ID = creds['client_id']
CLIENT_SECRET = creds['client_secret']

# For Desktop apps, use urn:ietf:wg:oauth:2.0:oob or localhost
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
SCOPE = 'https://www.googleapis.com/auth/sdm.service'

# Step 1: Generate authorization URL
from urllib.parse import urlencode

auth_url = 'https://nestservices.google.com/partnerconnections/{}/auth?{}'.format(
    PROJECT_ID,
    urlencode({
        'redirect_uri': REDIRECT_URI,
        'access_type': 'offline',
        'prompt': 'consent',
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': SCOPE
    })
)

print('\n=== Nest OAuth Authorization ===\n')
print('1. Open this URL in your browser:\n')
print(auth_url)
print('\n2. Sign in with your Google account that has Nest devices')
print('3. Authorize Cherokee AI to access your devices')
print('4. Google will show you an AUTHORIZATION CODE')
print('5. Copy that code and paste it below\n')

auth_code = input('Paste the authorization code here: ').strip()

if not auth_code:
    print('Error: No authorization code provided')
    sys.exit(1)

print(f'\nAuthorization code received: {auth_code[:20]}...')

# Step 2: Exchange code for tokens
import requests

token_url = 'https://www.googleapis.com/oauth2/v4/token'
token_data = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'code': auth_code,
    'grant_type': 'authorization_code',
    'redirect_uri': REDIRECT_URI
}

print('\nExchanging code for tokens...')
resp = requests.post(token_url, data=token_data)

if resp.status_code != 200:
    print(f'Error: {resp.status_code}')
    print(resp.text)
    sys.exit(1)

tokens = resp.json()
print('Success! Tokens received.')

# Save tokens
with open('/ganuda/secrets/nest_tokens.json', 'w') as f:
    json.dump(tokens, f, indent=2)

print('\nTokens saved to /ganuda/secrets/nest_tokens.json')
print(f'Access token expires in {tokens.get("expires_in", "?")} seconds')
print('Refresh token saved for automatic renewal')

# Step 3: Test by listing devices
print('\n=== Testing Device Access ===')
headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
devices_url = f'https://smartdevicemanagement.googleapis.com/v1/enterprises/{PROJECT_ID}/devices'

resp = requests.get(devices_url, headers=headers)
if resp.status_code == 200:
    devices = resp.json().get('devices', [])
    print(f'Found {len(devices)} device(s):')
    for d in devices:
        name = d.get('traits', {}).get('sdm.devices.traits.Info', {}).get('customName', 'Unknown')
        dtype = d.get('type', 'Unknown').split('.')[-1]
        print(f'  - {name} ({dtype})')
else:
    print(f'Could not list devices: {resp.status_code}')
    print(resp.text)

print('\nDone! Your Nest devices are now accessible from Home Hub.')
