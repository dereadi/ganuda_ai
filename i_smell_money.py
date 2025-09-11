#!/usr/bin/env python3
"""
💰 I SMELL MONEY
The sweet scent of gains in the air
When you can smell it, it's about to rain profits
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                          💰 I SMELL MONEY 💰                             ║
║                    The Sweet Scent of Incoming Gains                      ║
║                         It's Thick in the Air...                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - THE SCENT IS STRONG!")
print("=" * 70)

# Get current state
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])

print("\n👃 WHAT I SMELL:")
print("-" * 40)
print(f"BTC: ${btc:,.0f} - Coiled at $112,180 ready to explode")
print(f"ETH: ${eth:.2f} - 0.0029% band = MONEY INCOMING")
print(f"SOL: ${sol:.2f} - Consolidated above $208 = BULLISH")
print(f"XRP: ${xrp:.4f} - Kiss away from $3.00 = EXPLOSIVE")

# Calculate potential gains
accounts = client.get_accounts()['accounts']
positions = {}
for acc in accounts:
    bal = float(acc['available_balance']['value'])
    if bal > 0.01:
        positions[acc['currency']] = bal

print("\n💰 THE MONEY I SMELL (Next leg projections):")
print("-" * 40)

# Project next move gains
btc_target = 112500
eth_target = 4570
sol_target = 210
xrp_target = 3.00

if 'BTC' in positions:
    btc_gain = (btc_target - btc) * positions['BTC']
    print(f"BTC → ${btc_target:,.0f}: +${btc_gain:,.2f}")

if 'ETH' in positions:
    eth_gain = (eth_target - eth) * positions['ETH']
    print(f"ETH → ${eth_target:.0f}: +${eth_gain:.2f}")

if 'SOL' in positions:
    sol_gain = (sol_target - sol) * positions['SOL']
    print(f"SOL → ${sol_target:.0f}: +${sol_gain:.2f}")

total_smell = 0
if 'BTC' in positions:
    total_smell += (btc_target - btc) * positions['BTC']
if 'ETH' in positions:
    total_smell += (eth_target - eth) * positions['ETH']
if 'SOL' in positions:
    total_smell += (sol_target - sol) * positions['SOL']

print(f"\n🤑 TOTAL MONEY SMELL: +${total_smell:.2f}")

print("\n🎯 WHY THE SMELL IS SO STRONG:")
print("-" * 40)
print("• Double squeeze on BTC/ETH (0.005% + 0.003%)")
print("• Just deployed $2,428 at perfect timing")
print("• 23:00 party momentum still building")
print("• Asian markets fully engaged")
print("• Bands tightening = Explosion imminent")
print("• Everything coiled in tight spirals")

# Track the scent getting stronger
print("\n👃 SCENT INTENSITY TRACKER:")
print("-" * 40)

for i in range(5):
    btc_new = float(client.get_product('BTC-USD')['price'])
    eth_new = float(client.get_product('ETH-USD')['price'])
    
    if btc_new > btc:
        print(f"{datetime.now().strftime('%H:%M:%S')}: 💰 MONEY SMELL INTENSIFYING!")
        print(f"  BTC: ${btc_new:,.0f} (+${btc_new - btc:.0f})")
    elif eth_new > eth:
        print(f"{datetime.now().strftime('%H:%M:%S')}: 💰 ETHEREUM MONEY SCENT!")
        print(f"  ETH: ${eth_new:.2f} (+${eth_new - eth:.2f})")
    else:
        print(f"{datetime.now().strftime('%H:%M:%S')}: 👃 Still smelling it...")
    
    time.sleep(3)

print("\n" + "=" * 70)
print("💭 WHEN YOU SMELL MONEY:")
print("• Trust your instincts")
print("• The market is speaking to you")
print("• Gains are materializing in the quantum field")
print("• The crawdads can smell it too")
print("• IT'S ABOUT TO RAIN PROFITS!")
print("=" * 70)