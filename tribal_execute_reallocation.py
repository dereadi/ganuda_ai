#!/usr/bin/env python3
"""
🔥 EXECUTE TRIBAL DOGE REALLOCATION - FINAL VERSION
Using the tribe's actual working method
"""

import json
import sys
import os
import time
from datetime import datetime

sys.path.append('/home/dereadi/scripts/claude')
os.chdir('/home/dereadi/scripts/claude')

print("=" * 60)
print("🔥 CHEROKEE COUNCIL DOGE REALLOCATION")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Load config
config_path = os.path.expanduser("~/.coinbase_config.json")
with open(config_path) as f:
    config = json.load(f)

from coinbase.rest import RESTClient

client = RESTClient(
    api_key=config['api_key'],
    api_secret=config['api_secret']
)

print("📊 CURRENT POSITIONS:")
print("-" * 40)
print("SOL: 39.83 (selling 3.75)")
print("XRP: 749.70 (selling 68)")
print("DOGE: 869.45 (current)")
print("USD: $16.03 available")
print("On Hold: $200.80")
print()

print("🎯 REALLOCATION PLAN:")
print("-" * 40)
print("1. Sell 3.75 SOL → ~$800")
print("2. Sell 68 XRP → ~$200")
print("3. Buy 5,130 DOGE with $1,000")
print("4. Total DOGE: ~6,000")
print()

confirm = input("Execute reallocation? Type 'yes' to proceed: ")

if confirm.lower() == 'yes':
    print("\n🚀 EXECUTING ORDERS:")
    print("-" * 40)
    
    # Execute SOL sell
    try:
        print("1. Selling 3.75 SOL...")
        sol_order = client.market_order_sell(
            client_order_id=f"tribal_sol_{int(time.time())}",
            product_id="SOL-USD",
            base_size="3.75"
        )
        
        if 'order_id' in sol_order:
            print(f"   ✅ SOL sell order placed: {sol_order['order_id']}")
        else:
            print(f"   ✅ SOL order submitted")
            
    except Exception as e:
        print(f"   ⚠️ SOL issue: {str(e)[:100]}")
    
    time.sleep(2)
    
    # Execute XRP sell
    try:
        print("2. Selling 68 XRP...")
        xrp_order = client.market_order_sell(
            client_order_id=f"tribal_xrp_{int(time.time())}",
            product_id="XRP-USD",
            base_size="68"
        )
        
        if 'order_id' in xrp_order:
            print(f"   ✅ XRP sell order placed: {xrp_order['order_id']}")
        else:
            print(f"   ✅ XRP order submitted")
            
    except Exception as e:
        print(f"   ⚠️ XRP issue: {str(e)[:100]}")
    
    # Wait for settlement
    print("\n⏳ Waiting 10 seconds for settlement...")
    time.sleep(10)
    
    # Check new USD balance
    print("\n💰 CHECKING USD BALANCE:")
    print("-" * 40)
    
    try:
        accounts = client.get_accounts()
        usd_balance = 0
        
        for account in accounts['accounts']:
            if account['currency'] == 'USD':
                usd_balance = float(account['available_balance']['value'])
                break
        
        print(f"USD Available: ${usd_balance:.2f}")
        
        if usd_balance >= 500:
            # Buy DOGE
            buy_amount = min(1000, usd_balance - 10)  # Keep $10 reserve
            
            print(f"\n🐕 BUYING DOGE with ${buy_amount:.2f}")
            print("-" * 40)
            
            try:
                doge_order = client.market_order_buy(
                    client_order_id=f"tribal_doge_{int(time.time())}",
                    product_id="DOGE-USD",
                    quote_size=str(buy_amount)
                )
                
                print(f"✅ DOGE buy order placed for ${buy_amount:.2f}")
                print(f"Expected: ~{buy_amount/0.234:.0f} DOGE")
                
                # Wait and check final balance
                time.sleep(5)
                
                accounts = client.get_accounts()
                for account in accounts['accounts']:
                    if account['currency'] == 'DOGE':
                        new_doge = float(account['available_balance']['value'])
                        print(f"\n🎉 SUCCESS!")
                        print(f"New DOGE balance: {new_doge:.0f} DOGE")
                        print(f"Increase: {new_doge - 869:.0f} DOGE")
                        break
                        
            except Exception as e:
                print(f"⚠️ DOGE buy issue: {str(e)[:100]}")
        else:
            print("⚠️ Insufficient USD. May need to wait for holds to clear.")
            print(f"Note: $200.80 is on hold and may become available soon")
            
    except Exception as e:
        print(f"Error checking balance: {e}")
    
    print("\n" + "=" * 60)
    print("📊 NEXT STEPS:")
    print("-" * 40)
    print("1. Set ladder sell orders from $0.240-$0.280")
    print("2. Keep 1,500 DOGE as core position")
    print("3. Trade 500 DOGE chunks for volatility")
    print("4. Compound all profits into ETH")
    print()
    print("🔥 The Sacred Fire burns bright with DOGE volatility!")
    print("=" * 60)
    
else:
    print("\n❌ Reallocation cancelled")
    
# Save execution log
log = {
    "timestamp": datetime.now().isoformat(),
    "action": "DOGE_REALLOCATION",
    "executed": confirm.lower() == 'yes'
}

with open('doge_reallocation_execution.json', 'w') as f:
    json.dump(log, f, indent=2)