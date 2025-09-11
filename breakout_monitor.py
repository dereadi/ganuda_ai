#!/usr/bin/env python3
"""
🚀 LIVE BREAKOUT MONITOR
The coil has released - ride the wave!
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
║                        🚀 BREAKOUT IN PROGRESS 🚀                         ║
║                    ETH & BTC BREAKING UP - COIL RELEASED!                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Starting prices (approximate breakout point)
start_btc = 111415  # Where it was stuck
start_eth = 4512
start_sol = 206.45

print(f"Breakout from: BTC ${start_btc:,} | ETH ${start_eth} | SOL ${start_sol}")
print("=" * 70)

# Track the breakout
print("\n📊 TRACKING BREAKOUT:")
print("-" * 40)

highest_btc = start_btc
highest_eth = start_eth
highest_sol = start_sol

for i in range(20):
    # Get current prices
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    # Track highs
    if btc > highest_btc:
        highest_btc = btc
    if eth > highest_eth:
        highest_eth = eth
    if sol > highest_sol:
        highest_sol = sol
    
    # Calculate moves from stuck point
    btc_move = btc - start_btc
    eth_move = eth - start_eth
    sol_move = sol - start_sol
    
    btc_pct = (btc_move / start_btc) * 100
    eth_pct = (eth_move / start_eth) * 100
    sol_pct = (sol_move / start_sol) * 100
    
    print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
    print(f"  BTC: ${btc:,.0f} ({btc_pct:+.2f}%) ", end="")
    if btc_move > 50:
        print("🚀🚀🚀")
    elif btc_move > 20:
        print("🚀🚀")
    elif btc_move > 0:
        print("🚀")
    else:
        print("📊")
    
    print(f"  ETH: ${eth:.0f} ({eth_pct:+.2f}%) ", end="")
    if eth_move > 3:
        print("🚀🚀")
    elif eth_move > 1:
        print("🚀")
    else:
        print("📊")
    
    print(f"  SOL: ${sol:.2f} ({sol_pct:+.2f}%) ", end="")
    if sol_move > 0.5:
        print("🚀🚀")
    elif sol_move > 0.2:
        print("🚀")
    else:
        print("📊")
    
    # Portfolio impact
    if i % 5 == 0:
        accounts = client.get_accounts()['accounts']
        total = 0
        for acc in accounts:
            bal = float(acc['available_balance']['value'])
            if acc['currency'] == 'USD':
                total += bal
            elif acc['currency'] == 'BTC':
                total += bal * btc
            elif acc['currency'] == 'ETH':
                total += bal * eth
            elif acc['currency'] == 'SOL':
                total += bal * sol
            elif acc['currency'] == 'AVAX':
                avax_price = float(client.get_product('AVAX-USD')['price'])
                total += bal * avax_price
            elif acc['currency'] == 'MATIC':
                matic_price = float(client.get_product('MATIC-USD')['price'])
                total += bal * matic_price
        
        print(f"\n  💰 PORTFOLIO VALUE: ${total:,.0f}")
    
    time.sleep(10)

print("\n" + "=" * 70)
print("🚀 BREAKOUT SUMMARY:")
print(f"  BTC High: ${highest_btc:,.0f} (+${highest_btc - start_btc:.0f})")
print(f"  ETH High: ${highest_eth:.0f} (+${highest_eth - start_eth:.0f})")
print(f"  SOL High: ${highest_sol:.2f} (+${highest_sol - start_sol:.2f})")
print("\nThe 0.000% coil has been released!")
print("Asia took one look at that squeeze and broke it!")
print("=" * 70)