#!/usr/bin/env python3
"""
🚀 EXECUTE BTC SQUEEZE BREAKOUT TRADE
"""

import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("⚡ BTC SQUEEZE BREAKOUT EXECUTION")
print("=" * 60)

# Current situation
ticker = client.get_product("BTC-USD")
btc_price = float(ticker["price"])
print(f"BTC Price: ${btc_price:,.2f}")

# Bands are at $112,755 (upper) and $112,231 (lower)
upper_band = 112755
lower_band = 112231

print(f"Upper Band: ${upper_band:,.2f}")
print(f"Lower Band: ${lower_band:,.2f}")
print(f"Distance to upper: ${upper_band - btc_price:,.2f}")
print(f"Distance to lower: ${btc_price - lower_band:,.2f}")

# Check our ammo
accounts = client.get_accounts()["accounts"]
usd_balance = 0
matic_balance = 0

for acc in accounts:
    if acc["currency"] == "USD":
        usd_balance = float(acc["available_balance"]["value"])
    elif acc["currency"] == "MATIC":
        matic_balance = float(acc["available_balance"]["value"])

print(f"\nCurrent USD: ${usd_balance:.2f}")

# Need more liquidity for this critical squeeze play
if usd_balance < 200 and matic_balance > 1000:
    print("\n🔥 GENERATING SQUEEZE LIQUIDITY:")
    try:
        # Sell 1000 MATIC for quick USD
        order = client.market_order_sell(
            client_order_id=f"matic_squeeze_liq_{int(time.time()*1000)}",
            product_id="MATIC-USD",
            base_size="1000"
        )
        print("✅ Sold 1000 MATIC for liquidity")
        time.sleep(2)
        
        # Recheck USD
        accounts = client.get_accounts()["accounts"]
        for acc in accounts:
            if acc["currency"] == "USD":
                usd_balance = float(acc["available_balance"]["value"])
                print(f"New USD: ${usd_balance:.2f}")
                break
    except Exception as e:
        print(f"Liquidity generation failed: {e}")

# Deploy BTC squeeze trades
if usd_balance > 100:
    print("\n🚀 DEPLOYING SQUEEZE TRADES:")
    
    # Split capital for bi-directional setup
    trade_size = min(100, usd_balance * 0.4)
    
    print(f"Trade size per side: ${trade_size:.2f}")
    
    # Place initial position
    try:
        order = client.market_order_buy(
            client_order_id=f"btc_squeeze_entry_{int(time.time()*1000)}",
            product_id="BTC-USD",
            quote_size=str(trade_size)
        )
        print(f"✅ BTC position established: ${trade_size:.2f}")
        
        # Also position ETH for sympathy
        if usd_balance - trade_size > 50:
            eth_order = client.market_order_buy(
                client_order_id=f"eth_sympathy_{int(time.time()*1000)}",
                product_id="ETH-USD",
                quote_size="50"
            )
            print(f"✅ ETH sympathy position: $50")
            
    except Exception as e:
        print(f"Entry failed: {e}")
        
else:
    print("\n⚠️ Insufficient liquidity for squeeze play")
    print("Monitor for breakout direction before entering")

# Alert all systems
print("\n🎯 SQUEEZE STRATEGY ACTIVATED:")
print("-" * 60)
print("• IF breaks above $112,755 → ADD aggressively (target $115,000)")
print("• IF breaks below $112,231 → SELL and reverse short")
print("• Current position: READY")
print("• All specialists: ALERT STATUS")

# Write alert for other systems
alert = {
    "type": "BTC_SQUEEZE",
    "price": btc_price,
    "upper": upper_band,
    "lower": lower_band,
    "width_pct": 0.47,
    "timestamp": time.time()
}

with open("/tmp/btc_squeeze_alert.json", "w") as f:
    json.dump(alert, f)

print("\n⚡ SQUEEZE PLAY READY - BREAKOUT IMMINENT!")
print("=" * 60)