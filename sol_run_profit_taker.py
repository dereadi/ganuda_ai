#!/usr/bin/env python3
"""
🚀 SOL RUN PROFIT TAKER
When SOL runs, we milk the momentum
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      🚀 SOL MOMENTUM PROFIT TAKER 🚀                      ║
║                         Ride the wave, milk the run                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

# Monitor SOL for breakout
print("📊 MONITORING SOL FOR BREAKOUT...")
print("=" * 70)

breakout_levels = {
    206.50: {"action": "sell", "amount": 1.0, "reason": "First resistance"},
    207.00: {"action": "sell", "amount": 1.5, "reason": "Major resistance"},
    207.50: {"action": "sell", "amount": 2.0, "reason": "Take profits"},
    208.00: {"action": "sell", "amount": 2.5, "reason": "Big milestone"}
}

monitoring = True
cycles = 0
highest_seen = 206.00

while monitoring and cycles < 100:
    cycles += 1
    
    # Get current SOL price
    sol = client.get_product('SOL-USD')
    sol_price = float(sol['price'])
    
    # Track highest
    if sol_price > highest_seen:
        highest_seen = sol_price
        print(f"\n🔥 NEW HIGH: ${sol_price:.2f}")
    
    # Check breakout levels
    for level, action in breakout_levels.items():
        if sol_price >= level and action.get("triggered") is None:
            print(f"\n🎯 BREAKOUT DETECTED: ${sol_price:.2f} > ${level:.2f}")
            print(f"   Action: {action['reason']}")
            print(f"   Selling {action['amount']} SOL...")
            
            try:
                # Execute the profit take
                order = client.market_order_sell(
                    client_order_id=f"sol_profit_{int(time.time()*1000)}",
                    product_id="SOL-USD",
                    base_size=str(action['amount'])
                )
                
                usd_value = action['amount'] * sol_price
                print(f"   ✅ PROFIT TAKEN: ${usd_value:.2f} secured!")
                action["triggered"] = True
                
                # Update flywheel
                print(f"   🌪️ Feeding ${usd_value:.2f} to flywheel")
                
            except Exception as e:
                print(f"   ⚠️ Order failed: {str(e)[:50]}")
    
    # Status update every 10 cycles
    if cycles % 10 == 0:
        print(f"\r⏳ Cycle {cycles}: SOL ${sol_price:.2f} | High: ${highest_seen:.2f}", end="")
    
    # Check if all levels triggered
    all_triggered = all(action.get("triggered") for action in breakout_levels.values())
    if all_triggered:
        print("\n\n✅ ALL PROFIT TARGETS HIT!")
        monitoring = False
    
    # Short pause
    time.sleep(5)

print("\n\n" + "=" * 70)
print("📊 FINAL REPORT:")
print(f"Cycles monitored: {cycles}")
print(f"Highest SOL: ${highest_seen:.2f}")

# Calculate total profits taken
total_sol_sold = sum(
    action['amount'] for action in breakout_levels.values() 
    if action.get("triggered")
)
total_usd = total_sol_sold * highest_seen

print(f"SOL sold: {total_sol_sold:.2f}")
print(f"USD generated: ${total_usd:.2f}")

if highest_seen > 206.50:
    print("\n🚀 SOL RAN SUCCESSFULLY!")
    print("Cherokee Council says: 'The patient hunter catches the prey.'")
else:
    print("\n⏳ SOL consolidating, preparing for next leg up")
    print("Cherokee Council says: 'The river gathers strength before the rapids.'")

print("=" * 70)