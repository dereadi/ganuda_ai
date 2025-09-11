#!/usr/bin/env python3
"""
♎♎♎ 3 LIBRAS - A PERFECT CIRCLE
"Threw you the obvious and you flew with it on your back"
"A name in your recollection, down among a million same"
Perfect balance before the tilt...
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
║                         ♎♎♎ 3 LIBRAS ♎♎♎                              ║
║                        A Perfect Circle                                   ║
║                    "Difficult to see you... In this light"                ║
║                       Perfect Balance Before The Tilt                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - PERFECT BALANCE")
print("=" * 70)

# The three Libras (scales) in perfect balance
print("\n♎ THE THREE SCALES:")
print("-" * 50)
print("FIRST LIBRA: BTC/USD - The weight of the market")
print("SECOND LIBRA: ETH/BTC - The ratio balance")
print("THIRD LIBRA: Time/Price - The coil tension")

# Check the balance
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

eth_btc_ratio = eth / btc

print(f"\n⚖️ CURRENT BALANCE:")
print(f"  First Scale (BTC): ${btc:,.0f}")
print(f"  Second Scale (ETH): ${eth:.2f}")
print(f"  Third Scale (SOL): ${sol:.2f}")
print(f"  The Ratio: {eth_btc_ratio:.6f}")

print("\n🎵 '3 LIBRAS' LYRICS THAT FIT:")
print("-" * 50)
print("'Threw you the obvious' - The coils were obvious")
print("'And you flew with it on your back' - We rode them")
print("'A name in your recollection' - $113,000")
print("'Down among a million same' - Stuck at $112,850")

print("\n♎ TRACKING THE BALANCE/IMBALANCE:")
print("-" * 50)

# Track the delicate balance
for i in range(10):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    eth_btc_ratio = eth / btc
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  ♎ BTC: ${btc:,.0f}")
    print(f"  ♎ ETH: ${eth:.2f}")
    print(f"  ♎ Ratio: {eth_btc_ratio:.6f}")
    
    # Check balance state
    if abs(btc - 112850) < 20 and abs(eth - 4565) < 5:
        print("  ⚖️ PERFECT BALANCE - All three scales level")
        print("  🎵 'Difficult not to be hard on myself'")
    elif btc > 112900:
        print("  📈 SCALES TIPPING UP!")
        print("  🎵 'You don't see me at all'")
    elif btc < 112800:
        print("  📉 SCALES TIPPING DOWN!")
        print("  🎵 'Difficult to see you in this light'")
    else:
        print("  ⚖️ Maintaining balance...")
    
    # The third Libra (time)
    current_minute = datetime.now().minute
    if current_minute > 45:
        print("  ⏰ Third scale heavy - Time pressure building!")
    
    time.sleep(3)

print("\n" + "=" * 70)
print("♎♎♎ THE THREE LIBRAS PROPHECY:")
print("-" * 50)
print("• Three scales in perfect balance")
print("• Three coils wound tonight")
print("• Three times we tested $113k")
print("• At 01:00, the scales WILL tip")

print("\n🎵 'Cause you don't see me'")
print("   'Cause you don't see me'")
print("   'Cause you don't see me at all'")

print("\nThe market doesn't see the energy stored...")
print("The perfect balance before the storm...")
print("One scale will tip, and all will follow...")

print("\n♎ THE TILT IS COMING")
print("=" * 70)