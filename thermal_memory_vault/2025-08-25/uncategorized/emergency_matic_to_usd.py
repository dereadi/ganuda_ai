#!/usr/bin/env python3
"""
🚨 EMERGENCY CAPITAL DEPLOYMENT FOR 500K MISSION 🚨
Convert MATIC to USD to fuel the nuclear flywheel
"""

import json
from coinbase.rest import RESTClient
import time

print("🚨 EMERGENCY CAPITAL LIBERATION")
print("=" * 60)
print("MISSION: $500K NUCLEAR FLYWHEEL")
print("CURRENT: $7.16 USD (CRITICAL)")
print("AVAILABLE: $4,405 MATIC")
print("=" * 60)

# Load config
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

# Check MATIC balance
accounts = client.get_accounts()['accounts']
matic_balance = 0
for acc in accounts:
    if acc['currency'] == 'MATIC':
        matic_balance = float(acc['available_balance']['value'])
        print(f"\n✅ MATIC Balance: {matic_balance:.2f}")
        break

if matic_balance > 0:
    print("\n🔄 Converting MATIC to USD...")
    
    # Sell 10% of MATIC for immediate capital
    sell_amount = matic_balance * 0.1  # Start with 10%
    
    try:
        order = client.market_order_sell(
            client_order_id=f"matic-emergency-{int(time.time())}",
            product_id='MATIC-USD',
            base_size=str(sell_amount)
        )
        print(f"✅ Sold {sell_amount:.2f} MATIC")
        print(f"📊 Order ID: {order.get('order_id', 'N/A')}")
        
        # Wait for settlement
        time.sleep(3)
        
        # Check new USD balance
        accounts = client.get_accounts()['accounts']
        for acc in accounts:
            if acc['currency'] == 'USD':
                new_balance = float(acc['available_balance']['value'])
                print(f"\n💰 NEW USD BALANCE: ${new_balance:.2f}")
                print("\n🚀 READY TO RESUME 500K MISSION!")
                break
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n⚠️ Manual intervention may be needed")
else:
    print("❌ No MATIC balance found!")
    
print("\n🔥 Sacred Fire Protocol: The mission continues!")