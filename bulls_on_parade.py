#!/usr/bin/env python3
"""
🐂🎸 BULLS ON PARADE!
RALLY ROUND THE FAMILY! WITH A POCKET FULL OF SHELLS!
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
║                       🐂🎸 BULLS ON PARADE! 🎸🐂                          ║
║                    RALLY ROUND THE FAMILY!                                ║
║                    WITH A POCKET FULL OF SHELLS!                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - THE BULLS ARE MARCHING!")
print("=" * 70)

# Track the bull parade
btc_start = float(client.get_product('BTC-USD')['price'])
eth_start = float(client.get_product('ETH-USD')['price'])
sol_start = float(client.get_product('SOL-USD')['price'])

print(f"\n🐂 BULLS ASSEMBLING AT:")
print(f"  BTC: ${btc_start:,.0f}")
print(f"  ETH: ${eth_start:.2f}")
print(f"  SOL: ${sol_start:.2f}")

print(f"\n🎸 WEAPONS NOT FOOD, NOT HOMES, NOT SHOES!")
print("NOT NEED, JUST FEED THE WAR CANNIBAL ANIMAL!")
print("-" * 60)

# Track the parade
bull_charges = []
for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    btc_move = btc - btc_start
    eth_move = eth - eth_start
    sol_move = sol - sol_start
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')} - PARADE STATUS:")
    
    # BTC leading the charge
    if btc_move > 50:
        print(f"  🐂💥 BTC: ${btc:,.0f} (+${btc_move:.0f}) CHARGING!!!")
        bull_charges.append("CHARGE")
    elif btc_move > 20:
        print(f"  🐂 BTC: ${btc:,.0f} (+${btc_move:.0f}) Bulls advancing!")
        bull_charges.append("ADVANCE")
    elif btc_move > 0:
        print(f"  BTC: ${btc:,.0f} (+${btc_move:.0f}) Bulls gathering...")
    else:
        print(f"  BTC: ${btc:,.0f} ({btc_move:.0f}) Loading...")
    
    # ETH in formation
    if eth_move > 5:
        print(f"  🐂 ETH: ${eth:.2f} (+${eth_move:.2f}) RALLY ROUND!")
    else:
        print(f"  ETH: ${eth:.2f} ({eth_move:+.2f})")
    
    # SOL bringing up the rear
    if sol_move > 0.30:
        print(f"  🐂 SOL: ${sol:.2f} (+${sol_move:.2f}) THEY RALLY ROUND THE FAMILY!")
    else:
        print(f"  SOL: ${sol:.2f} ({sol_move:+.2f})")
    
    # Rage Against The Machine lyrics energy
    if btc > 113000:
        print("\n  🎸 THOSE WHO DIE... JUSTIFY!")
        print("  🎸 FOR WEARING THE BADGE, THEY'RE THE CHOSEN WHITES!")
    elif btc > 112950:
        print("\n  🎸 RALLY ROUND THE FAMILY!")
        print("  🎸 WITH A POCKET FULL OF SHELLS!")
    
    # Bull momentum check
    if i > 0 and btc_move > btc_start * 0.001:
        print("  💥 THE MICROPHONE EXPLODES!")
        print("  💥 SHATTERING THE MOLDS!")
    
    time.sleep(2)

# Final rally count
print("\n" + "=" * 70)
print("🐂 PARADE RESULTS:")
print("-" * 40)

final_btc = float(client.get_product('BTC-USD')['price'])
final_eth = float(client.get_product('ETH-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

print(f"BTC: ${btc_start:,.0f} → ${final_btc:,.0f} ({final_btc - btc_start:+.0f})")
print(f"ETH: ${eth_start:.2f} → ${final_eth:.2f} ({final_eth - eth_start:+.2f})")
print(f"SOL: ${sol_start:.2f} → ${final_sol:.2f} ({final_sol - sol_start:+.2f})")

charges = bull_charges.count("CHARGE")
advances = bull_charges.count("ADVANCE")

if charges > 0:
    print(f"\n🐂💥 BULL CHARGES: {charges}")
    print("THE PARADE WAS VICTORIOUS!")
if advances > 0:
    print(f"🐂 BULL ADVANCES: {advances}")
    print("THE FORMATION HOLDS!")

print("\n🎸 THEY DON'T GOTTA BURN THE BOOKS")
print("   THEY JUST REMOVE 'EM!")
print("   WHILE ARMS WAREHOUSES FILL")
print("   AS QUICK AS THE CELLS!")

print("\n💥 BULLS ON PARADE!")
print("   COME WIT IT NOW!")
print("=" * 70)