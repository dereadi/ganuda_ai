#!/usr/bin/env python3
"""
🦀💰 DEPLOY NEW CAPITAL STRATEGICALLY
======================================
$307.53 to allocate based on solar forecast
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

# Load config
config_path = "/home/dereadi/.coinbase_config.json"
with open(config_path) as f:
    config = json.load(f)

client = RESTClient(
    api_key=config["api_key"],
    api_secret=config["api_secret"]
)

print("🦀💰 QUANTUM CRAWDAD CAPITAL DEPLOYMENT")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Check current balance
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"💵 Available USD: ${usd_balance:.2f}")
print()

# Strategy based on quiet solar forecast
print("🌞 SOLAR FORECAST: QUIET")
print("Strategy: Build long positions during calm")
print()

# Allocation strategy for quiet sun
allocations = {
    "SOL": 0.35,  # 35% - Most volatile, highest upside
    "ETH": 0.25,  # 25% - Solid medium risk
    "BTC": 0.20,  # 20% - Conservative anchor
    "RESERVE": 0.20  # 20% - Keep for opportunities/shorts
}

print("📊 ALLOCATION PLAN:")
print("-"*40)

deployment_amount = usd_balance * 0.80  # Deploy 80% of available
reserve_amount = usd_balance * 0.20

for asset, pct in allocations.items():
    if asset != "RESERVE":
        amount = deployment_amount * (pct / 0.80)  # Adjust for reserve
        print(f"  {asset}: ${amount:.2f} ({pct*100:.0f}%)")

print(f"  RESERVE: ${reserve_amount:.2f} (20%)")
print()

# Execute trades
print("🚀 EXECUTING DEPLOYMENT:")
print("-"*40)

trades_executed = []

for asset in ["SOL", "ETH", "BTC"]:
    try:
        # Calculate trade size
        trade_pct = allocations[asset]
        trade_amount = deployment_amount * (trade_pct / 0.80)
        
        # Skip if too small
        if trade_amount < 10:
            print(f"  ⚠️ {asset}: Amount too small (${trade_amount:.2f})")
            continue
        
        print(f"\n  🦀 Buying {asset}...")
        print(f"     Amount: ${trade_amount:.2f}")
        
        # Execute market buy
        order = client.market_order_buy(
            client_order_id=f"deploy_{asset}_{int(time.time())}",
            product_id=f"{asset}-USD",
            quote_size=str(round(trade_amount, 2))
        )
        
        if order:
            # Handle response object
            order_id = order.order_id if hasattr(order, 'order_id') else str(order)[:8]
            print(f"     ✅ Success! Order ID: {order_id}...")
            trades_executed.append({
                "asset": asset,
                "amount": trade_amount,
                "order_id": order_id,
                "timestamp": datetime.now().isoformat()
            })
        else:
            print(f"     ❌ Failed to execute")
            
        # Rate limiting
        time.sleep(1)
        
    except Exception as e:
        print(f"     ❌ Error: {e}")

print()
print("="*60)
print("📈 DEPLOYMENT SUMMARY:")
print(f"  Trades executed: {len(trades_executed)}")
print(f"  Total deployed: ${sum(t['amount'] for t in trades_executed):.2f}")
print(f"  Reserve kept: ${reserve_amount:.2f}")

# Check new positions
print()
print("💼 UPDATED PORTFOLIO:")
print("-"*40)

time.sleep(2)  # Let orders settle

accounts = client.get_accounts()
total_value = 0

for account in accounts['accounts']:
    balance = float(account['available_balance']['value'])
    if balance > 0:
        currency = account['currency']
        print(f"  {currency}: {balance:.8f}")
        
        if currency == "USD":
            total_value += balance
        else:
            try:
                ticker = client.get_product(f"{currency}-USD")
                price = float(ticker.get('price', 0))
                usd_value = balance * price
                total_value += usd_value
                print(f"    → ${usd_value:.2f} USD")
            except:
                pass

print()
print(f"💎 TOTAL PORTFOLIO VALUE: ${total_value:.2f}")

# Calculate targets
daily_target = total_value * 0.04  # 4% daily
weekly_target = daily_target * 7

print()
print("🎯 TARGETS FROM CURRENT POSITION:")
print(f"  4% Daily: ${daily_target:.2f}")
print(f"  Weekly Goal: ${weekly_target:.2f}")

# Save deployment record
deployment_record = {
    "timestamp": datetime.now().isoformat(),
    "initial_balance": usd_balance,
    "deployed": sum(t['amount'] for t in trades_executed),
    "reserved": reserve_amount,
    "trades": trades_executed,
    "total_portfolio": total_value,
    "targets": {
        "daily": daily_target,
        "weekly": weekly_target
    }
}

with open("capital_deployment.json", "w") as f:
    json.dump(deployment_record, f, indent=2)

print()
print("🦀 CRAWDAD WISDOM:")
print("  • Positions built during quiet sun")
print("  • 20% reserved for solar storm shorts")
print("  • Alert system monitoring 24/7")
print("  • Ready for both directions!")
print()
print("✅ Deployment complete!")