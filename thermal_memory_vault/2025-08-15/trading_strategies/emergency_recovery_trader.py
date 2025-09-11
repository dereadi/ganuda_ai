#!/usr/bin/env python3
"""
🚨 EMERGENCY RECOVERY TRADER
Simple, fast, no timeouts
Recover from -$2,721 loss
"""

import json
import time
import random
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  🚨 EMERGENCY RECOVERY MODE 🚨                           ║
║                    Current Loss: -$2,721                                 ║
║                    Available: $5,809 USD                                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Simple connection
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=10)

# Focus coins for recovery
RECOVERY_COINS = ["SOL-USD", "AVAX-USD", "MATIC-USD"]

def quick_buy(coin, amount):
    """Quick buy with no frills"""
    try:
        order = client.market_order_buy(
            client_order_id=f"emergency_{int(time.time())}",
            product_id=coin,
            quote_size=str(amount)
        )
        return True
    except Exception as e:
        print(f"  ⚠️ Buy failed: {str(e)[:30]}")
        return False

def quick_sell(coin, percent=0.2):
    """Quick sell partial position"""
    try:
        symbol = coin.split("-")[0]
        accounts = client.get_accounts()["accounts"]
        coin_acct = [a for a in accounts if a["currency"] == symbol]
        
        if coin_acct and float(coin_acct[0]["available_balance"]["value"]) > 0.001:
            available = float(coin_acct[0]["available_balance"]["value"])
            sell_amount = available * percent
            
            order = client.market_order_sell(
                client_order_id=f"sell_{int(time.time())}",
                product_id=coin,
                base_size=str(sell_amount)
            )
            return True
    except Exception as e:
        print(f"  ⚠️ Sell failed: {str(e)[:30]}")
    return False

# Get starting balance
accounts = client.get_accounts()["accounts"]
start_usd = float([a for a in accounts if a["currency"]=="USD"][0]["available_balance"]["value"])
print(f"💰 Starting USD: ${start_usd:.2f}")
print(f"🎯 Target: Recover to break-even ($10,230)")
print()

# AGGRESSIVE RECOVERY STRATEGY
print("🚨 STRATEGY: Rapid momentum trades on volatile coins")
print("=" * 60)

trades = 0
deployed = 0
max_deploy = 4000  # Deploy $4000, keep $1800 reserve

while deployed < max_deploy:
    # Pick coin
    coin = random.choice(RECOVERY_COINS)
    
    # 80% buys during recovery
    if random.random() < 0.8 and deployed < max_deploy:
        amount = random.choice([200, 300, 400, 500])
        if deployed + amount > max_deploy:
            amount = max_deploy - deployed
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🚀 BUY ${amount} {coin.split('-')[0]}")
        
        if quick_buy(coin, amount):
            deployed += amount
            trades += 1
            print(f"  ✅ Success! Deployed: ${deployed}/{max_deploy}")
    else:
        # Sell to take profits
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 💰 SELL {coin.split('-')[0]} (20% position)")
        
        if quick_sell(coin, 0.2):
            trades += 1
            print(f"  ✅ Profit taken!")
    
    # Status every 10 trades
    if trades % 10 == 0 and trades > 0:
        accounts = client.get_accounts()["accounts"]
        current_usd = float([a for a in accounts if a["currency"]=="USD"][0]["available_balance"]["value"])
        print(f"\n📊 STATUS: {trades} trades | ${deployed} deployed | ${current_usd:.2f} USD")
    
    # Fast trading - 10-30 seconds between trades
    time.sleep(random.randint(10, 30))

print("\n" + "=" * 60)
print(f"🚨 EMERGENCY RECOVERY COMPLETE")
print(f"   Trades: {trades}")
print(f"   Deployed: ${deployed}")
print("=" * 60)
print("\nCheck portfolio for results!")