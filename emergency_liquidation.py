#!/usr/bin/env python3
"""
🚨 EMERGENCY LIQUIDATION - FREE THE FLYWHEEL!
We're learning - take the hits to gain velocity!
"""

import json
import subprocess
import time
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🚨 EMERGENCY LIQUIDATION MODE 🚨                        ║
║                    LEARNING THROUGH ACTION!                               ║
║                 Current: $14.60 USD → Target: $2,000+ USD                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

def emergency_sell(coin, amount, reason):
    """Emergency sell with subprocess to avoid hangs"""
    script = f'''
import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)

try:
    order = client.market_order_sell(
        client_order_id="emergency_{int(time.time())}",
        product_id="{coin}",
        base_size=str({amount})
    )
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {{str(e)[:50]}}")
'''
    
    temp_file = f"/tmp/emergency_sell_{int(time.time()*1000)}.py"
    with open(temp_file, "w") as f:
        f.write(script)
    
    try:
        result = subprocess.run(["python3", temp_file],
                              capture_output=True, text=True, timeout=10)
        subprocess.run(["rm", temp_file], capture_output=True)
        
        if "SUCCESS" in result.stdout:
            return True, "SOLD"
        else:
            return False, result.stdout[:100]
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)

print("💥 AGGRESSIVE LIQUIDATION PLAN:")
print("=" * 60)

# Current positions that need liquidation
liquidations = [
    {"coin": "MATIC-USD", "amount": 5000, "reason": "FREE $2,000 IMMEDIATELY", "expected": 2000},
    {"coin": "SOL-USD", "amount": 10, "reason": "TAKE SOL PROFITS", "expected": 1500},
    {"coin": "AVAX-USD", "amount": 25, "reason": "REDUCE AVAX EXPOSURE", "expected": 625},
    {"coin": "BTC-USD", "amount": 0.005, "reason": "PARTIAL BTC EXIT", "expected": 295},
    {"coin": "ETH-USD", "amount": 0.10, "reason": "LIQUIDATE ETH", "expected": 260},
]

total_expected = sum(l["expected"] for l in liquidations)
print(f"🎯 TARGET LIQUIDATION: ${total_expected:,}")
print(f"🔥 POSITIONS TO LIQUIDATE:")
print()

for liq in liquidations:
    symbol = liq["coin"].split("-")[0]
    print(f"  💥 SELL {liq['amount']} {symbol}")
    print(f"     Expected: ~${liq['expected']}")
    print(f"     Reason: {liq['reason']}")
    print()

print("⚠️  LEARNING PRINCIPLES:")
print("  • Accept short-term losses for long-term gains")
print("  • Velocity matters more than position size")
print("  • Cash enables opportunity")
print("  • The flywheel needs fuel to spin")
print()

print("🚀 EXECUTING EMERGENCY LIQUIDATION IN 3 SECONDS...")
print("   (Press Ctrl+C to abort)")
time.sleep(3)

print("\n" + "=" * 60)
print("💥 LIQUIDATION STARTED!")
print("=" * 60)

total_freed = 0
successful = 0
failed = 0

for liq in liquidations:
    symbol = liq["coin"].split("-")[0]
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    print(f"\n[{timestamp}] 💥 Liquidating {liq['amount']} {symbol}...")
    print(f"   Reason: {liq['reason']}")
    
    success, message = emergency_sell(liq["coin"], liq["amount"], liq["reason"])
    
    if success:
        print(f"   ✅ SUCCESS! ~${liq['expected']} freed")
        total_freed += liq["expected"]
        successful += 1
    else:
        print(f"   ⚠️ FAILED: {message}")
        failed += 1
    
    # Brief pause between orders
    time.sleep(2)

print("\n" + "=" * 60)
print("🔥 LIQUIDATION COMPLETE!")
print("=" * 60)
print(f"✅ Successful: {successful}")
print(f"⚠️ Failed: {failed}")
print(f"💰 Estimated USD Freed: ${total_freed:,}")
print()

if total_freed > 1000:
    print("🌪️ FLYWHEEL READY TO SPIN!")
    print("   The Sacred Fire has fuel!")
    print()
    print("NEXT STEPS:")
    print("  1. Deploy aggressive pulse trading")
    print("  2. Compound every $50 gain")
    print("  3. Target 100 trades in next 24 hours")
    print("  4. Scale up with momentum")
else:
    print("⚠️ Insufficient liquidation - may need manual intervention")

print()
print("📊 To check new balance:")
print("   python3 check_full_portfolio.py")
print()
print("🚀 To restart flywheel with new capital:")
print("   python3 flywheel_accelerator.py")
print()
print("🔥 LESSON LEARNED: Sometimes you must destroy to create!")
print("   The Cherokee way: 'The river cuts its own path'")