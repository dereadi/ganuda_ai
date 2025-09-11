#!/usr/bin/env python3
"""
🤒 DOWN WITH THE SICKNESS - DISTURBED
"Get up, come on get down with the sickness"
The market turned... from up to DOWN
Seven seals can work both ways
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
║                  🤒 DOWN WITH THE SICKNESS 🤒                             ║
║                          DISTURBED                                        ║
║            "Get up, come on get down with the sickness"                   ║
║                    The Market Turned SICK                                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - OH WA AH AH AH")
print("=" * 70)

# Check the sickness
btc_start = float(client.get_product('BTC-USD')['price'])
print(f"\n🤒 The sickness begins at: ${btc_start:,.0f}")

if btc_start < 113050:
    print("📉 Already infected!")
    print("   The sickness is spreading...")

print("\n🤒 TRACKING THE SICKNESS:")
print("-" * 50)

lowest = btc_start
btc_samples = []

for i in range(15):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    btc_samples.append(btc)
    drop = btc - btc_start
    
    if btc < lowest:
        lowest = btc
    
    if i % 3 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
        print(f"  BTC: ${btc:,.0f} ({drop:+.0f})")
        print(f"  ETH: ${eth:.2f}")
        print(f"  SOL: ${sol:.2f}")
        
        if drop < -50:
            print("  🤒🤒🤒 'OH WA AH AH AH!'")
            print("  MAJOR SICKNESS SPREADING!")
        elif drop < -30:
            print("  🤒🤒 'Get up, come on get down!'")
            print("  The infection deepens!")
        elif drop < -10:
            print("  🤒 'With the sickness!'")
            print("  Bears are taking control!")
        elif drop < 0:
            print("  📉 'Open up your hate'")
            print("  The weakness shows...")
        else:
            print("  📊 'And let it flow into me'")
            print("  Fighting the infection...")
    
    time.sleep(2)

# Sickness report
final_btc = btc_samples[-1]
total_drop = final_btc - btc_start
max_drop = lowest - btc_start

print("\n" + "=" * 70)
print("🤒 SICKNESS REPORT:")
print("-" * 50)
print(f"Started at: ${btc_start:,.0f}")
print(f"Current: ${final_btc:,.0f}")
print(f"Lowest point: ${lowest:,.0f}")
print(f"Total movement: ${total_drop:+.0f}")
print(f"Maximum sickness: ${max_drop:+.0f}")

# Diagnosis
print("\n💊 DIAGNOSIS:")
print("-" * 50)

if max_drop < -100:
    print("🤒🤒🤒 SEVERE INFECTION!")
    print("'Drowning deep in my sea of loathing'")
    print("Major support broken!")
elif max_drop < -50:
    print("🤒🤒 MODERATE SICKNESS")
    print("'Get up, come on get down with the sickness'")
    print("Testing support levels...")
elif max_drop < -20:
    print("🤒 MILD SYMPTOMS")
    print("'You mother get up'")
    print("Normal pullback after seven seals...")
else:
    print("💊 FIGHTING IT OFF")
    print("'I can see inside you'")
    print("Bulls trying to recover...")

print("\n🎵 DISTURBED WISDOM:")
print("-" * 50)
print("• Seven seals can break both ways")
print("• What goes up must come down")
print("• The sickness spreads through fear")
print("• 'OH WA AH AH AH!'")
print("• Get down with it or get out")

# Support levels
print("\n🏥 SUPPORT LEVELS (HOSPITALS):")
print("-" * 50)

supports = [
    (113000, "First aid"),
    (112900, "Emergency room"),
    (112800, "ICU"),
    (112700, "Critical condition"),
    (112500, "Life support")
]

for support, condition in supports:
    if final_btc > support:
        print(f"${support:,} ({condition}): Holding above ✓")
    else:
        print(f"${support:,} ({condition}): BROKEN! 🤒")

print("\n🤒 'GET UP, COME ON GET DOWN'")
print("   'WITH THE SICKNESS!'")
print("   OH WA AH AH AH!")
print("=" * 70)