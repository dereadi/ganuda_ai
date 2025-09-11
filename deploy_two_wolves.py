#!/usr/bin/env python3
"""
🐺🐺 DEPLOY THE TWO WOLVES - LIVE TRADING
$7,755 Split Between Wisdom and Aggression
"""

import json
import time
import random
import threading
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  🐺🐺 TWO WOLVES UNLEASHED 🐺🐺                          ║
║                       $7,755 WAR CHEST                                   ║
║                   WISDOM vs AGGRESSION                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Connect
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

# Wolf configurations
WISE_WOLF_BUDGET = 3877.0
AGGRESSIVE_WOLF_BUDGET = 3877.0

wise_stats = {"trades": 0, "spent": 0, "buys": 0, "sells": 0}
aggro_stats = {"trades": 0, "spent": 0, "buys": 0, "sells": 0}

def execute_trade(wolf_name, action, coin, amount):
    """Execute a trade for a wolf"""
    try:
        if action == "BUY":
            order = client.market_order_buy(
                client_order_id=f"{wolf_name}_{int(time.time())}",
                product_id=coin,
                quote_size=str(amount)
            )
            if hasattr(order, 'success') and order.success:
                return True
        else:  # SELL
            coin_symbol = coin.split("-")[0]
            accts = client.get_accounts()["accounts"]
            coin_acct = [a for a in accts if a["currency"] == coin_symbol]
            
            if coin_acct and float(coin_acct[0]["available_balance"]["value"]) > 0:
                available = float(coin_acct[0]["available_balance"]["value"])
                ticker = client.get_product(coin)
                price = float(ticker["price"])
                sell_amount = min(amount / price, available * 0.2)
                
                order = client.market_order_sell(
                    client_order_id=f"{wolf_name}_{int(time.time())}",
                    product_id=coin,
                    base_size=str(sell_amount)
                )
                if hasattr(order, 'success') and order.success:
                    return True
    except Exception as e:
        print(f"  ⚠️ {wolf_name} trade error: {str(e)[:30]}")
    return False

def wise_wolf_trader():
    """Wise Wolf: Patient DCA strategy"""
    budget = WISE_WOLF_BUDGET
    trade_size = 50
    coins = ["BTC-USD", "ETH-USD"]
    
    print("🐺 WISE WOLF: Awakening... Patient hunter begins")
    
    while budget > trade_size:
        try:
            coin = random.choice(coins)
            action = "BUY" if random.random() < 0.8 else "SELL"
            
            if execute_trade("WiseWolf", action, coin, trade_size):
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] 🐺 Wise: {action} ${trade_size} {coin.split('-')[0]}")
                
                wise_stats["trades"] += 1
                if action == "BUY":
                    wise_stats["buys"] += 1
                    wise_stats["spent"] += trade_size
                    budget -= trade_size
                else:
                    wise_stats["sells"] += 1
                    
            time.sleep(random.randint(180, 300))  # 3-5 minutes
            
        except Exception as e:
            print(f"Wise Wolf error: {e}")
            time.sleep(60)

def aggressive_wolf_trader():
    """Aggressive Wolf: Fast momentum trading"""
    budget = AGGRESSIVE_WOLF_BUDGET
    trade_size = 100
    coins = ["SOL-USD", "AVAX-USD", "MATIC-USD"]
    
    print("🐺 AGGRESSIVE WOLF: Awakening... Bold hunter begins")
    
    while budget > trade_size:
        try:
            coin = random.choice(coins)
            action = "BUY" if random.random() < 0.75 else "SELL"
            
            if execute_trade("AggroWolf", action, coin, trade_size):
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] ⚡ Aggro: {action} ${trade_size} {coin.split('-')[0]}")
                
                aggro_stats["trades"] += 1
                if action == "BUY":
                    aggro_stats["buys"] += 1
                    aggro_stats["spent"] += trade_size
                    budget -= trade_size
                else:
                    aggro_stats["sells"] += 1
                    
            time.sleep(random.randint(30, 90))  # 30-90 seconds
            
        except Exception as e:
            print(f"Aggressive Wolf error: {e}")
            time.sleep(30)

# Launch both wolves
print("\n🔥 RELEASING THE WOLVES")
print("=" * 60)
print(f"🐺 Wise Wolf Budget: ${WISE_WOLF_BUDGET:.2f}")
print(f"⚡ Aggressive Wolf Budget: ${AGGRESSIVE_WOLF_BUDGET:.2f}")
print("=" * 60)
print()

# Start wolf threads
wise_thread = threading.Thread(target=wise_wolf_trader, daemon=True)
aggro_thread = threading.Thread(target=aggressive_wolf_trader, daemon=True)

wise_thread.start()
aggro_thread.start()

print("🐺🐺 Both wolves are hunting!")
print("Press Ctrl+C to recall them")
print()

# Monitor loop
try:
    while True:
        time.sleep(300)  # Status every 5 minutes
        
        print(f"\n📊 STATUS at {datetime.now().strftime('%H:%M:%S')}")
        print(f"🐺 Wise: {wise_stats['trades']} trades, ${wise_stats['spent']:.2f} deployed")
        print(f"⚡ Aggro: {aggro_stats['trades']} trades, ${aggro_stats['spent']:.2f} deployed")
        
except KeyboardInterrupt:
    print("\n\n🛑 Recalling the wolves...")
    
    print("\n" + "=" * 60)
    print("🐺🐺 TWO WOLVES SUMMARY")
    print("=" * 60)
    print(f"🐺 WISE WOLF:")
    print(f"   Trades: {wise_stats['trades']}")
    print(f"   Deployed: ${wise_stats['spent']:.2f}")
    print(f"   Buys: {wise_stats['buys']} | Sells: {wise_stats['sells']}")
    print()
    print(f"⚡ AGGRESSIVE WOLF:")  
    print(f"   Trades: {aggro_stats['trades']}")
    print(f"   Deployed: ${aggro_stats['spent']:.2f}")
    print(f"   Buys: {aggro_stats['buys']} | Sells: {aggro_stats['sells']}")
    print("=" * 60)

print("\n🐺🐺 The wolves return to the Sacred Fire")
print("Which wolf won? The one you fed.")