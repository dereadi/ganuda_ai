#!/usr/bin/env python3
"""
COINBASE API SETUP HELPER
==========================
Fixes the PEM file error
"""

import json
import os

print("🔑 COINBASE API SETUP")
print("="*50)
print()
print("📝 You need to get your API credentials from:")
print("https://www.coinbase.com/settings/api")
print("(NOT cloud.coinbase.com)")
print()
print("For the NEW Coinbase Advanced Trade API:")
print("1. Go to Coinbase.com → Settings → API")
print("2. Click '+ New API Key'")
print("3. Select account permissions:")
print("   ✓ View your accounts")
print("   ✓ Trade")
print("4. Click 'Create'")
print("5. You'll get:")
print("   - API Key Name (like 'organizations/xxx/apiKeys/yyy')")
print("   - API Secret (starts with '-----BEGIN EC PRIVATE KEY-----')")
print()

# Get credentials
print("Enter your Coinbase API credentials:")
print()
api_key = input("API Key Name (organizations/xxx/apiKeys/yyy): ").strip()
print()
print("API Secret (paste the ENTIRE private key including BEGIN/END lines):")
print("Press Enter twice when done:")

secret_lines = []
while True:
    line = input()
    if not line and secret_lines and secret_lines[-1] == '':
        break
    secret_lines.append(line)

api_secret = '\n'.join(secret_lines[:-1])  # Remove last empty line

# Validate format
if not api_key.startswith("organizations/"):
    print("⚠️ API Key should start with 'organizations/'")
    print("Make sure you're using the new Advanced Trade API")

if "BEGIN EC PRIVATE KEY" not in api_secret:
    print("⚠️ API Secret should contain 'BEGIN EC PRIVATE KEY'")
    print("Make sure to copy the ENTIRE private key")

# Save config
config = {
    "api_key": api_key,
    "api_secret": api_secret,
    "capital": 300.0,
    "type": "advanced_trade"
}

config_file = os.path.expanduser("~/.coinbase_config.json")
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

os.chmod(config_file, 0o600)

print()
print("✅ Configuration saved to:", config_file)
print("💰 Capital set to: $300")
print()
print("🚀 Now run: ./quantum_crawdad_env/bin/python3 coinbase_quantum_megapod.py")