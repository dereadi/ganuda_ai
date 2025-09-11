#!/usr/bin/env python3
"""
📈 AFTERNOON UPTICK TRADER
==========================
Catch the 2-4 PM wave!
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

# Load config
config = json.load(open("/home/dereadi/.coinbase_config.json"))
client = RESTClient(api_key=config["api_key"], api_secret=config["api_secret"])

print("🏄 AFTERNOON UPTICK TRADER")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("Strategy: Ride the 2-4 PM institutional wave")
print()

# Check current balance
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"💰 Available USD: ${usd_balance:.2f}")
print()

# Allocate for afternoon surge
trade_amount = min(usd_balance * 0.5, 50)  # 50% or $50 max for safety

if trade_amount < 10:
    print("⚠️ Insufficient balance for trading")
else:
    print("📈 EXECUTING AFTERNOON UPTICK TRADES:")
    print("-"*40)
    
    # Priority order based on uptick strength
    trades = [
        ("SOL", 0.4),  # 40% - strongest uptick
        ("ETH", 0.35), # 35% - solid uptick
        ("BTC", 0.25), # 25% - stable uptick
    ]
    
    executed = []
    
    for symbol, allocation in trades:
        size = trade_amount * allocation
        
        if size >= 10:  # Minimum $10
            try:
                print(f"\n🏄 Surfing {symbol} uptick...")
                print(f"   Amount: ${size:.2f}")
                
                # Execute market buy
                order = client.market_order_buy(
                    client_order_id=f"uptick_{symbol}_{int(time.time())}",
                    product_id=f"{symbol}-USD",
                    quote_size=str(round(size, 2))
                )
                
                if order:
                    print(f"   ✅ Success!")
                    executed.append({
                        "symbol": symbol,
                        "amount": size,
                        "time": datetime.now().strftime('%H:%M:%S')
                    })
                
                time.sleep(1)  # Rate limit
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    print()
    print("="*60)
    print("📊 AFTERNOON UPTICK SUMMARY:")
    print(f"  Trades executed: {len(executed)}")
    print(f"  Total deployed: ${sum(t['amount'] for t in executed):.2f}")
    
    if executed:
        print("\n  Positions:")
        for trade in executed:
            print(f"    • {trade['symbol']}: ${trade['amount']:.2f} at {trade['time']}")
    
    print()
    print("⏰ EXIT STRATEGY:")
    print("  • Take profits at 3:30 PM")
    print("  • Or if prices rise 0.5%+")
    print("  • Stop loss at -0.3%")
    
    # Save trade record
    with open("afternoon_trades.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "strategy": "afternoon_uptick",
            "trades": executed,
            "total": sum(t['amount'] for t in executed)
        }, f, indent=2)

print()
print("🦀 Q-Dads riding the afternoon wave!")
print("Monitor for 3 PM power hour surge!")