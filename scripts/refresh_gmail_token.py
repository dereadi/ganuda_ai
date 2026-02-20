#!/usr/bin/env python3
"""Refresh Gmail OAuth token - two-step: generate URL, then exchange code."""

import os
import sys
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

TOKEN_FILE = os.path.expanduser("~/.gmail_credentials/token.pickle")

# Load existing token to extract client_id and client_secret
with open(TOKEN_FILE, "rb") as f:
    old_creds = pickle.load(f)

client_id = old_creds.client_id
client_secret = old_creds.client_secret

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

REDIRECT_URI = "http://localhost:9999/"

client_config = {
    "installed": {
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [REDIRECT_URI],
    }
}

flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
flow.redirect_uri = REDIRECT_URI

if len(sys.argv) > 1 and sys.argv[1] == "--exchange":
    # Step 2: Exchange the code from the redirect URL
    redirect_url = sys.argv[2]
    flow.fetch_token(authorization_response=redirect_url)
    creds = flow.credentials

    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)

    print(f"Token refreshed and saved to {TOKEN_FILE}")
    print(f"Valid: {creds.valid}")
else:
    # Step 1: Generate auth URL
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )
    print("=" * 60)
    print("STEP 1: Open this URL in any browser:")
    print("=" * 60)
    print(auth_url)
    print()
    print("=" * 60)
    print("STEP 2: After authorizing, the browser will try to redirect")
    print("to localhost:9999 and FAIL. That's OK!")
    print("Copy the FULL URL from the browser address bar.")
    print("It will look like: http://localhost:9999/?state=...&code=...&scope=...")
    print("Then run:")
    print(f"  python3 {__file__} --exchange 'PASTE_FULL_URL_HERE'")
    print("=" * 60)
