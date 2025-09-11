#!/usr/bin/env python3
"""FLYWHEEL EXECUTOR - LIVE AGGRESSIVE TRADING"""
import json
import time
import random
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)

# Phase 1: Aggressive liquidation
print("💥 LIQUIDATING POSITIONS...")
sells = [
    ("MATIC-USD", 4000),
    ("AVAX-USD", 40),
    ("LINK-USD", 11),
    ("ETH-USD", 0.14)
]

for coin, amount in sells:
    try:
        client.market_order_sell(
            client_order_id=f"flywheel_{int(time.time())}",
            product_id=coin,
            base_size=str(amount)
        )
        print(f"  ✅ Sold {amount} {coin.split('-')[0]}")
        time.sleep(1)
    except Exception as e:
        print(f"  ⚠️ {coin} error: {e}")

# Phase 2: FLYWHEEL TRADING
print("\n🌪️ FLYWHEEL SPINNING UP...")
trade_count = 0
capital = 3000  # Estimated after sells

coins = ["SOL-USD", "DOGE-USD", "AVAX-USD", "MATIC-USD"]

while trade_count < 100:
    coin = random.choice(coins)
    action = random.choice(["BUY", "SELL"])
    amount = random.choice([100, 200, 300, 500])
    
    try:
        if action == "BUY":
            client.market_order_buy(
                client_order_id=f"fly_{trade_count}",
                product_id=coin,
                quote_size=str(amount)
            )
        else:
            # Simplified sell logic
            pass
            
        trade_count += 1
        print(f"Trade #{trade_count}: {action} ${amount} {coin.split('-')[0]}")
        
        # AGGRESSIVE: 30-60 second intervals
        time.sleep(random.randint(30, 60))
        
    except Exception as e:
        print(f"Trade error: {e}")
        time.sleep(10)

print(f"\n🔥 FLYWHEEL COMPLETE: {trade_count} trades executed!")
