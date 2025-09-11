#!/usr/bin/env python3
"""
💰 SYNTHETIC PUT SELLER
Simulates selling puts using limit orders
Collect "premium" by buying dips and selling rips
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("💰 SYNTHETIC PUT SELLING STRATEGY")
print("=" * 60)
print("Strategy: Place buy orders below market")
print("         Like selling puts at various strikes")
print("=" * 60)

# Get current prices
btc = client.get_product("BTC-USD")
eth = client.get_product("ETH-USD")
sol = client.get_product("SOL-USD")

btc_price = float(btc["price"])
eth_price = float(eth["price"])
sol_price = float(sol["price"])

print(f"\n📊 CURRENT PRICES:")
print(f"BTC: ${btc_price:,.2f}")
print(f"ETH: ${eth_price:,.2f}")
print(f"SOL: ${sol_price:.2f}")

# Check available capital
accounts = client.get_accounts()["accounts"]
usd_balance = 0
for acc in accounts:
    if acc["currency"] == "USD":
        usd_balance = float(acc["available_balance"]["value"])
        break

print(f"\n💵 Available Capital: ${usd_balance:.2f}")

if usd_balance > 500:
    print("\n🎯 SYNTHETIC PUT LADDER:")
    print("-" * 60)
    
    # Calculate "strike prices" (support levels)
    put_strikes = {
        "BTC": [
            {"strike": btc_price * 0.98, "size": 100},  # 2% OTM
            {"strike": btc_price * 0.97, "size": 150},  # 3% OTM
            {"strike": btc_price * 0.95, "size": 200},  # 5% OTM
        ],
        "ETH": [
            {"strike": eth_price * 0.98, "size": 100},  # 2% OTM
            {"strike": eth_price * 0.96, "size": 150},  # 4% OTM
        ],
        "SOL": [
            {"strike": sol_price * 0.97, "size": 50},   # 3% OTM
            {"strike": sol_price * 0.95, "size": 75},   # 5% OTM
        ]
    }
    
    orders_placed = []
    total_allocated = 0
    
    # Place limit buy orders (synthetic short puts)
    for coin, strikes in put_strikes.items():
        print(f"\n{coin} Synthetic Puts:")
        
        for strike_data in strikes:
            strike = strike_data["strike"]
            size = strike_data["size"]
            
            if total_allocated + size > usd_balance * 0.8:  # Keep 20% reserve
                print(f"  ⚠️ Skipping ${strike:.2f} - insufficient capital")
                continue
                
            # Calculate equivalent shares
            if coin == "BTC":
                base_size = size / strike
                product_id = "BTC-USD"
            elif coin == "ETH":
                base_size = size / strike
                product_id = "ETH-USD"
            else:
                base_size = size / strike
                product_id = "SOL-USD"
            
            try:
                # Place limit buy order (synthetic short put)
                order = client.limit_order_gtc_buy(
                    client_order_id=f"synth_put_{coin}_{int(strike)}_{int(time.time()*1000)}",
                    product_id=product_id,
                    base_size=str(round(base_size, 8)),
                    limit_price=str(round(strike, 2))
                )
                
                current_price = btc_price if coin == "BTC" else (eth_price if coin == "ETH" else sol_price)
                discount = (1 - strike/current_price) * 100
                
                print(f"  ✅ Strike ${strike:.2f} ({discount:.1f}% OTM) - Size: ${size}")
                orders_placed.append(f"{coin} ${strike:.2f}")
                total_allocated += size
                
            except Exception as e:
                print(f"  ❌ Failed: {e}")
    
    print(f"\n📈 SYNTHETIC PUTS SUMMARY:")
    print(f"Total Orders: {len(orders_placed)}")
    print(f"Capital Allocated: ${total_allocated:.2f}")
    print(f"Reserve Kept: ${usd_balance - total_allocated:.2f}")
    
    print("\n💡 PROFIT SCENARIOS:")
    print("-" * 60)
    print("1. Price stays above strikes → Orders don't fill, we keep studying")
    print("2. Price dips to strike → We buy the dip automatically")
    print("3. Price bounces → We sell for profit (like put expired profitable)")
    print("4. Price keeps falling → We own assets (like put assignment)")
    
    # Save order data for monitoring
    order_data = {
        "timestamp": datetime.now().isoformat(),
        "orders": orders_placed,
        "total_allocated": total_allocated,
        "strikes": put_strikes
    }
    
    with open("/tmp/synthetic_puts.json", "w") as f:
        json.dump(order_data, f)
    
    print("\n✅ Synthetic put ladder deployed!")
    print("   Monitor /tmp/synthetic_puts.json for status")
    
else:
    print("\n⚠️ Insufficient capital for synthetic puts")
    print(f"   Need at least $500, have ${usd_balance:.2f}")

print("=" * 60)