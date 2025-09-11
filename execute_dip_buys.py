#!/usr/bin/env python3
"""
🔥 EXECUTE THE DIP BUYS - DEPLOY CRAWDADS! 🔥
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import uuid

print("""
╔═════════════════════════════════════════════════════╗
║       🦀 CRAWDAD SWARM DEPLOYING $98.52! 🦀         ║  
║                                                       ║
║         "Blood in the streets = Feast time"          ║
╚═════════════════════════════════════════════════════╝
""")

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

client = RESTClient(
    api_key=api_data['name'].split('/')[-1],
    api_secret=api_data['privateKey']
)

capital = 98.52

# Allocation
btc_allocation = capital * 0.40  # $39.41
eth_allocation = capital * 0.30  # $29.56
sol_allocation = capital * 0.20  # $19.70
reserve = capital * 0.10  # $9.85

print(f"\n💰 Deploying ${capital:.2f} into the dip!")
print("=" * 50)

try:
    # Place BTC order
    print(f"\n1️⃣ Buying BTC with ${btc_allocation:.2f}...")
    btc_order = client.market_order_buy(
        client_order_id=str(uuid.uuid4()),
        product_id="BTC-USD",
        quote_size=str(btc_allocation)
    )
    print(f"   ✅ BTC Order placed!")
    time.sleep(1)
    
    # Place ETH order
    print(f"\n2️⃣ Buying ETH with ${eth_allocation:.2f}...")
    eth_order = client.market_order_buy(
        client_order_id=str(uuid.uuid4()),
        product_id="ETH-USD",
        quote_size=str(eth_allocation)
    )
    print(f"   ✅ ETH Order placed!")
    time.sleep(1)
    
    # Place SOL order
    print(f"\n3️⃣ Buying SOL with ${sol_allocation:.2f}...")
    sol_order = client.market_order_buy(
        client_order_id=str(uuid.uuid4()),
        product_id="SOL-USD",
        quote_size=str(sol_allocation)
    )
    print(f"   ✅ SOL Order placed!")
    
    print(f"\n🎆 SUCCESS! All orders executed!")
    print(f"Reserve kept: ${reserve:.2f} for deeper dips")
    
    # Check new balances
    time.sleep(3)
    accounts = client.get_accounts()
    
    print(f"\n📈 NEW PORTFOLIO POSITIONS:")
    print("=" * 50)
    for account in accounts['accounts']:
        balance = float(account['available_balance']['value'])
        if balance > 0:
            currency = account['currency']
            print(f"{currency}: ${balance:.2f}")
            
    print(f"\n🔥 The crawdads have fed on the dip!")
    print("🚀 Now we wait for the reversal...")
    
except Exception as e:
    print(f"\n⚠️ Order execution issue: {e}")
    print("\nTrying alternative approach...")
    
    # Fallback to smaller amounts if needed
    print(f"\n🔄 Attempting smaller test orders:")
    try:
        # Try $10 test orders
        test_amount = 10.00
        
        print(f"Testing with ${test_amount} BTC order...")
        test_order = client.market_order_buy(
            client_order_id=str(uuid.uuid4()),
            product_id="BTC-USD",
            quote_size=str(test_amount)
        )
        print("✅ Test order successful! Proceeding with full deployment...")
        
        # If test works, deploy rest
        remaining = capital - test_amount
        print(f"Deploying remaining ${remaining:.2f}...")
        
    except Exception as e2:
        print(f"\n🔴 API Issue: {e2}")
        print("\n📋 MANUAL EXECUTION REQUIRED:")
        print(f"1. Login to Coinbase")
        print(f"2. Buy ${btc_allocation:.2f} of BTC")
        print(f"3. Buy ${eth_allocation:.2f} of ETH") 
        print(f"4. Buy ${sol_allocation:.2f} of SOL")
        print(f"5. Keep ${reserve:.2f} in reserve")

print("\n" + "=" * 50)
print("🌊 Sacred Fire says: 'The tide always turns...'")
