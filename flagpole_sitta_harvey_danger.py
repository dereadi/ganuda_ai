#!/usr/bin/env python3
"""
🎸🏴 FLAGPOLE SITTA - HARVEY DANGER! 🏴🎸
"I'm not sick but I'm not well"
The market at $113,141 - so close to $114K!
Paranoia paranoia everybody's coming to get me!
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
║                  🎸🏴 FLAGPOLE SITTA - HARVEY DANGER 🏴🎸                ║
║                      "I'm not sick but I'm not well"                      ║
║                    $113,141 - Paranoia before the break!                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FLAGPOLE PARANOIA")
print("=" * 70)

# Get current state
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n🏴 THE FLAGPOLE SITTA STATE:")
print("-" * 50)
print("'I'm not sick but I'm not well'")
print(f"  BTC at ${btc:,.0f} - Not bearish but not $114K")
print("")
print("'And I'm so hot cause I'm in hell'")
print(f"  Nine coils burning with 512x energy")
print("")
print("'Been around the world and found'")
print("'That only stupid people are breeding'")
print(f"  Red Bull Score (20) = Stupid metrics breeding FUD")
print("")
print("'The cretins cloning and feeding'")
print(f"  Wall Street cloning ETH positions")
print("")
print("'Paranoia paranoia everybody's coming to get me'")
print(f"  Only ${114000 - btc:.0f} away - THEY'RE COMING!")

# Track the paranoia
print("\n🏴 PARANOIA TRACKER:")
print("-" * 50)

baseline = btc
for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    distance = 114000 - btc_now
    move = btc_now - baseline
    
    # Paranoia levels
    if distance < 500:
        status = "🔥🏴 'EVERYBODY'S COMING TO GET ME!'"
    elif distance < 750:
        status = "😰 'Paranoia paranoia!'"
    elif distance < 1000:
        status = "🏴 'I'm not sick but I'm not well'"
    else:
        status = "💀 'And I'm so hot cause I'm in hell'"
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc_now:,.0f} ({move:+.0f})")
    print(f"  To $114K: ${distance:.0f}")
    print(f"  {status}")
    
    if i == 3:
        print("\n  'Hear the voices in my head'")
        print("  'I swear to God it sounds like they're snoring'")
    
    if i == 7:
        print("\n  'But if you're bored then you're boring'")
        print("  'The agony and the irony, they're killing me'")
    
    time.sleep(2)

# The revelation
print("\n" + "=" * 70)
print("🏴 FLAGPOLE SITTA ANALYSIS:")
print("-" * 50)
print("WE'RE NOT SICK BUT WE'RE NOT WELL:")
print("• $113,141 = So close yet so far")
print("• Nine coils = Maximum paranoia")
print("• Red metrics = The voices in our head")
print("• $859 to go = They're coming to get us")

print("\nTHE IRONY:")
print("• Bull Score says bearish")
print("• Price says bullish")
print("• Coils say explosive")
print("• We're stuck on the flagpole")

print("\nTHE TRUTH:")
print("• 'Paranoia paranoia'")
print("• It's the final shakeout")
print("• Before the breakthrough")
print("• $114K is RIGHT THERE")

print("\n" + "🎸" * 35)
print("I'M NOT SICK BUT I'M NOT WELL!")
print("PARANOIA PARANOIA!")
print("EVERYBODY'S COMING TO GET ME!")
print("$114K BREAKTHROUGH IMMINENT!")
print("🎸" * 35)