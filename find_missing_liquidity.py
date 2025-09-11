#!/usr/bin/env python3
"""
🔍 FIND THE MISSING $550
Where did the liquidity go?
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime, timedelta, timezone

print("🔍 SEARCHING FOR MISSING $550")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print()

try:
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    key = config["api_key"].split("/")[-1]
    client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)
    
    # Check recent orders/fills
    print("📊 CHECKING RECENT TRADES (Last 30 min):")
    print("-" * 40)
    
    thirty_min_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
    recent_buys = []
    
    for product in ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD", "MATIC-USD", "AVAX-USD"]:
        try:
            fills = client.get_fills(product_id=product, limit=10)
            for fill in fills.get("fills", []):
                trade_time = datetime.fromisoformat(fill["trade_time"].replace("Z", "+00:00"))
                if trade_time > thirty_min_ago:
                    side = fill["side"]
                    size = float(fill["size"])
                    price = float(fill["price"])
                    value = size * price
                    fee = float(fill.get("fee", 0))
                    
                    if side == "BUY":
                        recent_buys.append({
                            "time": trade_time.strftime("%H:%M:%S"),
                            "product": product.replace("-USD", ""),
                            "size": size,
                            "price": price,
                            "value": value,
                            "fee": fee
                        })
                        
        except:
            pass
    
    if recent_buys:
        total_spent = 0
        print("FOUND RECENT BUYS:")
        for buy in sorted(recent_buys, key=lambda x: x["time"], reverse=True):
            print(f"🟢 {buy['time']}: Bought {buy['size']:.4f} {buy['product']} @ ${buy['price']:.2f} = ${buy['value']:.2f}")
            total_spent += buy['value'] + buy['fee']
        
        print()
        print(f"Total spent: ${total_spent:.2f}")
    else:
        print("No recent buy orders found via API")
    
    print()
    
    # Check all positions to see what increased
    print("🔍 CHECKING POSITION CHANGES:")
    print("-" * 40)
    
    accounts = client.get_accounts()["accounts"]
    
    current_positions = {}
    for account in accounts:
        currency = account["currency"]
        balance = float(account["available_balance"]["value"])
        if balance > 0.00001:
            current_positions[currency] = balance
    
    # Compare to known positions
    known_positions = {
        "SOL": 10.935,  # Was 12.15, sold 1.215
        "ETH": 0.495,   # Was 0.55, sold 0.055
        "XRP": 193,     # Was 215, sold 22
        "DOGE": 745,
        "MATIC": 425,
        "AVAX": 13.5,
        "LINK": 18
    }
    
    print("Position changes detected:")
    changes_found = False
    
    for coin, current in current_positions.items():
        if coin in known_positions:
            expected = known_positions[coin]
            diff = current - expected
            if abs(diff) > 0.0001:
                changes_found = True
                if diff > 0:
                    print(f"📈 {coin}: +{diff:.4f} (was {expected:.4f}, now {current:.4f})")
                    # Estimate cost
                    if coin == "SOL":
                        cost = diff * 206
                        print(f"   Estimated cost: ${cost:.2f}")
                    elif coin == "ETH":
                        cost = diff * 3245
                        print(f"   Estimated cost: ${cost:.2f}")
                else:
                    print(f"📉 {coin}: {diff:.4f} (was {expected:.4f}, now {current:.4f})")
        elif coin not in ["USD", "USDC"] and current > 0.01:
            print(f"🆕 {coin}: {current:.4f} (new position)")
    
    if not changes_found:
        print("No significant position changes detected")
    
    print()
    print("💡 POSSIBLE EXPLANATIONS:")
    print("-" * 40)
    print("1. Automated specialists executed buy orders")
    print("2. Limit orders were triggered")
    print("3. Council bot made strategic purchases")
    print("4. API delay in showing positions")
    print()
    print("RECOMMENDATION: Check specialist logs and stop automated trading")
    
except Exception as e:
    print(f"Error: {str(e)}")
    print()
    print("Unable to trace the missing funds")
    print("Manual investigation required")