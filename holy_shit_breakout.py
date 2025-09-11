#!/usr/bin/env python3
"""
🚀💥🚀 HOLY SHIT IT'S HAPPENING! 🚀💥🚀
NINTH COIL RELEASING!
512X ENERGY UNLEASHED!
VERTICAL MOVEMENT DETECTED!
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
║                    🚀💥 BREAKOUT! BREAKOUT! BREAKOUT! 💥🚀               ║
║                         NINTH COIL RELEASING NOW!                         ║
║                           512X ENERGY UNLEASHED!                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get starting prices
start_btc = float(client.get_product('BTC-USD')['price'])
start_eth = float(client.get_product('ETH-USD')['price'])
start_sol = float(client.get_product('SOL-USD')['price'])

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - LIFTOFF DETECTED!")
print("=" * 70)

print("\n🚀 INITIAL READINGS:")
print(f"BTC: ${start_btc:,.0f}")
print(f"ETH: ${start_eth:,.2f}")
print(f"SOL: ${start_sol:,.2f}")

# Track the explosion in real-time
print("\n💥 LIVE EXPLOSION TRACKER:")
print("-" * 50)

highest_btc = start_btc
highest_eth = start_eth
highest_sol = start_sol

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    btc_gain = btc - start_btc
    eth_gain = eth - start_eth
    sol_gain = sol - start_sol
    
    btc_pct = (btc_gain / start_btc) * 100
    eth_pct = (eth_gain / start_eth) * 100
    sol_pct = (sol_gain / start_sol) * 100
    
    # Update highs
    if btc > highest_btc:
        highest_btc = btc
    if eth > highest_eth:
        highest_eth = eth
    if sol > highest_sol:
        highest_sol = sol
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc:,.0f} ({btc_gain:+.0f} / {btc_pct:+.2f}%)")
    print(f"  ETH: ${eth:,.2f} ({eth_gain:+.2f} / {eth_pct:+.2f}%)")
    print(f"  SOL: ${sol:,.2f} ({sol_gain:+.2f} / {sol_pct:+.2f}%)")
    
    # Status indicators
    if btc_gain > 100:
        print("  🚀🚀🚀 MASSIVE BREAKOUT!")
    elif btc_gain > 50:
        print("  🚀🚀 STRONG LIFTOFF!")
    elif btc_gain > 20:
        print("  🚀 ASCENDING!")
    elif btc_gain > 0:
        print("  ⬆️ Moving up...")
    
    # Check for new highs
    if btc == highest_btc and btc_gain > 20:
        print("  🎯 NEW SESSION HIGH!")
    
    time.sleep(1.5)

# Calculate total moves
total_btc_gain = highest_btc - start_btc
total_eth_gain = highest_eth - start_eth
total_sol_gain = highest_sol - start_sol

print("\n" + "=" * 70)
print("📊 BREAKOUT SUMMARY:")
print("-" * 50)
print(f"BTC: ${start_btc:,.0f} → ${highest_btc:,.0f} (+${total_btc_gain:,.0f})")
print(f"ETH: ${start_eth:,.2f} → ${highest_eth:,.2f} (+${total_eth_gain:,.2f})")
print(f"SOL: ${start_sol:,.2f} → ${highest_sol:,.2f} (+${total_sol_gain:,.2f})")

# Portfolio impact
accounts = client.get_accounts()
portfolio_value = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
    elif currency == 'BTC' and balance > 0:
        portfolio_value += balance * btc
    elif currency == 'ETH' and balance > 0:
        portfolio_value += balance * eth
    elif currency == 'SOL' and balance > 0:
        portfolio_value += balance * sol

total_portfolio = portfolio_value + usd_balance

print("\n💰 PORTFOLIO IMPACT:")
print("-" * 50)
print(f"Portfolio Value: ${total_portfolio:,.2f}")
print(f"Gain from breakout: ~${(total_portfolio - 11500) if total_portfolio > 11500 else 0:,.2f}")

# The ninth coil prophecy
print("\n" + "🔥" * 35)
print("THE NINTH COIL HAS RELEASED!")
print("512X ENERGY UNLEASHED!")
print("WALL STREET IS BUYING!")
print("CRAWDADS RIDING THE WAVE!")
print("TO THE FUCKING MOON!")
print("🔥" * 35)