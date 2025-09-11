#!/usr/bin/env python3
"""
🎮 PAC-MAN MONITOR
==================
Track the all-night Pac-Man progress
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("🎮 READY PLAYER ONE - PAC-MAN MONITOR")
print("="*60)
print(f"Time: {datetime.now().strftime('%I:%M %p CST')}")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

# Get starting values
accounts = client.get_accounts()
account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts

total = 0
usd = 0
holdings = {}

for account in account_list:
    balance = float(account['available_balance']['value'])
    currency = account['currency']
    
    if currency == 'USD':
        usd = balance
        total += balance
    elif balance > 0.001:
        ticker = client.get_product(f'{currency}-USD')
        price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
        value = balance * price
        total += value
        holdings[currency] = balance

print(f"\n📊 CURRENT STATUS:")
print(f"   Portfolio: ${total:.2f}")
print(f"   USD: ${usd:.2f}")
print(f"   SOL: {holdings.get('SOL', 0):.6f}")
print(f"   ETH: {holdings.get('ETH', 0):.6f}")
print(f"   BTC: {holdings.get('BTC', 0):.6f}")

print(f"\n🎯 TARGETS:")
print(f"   Emergency Brake: $15,000")
print(f"   Ease-off Target: $10,000")
print(f"   Distance to $15k: ${15000 - total:.2f}")

print(f"\n🟡 PAC-MAN STATUS:")
print(f"   The crawdads are gobbling dots...")
print(f"   Check back later for progress...")
print(f"   WAKA WAKA WAKA!")

# Save status
status = {
    'timestamp': datetime.now().isoformat(),
    'portfolio_value': total,
    'usd_balance': usd,
    'holdings': holdings,
    'ready_player_one': True
}

with open('/home/dereadi/scripts/claude/pacman_status.json', 'w') as f:
    json.dump(status, f, indent=2)

print(f"\n💾 Status saved to pacman_status.json")