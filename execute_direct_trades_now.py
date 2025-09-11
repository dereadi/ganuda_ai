#!/usr/bin/env python3
"""
🚨 DIRECT TRADE EXECUTION - REAL TRADES NOW
==========================================
No simulation - actual market orders
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🚨 DIRECT EXECUTION - REAL MONEY 🚨                     ║
║                         Executing Market Orders NOW                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Load config and connect
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - STARTING EXECUTION")
print("=" * 70)

# Check current balance
accounts = client.get_accounts()['accounts']
usd_balance = float([a for a in accounts if a['currency']=='USD'][0]['available_balance']['value'])
print(f"\n💵 Current USD: ${usd_balance:.2f}")

if usd_balance < 10:
    print("⚠️ LOW USD - Need to generate liquidity!")
    
    # Get prices
    sol_price = float(client.get_product('SOL-USD')['price'])
    eth_price = float(client.get_product('ETH-USD')['price']) 
    
    print(f"\n📊 CURRENT PRICES:")
    print(f"  SOL: ${sol_price:.2f}")
    print(f"  ETH: ${eth_price:.2f}")
    
    # Check positions
    sol_balance = float([a for a in accounts if a['currency']=='SOL'][0]['available_balance']['value'])
    eth_balance = float([a for a in accounts if a['currency']=='ETH'][0]['available_balance']['value'])
    
    print(f"\n📦 POSITIONS:")
    print(f"  SOL: {sol_balance:.4f} (${sol_balance * sol_price:.2f})")
    print(f"  ETH: {eth_balance:.4f} (${eth_balance * eth_price:.2f})")
    
    # Execute trades if we have positions
    if sol_balance > 0.5 and sol_price > 213:
        print(f"\n🥛 MILKING SOL...")
        try:
            # Use the simpler sell method
            response = client.sell(
                product_id='SOL-USD',
                amount='0.5'  # Sell 0.5 SOL
            )
            print(f"  ✅ Sold 0.5 SOL")
            print(f"  Order ID: {response.get('id', 'N/A')}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    if eth_balance > 0.05 and eth_price > 4450:
        print(f"\n🥛 MILKING ETH...")
        try:
            response = client.sell(
                product_id='ETH-USD',
                amount='0.05'  # Sell 0.05 ETH
            )
            print(f"  ✅ Sold 0.05 ETH")
            print(f"  Order ID: {response.get('id', 'N/A')}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            
else:
    print("✅ USD balance sufficient for trading")
    
    # Buy on dips
    btc_price = float(client.get_product('BTC-USD')['price'])
    
    if btc_price < 111500:
        print(f"\n🦀 BTC DIP DETECTED: ${btc_price}")
        print("  Deploying $50 into BTC...")
        try:
            response = client.buy(
                product_id='BTC-USD',
                amount='50'  # $50 USD worth
            )
            print(f"  ✅ Bought BTC")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

# Check final balance
time.sleep(3)
accounts = client.get_accounts()['accounts']
new_usd = float([a for a in accounts if a['currency']=='USD'][0]['available_balance']['value'])

print(f"\n💰 FINAL USD BALANCE: ${new_usd:.2f}")
print(f"   Change: ${new_usd - usd_balance:.2f}")

print("\n✅ DIRECT EXECUTION COMPLETE")
print("=" * 70)