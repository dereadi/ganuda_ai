#!/usr/bin/env python3
"""
Check what the specialists are doing
"""

import json
from coinbase.rest import RESTClient
import subprocess

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🔍 SPECIALIST ACTIVITY CHECK")
print("=" * 50)

# Get real balance
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"USD Balance: ${usd_balance:,.2f}")

# Determine mode
if usd_balance > 500:
    mode = "🟢 DEPLOY MODE"
    action = "Should be BUYING dips and accumulating"
elif usd_balance > 250:
    mode = "🟡 BALANCED MODE"
    action = "Normal trading operations"
else:
    mode = "🔴 RETRIEVE MODE"
    action = "Should be SELLING for liquidity"

print(f"Operating Mode: {mode}")
print(f"Expected Action: {action}")
print()

# Check if USD is actually $1013
if usd_balance > 1000:
    print("✅ With $1,013 the specialists should be:")
    print("  - Buying SOL dips (Asian session)")
    print("  - Positioning in AVAX (66% growth news)")
    print("  - Catching ETH/BTC sawteeth")
    print("  - Building positions aggressively")
    print()
    print("⚠️ If they're NOT buying, there's a config issue!")
else:
    print("❌ USD appears low, checking why...")

# Check running processes
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
specialists_running = 0
for line in result.stdout.split('\n'):
    if 'specialist_v2.py' in line:
        specialists_running += 1

print(f"\nSpecialists Running: {specialists_running}/4")

# Recent orders check
print("\n📊 Checking for recent trades...")
print("(Specialists may be waiting for opportunities)")