#!/usr/bin/env python3
"""
🦀 QUANTUM CRAWDAD LIVE TRADER - SIMPLIFIED
Working version with proper error handling
"""

import json
import time
import random
from datetime import datetime
from coinbase.rest import RESTClient

print("🦀 QUANTUM CRAWDAD LIVE TRADER")
print("=" * 50)

# Load config
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]

# Connect to Coinbase
print("Connecting to Coinbase...")
client = RESTClient(api_key=key, api_secret=config["api_secret"])

# Get balance
accounts = client.get_accounts()
usd_account = [a for a in accounts["accounts"] if a["currency"] == "USD"][0]
balance = float(usd_account["available_balance"]["value"])

print(f"✅ Connected! Balance: ${balance:.2f}")
print()

# Trading parameters
TRADE_AMOUNT = 10.0  # Trade $10 at a time
COINS = ["BTC-USD", "ETH-USD", "SOL-USD"]

print(f"Trading ${TRADE_AMOUNT} per trade on: {', '.join(COINS)}")
print("Starting in 5 seconds...")
time.sleep(5)

trade_count = 0
while True:
    try:
        # Pick random coin
        coin = random.choice(COINS)
        action = random.choice(["BUY", "BUY", "SELL"])  # Favor buying
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Trade #{trade_count + 1}")
        
        if action == "BUY":
            # Buy $10 worth
            print(f"  📈 Buying ${TRADE_AMOUNT} of {coin.split('-')[0]}...")
            order = client.market_order_buy(
                client_order_id=f"crawdad_{int(time.time())}",
                product_id=coin,
                quote_size=str(TRADE_AMOUNT)
            )
        else:
            # Check if we have any to sell
            coin_symbol = coin.split("-")[0]
            coin_accounts = [a for a in accounts["accounts"] if a["currency"] == coin_symbol]
            
            if coin_accounts and float(coin_accounts[0]["available_balance"]["value"]) > 0:
                # Sell $10 worth
                print(f"  📉 Selling ${TRADE_AMOUNT} of {coin_symbol}...")
                
                # Get current price to calculate quantity
                ticker = client.get_product(coin)
                price = float(ticker["price"])
                quantity = TRADE_AMOUNT / price
                
                order = client.market_order_sell(
                    client_order_id=f"crawdad_{int(time.time())}",
                    product_id=coin,
                    base_size=str(quantity)
                )
            else:
                print(f"  ⏭️  No {coin_symbol} to sell, skipping...")
                continue
        
        if order and "order_id" in order:
            print(f"  ✅ Order placed: {order['order_id']}")
            trade_count += 1
        else:
            print(f"  ⚠️  Order failed: {order}")
        
        # Wait 30-60 seconds between trades
        wait = random.randint(30, 60)
        print(f"  💤 Waiting {wait} seconds...")
        time.sleep(wait)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        break
    except Exception as e:
        print(f"  ❌ Error: {e}")
        time.sleep(30)

print(f"\nTotal trades: {trade_count}")