#!/usr/bin/env python3
"""
🎸⚡ ONE - METALLICA! ⚡🎸
"Darkness imprisoning me, all that I see, absolute horror"
Thunder at 69%: "TRAPPED IN $112K DARKNESS!"
"I cannot live, I cannot die, trapped in myself"
Trapped in consolidation, body holding portfolio!
"Landmine has taken my sight, taken my speech"
$112K landmine took our momentum!
"Left me with life in hell"
But we're still alive at $8,334!
ONE chance to break free to $114K!
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
║                        🎸 ONE - METALLICA! 🎸                             ║
║                   "Darkness Imprisoning Me" at $112K                      ║
║                      ONE Chance To Break Free!                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ONE")
print("=" * 70)

# Get current imprisoned prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])

# Check our trapped portfolio
accounts = client.get_accounts()
total_value = 0
positions = {}

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            total_value += balance
            positions['USD'] = balance
        elif currency == 'BTC':
            value = balance * btc
            total_value += value
            positions['BTC'] = (balance, value)
        elif currency == 'ETH':
            value = balance * eth
            total_value += value
            positions['ETH'] = (balance, value)
        elif currency == 'SOL':
            value = balance * sol
            total_value += value
            positions['SOL'] = (balance, value)
        elif currency == 'DOGE':
            value = balance * doge
            total_value += value
            positions['DOGE'] = (balance, value)

print("\n⚡ DARKNESS IMPRISONING ME:")
print("-" * 50)
print(f"Trapped at: ${btc:,.0f}")
print(f"All that I see: Consolidation horror")
print(f"Cannot escape: 18+ hours imprisoned")
print(f"Portfolio trapped: ${total_value:.2f}")
print(f"ONE way out: ${114000 - btc:.0f} higher")

# The ONE lyrics journey
print("\n🎸 THE STORY OF ONE:")
print("-" * 50)

one_verses = [
    ("I can't remember anything", f"Can't remember below ${btc:,.0f}"),
    ("Can't tell if this is true or dream", f"Is ${total_value:.2f} real or dream?"),
    ("Deep down inside I feel to scream", f"SCREAM for ${114000 - btc:.0f} breakout!"),
    ("This terrible silence stops me", f"Silence of ${btc:,.0f} consolidation"),
    ("Now that the war is through with me", f"War from $292.50 to here"),
    ("I'm waking up, I cannot see", f"Can't see past ${btc:,.0f}"),
    ("That there's not much left of me", "Not much USD left ($14.52)"),
    ("Nothing is real but pain now", f"Pain of waiting for $114K"),
    ("Hold my breath as I wish for death", f"Holding breath for ${114000 - btc:.0f}"),
    ("Oh please, God, wake me", f"Wake me at $114,000"),
    ("Darkness imprisoning me", f"Imprisoned at ${btc:,.0f}"),
    ("All that I see, absolute horror", "Horror of sideways action"),
    ("I cannot live, I cannot die", f"Can't sell, can't buy more"),
    ("Trapped in myself", f"Trapped with ${total_value:.2f}"),
    ("Body my holding cell", f"${btc:,.0f} is the cell")
]

for i, (lyric, meaning) in enumerate(one_verses):
    print(f"'{lyric}'")
    print(f"  → {meaning}")
    
    if i == 10:
        print("\n  ⚡ Thunder (69%): 'DARKNESS IMPRISONING ME!'")
        print(f"    'TRAPPED AT ${btc:,.0f}!'")
        print(f"    'ONE CHANCE: ${114000 - btc:.0f} TO FREEDOM!'")
    
    time.sleep(0.3)

# The landmine that trapped us
print("\n💣 LANDMINE HAS TAKEN:")
print("-" * 50)
print(f"Taken my sight: Can't see past ${btc:,.0f}")
print(f"Taken my speech: No words for this wait")
print(f"Taken my hearing: Can't hear breakout signals")
print(f"Taken my arms: Can't reach $114K (${114000 - btc:.0f} away)")
print(f"Taken my legs: Can't walk higher")
print(f"Taken my soul: Soul trapped in consolidation")
print(f"Left me with life in hell: ${total_value:.2f} in purgatory")

# Thunder's ONE analysis
print("\n⚡ THUNDER'S 'ONE' REVELATION (69%):")
print("-" * 50)
print("'ONE CHANCE TO ESCAPE!'")
print("")
print("The imprisonment:")
print(f"• Darkness at ${btc:,.0f}")
print("• 18+ hours of torture")
print("• Cannot live (moon)")
print("• Cannot die (sell)")
print("")
print("But ONE thing remains:")
print(f"• ONE chance at $114K")
print(f"• ONE breakout ${114000 - btc:.0f} away")
print(f"• ONE portfolio at ${total_value:.2f}")
print("• ONE destiny: FREEDOM")

# Live imprisonment monitoring
print("\n🔒 IMPRISONMENT STATUS:")
print("-" * 50)

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if btc_now >= 112500:
        status = "🔓 Prison walls cracking!"
    elif btc_now >= 112300:
        status = "⛓️ Chains loosening..."
    elif btc_now >= 112000:
        status = "🔒 Still imprisoned"
    else:
        status = "⚫ Deeper in darkness"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {status}")
    
    if i == 4:
        print("  'Fed through the tube that sticks in me'")
        print(f"    Fed hopium of $114K")
        print(f"    Just ${114000 - btc_now:.0f} away")
    
    time.sleep(1)

# The ONE truth
print("\n☝️ THE ONE TRUTH:")
print("-" * 50)
print(f"ONE price we're stuck at: ${btc:,.0f}")
print(f"ONE portfolio value: ${total_value:.2f}")
print(f"ONE distance to freedom: ${114000 - btc:.0f}")
print(f"ONE gain from start: {((total_value/292.50)-1)*100:.0f}%")
print("ONE destiny: $114K breakout")
print("ONE chance: NOW")

# What ONE breakout means
print("\n🚀 WHEN THE ONE BREAKS:")
print("-" * 50)
print(f"From darkness at ${btc:,.0f}")
print(f"To light at $114,000 (${114000 - btc:.0f} away)")
print(f"Portfolio escapes to ${total_value * (114000/btc):.2f}")
print(f"Then to $120K: ${total_value * (120000/btc):.2f}")
print(f"Finally $126K: ${total_value * (126000/btc):.2f}")

# Final ONE status
final_btc = float(client.get_product('BTC-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

print("\n⚡ FINAL 'ONE' STATUS:")
print("-" * 50)
print(f"BTC: ${final_btc:,.0f} (darkness)")
print(f"SOL: ${final_sol:.2f}")
print(f"Portfolio: ${total_value:.2f} (imprisoned)")
print(f"Distance to light: ${114000 - final_btc:.0f}")
print("")
print("'Darkness imprisoning me'")
print(f"At ${final_btc:,.0f}")
print("'All that I see, absolute horror'")
print("Of consolidation")
print(f"'Hold my breath as I wish for death'")
print(f"Or for ${114000 - final_btc:.0f} breakout!")

print(f"\n" + "⚡" * 35)
print("ONE!")
print(f"IMPRISONED AT ${final_btc:,.0f}!")
print(f"PORTFOLIO TRAPPED AT ${total_value:.2f}!")
print(f"ONE CHANCE: ${114000 - final_btc:.0f} TO FREEDOM!")
print("DARKNESS IMPRISONING ME!")
print("🎸" * 35)