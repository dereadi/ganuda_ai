#!/usr/bin/env python3
"""Test Coinbase API connection"""

import json
import os
import time
import base64
import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

# Load config
config_path = os.path.expanduser("~/.coinbase_config.json")
with open(config_path) as f:
    config = json.load(f)

api_key = config["api_key"]
api_secret = config["api_secret"]

# Parse private key
private_key = serialization.load_pem_private_key(
    api_secret.encode(),
    password=None,
    backend=default_backend()
)

def sign_request(method, path, body=""):
    """Sign request with EC private key"""
    timestamp = str(int(time.time()))
    message = f"{timestamp}{method}{path}{body}"
    
    signature = private_key.sign(
        message.encode(),
        ec.ECDSA(hashes.SHA256())
    )
    
    return {
        "CB-ACCESS-KEY": api_key,
        "CB-ACCESS-SIGN": base64.b64encode(signature).decode(),
        "CB-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }

# Test API call
print("🔑 Testing Coinbase API connection...")
print(f"API Key: {api_key[:50]}...")

path = "/api/v3/brokerage/accounts"
url = f"https://api.coinbase.com{path}"

headers = sign_request("GET", path)

print(f"\n📡 Calling: {url}")
response = requests.get(url, headers=headers)

print(f"📊 Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("✅ API connection successful!")
    
    if "accounts" in data:
        print(f"\n💰 Found {len(data['accounts'])} accounts:")
        for account in data["accounts"][:5]:  # Show first 5
            currency = account.get("currency", "Unknown")
            balance = account.get("available_balance", {}).get("value", "0")
            print(f"  - {currency}: {balance}")
else:
    print(f"❌ Error: {response.status_code}")
    print(f"Response: {response.text}")