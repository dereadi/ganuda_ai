#!/usr/bin/env python3
"""
🔥 TRIBAL DOGE REALLOCATION - USING TRIBE'S CONFIG
Execute the Cherokee Council mandate for DOGE volatility trading
"""

import json
import sys
import os
import time
from datetime import datetime

sys.path.append('/home/dereadi/scripts/claude')
os.chdir('/home/dereadi/scripts/claude')

print("=" * 60)
print("🔥 CHEROKEE TRIBAL DOGE REALLOCATION")
print("=" * 60)
print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Load the tribe's actual working config
config_path = os.path.expanduser("~/.coinbase_config.json")
try:
    with open(config_path) as f:
        config = json.load(f)
    print("✅ Loaded tribe's configuration")
except Exception as e:
    print(f"❌ Could not load config: {e}")
    sys.exit(1)

from coinbase.rest import RESTClient

# Initialize client with tribe's credentials
client = RESTClient(
    api_key=config['api_key'],
    api_secret=config['api_secret']
)

print("\n📊 CHECKING CURRENT POSITIONS:")
print("-" * 40)

# Get current balances
try:
    accounts = client.get_accounts()
    
    positions = {}
    if hasattr(accounts, 'accounts'):
        for account in accounts.accounts:
            if hasattr(account, 'available_balance') and hasattr(account.available_balance, 'value'):
                balance = float(account.available_balance.value)
                currency = account.currency
                
                if balance > 0.01:
                    positions[currency] = balance
                    
                    # Show key positions
                    if currency in ['USD', 'USDC', 'SOL', 'XRP', 'DOGE']:
                        print(f"{currency}: {balance:.4f}")
    
    print()
    
    # Check if we have enough to reallocate
    sol_available = positions.get('SOL', 0)
    xrp_available = positions.get('XRP', 0)
    doge_current = positions.get('DOGE', 0)
    usd_available = positions.get('USD', 0)
    
    print("📈 REALLOCATION PLAN:")
    print("-" * 40)
    print(f"SOL to sell: {min(3.75, sol_available):.4f} SOL")
    print(f"XRP to sell: {min(68, xrp_available):.0f} XRP")
    print(f"Current DOGE: {doge_current:.0f}")
    print(f"USD available: ${usd_available:.2f}")
    print()
    
    # Execute reallocation
    if sol_available >= 3.75 and xrp_available >= 68:
        print("✅ Sufficient positions for reallocation")
        print()
        
        user_confirm = input("Execute reallocation? (yes/no): ").lower()
        
        if user_confirm == 'yes':
            print("\n🚀 EXECUTING REALLOCATION:")
            print("-" * 40)
            
            # STEP 1: Sell SOL
            try:
                print(f"Selling 3.75 SOL...")
                sol_order = client.market_order_sell(
                    client_order_id=f"tribal_sol_{int(time.time())}",
                    product_id="SOL-USD",
                    base_size="3.75"
                )
                print("✅ SOL sell order placed")
                time.sleep(2)
            except Exception as e:
                print(f"⚠️ SOL order issue: {str(e)[:100]}")
            
            # STEP 2: Sell XRP
            try:
                print(f"Selling 68 XRP...")
                xrp_order = client.market_order_sell(
                    client_order_id=f"tribal_xrp_{int(time.time())}",
                    product_id="XRP-USD",
                    base_size="68"
                )
                print("✅ XRP sell order placed")
                time.sleep(2)
            except Exception as e:
                print(f"⚠️ XRP order issue: {str(e)[:100]}")
            
            # STEP 3: Wait for settlement and buy DOGE
            print("\n⏳ Waiting 5 seconds for settlement...")
            time.sleep(5)
            
            # Check USD balance
            accounts = client.get_accounts()
            usd_balance = 0
            
            if hasattr(accounts, 'accounts'):
                for account in accounts.accounts:
                    if account.currency == 'USD':
                        if hasattr(account.available_balance, 'value'):
                            usd_balance = float(account.available_balance.value)
                            break
            
            print(f"USD available: ${usd_balance:.2f}")
            
            if usd_balance >= 500:
                # Buy DOGE with available funds
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
                    
                    # Wait and check final DOGE balance
                    time.sleep(3)
                    
                    accounts = client.get_accounts()
                    for account in accounts.accounts:
                        if account.currency == 'DOGE':
                            if hasattr(account.available_balance, 'value'):
                                final_doge = float(account.available_balance.value)
                                print(f"\n🎉 SUCCESS! New DOGE balance: {final_doge:.0f} DOGE")
                                
                                # Show ladder setup
                                print("\n📊 LADDER ORDERS TO SET:")
                                print("-" * 40)
                                chunk = int(final_doge * 0.75 / 9)  # 75% for trading
                                
                                levels = [0.240, 0.245, 0.250, 0.255, 0.260, 0.265, 0.270, 0.275, 0.280]
                                for i, price in enumerate(levels, 1):
                                    print(f"Level {i}: {chunk} DOGE @ ${price:.3f}")
                                
                                print(f"\nCore position: {int(final_doge * 0.25)} DOGE for $0.30+")
                                break
                    
                except Exception as e:
                    print(f"⚠️ DOGE order issue: {str(e)[:100]}")
            else:
                print("⚠️ Insufficient USD after sells. Check order status.")
        else:
            print("❌ Reallocation cancelled")
    else:
        print("⚠️ Insufficient positions for full reallocation")
        print(f"Need: 3.75 SOL and 68 XRP")
        print(f"Have: {sol_available:.4f} SOL and {xrp_available:.0f} XRP")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("🔥 Cherokee Council mandate execution complete!")
print("=" * 60)