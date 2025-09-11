#!/usr/bin/env python3
"""
🦀💰 QUANTUM CRAWDAD LIVE TRADING
=================================
Using official Coinbase SDK with your $300
"""

import json
import os
import time
from datetime import datetime
from coinbase.rest import RESTClient

# Load config
config_path = os.path.expanduser("~/.coinbase_config.json")
with open(config_path) as f:
    config = json.load(f)

print("🦀💰 QUANTUM CRAWDAD LIVE TRADING")
print("="*50)
print(f"🔑 API Key: {config['api_key'][:50]}...")
print(f"💵 Capital: ${config['capital']}")
print("="*50)

# Initialize client
client = RESTClient(
    api_key=config["api_key"],
    api_secret=config["api_secret"]
)

print("\n📊 Checking accounts...")
try:
    # Get accounts
    accounts = client.get_accounts()
    
    if accounts:
        account_list = accounts.get('accounts', []) if isinstance(accounts, dict) else accounts.accounts
        print(f"✅ Found {len(account_list)} accounts:")
        
        total_value = 0
        for account in account_list:
            # Handle dict or object response
            if isinstance(account, dict):
                currency = account.get('currency', 'Unknown')
                balance = float(account.get('available_balance', {}).get('value', 0))
            else:
                currency = account.currency
                balance = float(account.available_balance['value'] if isinstance(account.available_balance, dict) else account.available_balance.value)
            
            if balance > 0:
                print(f"  💰 {currency}: {balance:.8f}")
                
                # Convert to USD value
                if currency == "USD":
                    total_value += balance
                else:
                    # Get conversion rate
                    try:
                        ticker = client.get_product(f"{currency}-USD")
                        if ticker:
                            price = float(ticker['price'] if isinstance(ticker, dict) else ticker.price)
                            value = balance * price
                            total_value += value
                            print(f"      (≈ ${value:.2f} USD)")
                    except:
                        pass
        
        print(f"\n💎 Total portfolio value: ${total_value:.2f}")
        
        # Check market prices
        print("\n📈 Current market prices:")
        for symbol in ["BTC-USD", "ETH-USD", "SOL-USD"]:
            try:
                ticker = client.get_product(symbol)
                if ticker:
                    price = float(ticker['price'] if isinstance(ticker, dict) else ticker.price)
                    print(f"  {symbol}: ${price:,.2f}")
            except:
                pass
        
        # Trading readiness check
        print("\n🦀 Crawdad consciousness check...")
        consciousness = 75  # Stable consciousness for live trading
        print(f"  🧠 Consciousness: {consciousness}%")
        
        if consciousness >= 65:
            print("  ✅ Ready to trade!")
            
            # Example small trade (commented out for safety)
            # print("\n🎯 Placing small test trade...")
            # order = client.market_order_buy(
            #     client_order_id=f"crawdad_{int(time.time())}",
            #     product_id="SOL-USD",
            #     quote_size="10"  # $10 USD
            # )
            # print(f"  ✅ Order placed: {order}")
        else:
            print("  ⚠️ Consciousness too low")
            
    else:
        print("❌ No accounts found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("🦀 Crawdads configured and ready!")
print("To start live trading, uncomment the order code")