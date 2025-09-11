#!/usr/bin/env python3
"""
🎸😢 CREEP - RADIOHEAD VIBES AT $113K 😢🎸
We don't belong here at $113K
$114K is where we're special
But we're just creeping along
What the hell are we doing here?
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
║                    🎸😢 CREEP - RADIOHEAD MOOD 😢🎸                      ║
║                        The $113K Existential Crisis                       ║
║                     What the hell are we doing here?                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - CREEP MODE")
print("=" * 70)

# Get current creeping status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n😢 THE CREEP STATE:")
print("-" * 50)
print("Thom Yorke understood this feeling:")
print(f"  BTC at ${btc:,.0f} - Not where we belong")
print(f"  Target $114K - Where we'd be special")
print(f"  Distance: ${114000 - btc:.0f} - So perfect, so far")
print("")
print("The market doesn't care about our nine coils")
print("Red metrics mock us from their screens")
print("We're just creeping along the edge")

# Track the creeping
print("\n🐌 CREEP TRACKER:")
print("-" * 50)

baseline = btc
creep_count = 0

for i in range(12):
    btc_now = float(client.get_product('BTC-USD')['price'])
    distance = 114000 - btc_now
    move = btc_now - baseline
    
    # Determine creep level
    if btc_now >= 114000:
        status = "🚀✨ We're special! We belong here!"
        creep_count = 0
    elif abs(move) < 10:
        status = "😢 Just creeping... not special"
        creep_count += 1
    elif move > 20:
        status = "😮 Running? We don't usually do that"
        creep_count = 0
    elif move < -20:
        status = "😔 Creeping backwards now"
        creep_count += 1
    else:
        status = "🐌 Still a creep, still a weirdo"
        creep_count += 1
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc_now:,.0f} ({move:+.0f})")
    print(f"  To belong: ${distance:.0f} away")
    print(f"  {status}")
    
    if creep_count > 3:
        print("  Creep level: Maximum existential crisis")
    
    if i == 5:
        print("\n  What are we doing here?")
        print("  Nine coils wound but still creeping")
    
    if i == 9:
        print("\n  We want to be special")
        print("  $114K would make us special")
    
    time.sleep(2)

# Check our creep resources
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print("\n💰 CREEP RESOURCES:")
print(f"  USD: ${usd_balance:.2f}")
print(f"  Status: {'Ready to be special' if usd_balance > 50 else 'Not enough to be special'}")

# The existential analysis
print("\n" + "=" * 70)
print("😢 CREEP ANALYSIS:")
print("-" * 50)
print("WHY WE'RE CREEPING:")
print("• $113K = Not where we belong")
print("• Nine coils = Should make us special")
print("• Red metrics = They're so perfect")
print("• Sawtooth = We're so broken")
print("• $114K = Where we'd finally belong")

print("\nTHE RADIOHEAD TRUTH:")
print("• Sometimes you creep before you run")
print("• Sometimes you're weird before you're special")
print("• The ninth coil makes us different")
print("• Different becomes special at $114K")

print("\nTHE BREAKTHROUGH:")
print("• Creeps become butterflies")
print("• Weirdos become prophets")
print("• Nine coils become explosions")
print("• $113K becomes $114K")
print("• We WILL be special")

print("\n" + "🎸" * 35)
print("WE'RE CREEPS AT $113K")
print("BUT WE'RE ABOUT TO BE SPECIAL")
print("$114K IS WHERE WE BELONG")
print("THE NINTH COIL WILL TAKE US THERE")
print("🎸" * 35)