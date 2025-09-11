#!/usr/bin/env python3
"""
🎸🦋 BULLET WITH BUTTERFLY WINGS - SMASHING PUMPKINS! 🦋🎸
"Despite all my rage I am still just a rat in a cage"
Nine coils wound, $113K cage, $114K just out of reach
Billy Corgan felt this exact pain!
THE WORLD IS A VAMPIRE!
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
║           🎸🦋 BULLET WITH BUTTERFLY WINGS - SMASHING PUMPKINS 🦋🎸       ║
║                  "Despite all my rage I am still just                     ║
║                        a rat in a cage"                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - RAT IN A CAGE")
print("=" * 70)

# Get current cage status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n🦋 THE CAGE:")
print("-" * 50)
print("'The world is a vampire'")
print("  Wall Street sucking liquidity")
print("")
print("'Sent to drain'")
print("  Red metrics draining confidence")
print("")
print("'Secret destroyers'")
print("  Whales with their sawtooth pattern")
print("")
print("'Hold you up to the flames'")
print(f"  Holding at ${btc:,.0f} - SO CLOSE TO $114K!")
print("")
print("'And what do I get'")
print("'For my pain?'")
print(f"  Only ${114000 - btc:.0f} away from freedom!")
print("")
print("'Despite all my rage I am still just a rat in a cage'")
print("  Nine coils wound but STILL CAGED!")

# Track the rage
print("\n🔥 RAGE MONITOR:")
print("-" * 50)

baseline = btc
rage_level = 0

for i in range(12):
    btc_now = float(client.get_product('BTC-USD')['price'])
    distance = 114000 - btc_now
    move = btc_now - baseline
    
    # Determine rage level
    if btc_now >= 114000:
        status = "🦋🚀 'JESUS WAS AN ONLY SON!' - FREE AT LAST!"
        rage_level = 0
    elif distance < 500:
        status = "🔥🔥🔥 'DESPITE ALL MY RAGE!' - SO CLOSE!"
        rage_level += 2
    elif distance < 750:
        status = "🔥🔥 'Tell me I'm the only one!' - RAGING!"
        rage_level += 1
    elif distance < 1000:
        status = "🔥 'And I still believe that I cannot be saved'"
        rage_level += 1
    else:
        status = "🦋 'Rat in a cage' - Trapped at $113K"
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc_now:,.0f} ({move:+.0f})")
    print(f"  Cage bars: ${distance:.0f} to freedom")
    print(f"  {status}")
    print(f"  Rage level: {'🔥' * min(rage_level, 10)}")
    
    if i == 4:
        print("\n  'Even though I know'")
        print("  'I suppose I'll show'")
        print("  'All my cool and cold'")
        print("  'Like old Job'")
    
    if i == 8:
        print("\n  'Someone will say what is lost can never be saved'")
        print("  'Despite all my rage I am still just a rat in a cage'")
    
    time.sleep(2)

# Check our ammunition
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print("\n💰 CAGE RESOURCES:")
print(f"  USD ammo: ${usd_balance:.2f}")
print(f"  Status: {'🔥 Ready to rage!' if usd_balance > 50 else '⚠️ Need more rage fuel!'}")

# The truth
print("\n" + "=" * 70)
print("🦋 BULLET WITH BUTTERFLY WINGS TRUTH:")
print("-" * 50)
print("THE CAGE:")
print("• $113K = Our rat cage")
print("• $114K = Freedom")
print("• Nine coils = Maximum rage compression")
print("• Red metrics = The vampire world")
print("• Sawtooth = Secret destroyers")

print("\nDESPITE ALL OUR RAGE:")
print("• We're still trapped at $113K")
print("• But rage builds pressure")
print("• Pressure breaks cages")
print("• The butterfly will emerge")
print("• With bullet wings")

print("\nTHE PROPHECY:")
print("• 'Tell me I'm the only one'")
print("• The ninth coil IS the only one")
print("• Never been done before")
print("• The cage WILL break")
print("• Freedom at $114K")

print("\n" + "🎸" * 35)
print("DESPITE ALL MY RAGE")
print("I AM STILL JUST A RAT IN A CAGE!")
print("BUT THIS CAGE IS ABOUT TO EXPLODE!")
print("THE WORLD IS A VAMPIRE!")
print("AND WE'RE BREAKING FREE!")
print("🎸" * 35)