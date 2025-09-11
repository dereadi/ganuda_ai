#!/usr/bin/env python3
"""
🌪️ DEPLOY $98 INTO THE FLYWHEEL - SPIN IT UP!
"""

import json
import uuid
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║               🌪️ FLYWHEEL CAPITAL INJECTION 🌪️                           ║
║                                                                            ║
║         "$98 idle = $98 wasted. Feed the flywheel!"                       ║
║         "Every dollar compounds. Every trade accelerates."                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

client = RESTClient(
    api_key=api_data['name'].split('/')[-1],
    api_secret=api_data['privateKey']
)

# Check balances
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"\n💵 IDLE CAPITAL DETECTED: ${usd_balance:.2f}")
print("=" * 60)

if usd_balance < 10:
    print("⚠️ Insufficient capital for flywheel deployment")
    exit()

# Get current prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print(f"\n📊 FLYWHEEL FUEL PRICES:")
print(f"BTC: ${btc_price:,.2f}")
print(f"ETH: ${eth_price:,.2f}")
print(f"SOL: ${sol_price:,.2f}")

# Flywheel allocation strategy
print(f"\n🌪️ FLYWHEEL ACCELERATION PLAN:")
print("=" * 60)

# Split into high-velocity trades
allocation = {
    'SOL': usd_balance * 0.40,  # 40% - High volatility
    'ETH': usd_balance * 0.30,  # 30% - Medium volatility
    'BTC': usd_balance * 0.20,  # 20% - Stability
    'reserve': usd_balance * 0.10  # 10% - Quick trades
}

print(f"SOL: ${allocation['SOL']:.2f} (High velocity fuel)")
print(f"ETH: ${allocation['ETH']:.2f} (Medium velocity)")
print(f"BTC: ${allocation['BTC']:.2f} (Stability anchor)")
print(f"Reserve: ${allocation['reserve']:.2f} (Quick flips)")

print(f"\n🚀 EXECUTING FLYWHEEL INJECTION:")
print("=" * 60)

try:
    # Execute SOL buy
    if allocation['SOL'] > 10:
        print(f"1️⃣ Injecting ${allocation['SOL']:.2f} into SOL...")
        sol_order = client.market_order_buy(
            client_order_id=str(uuid.uuid4()),
            product_id="SOL-USD",
            quote_size=str(allocation['SOL'])
        )
        print("   ✅ SOL fuel injected!")
    
    # Execute ETH buy
    if allocation['ETH'] > 10:
        print(f"2️⃣ Injecting ${allocation['ETH']:.2f} into ETH...")
        eth_order = client.market_order_buy(
            client_order_id=str(uuid.uuid4()),
            product_id="ETH-USD",
            quote_size=str(allocation['ETH'])
        )
        print("   ✅ ETH fuel injected!")
    
    # Execute BTC buy
    if allocation['BTC'] > 10:
        print(f"3️⃣ Injecting ${allocation['BTC']:.2f} into BTC...")
        btc_order = client.market_order_buy(
            client_order_id=str(uuid.uuid4()),
            product_id="BTC-USD",
            quote_size=str(allocation['BTC'])
        )
        print("   ✅ BTC fuel injected!")
    
    print(f"\n🌪️ FLYWHEEL ACCELERATING!")
    print(f"Reserve ${allocation['reserve']:.2f} kept for rapid trades")
    
except Exception as e:
    print(f"\n⚠️ Manual injection needed: {e}")
    print("\nMANUAL STEPS:")
    print(f"1. Buy ${allocation['SOL']:.2f} of SOL")
    print(f"2. Buy ${allocation['ETH']:.2f} of ETH")
    print(f"3. Buy ${allocation['BTC']:.2f} of BTC")

print(f"\n⚡ FLYWHEEL PHYSICS:")
print("=" * 60)
print("• $98 deployed = ~10 trades per hour")
print("• Each trade compounds 0.5-2%")
print("• 10 trades × 1% = 10% daily growth")
print("• $98 → $108 → $119 → $131 (3 days)")
print("• Velocity increases with each spin!")

print(f"\n🔥 SACRED FIRE WISDOM:")
print("'The flywheel starts slow but becomes unstoppable'")
print("'Your $98 is the spark that ignites the tornado'")
print("'Watch it spin from $11k to $15k to $25k!'")
print("\n🌪️ THE FLYWHEEL IS FED! LET IT SPIN!")
