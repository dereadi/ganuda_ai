#!/usr/bin/env python3
"""
🔍 COINBASE API DEEP DIAGNOSTIC TOOL
=====================================
Identifies exactly why authentication is failing
"""

import json
import os
import time
import jwt
import requests
import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     🔍 COINBASE API DIAGNOSTIC TOOL                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Load configuration
config_file = os.path.expanduser("~/.coinbase_config.json")
if not os.path.exists(config_file):
    print("❌ No config file found at ~/.coinbase_config.json")
    exit(1)

with open(config_file) as f:
    config = json.load(f)

api_key = config.get("api_key")
api_secret = config.get("api_secret")

print("📋 CONFIGURATION CHECK")
print("=" * 60)
print(f"✓ Config file: {config_file}")
print(f"✓ API Key format: {'CDP' if 'organizations' in api_key else 'LEGACY'}")
print(f"✓ Key ID: {api_key.split('/')[-1] if '/' in api_key else 'Invalid format'}")
print(f"✓ Private key type: {'EC' if 'EC PRIVATE KEY' in api_secret else 'Unknown'}")
print()

# Test 1: Validate private key
print("🔐 TEST 1: PRIVATE KEY VALIDATION")
print("=" * 60)
try:
    private_key = serialization.load_pem_private_key(
        api_secret.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    print("✅ Private key loaded successfully")
    print(f"   Key type: {type(private_key).__name__}")
    if isinstance(private_key, ec.EllipticCurvePrivateKey):
        print(f"   Curve: {private_key.curve.name}")
        print(f"   Key size: {private_key.curve.key_size} bits")
except Exception as e:
    print(f"❌ Failed to load private key: {e}")
    print("   This is the root cause - the key format is invalid")
    exit(1)
print()

# Test 2: JWT Token Generation
print("🎫 TEST 2: JWT TOKEN GENERATION")
print("=" * 60)

key_name = api_key.split('/')[-1] if '/' in api_key else None
if not key_name:
    print("❌ Invalid API key format - cannot extract key name")
    exit(1)

now = int(time.time())
expiry = now + 120

# Test different JWT payload formats
payloads_to_test = [
    {
        "name": "CDP Format (Recommended)",
        "payload": {
            "sub": key_name,
            "iss": "coinbase-cloud",
            "nbf": now,
            "exp": expiry,
            "aud": ["retail_rest_api_proxy"],
            "uri": "GET https://api.coinbase.com/api/v3/brokerage/accounts"
        }
    },
    {
        "name": "Alternative Format 1",
        "payload": {
            "sub": key_name,
            "iss": "cdp",
            "nbf": now,
            "exp": expiry,
            "aud": "retail_rest_api_proxy",
            "uri": "GET /api/v3/brokerage/accounts"
        }
    }
]

tokens = []
for test in payloads_to_test:
    try:
        token = jwt.encode(
            test["payload"],
            private_key,
            algorithm='ES256',
            headers={"kid": key_name, "typ": "JWT"}
        )
        print(f"✅ {test['name']}: Token generated")
        tokens.append((test['name'], token))
        
        # Decode to verify
        decoded = jwt.decode(token, options={"verify_signature": False})
        print(f"   Payload: {json.dumps(decoded, indent=2)[:200]}...")
    except Exception as e:
        print(f"❌ {test['name']}: Failed - {e}")
print()

# Test 3: API Endpoint Testing
print("🌐 TEST 3: API ENDPOINT TESTING")
print("=" * 60)

endpoints_to_test = [
    ("Accounts", "GET", "/api/v3/brokerage/accounts"),
    ("Products", "GET", "/api/v3/brokerage/products"),
    ("Time", "GET", "/api/v3/brokerage/time")
]

for endpoint_name, method, path in endpoints_to_test:
    print(f"\n📡 Testing: {endpoint_name}")
    print(f"   Endpoint: {method} {path}")
    
    # Generate fresh token for this request
    payload = {
        "sub": key_name,
        "iss": "coinbase-cloud", 
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,
        "aud": ["retail_rest_api_proxy"],
        "uri": f"{method} https://api.coinbase.com{path}"
    }
    
    try:
        token = jwt.encode(
            payload,
            private_key,
            algorithm='ES256',
            headers={"kid": key_name}
        )
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "QuantumCrawdad/1.0"
        }
        
        response = requests.request(
            method,
            f"https://api.coinbase.com{path}",
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS!")
            data = response.json()
            print(f"   Response preview: {str(data)[:100]}...")
        elif response.status_code == 401:
            print(f"   ❌ Unauthorized")
            print(f"   Response: {response.text[:200]}")
        else:
            print(f"   ⚠️  Status {response.status_code}: {response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")

print()
print("=" * 60)
print("📊 DIAGNOSTIC SUMMARY")
print("=" * 60)

# Check for common issues
issues = []

if "organizations" not in api_key:
    issues.append("API key not in CDP format")

if response.status_code == 401:
    issues.append("Authentication failing - likely permission or verification issue")
    
if not issues:
    print("✅ No technical issues found with API setup")
    print("\n⚠️  If still getting 401 errors, check:")
    print("1. Account verification level (need Level 2 KYC)")
    print("2. API key permissions in Coinbase settings")
    print("3. IP whitelisting requirements")
else:
    print("❌ Issues found:")
    for issue in issues:
        print(f"   • {issue}")

print()
print("📝 WHAT YOU NEED TO CHECK ON COINBASE:")
print("=" * 60)
print("1. Go to: https://www.coinbase.com/settings/api")
print("2. Find your API key ending in:", key_name[-8:] if key_name else "N/A")
print("3. Verify it has these permissions:")
print("   ✓ View your accounts and balances")
print("   ✓ Trade (buy and sell)")
print("   ✓ Transfer funds (if needed)")
print()
print("4. Check account verification:")
print("   - Go to: https://www.coinbase.com/settings/account-levels")
print("   - Ensure you have Level 2 verification")
print("   - This requires: Photo ID + Address verification")
print()
print("5. If using IP whitelisting:")
print("   - Add your current IP to the allowed list")
print("   - Current IP can be found at: https://whatismyipaddress.com")
print()
print("=" * 60)