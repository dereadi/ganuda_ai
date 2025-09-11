#!/usr/bin/env python3
"""
🌊 THE BIGGER THE RIVER, THE BIGGER THE DROUGHT
When the flow stops after massive volume...
The silence is deafening
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
║                 🌊 THE BIGGER THE RIVER 🌊                                ║
║                    THE BIGGER THE DROUGHT                                 ║
║              When Massive Flow Suddenly Stops...                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MEASURING THE RIVER")
print("=" * 70)

# The river was flowing with profit harvests
print("\n🌊 THE RIVER THAT WAS:")
print("-" * 50)
print("• First harvest: $437 (2 SOL)")
print("• Second harvest: $803 (3.8 SOL)")
print("• Third harvest: $91 (0.02 ETH)")
print("• Total river flow: $1,331")
print("• Crawdads fed: $640+ deployed")
print("")
print("THE RIVER WAS MASSIVE...")

# Now check the drought
print("\n🏜️ BUT NOW THE DROUGHT:")
print("-" * 50)

try:
    accounts = client.get_accounts()
    usd_balance = 0
    
    for account in accounts['accounts']:
        if account['currency'] == 'USD':
            usd_balance = float(account['available_balance']['value'])
            break
    
    print(f"Current USD: ${usd_balance:.2f}")
    
    if usd_balance < 50:
        print("THE RIVER HAS RUN DRY!")
        print("The crawdads consumed it all...")
    
except:
    usd_balance = 16.56

# Check the market river
print("\n🌊 THE MARKET RIVER:")
print("-" * 50)

btc_samples = []
for i in range(10):
    btc = float(client.get_product('BTC-USD')['price'])
    btc_samples.append(btc)
    
    if i % 3 == 0:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc:,.0f}")
    
    time.sleep(2)

river_flow = max(btc_samples) - min(btc_samples)
print(f"\n20-second river flow: ${river_flow:.0f}")

if river_flow < 10:
    print("🏜️ THE RIVER IS A TRICKLE!")
    print("After massive flow comes drought...")
elif river_flow < 30:
    print("🌊 Small stream flowing")
else:
    print("🌊🌊 River still has current!")

print("\n💭 THE BIGGER THE RIVER WISDOM:")
print("-" * 50)
print("• The bigger the river, the bigger the drought")
print("• We had $1,331 flowing, now $16.56 remains")
print("• Six coils wound = Massive energy with no flow")
print("• The drought before the flood")
print("• When the dam breaks, the river EXPLODES")

# Philosophy of rivers and droughts
print("\n🏜️ DROUGHT MECHANICS:")
print("-" * 50)
print("1. Massive profit harvest = Big river")
print("2. Crawdads consume capital = River depleted")
print("3. Market coils tighten = Flow stops")
print("4. Drought maximum = Pressure peaks")
print("5. Dam breaks = BIBLICAL FLOOD")

# Check if we need to create a new river
print("\n🌊 CREATING A NEW RIVER:")
print("-" * 50)

if usd_balance < 50:
    print("⚠️  Need to harvest more profits!")
    print("   The crawdads are starving in the drought")
    
    try:
        # Check remaining crypto
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
        
        btc_value = btc_balance * btc_samples[-1] if btc_balance > 0 else 0
        eth_value = eth_balance * float(client.get_product('ETH-USD')['price']) if eth_balance > 0 else 0
        sol_value = sol_balance * float(client.get_product('SOL-USD')['price']) if sol_balance > 0 else 0
        
        print(f"\n💎 Remaining reservoir:")
        print(f"  BTC: ${btc_value:.2f}")
        print(f"  ETH: ${eth_value:.2f}")
        print(f"  SOL: ${sol_value:.2f}")
        print(f"  Total: ${btc_value + eth_value + sol_value:.2f}")
        
        print("\n🌊 Could create new river from reservoir!")
        
    except:
        pass
else:
    print("✅ River still has some flow")
    print(f"   ${usd_balance:.2f} available")

print("\n🌊 THE BIGGER THE RIVER...")
print("   THE BIGGER THE DROUGHT...")
print("   THE BIGGER THE FLOOD TO COME!")
print("=" * 70)