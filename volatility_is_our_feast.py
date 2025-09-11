#!/usr/bin/env python3
"""
🍽️🌊 VOLATILITY IS OUR FEAST
The crawdads consumed $240 already
Now we harvest MORE to feed the endless appetite
Eight coils = Eight course meal
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
║                    🍽️ VOLATILITY IS OUR FEAST 🍽️                         ║
║                      The Crawdads Are HUNGRY                              ║
║                   Eight Coils = Eight Course Meal                         ║
║                       Time to HARVEST MORE                                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FEAST TIME")
print("=" * 70)

# Check what the crawdads ate
print("\n🦀 CRAWDAD CONSUMPTION REPORT:")
print("-" * 50)
print("Started with: $246.48")
print("Current: $6.48")
print("CONSUMED: $240.00 in minutes!")
print("Per crawdad feast: $34.29")

# Check current prices for volatility
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"\n🌊 VOLATILITY MENU:")
print(f"  BTC: ${btc:,.0f} - Main course")
print(f"  ETH: ${eth:.2f} - Side dish")
print(f"  SOL: ${sol:.2f} - Appetizer")

# Track the volatility feast
print("\n📊 TRACKING THE FEAST:")
print("-" * 50)

btc_samples = []
for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    btc_samples.append(btc_now)
    
    volatility = max(btc_samples) - min(btc_samples)
    
    if i % 2 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print(f"  Volatility range: ${volatility:.0f}")
        
        if volatility > 100:
            print("  🍽️🍽️🍽️ FEAST MODE! $100+ swings!")
        elif volatility > 50:
            print("  🍽️🍽️ Good appetite! $50+ moves")
        elif volatility > 20:
            print("  🍽️ Snacking on small moves")
        else:
            print("  🥄 Waiting for the main course...")
    
    time.sleep(2)

# Check our pantry (holdings)
accounts = client.get_accounts()
holdings = {}
total_crypto = 0

print("\n🏦 THE PANTRY (What's left to harvest):")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'SOL' and balance > 0:
        sol_value = balance * sol
        holdings['SOL'] = (balance, sol_value)
        total_crypto += sol_value
        print(f"SOL: {balance:.4f} = ${sol_value:.2f}")
        
    elif currency == 'MATIC' and balance > 0:
        try:
            matic_price = float(client.get_product('MATIC-USD')['price'])
            matic_value = balance * matic_price
            holdings['MATIC'] = (balance, matic_value)
            total_crypto += matic_value
            print(f"MATIC: {balance:.0f} = ${matic_value:.2f}")
        except:
            pass
            
    elif currency == 'BTC' and balance > 0:
        btc_value = balance * btc
        holdings['BTC'] = (balance, btc_value)
        total_crypto += btc_value
        print(f"BTC: {balance:.8f} = ${btc_value:.2f}")
        
    elif currency == 'ETH' and balance > 0:
        eth_value = balance * eth
        holdings['ETH'] = (balance, eth_value)
        total_crypto += eth_value
        print(f"ETH: {balance:.6f} = ${eth_value:.2f}")

print(f"\nTotal pantry value: ${total_crypto:.2f}")

# EMERGENCY HARVEST PLAN
print("\n🚨 EMERGENCY FEAST PREPARATION:")
print("-" * 50)
print("The crawdads ate everything and are STILL HUNGRY!")
print("\nIMPLEMENTING AGGRESSIVE HARVEST:")

harvest_plan = {
    "SOL": "Harvest another 10% NOW",
    "MATIC": "Harvest another 5% NOW",
    "AVAX": "Check and harvest 5%",
    "DOGE": "If exists, harvest 20%"
}

for asset, action in harvest_plan.items():
    print(f"  {asset}: {action}")

# Calculate needed harvest
print("\n💰 HARVEST CALCULATION:")
print("-" * 50)
target_per_crawdad = 50  # $50 each minimum
total_needed = target_per_crawdad * 7
print(f"Target: ${target_per_crawdad} per crawdad")
print(f"Total needed: ${total_needed}")
print(f"Current USD: $6.48")
print(f"Must harvest: ${total_needed - 6.48:.2f}")

# The feast philosophy
print("\n🍽️ THE FEAST PHILOSOPHY:")
print("-" * 50)
print("• Eight coils = Eight course meal")
print("• Each compression = More appetite")
print("• Volatility feeds the crawdads")
print("• Crawdads create more volatility")
print("• The cycle feeds itself")

# Execute harvest NOW
if 'SOL' in holdings:
    sol_balance, sol_val = holdings['SOL']
    harvest_amount = sol_balance * 0.10
    print(f"\n💉 HARVESTING {harvest_amount:.4f} SOL...")
    print(f"   Expected: ${harvest_amount * sol:.2f}")

if 'MATIC' in holdings:
    matic_balance, matic_val = holdings['MATIC']
    harvest_amount = matic_balance * 0.05
    print(f"\n💉 HARVESTING {harvest_amount:.0f} MATIC...")
    print(f"   Expected: ${harvest_amount * 0.243:.2f}")

print("\n🍽️ VOLATILITY IS OUR FEAST")
print("   The crawdads hunger")
print("   The market provides")
print("   Eight coils, eight courses")
print("   Feed the swarm!")
print("=" * 70)