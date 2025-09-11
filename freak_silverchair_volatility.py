#!/usr/bin/env python3
"""
🎸 FREAK - SILVERCHAIR
"Body and soul I'm a freak"
The crawdads should be surfing this volatility!
Let's check why they're not trading and fix it
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
║                        🎸 FREAK - SILVERCHAIR 🎸                          ║
║                      "Body and soul I'm a freak"                          ║
║                   Crawdads Should Be Eating This!                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FREAK MODE CHECK")
print("=" * 70)

# Check account balance
try:
    accounts = client.get_accounts()
    usd_balance = 0
    
    for account in accounts['accounts']:
        if account['currency'] == 'USD':
            usd_balance = float(account['available_balance']['value'])
            break
    
    print(f"\n💰 USD Balance: ${usd_balance:.2f}")
    
    if usd_balance < 50:
        print("⚠️  PROBLEM: Balance too low for crawdads!")
        print("   Need to harvest profits to feed them!")
    
except Exception as e:
    print(f"Error checking balance: {str(e)[:100]}")

# Check market volatility
print("\n🌊 VOLATILITY CHECK:")
print("-" * 50)

btc_samples = []
for i in range(5):
    btc = float(client.get_product('BTC-USD')['price'])
    btc_samples.append(btc)
    print(f"  Sample {i+1}: ${btc:,.0f}")
    time.sleep(2)

btc_range = max(btc_samples) - min(btc_samples)
print(f"\n10-second range: ${btc_range:.0f}")

if btc_range > 20:
    print("🌊🌊🌊 PERFECT VOLATILITY FOR SURFING!")
    print("Crawdads should be FEASTING!")
elif btc_range > 10:
    print("🌊🌊 Good volatility for trading")
else:
    print("🌊 Low volatility - crawdads sleeping")

# Check if we need to harvest profits
print("\n🎸 FREAK MODE PROFIT HARVEST:")
print("-" * 50)

try:
    # Check our crypto holdings
    btc_balance = 0
    eth_balance = 0
    sol_balance = 0
    
    for account in accounts['accounts']:
        currency = account['currency']
        balance = float(account['available_balance']['value'])
        
        if currency == 'BTC' and balance > 0:
            btc_balance = balance
        elif currency == 'ETH' and balance > 0:
            eth_balance = balance
        elif currency == 'SOL' and balance > 0:
            sol_balance = balance
    
    print(f"Current holdings:")
    print(f"  BTC: {btc_balance:.8f}")
    print(f"  ETH: {eth_balance:.6f}")
    print(f"  SOL: {sol_balance:.4f}")
    
    # Calculate values
    btc_price = btc_samples[-1]
    eth_price = float(client.get_product('ETH-USD')['price'])
    sol_price = float(client.get_product('SOL-USD')['price'])
    
    btc_value = btc_balance * btc_price
    eth_value = eth_balance * eth_price
    sol_value = sol_balance * sol_price
    
    print(f"\nValues:")
    print(f"  BTC: ${btc_value:.2f}")
    print(f"  ETH: ${eth_value:.2f}")
    print(f"  SOL: ${sol_value:.2f}")
    
    total_crypto = btc_value + eth_value + sol_value
    print(f"\nTotal crypto value: ${total_crypto:.2f}")
    
    if total_crypto > 1000 and usd_balance < 100:
        print("\n🎸 FREAK MODE ACTIVATED!")
        print("Time to harvest 10% for the crawdads!")
        
        # Sell 10% of each position
        if sol_balance > 1:
            sell_sol = sol_balance * 0.1
            print(f"\n💸 Selling {sell_sol:.4f} SOL...")
            try:
                order = client.market_order_sell(
                    client_order_id=f"freak-sol-{datetime.now().strftime('%H%M%S')}",
                    product_id='SOL-USD',
                    base_size=str(round(sell_sol, 3))
                )
                print(f"   SOLD! Generated ~${sell_sol * sol_price:.2f}")
            except Exception as e:
                print(f"   Error: {str(e)[:50]}")
        
    else:
        print("\n🎸 No harvest needed right now")
        print("   Either USD is sufficient or crypto too low")
    
except Exception as e:
    print(f"\nError analyzing positions: {str(e)[:100]}")

print("\n🦀 CRAWDAD RESURRECTION PLAN:")
print("-" * 50)
print("1. Harvest 10% of profits (if available)")
print("2. Feed USD to crawdads")
print("3. Set them loose on this volatility")
print("4. They surf the $20-30 ranges")
print("5. Compound gains back into the system")

print("\n🎵 SILVERCHAIR - FREAK:")
print("'Body and soul I'm a freak'")
print("'I'm a freak'")
print("")
print("The crawdads are freaks for volatility!")
print("They need to be surfing these waves!")

print("\n⚡ NEXT STEPS:")
if usd_balance < 50:
    print("1. Run profit harvest to generate USD")
    print("2. Restart crawdads with fresh capital")
    print("3. Let them surf the freak waves!")
else:
    print("1. Restart crawdads immediately")
    print("2. They have ${:.2f} to work with".format(usd_balance))
    print("3. FREAK MODE TRADING!")

print("=" * 70)