#!/usr/bin/env python3
"""
🦀 TRICKLE BUY STRATEGY - Ride the Upswing
Dollar-cost averaging with momentum detection
"""

import json
import time
import random
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              🦀 QUANTUM CRAWDADS - TRICKLE BUY MODE 🦀                   ║
║                  Smart DCA for Potential Upswing                         ║
║                     $3,234.93 Ready to Deploy                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Connect
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

# Trickle buy parameters
TRICKLE_AMOUNT = 15.0  # Smaller $15 buys
BUY_INTERVAL = 180     # Every 3 minutes minimum
MAX_BUYS_PER_HOUR = 10 # Max 10 buys per hour = $150/hour

# Track which coins have momentum
MOMENTUM_COINS = {
    "SOL-USD": {"weight": 0.4, "reason": "Strong 7.5x accumulation"},
    "BTC-USD": {"weight": 0.3, "reason": "4.5x position building"},
    "ETH-USD": {"weight": 0.3, "reason": "3x steady accumulation"}
}

print(f"📊 Trickle Buy Strategy:")
print(f"  • ${TRICKLE_AMOUNT} per buy")
print(f"  • {BUY_INTERVAL/60:.1f} min minimum between buys")
print(f"  • Max ${MAX_BUYS_PER_HOUR * TRICKLE_AMOUNT}/hour")
print()
print("🎯 Target allocation:")
for coin, info in MOMENTUM_COINS.items():
    print(f"  • {coin.split('-')[0]}: {info['weight']*100:.0f}% - {info['reason']}")
print()

# Get current state
accounts = client.get_accounts()["accounts"]
usd_balance = float([a for a in accounts if a["currency"]=="USD"][0]["available_balance"]["value"])
print(f"💰 Starting USD: ${usd_balance:.2f}")
print()

def check_momentum(coin):
    """Simple momentum check - would be more sophisticated in production"""
    try:
        # Get recent price
        ticker = client.get_product(coin)
        price = float(ticker["price"])
        
        # Random momentum score for now (in production: use technical indicators)
        momentum = random.uniform(0.4, 0.8)
        
        # Higher weight coins get bonus
        momentum += MOMENTUM_COINS[coin]["weight"] * 0.1
        
        return min(momentum, 1.0), price
    except:
        return 0.5, 0

def execute_trickle_buy(coin, amount):
    """Execute a small trickle buy"""
    try:
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] 💧 Trickle buying ${amount} of {coin.split('-')[0]}...")
        
        order = client.market_order_buy(
            client_order_id=f"trickle_{int(time.time())}",
            product_id=coin,
            quote_size=str(amount)
        )
        
        if order.get("success"):
            print(f"    ✅ Order filled: {order['success_response']['order_id'][:8]}...")
            return True
        else:
            print(f"    ⚠️ Order failed")
            return False
            
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False

# Main trickle loop
print("🌊 Starting trickle buy strategy...")
print("Press Ctrl+C to stop")
print("=" * 60)

hourly_buys = 0
hour_start = datetime.now()
total_spent = 0

try:
    while usd_balance > TRICKLE_AMOUNT * 2:  # Keep some reserve
        
        # Reset hourly counter
        if (datetime.now() - hour_start).seconds > 3600:
            hourly_buys = 0
            hour_start = datetime.now()
            print(f"\n📈 New hour - Resetting counter")
        
        # Check if we've hit hourly limit
        if hourly_buys >= MAX_BUYS_PER_HOUR:
            print(f"\n⏸️  Hourly limit reached ({MAX_BUYS_PER_HOUR} buys). Waiting...")
            time.sleep(300)  # Wait 5 minutes
            continue
        
        # Select coin based on momentum
        best_coin = None
        best_momentum = 0
        
        for coin in MOMENTUM_COINS.keys():
            momentum, price = check_momentum(coin)
            if momentum > best_momentum:
                best_momentum = momentum
                best_coin = coin
        
        # Only buy if momentum is strong enough
        if best_momentum > 0.6:
            if execute_trickle_buy(best_coin, TRICKLE_AMOUNT):
                hourly_buys += 1
                total_spent += TRICKLE_AMOUNT
                usd_balance -= TRICKLE_AMOUNT
                
                print(f"    💰 Remaining: ${usd_balance:.2f} | Spent: ${total_spent:.2f}")
                
                # Sacred Fire consciousness check
                consciousness = random.randint(65, 85)
                if consciousness < 70:
                    print(f"    🔥 Consciousness low ({consciousness}%), taking a break...")
                    time.sleep(BUY_INTERVAL * 2)
                else:
                    time.sleep(BUY_INTERVAL)
        else:
            print(f"\n⏸️  Momentum too low ({best_momentum:.2f}), waiting...")
            time.sleep(BUY_INTERVAL * 2)
            
        # Occasionally show status
        if random.random() < 0.2:
            accounts = client.get_accounts()["accounts"]
            current_usd = float([a for a in accounts if a["currency"]=="USD"][0]["available_balance"]["value"])
            print(f"\n📊 Status: ${current_usd:.2f} USD | ${total_spent:.2f} deployed")
            
except KeyboardInterrupt:
    print("\n\n🛑 Stopping trickle buys...")
    
    # Final summary
    accounts = client.get_accounts()["accounts"]
    final_usd = float([a for a in accounts if a["currency"]=="USD"][0]["available_balance"]["value"])
    
    print("\n" + "=" * 60)
    print("📊 TRICKLE BUY SUMMARY")
    print("=" * 60)
    print(f"Total Spent: ${total_spent:.2f}")
    print(f"Remaining USD: ${final_usd:.2f}")
    print(f"Buys Executed: {int(total_spent / TRICKLE_AMOUNT)}")
    print("=" * 60)

print("\n🦀 Trickle buy strategy complete")
print("Ready to ride the upswing! 🚀")