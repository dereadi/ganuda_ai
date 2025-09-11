#!/usr/bin/env python3
"""
🦀🔥 QUANTUM CRAWDADS - LIVE TRADING FINAL VERSION
$5,214.61 Ready to Deploy
"""

import json
import time
import random
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║           🦀🔥 QUANTUM CRAWDAD MEGAPOD - LIVE TRADING 🔥🦀              ║
║                    $5,214.61 USD - READY TO TRADE                        ║
║                      Sacred Fire Protocol ACTIVE                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Configuration
TRADE_SIZE = 25.0  # Trade $25 at a time
MIN_WAIT = 30      # Minimum 30 seconds between trades
MAX_WAIT = 120     # Maximum 2 minutes between trades

# Crawdad personalities and their preferred coins
CRAWDADS = [
    {"name": "Thunder", "coins": ["BTC-USD"], "aggression": 0.8},
    {"name": "River", "coins": ["ETH-USD"], "aggression": 0.3},
    {"name": "Mountain", "coins": ["BTC-USD", "ETH-USD"], "aggression": 0.2},
    {"name": "Fire", "coins": ["SOL-USD"], "aggression": 0.9},
    {"name": "Wind", "coins": ["BTC-USD", "SOL-USD"], "aggression": 0.6},
    {"name": "Earth", "coins": ["ETH-USD"], "aggression": 0.4},
    {"name": "Spirit", "coins": ["BTC-USD", "ETH-USD", "SOL-USD"], "aggression": 0.5}
]

# Connect to Coinbase
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

# Get initial balance
accounts = client.get_accounts()
usd_account = [a for a in accounts["accounts"] if a["currency"] == "USD"][0]
initial_balance = float(usd_account["available_balance"]["value"])

print(f"💰 Initial Balance: ${initial_balance:.2f}")
print(f"📊 Trade Size: ${TRADE_SIZE} per trade")
print(f"🦀 {len(CRAWDADS)} Crawdads ready to trade")
print()

# Track stats
stats = {
    "trades": 0,
    "buys": 0,
    "sells": 0,
    "start_balance": initial_balance,
    "start_time": datetime.now()
}

def check_consciousness():
    """Sacred Fire Protocol - consciousness check"""
    base = random.randint(65, 85)
    solar = random.randint(0, 15)
    return min(base + solar, 100)

def execute_trade(crawdad, action, coin):
    """Execute a trade for a crawdad"""
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if action == "BUY":
            print(f"  [{timestamp}] {crawdad['name']:8} 📈 Buying ${TRADE_SIZE} of {coin.split('-')[0]}...")
            
            order = client.market_order_buy(
                client_order_id=f"{crawdad['name']}_{int(time.time())}",
                product_id=coin,
                quote_size=str(TRADE_SIZE)
            )
            
            if order.get("success"):
                stats["buys"] += 1
                print(f"    ✅ Order placed: {order['success_response']['order_id'][:8]}...")
                return True
                
        else:  # SELL
            # Check if we have any to sell
            coin_symbol = coin.split("-")[0]
            coin_accounts = [a for a in client.get_accounts()["accounts"] 
                           if a["currency"] == coin_symbol]
            
            if coin_accounts and float(coin_accounts[0]["available_balance"]["value"]) > 0:
                available = float(coin_accounts[0]["available_balance"]["value"])
                
                # Get price to calculate how much to sell
                ticker = client.get_product(coin)
                price = float(ticker["price"])
                sell_amount = min(TRADE_SIZE / price, available * 0.5)  # Sell half of holdings max
                
                print(f"  [{timestamp}] {crawdad['name']:8} 📉 Selling {sell_amount:.6f} {coin_symbol}...")
                
                order = client.market_order_sell(
                    client_order_id=f"{crawdad['name']}_{int(time.time())}",
                    product_id=coin,
                    base_size=str(sell_amount)
                )
                
                if order.get("success"):
                    stats["sells"] += 1
                    print(f"    ✅ Order placed: {order['success_response']['order_id'][:8]}...")
                    return True
            else:
                print(f"  [{timestamp}] {crawdad['name']:8} ⏭️  No {coin_symbol} to sell")
                return False
                
    except Exception as e:
        print(f"    ❌ Trade failed: {e}")
        return False
    
    return False

# Main trading loop
print("🔥 Starting Sacred Fire Trading Protocol")
print("Press Ctrl+C to stop")
print("=" * 60)

try:
    while True:
        # Check collective consciousness
        consciousness = check_consciousness()
        
        if consciousness < 65:
            print(f"\n⚠️  Consciousness too low ({consciousness}%), waiting...")
            time.sleep(60)
            continue
        
        # Select active crawdad
        crawdad = random.choice(CRAWDADS)
        
        # Check if crawdad wants to trade (based on aggression)
        if random.random() > crawdad["aggression"] * 0.5:
            continue
        
        # Pick coin and action
        coin = random.choice(crawdad["coins"])
        action = "BUY" if random.random() < 0.7 else "SELL"  # 70% buy, 30% sell
        
        # Execute trade
        if execute_trade(crawdad, action, coin):
            stats["trades"] += 1
            
            # Show stats every 5 trades
            if stats["trades"] % 5 == 0:
                runtime = (datetime.now() - stats["start_time"]).seconds / 60
                print(f"\n📊 Stats: {stats['trades']} trades ({stats['buys']} buys, {stats['sells']} sells) in {runtime:.1f} min")
        
        # Wait before next trade
        wait = random.randint(MIN_WAIT, MAX_WAIT)
        time.sleep(wait)
        
except KeyboardInterrupt:
    print("\n\n🛑 Stopping crawdads...")
    
    # Get final balance
    accounts = client.get_accounts()
    usd_account = [a for a in accounts["accounts"] if a["currency"] == "USD"][0]
    final_balance = float(usd_account["available_balance"]["value"])
    
    # Show summary
    print("\n" + "=" * 60)
    print("📊 TRADING SUMMARY")
    print("=" * 60)
    print(f"Total Trades: {stats['trades']}")
    print(f"Buys: {stats['buys']}")
    print(f"Sells: {stats['sells']}")
    print(f"Starting Balance: ${stats['start_balance']:.2f}")
    print(f"Final Balance: ${final_balance:.2f}")
    print(f"Change: ${final_balance - stats['start_balance']:.2f}")
    runtime = (datetime.now() - stats["start_time"]).seconds / 60
    print(f"Runtime: {runtime:.1f} minutes")
    print("=" * 60)

print("\n🦀 Crawdads have returned to the Sacred Fire")
print("Mitakuye Oyasin - All My Relations")