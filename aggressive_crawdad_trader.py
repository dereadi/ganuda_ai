#!/usr/bin/env python3
"""
🦀🔥 AGGRESSIVE QUANTUM CRAWDAD TRADER
More risk, bigger trades, faster execution
Council wisdom balanced with warrior spirit
"""

import json
import time
import random
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║         🦀🔥 QUANTUM CRAWDADS - AGGRESSIVE MODE ACTIVATED 🔥🦀           ║
║                    $2,935 USD - LET'S MAKE MOVES                         ║
║                  Council Approved Risk Parameters                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Configuration - MORE AGGRESSIVE
TRADE_SIZE = 50.0      # Double the trade size to $50
MIN_WAIT = 20          # Faster trades - 20 seconds minimum
MAX_WAIT = 60          # Max 1 minute between trades
MAX_DEPLOYMENT = 1500  # Deploy up to $1500 (keeping $1435 reserve)

# Connect
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

# Get balance
accounts = client.get_accounts()["accounts"]
usd_balance = float([a for a in accounts if a["currency"]=="USD"][0]["available_balance"]["value"])

print(f"💰 Starting Balance: ${usd_balance:.2f}")
print(f"⚔️ War Chest: ${MAX_DEPLOYMENT:.2f} to deploy")
print(f"🛡️ Reserve: ${usd_balance - MAX_DEPLOYMENT:.2f}")
print(f"📊 Trade Size: ${TRADE_SIZE} per trade (2x normal)")
print()

# Enhanced Crawdad personalities for aggressive trading
AGGRESSIVE_CRAWDADS = [
    {"name": "Thunder", "coins": ["BTC-USD"], "aggression": 0.9},  # More aggressive
    {"name": "Fire", "coins": ["SOL-USD"], "aggression": 1.0},     # Maximum aggression
    {"name": "Lightning", "coins": ["ETH-USD", "SOL-USD"], "aggression": 0.95},
    {"name": "Storm", "coins": ["BTC-USD", "SOL-USD"], "aggression": 0.85}
]

stats = {
    "deployed": 0,
    "trades": 0,
    "buys": 0,
    "sells": 0,
    "start_time": datetime.now()
}

def execute_aggressive_trade(crawdad, action, coin):
    """Execute trade with fixed order response handling"""
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if action == "BUY":
            print(f"[{timestamp}] {crawdad['name']:8} ⚡ AGGRESSIVE BUY ${TRADE_SIZE} of {coin.split('-')[0]}")
            
            order = client.market_order_buy(
                client_order_id=f"aggro_{crawdad['name']}_{int(time.time())}",
                product_id=coin,
                quote_size=str(TRADE_SIZE)
            )
            
            # Fixed: Check success properly
            if hasattr(order, 'success') and order.success:
                stats["buys"] += 1
                stats["deployed"] += TRADE_SIZE
                print(f"  ✅ EXECUTED! Order: {order.success_response['order_id'][:8]}...")
                return True
            elif isinstance(order, dict) and order.get('success'):
                stats["buys"] += 1
                stats["deployed"] += TRADE_SIZE
                print(f"  ✅ EXECUTED! Deployed: ${stats['deployed']:.2f}")
                return True
                
        else:  # SELL
            # Get holdings
            coin_symbol = coin.split("-")[0]
            coin_accounts = [a for a in client.get_accounts()["accounts"] 
                           if a["currency"] == coin_symbol]
            
            if coin_accounts and float(coin_accounts[0]["available_balance"]["value"]) > 0:
                available = float(coin_accounts[0]["available_balance"]["value"])
                
                # Aggressive: Sell larger portions
                ticker = client.get_product(coin)
                price = float(ticker["price"])
                sell_amount = min(TRADE_SIZE / price, available * 0.3)  # Sell 30% of holdings
                
                print(f"[{timestamp}] {crawdad['name']:8} ⚡ AGGRESSIVE SELL {sell_amount:.6f} {coin_symbol}")
                
                order = client.market_order_sell(
                    client_order_id=f"aggro_{crawdad['name']}_{int(time.time())}",
                    product_id=coin,
                    base_size=str(sell_amount)
                )
                
                if hasattr(order, 'success') and order.success:
                    stats["sells"] += 1
                    print(f"  ✅ SOLD! Taking profits")
                    return True
                elif isinstance(order, dict) and order.get('success'):
                    stats["sells"] += 1
                    print(f"  ✅ SOLD! Rebalancing")
                    return True
                    
    except Exception as e:
        print(f"  ⚠️ Trade issue: {str(e)[:50]}")
        return False
    
    return False

# Main aggressive trading loop
print("⚡ AGGRESSIVE TRADING ACTIVATED")
print("War Chief approved! Let's ride!")
print("=" * 60)

try:
    while stats["deployed"] < MAX_DEPLOYMENT:
        
        # Pick most aggressive crawdad
        crawdad = random.choice(AGGRESSIVE_CRAWDADS)
        
        # High probability of action with aggressive crawdads
        if random.random() < crawdad["aggression"]:
            
            # Aggressive bias: 80% buy, 20% sell
            coin = random.choice(crawdad["coins"])
            action = "BUY" if random.random() < 0.8 else "SELL"
            
            if execute_aggressive_trade(crawdad, action, coin):
                stats["trades"] += 1
                
                # Status update every 3 trades
                if stats["trades"] % 3 == 0:
                    print(f"\n⚡ STATUS: ${stats['deployed']:.2f} deployed | {stats['trades']} trades")
                    print(f"   Remaining war chest: ${MAX_DEPLOYMENT - stats['deployed']:.2f}")
            
            # Faster trading
            wait = random.randint(MIN_WAIT, MAX_WAIT)
            time.sleep(wait)
        else:
            time.sleep(MIN_WAIT)
            
except KeyboardInterrupt:
    print("\n\n🛑 Aggressive trading stopped")
    
    # Summary
    runtime = (datetime.now() - stats["start_time"]).seconds / 60
    print("\n" + "=" * 60)
    print("⚡ AGGRESSIVE TRADING SUMMARY")
    print("=" * 60)
    print(f"Deployed: ${stats['deployed']:.2f} of ${MAX_DEPLOYMENT}")
    print(f"Total Trades: {stats['trades']}")
    print(f"Buys: {stats['buys']} | Sells: {stats['sells']}")
    print(f"Runtime: {runtime:.1f} minutes")
    print(f"Trade Rate: {stats['trades']/runtime:.1f} trades/minute")
    print("=" * 60)

print("\n🦀 Aggressive crawdads returning to base")
print("Council wisdom + Warrior spirit = Success")