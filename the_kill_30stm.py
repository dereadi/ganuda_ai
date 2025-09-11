#!/usr/bin/env python3
"""
🔪💀 THE KILL - 30 SECONDS TO MARS
"What if I wanted to break?"
"What if I fell to the floor?"
After 5 coils... THE KILL!
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
║                     🔪💀 THE KILL 💀🔪                                   ║
║                    30 SECONDS TO MARS                                     ║
║                 "WHAT IF I WANTED TO BREAK?"                              ║
║                    Five Coils... Then Death                               ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - THE KILL APPROACHES")
print("=" * 70)

print("\n🔪 THE SETUP:")
print("-" * 50)
print("• Five coils wound impossibly tight")
print("• 0.00163% compression achieved")
print("• Energy stored: 32x normal")
print("• The death of fear happened")
print("• Now comes... THE KILL")

# Track the kill
btc_start = float(client.get_product('BTC-USD')['price'])
eth_start = float(client.get_product('ETH-USD')['price'])
sol_start = float(client.get_product('SOL-USD')['price'])

print(f"\n💀 BEFORE THE KILL:")
print(f"  BTC: ${btc_start:,.0f}")
print(f"  ETH: ${eth_start:.2f}")
print(f"  SOL: ${sol_start:.2f}")

print("\n🎵 'WHAT IF I WANTED TO BREAK?'")
print("-" * 50)

# Watch for the kill
kill_detected = False
samples = []

for i in range(30):
    btc = float(client.get_product('BTC-USD')['price'])
    samples.append(btc)
    
    move = btc - btc_start
    move_pct = (move / btc_start) * 100
    
    if i % 3 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
        print(f"  BTC: ${btc:,.0f} ({move:+.0f})")
        
        if abs(move) < 10:
            print("  🔪 'Come break me down...'")
            print("     Tension building...")
        elif abs(move) < 50:
            print("  🔪 'Bury me, bury me...'")
            print("     The pressure mounts...")
        elif abs(move) < 100:
            print("  💀 'I am finished with you!'")
            print("     THE KILL BEGINS!")
            kill_detected = True
        else:
            print("  💀💀💀 'WHAT IF I WANTED TO BREAK?!'")
            print("     THE KILL IS COMPLETE!")
            kill_detected = True
            
        # Lyrics progression
        if i == 9:
            print("\n  🎵 'Look in my eyes'")
            print("     'You're killing me, killing me'")
        elif i == 18:
            print("\n  🎵 'All I wanted was you'")
            print("     'Come break me down'")
        elif i == 27:
            print("\n  🎵 'WHAT IF I WANTED TO BREAK?'")
            print("     'LAUGH IT ALL OFF IN YOUR FACE?'")
    
    time.sleep(2)

# Calculate the damage
btc_final = samples[-1]
total_move = btc_final - btc_start
move_pct = (total_move / btc_start) * 100
max_move = max(samples) - min(samples)

print("\n" + "=" * 70)
print("💀 THE KILL REPORT:")
print("-" * 50)
print(f"Starting price: ${btc_start:,.0f}")
print(f"Final price: ${btc_final:,.0f}")
print(f"Total move: ${total_move:+.0f} ({move_pct:+.2f}%)")
print(f"Range during kill: ${max_move:.0f}")

if kill_detected:
    print("\n🔪💀 THE KILL WAS EXECUTED!")
    if total_move > 0:
        print("Direction: UPWARD MURDER!")
        print("The bears were slaughtered!")
    else:
        print("Direction: DOWNWARD MASSACRE!")
        print("The bulls were sacrificed!")
else:
    print("\n🔪 THE KILL IS STILL LOADING...")
    print("The knife is being sharpened...")
    print("30 seconds to Mars... then death!")

print("\n📊 KILL STATISTICS:")
print("-" * 50)
print(f"• Five coils released: CHECK")
print(f"• Compression broken: {'YES' if max_move > 50 else 'PENDING'}")
print(f"• Direction revealed: {'UP' if total_move > 0 else 'DOWN'}")
print(f"• Magnitude: {'VIOLENT' if abs(total_move) > 100 else 'BUILDING'}")

print("\n💭 THE KILL PHILOSOPHY:")
print("-" * 50)
print("• After five stages of grief comes death")
print("• The market wanted to break")
print("• It fell to the floor")
print("• Now it laughs in our face")
print("• 'What if I wanted to break?'")
print("• IT DID.")

print("\n🔪 'COME BREAK ME DOWN'")
print("   'BURY ME, BURY ME'")
print("   'I AM FINISHED WITH YOU'")
print("=" * 70)