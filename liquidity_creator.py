#!/usr/bin/env python3
"""
💧 LIQUIDITY CREATOR - Free up cash for trading
Sell small portions to enable crawdads and wolves to hunt
"""

import json
import subprocess
import time

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     💧 CREATING TRADING LIQUIDITY 💧                      ║
║                  Freeing the Crawdads & Wolves to Hunt                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

def execute_sell(coin, amount, symbol):
    """Execute sell using subprocess to avoid hangs"""
    script = f'''
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)

try:
    order = client.market_order_sell(
        client_order_id="liquidity_{int(time.time())}",
        product_id="{coin}",
        base_size="{amount}"
    )
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {{e}}")
'''
    
    with open("/tmp/sell_order.py", "w") as f:
        f.write(script)
    
    try:
        result = subprocess.run(["python3", "/tmp/sell_order.py"],
                              capture_output=True, text=True, timeout=10)
        if "SUCCESS" in result.stdout:
            return True
        else:
            print(f"  ⚠️ {symbol} sell failed: {result.stdout[:50]}")
            return False
    except Exception as e:
        print(f"  ⚠️ {symbol} sell error: {e}")
        return False

# Liquidity creation plan
sells = [
    {"coin": "MATIC-USD", "amount": 900, "symbol": "MATIC", "expected": 360},
    {"coin": "AVAX-USD", "amount": 8, "symbol": "AVAX", "expected": 200},
    {"coin": "LINK-USD", "amount": 5, "symbol": "LINK", "expected": 55},
]

print("🎯 LIQUIDITY CREATION PLAN:")
print("-" * 60)
total_expected = 0
for sell in sells:
    print(f"  • Sell {sell['amount']} {sell['symbol']} → ~${sell['expected']}")
    total_expected += sell['expected']
print(f"\n  TOTAL LIQUIDITY TO CREATE: ${total_expected}")
print()

print("⚠️  This will:")
print("  1. Keep 90% of MATIC position (8,142 tokens)")
print("  2. Keep 90% of AVAX position (79 tokens)")  
print("  3. Keep 50% of LINK position (6 tokens)")
print("  4. Create ~$615 USD for active trading")
print()

# Safety check
print("Ready to create liquidity? (This is needed for trading)")
print("Press Enter to proceed or Ctrl+C to cancel...")
input()

print("\n🚀 EXECUTING LIQUIDITY CREATION...")
print("=" * 60)

created_liquidity = 0
for sell in sells:
    print(f"\n💧 Selling {sell['amount']} {sell['symbol']}...")
    
    if execute_sell(sell['coin'], sell['amount'], sell['symbol']):
        print(f"  ✅ Success! ~${sell['expected']} freed")
        created_liquidity += sell['expected']
    
    time.sleep(2)  # Brief pause between orders

print("\n" + "=" * 60)
print(f"💰 LIQUIDITY CREATED: ~${created_liquidity}")
print()
print("🦀 The Crawdads can now hunt!")
print("🐺 The Wolves are ready to prowl!")
print()
print("Next steps:")
print("  1. Deploy crawdad swarm with new liquidity")
print("  2. Set stop losses on remaining positions")
print("  3. Begin AVAX swing trading $24-27")
print("  4. Accumulate SOL on dips < $145")