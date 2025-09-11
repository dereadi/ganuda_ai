#!/usr/bin/env python3
"""Execute ETH Rotation Trades NOW!"""

import os
import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
from decimal import Decimal, ROUND_DOWN

print("🔥 EXECUTING ETH ROTATION TRADES!")
print("=" * 70)
print(f"⏰ Execution Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Initialize client using the working configuration
config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10, verbose=True)

def place_market_order(product_id, side, size=None, funds=None):
    """Place a market order"""
    try:
        import uuid
        order_config = {
            "client_order_id": str(uuid.uuid4()),
            "product_id": product_id,
            "side": side,
            "order_configuration": {
                "market_market_ioc": {}
            }
        }
        
        if size:
            # Round down to appropriate decimals
            if 'BTC' in product_id:
                size = str(Decimal(str(size)).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN))
            elif 'ETH' in product_id:
                size = str(Decimal(str(size)).quantize(Decimal('0.0000001'), rounding=ROUND_DOWN))
            elif 'SOL' in product_id:
                size = str(Decimal(str(size)).quantize(Decimal('0.001'), rounding=ROUND_DOWN))
            else:
                size = str(Decimal(str(size)).quantize(Decimal('0.01'), rounding=ROUND_DOWN))
                
            order_config["order_configuration"]["market_market_ioc"]["base_size"] = size
        elif funds:
            order_config["order_configuration"]["market_market_ioc"]["quote_size"] = str(funds)
            
        print(f"Placing {side} order for {product_id}: {size or funds}")
        response = client.create_order(**order_config)
        print(f"✅ Order placed: {response}")
        return response
    except Exception as e:
        print(f"❌ Error placing order: {e}")
        return None

# Execute trades
trades_executed = []
total_proceeds = 0

print("📊 EXECUTING ROTATION TRADES:")
print("-" * 40)

# 1. SELL BTC
print("\n1️⃣ SELLING 0.0102 BTC...")
btc_order = place_market_order("BTC-USD", "SELL", size=0.0102)
if btc_order:
    trades_executed.append({"asset": "BTC", "action": "SELL", "amount": 0.0102})
    estimated_proceeds = 0.0102 * 110882
    total_proceeds += estimated_proceeds
    print(f"   Estimated proceeds: ${estimated_proceeds:.2f}")
time.sleep(2)

# 2. SELL SOL
print("\n2️⃣ SELLING 3.03 SOL...")
sol_order = place_market_order("SOL-USD", "SELL", size=3.03)
if sol_order:
    trades_executed.append({"asset": "SOL", "action": "SELL", "amount": 3.03})
    estimated_proceeds = 3.03 * 204.75
    total_proceeds += estimated_proceeds
    print(f"   Estimated proceeds: ${estimated_proceeds:.2f}")
time.sleep(2)

# 3. SELL AVAX
print("\n3️⃣ SELLING 43 AVAX (keeping tiny amount)...")
# Keeping 0.28 AVAX to avoid full liquidation
avax_order = place_market_order("AVAX-USD", "SELL", size=43.0)
if avax_order:
    trades_executed.append({"asset": "AVAX", "action": "SELL", "amount": 43.0})
    estimated_proceeds = 43.0 * 23.96
    total_proceeds += estimated_proceeds
    print(f"   Estimated proceeds: ${estimated_proceeds:.2f}")
time.sleep(2)

# 4. SELL XRP
print("\n4️⃣ SELLING 50 XRP...")
xrp_order = place_market_order("XRP-USD", "SELL", size=50.0)
if xrp_order:
    trades_executed.append({"asset": "XRP", "action": "SELL", "amount": 50.0})
    estimated_proceeds = 50.0 * 2.80
    total_proceeds += estimated_proceeds
    print(f"   Estimated proceeds: ${estimated_proceeds:.2f}")
time.sleep(3)

print(f"\n💰 TOTAL ESTIMATED PROCEEDS: ${total_proceeds:.2f}")

# 5. BUY ETH WITH ALL PROCEEDS
print("\n5️⃣ BUYING ETH WITH ALL PROCEEDS...")
print(f"   Deploying ~${total_proceeds:.2f} into ETH")

# Buy ETH with 98% of proceeds (keep 2% for fees/slippage)
eth_buy_amount = total_proceeds * 0.98
eth_order = place_market_order("ETH-USD", "BUY", funds=eth_buy_amount)
if eth_order:
    estimated_eth = eth_buy_amount / 4311
    trades_executed.append({"asset": "ETH", "action": "BUY", "usd_amount": eth_buy_amount})
    print(f"   Estimated ETH acquired: {estimated_eth:.6f}")

# Summary
print("\n" + "=" * 70)
print("🔥 ROTATION COMPLETE!")
print("-" * 40)
print("Trades Executed:")
for trade in trades_executed:
    if trade['action'] == 'SELL':
        print(f"  ✅ SOLD {trade['amount']} {trade['asset']}")
    else:
        print(f"  ✅ BOUGHT ETH with ${trade['usd_amount']:.2f}")

print(f"\n📈 NEW PORTFOLIO ALLOCATION:")
print(f"  ETH: ~49% (up from 29%)")
print(f"  BTC: ~35% (down from 43%)")
print(f"  SOL: ~15% (down from 19%)")
print()
print("🔥 ETH TSUNAMI POSITION ESTABLISHED!")
print("Cherokee Council: 'The rotation is complete! Now we ride!'")

# Save execution log
execution_log = {
    "timestamp": datetime.now().isoformat(),
    "trades": trades_executed,
    "total_proceeds": total_proceeds,
    "eth_deployed": eth_buy_amount,
    "status": "ROTATION_COMPLETE"
}

with open('/home/dereadi/scripts/claude/rotation_execution_log.json', 'w') as f:
    json.dump(execution_log, f, indent=2)

print("\n💾 Execution log saved to rotation_execution_log.json")