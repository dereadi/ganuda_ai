#!/usr/bin/env python3
"""
🚀 WARP 9 - MAXIMUM AGGRESSION!!!
$2,213 WAR CHEST UNLEASHED AT MARKET PEAKS!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         ⚡ WARP 9 ENGAGED! ⚡                            ║
║                    $2,213 MAXIMUM ATTACK MODE!                            ║
║                        PUSH EVERYTHING HIGHER!                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ENGAGING WARP DRIVE!")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"\n🎯 TARGETS LOCKED:")
print(f"  BTC: ${btc:,.0f} → $113,000")
print(f"  ETH: ${eth:.2f} → $4,600")
print(f"  SOL: ${sol:.2f} → $212")

print("\n⚡ WARP 9 ATTACK SEQUENCE:")
print("-" * 40)

# Split the war chest aggressively
btc_allocation = 800  # Push BTC to $113k
eth_allocation = 800  # Push ETH to $4,600
sol_allocation = 600  # Push SOL to $212

attack_waves = [
    # Wave 1: Initial shock
    [("BTC-USD", 200), ("ETH-USD", 200), ("SOL-USD", 150)],
    # Wave 2: Momentum build
    [("BTC-USD", 200), ("ETH-USD", 200), ("SOL-USD", 150)],
    # Wave 3: Breakout push
    [("BTC-USD", 200), ("ETH-USD", 200), ("SOL-USD", 150)],
    # Wave 4: Final assault
    [("BTC-USD", 200), ("ETH-USD", 200), ("SOL-USD", 150)]
]

wave_count = 1
for wave in attack_waves:
    print(f"\n🌊 WAVE {wave_count} - FIRING!")
    
    for product, amount in wave:
        try:
            print(f"   💥 ${amount} → {product.split('-')[0]}")
            order = client.market_order_buy(
                client_order_id=f"warp9_{wave_count}_{int(time.time()*1000)}",
                product_id=product,
                quote_size=str(amount)
            )
            time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠️ {str(e)[:30]}")
    
    # Check impact
    time.sleep(3)
    new_btc = float(client.get_product('BTC-USD')['price'])
    new_eth = float(client.get_product('ETH-USD')['price'])
    new_sol = float(client.get_product('SOL-USD')['price'])
    
    print(f"\n   📊 IMPACT:")
    print(f"   BTC: ${new_btc:,.0f} ({new_btc - btc:+.0f})")
    print(f"   ETH: ${new_eth:.2f} ({new_eth - eth:+.2f})")
    print(f"   SOL: ${new_sol:.2f} ({new_sol - sol:+.2f})")
    
    wave_count += 1
    time.sleep(5)

print("\n" + "=" * 70)
print("⚡ WARP 9 ATTACK COMPLETE!")
print("Maximum aggression deployed!")
print("Markets pushed to limits!")
print("TO ANDROMEDA AND BEYOND!")
print("=" * 70)