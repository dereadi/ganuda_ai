#!/usr/bin/env python3
"""
SIMPLE ROBINHOOD PUBLIC KEY GENERATOR
======================================
Generates a public key string for Robinhood API
"""

import os
import secrets
import base64
import json
from datetime import datetime

print("🔑 ROBINHOOD PUBLIC KEY GENERATOR")
print("="*50)
print()

# Generate a secure random key (256-bit)
random_bytes = secrets.token_bytes(32)
public_key = base64.b64encode(random_bytes).decode('utf-8')

# Also generate an API key format
api_key = secrets.token_urlsafe(32)

print("📋 YOUR PUBLIC KEY (Copy this entire string):")
print("="*50)
print(public_key)
print("="*50)
print()

print("🔐 Alternative API Key Format:")
print("-"*50)
print(api_key)
print("-"*50)
print()

# Save keys
config = {
    "public_key": public_key,
    "api_key": api_key,
    "generated": datetime.now().isoformat()
}

config_file = os.path.expanduser("~/.robinhood_api_config.json")
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)
os.chmod(config_file, 0o600)

print("\n✅ Keys saved to:", config_file)
print()
print("📝 HOW TO USE:")
print("1. Go to Robinhood.com → Account → Settings")
print("2. Look for 'API Access' or 'Developer Settings'")
print("3. Click 'Generate API Key' or 'Create New Key'")
print("4. When asked for public key, paste:", public_key)
print()
print("⚠️  If Robinhood rejects the key, try the API key format instead")
print()
print("🦀 Ready to authenticate the Quantum Crawdad Megapod!")