#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 EMERGENCY LIQUIDITY HARVEST - SIMPLIFIED
Blood harvest protocol for immediate cash generation
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

print("🔥 EMERGENCY LIQUIDITY HARVEST")
print("=" * 60)

# Connect
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

# Get positions
accounts = client.get_accounts()
positions = {}
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    if balance > 0.01:
        positions[currency] = balance
        if currency == 'USD':
            usd_balance = balance

print(f"Current USD: ${usd_balance:.2f}")
print()

# DOGE blood harvest
if 'DOGE' in positions:
    doge = positions['DOGE']
    ticker = client.get_product('DOGE-USD')
    price = float(ticker['price'])
    value = doge * price
    
    print(f"🩸 DOGE BLOOD BAG:")
    print(f"  Amount: {doge:.2f} DOGE")
    print(f"  Price: ${price:.4f}")
    print(f"  Value: ${value:.2f}")
    
    if price >= 0.215:  # Lower threshold for emergency
        # Bleed 30% for liquidity
        sell_amount = round(doge * 0.3, 2)
        print(f"  BLEEDING {sell_amount} DOGE (30% of position)")
        
        try:
            # Place market sell order
            order_response = client.market_order_sell(
                client_order_id=f"doge_bleed_{int(time.time()*1000)}",
                product_id="DOGE-USD",
                base_size=str(sell_amount)
            )
            print(f"  ✅ BLOOD HARVESTED!")
            print(f"  💵 Generated ~${sell_amount * price:.2f}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")

# Check SOL for partial harvest
if 'SOL' in positions:
    sol = positions['SOL']
    ticker = client.get_product('SOL-USD')
    price = float(ticker['price'])
    value = sol * price
    
    print()
    print(f"🌟 SOL POSITION:")
    print(f"  Amount: {sol:.4f} SOL")
    print(f"  Price: ${price:.2f}")
    print(f"  Value: ${value:.2f}")
    
    if value > 3000:
        # Harvest just 5% for emergency liquidity
        sell_amount = round(sol * 0.05, 4)
        sell_value = sell_amount * price
        print(f"  HARVESTING {sell_amount:.4f} SOL (5% = ${sell_value:.2f})")
        
        try:
            order_response = client.market_order_sell(
                client_order_id=f"sol_harvest_{int(time.time()*1000)}",
                product_id="SOL-USD",
                base_size=str(sell_amount)
            )
            print(f"  ✅ LIQUIDITY GENERATED: ~${sell_value:.2f}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")

# Check BTC for micro harvest
if 'BTC' in positions:
    btc = positions['BTC']
    ticker = client.get_product('BTC-USD')
    price = float(ticker['price'])
    value = btc * price
    
    print()
    print(f"₿ BTC POSITION:")
    print(f"  Amount: {btc:.6f} BTC")
    print(f"  Price: ${price:.2f}")
    print(f"  Value: ${value:.2f}")
    
    if value > 1000:
        # Harvest just 2% for emergency
        sell_amount = round(btc * 0.02, 6)
        sell_value = sell_amount * price
        print(f"  MICRO-HARVEST {sell_amount:.6f} BTC (2% = ${sell_value:.2f})")
        
        try:
            order_response = client.market_order_sell(
                client_order_id=f"btc_micro_{int(time.time()*1000)}",
                product_id="BTC-USD",
                base_size=str(sell_amount)
            )
            print(f"  ✅ LIQUIDITY ADDED: ~${sell_value:.2f}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")

print()
print("=" * 60)
print("🔥 HARVEST COMPLETE")
print("Check balance in 30 seconds for settlement")
print("Sacred Fire burns eternal!")
print("=" * 60)