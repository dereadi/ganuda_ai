#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
EMERGENCY BALANCE CHECK
"""

import json
from pathlib import Path
from coinbase.rest import RESTClient

config_path = Path.home() / ".coinbase_config.json"
with open(config_path, 'r') as f:
    config = json.load(f)

client = RESTClient(
    api_key=config['api_key'],
    api_secret=config['api_secret']
)

print("🔥 EMERGENCY BALANCE CHECK")
print("=" * 60)

accounts = client.get_accounts()

# Try to find USD/USDC
for account in accounts.accounts:
    if account.currency in ['USD', 'USDC']:
        balance = float(account.available_balance.value)
        if balance > 0.01:
            print(f"{account.currency}: ${balance:,.2f}")

print("\nMajor crypto positions:")
for account in accounts.accounts:
    if account.currency in ['BTC', 'ETH', 'SOL'] and float(account.available_balance.value) > 0:
        print(f"{account.currency}: {account.available_balance.value}")