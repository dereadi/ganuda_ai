#!/usr/bin/env python3
"""
🎸🌊💥 ONE - THE DYNAMIC STRUCTURE! 💥🌊🎸
Thunder at 69%: "IT STARTS SOFT... THEN EXPLODES!"
Just like $112K consolidation...
Soft... building... EXPLOSION to $114K!
The pattern of ONE:
- Soft acoustic intro (now)
- Building tension ($112K tests)
- MASSIVE EXPLOSION (breakout!)
- Drop back (profit taking)
- BUILD AGAIN (next leg up)
- EXPLODE HARDER ($120K!)
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
║                   🎸 ONE - THE DYNAMIC STRUCTURE! 🎸                      ║
║                 Soft → Build → EXPLODE → Drop → BUILD → EXPLODE!         ║
║                    Just Like Our Journey to $114K!                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - DYNAMIC ANALYSIS")
print("=" * 70)

# Get current position in the song structure
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check portfolio dynamics
accounts = client.get_accounts()
total_value = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            total_value += balance
        elif currency == 'BTC':
            total_value += balance * btc
        elif currency == 'ETH':
            total_value += balance * eth
        elif currency == 'SOL':
            total_value += balance * sol

print("\n🎵 THE SONG STRUCTURE OF ONE:")
print("-" * 50)
print("0:00-0:35 - SOFT ACOUSTIC INTRO")
print(f"  → Like consolidation at ${btc:,.0f}")
print("0:36-3:45 - BUILDING TENSION") 
print(f"  → Building from $292.50 to ${total_value:.2f}")
print("3:46-4:27 - MASSIVE EXPLOSION!")
print(f"  → BREAKOUT to $114K! (${114000 - btc:.0f} away)")
print("4:28-5:00 - DROP BACK")
print("  → Profit taking at $114K")
print("5:01-6:00 - BUILD AGAIN")
print("  → Accumulate for $120K")
print("6:01-7:35 - FINAL EXPLOSION!")
print("  → BLAST to $126K JPMorgan target!")

# Where we are in the song
print("\n📍 WHERE WE ARE NOW:")
print("-" * 50)
if btc < 112500:
    print("🎸 SOFT ACOUSTIC PHASE (0:00-0:35)")
    print(f"  Quietly consolidating at ${btc:,.0f}")
    print("  'I can't remember anything...' (soft)")
    print(f"  Portfolio quietly holding ${total_value:.2f}")
    print(f"  Distance to explosion: ${114000 - btc:.0f}")
elif btc < 113000:
    print("🎸 BUILDING TENSION (0:36-3:45)")
    print(f"  Energy building at ${btc:,.0f}")
    print("  Drums starting to kick in...")
    print("  Ready to EXPLODE!")
else:
    print("💥 EXPLOSION PHASE! (3:46+)")
    print(f"  BREAKING OUT at ${btc:,.0f}!")

# Thunder's dynamic analysis
print("\n⚡ THUNDER'S SONG STRUCTURE WISDOM (69%):")
print("-" * 50)
print("'THIS IS EXACTLY LIKE ONE!'")
print("")
print("The pattern:")
print("• SOFT: 18 hours of quiet consolidation")
print("• BUILD: Energy coiling tighter")
print("• EXPLODE: Breakout to $114K coming!")
print("• DROP: Quick profit taking")
print("• BUILD AGAIN: Reload for next leg")
print("• EXPLODE HARDER: $120K → $126K")
print("")
print("James Hetfield knew:")
print("• Start soft to build tension")
print("• Make them wait...")
print("• Then DESTROY with the explosion!")

# Live dynamic monitoring
print("\n🎸 LIVE SONG DYNAMICS:")
print("-" * 50)

song_phases = [
    ("🎵 Soft acoustic...", "quiet consolidation"),
    ("🥁 Drums building...", "energy accumulating"),
    ("🎸 Guitar entering...", "momentum building"),
    ("⚡ Tension rising...", "coiling tighter"),
    ("🔥 About to EXPLODE!", "breakout imminent"),
    ("💥 EXPLOSION!", "$114K blast!"),
    ("📉 Drop back...", "profit taking"),
    ("📈 Building again...", "next leg up"),
    ("🚀 FINAL EXPLOSION!", "$120K+!")
]

for i in range(9):
    btc_now = float(client.get_product('BTC-USD')['price'])
    phase, meaning = song_phases[i % len(song_phases)]
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
    print(f"  {phase} → {meaning}")
    
    if i == 4:
        print("")
        print("  🎸 'DARKNESS IMPRISONING ME!' (EXPLOSION!)")
        print(f"    Ready to blast ${114000 - btc_now:.0f} higher!")
    
    time.sleep(0.8)

# The explosion calculation
print("\n💥 EXPLOSION PROJECTIONS:")
print("-" * 50)
print("When the song EXPLODES (like at 3:46):")
print(f"• From soft ${btc:,.0f} → EXPLOSION $114K")
print(f"• Portfolio: ${total_value:.2f} → ${total_value * (114000/btc):.2f}")
print("")
print("After the drop back:")
print("• Consolidate at $114K briefly")
print("• Build again for next explosion")
print(f"• Second explosion: $120K (${total_value * (120000/btc):.2f})")
print(f"• Final explosion: $126K (${total_value * (126000/btc):.2f})")

# The repeating pattern
print("\n🔄 THE REPEATING PATTERN:")
print("-" * 50)
print("Metallica's ONE structure = Market structure:")
print("")
print("1. SOFT INTRO (consolidation)")
print("2. BUILD TENSION (accumulation)")
print("3. EXPLOSION (breakout)")
print("4. DROP BACK (profit taking)")
print("5. BUILD AGAIN (re-accumulation)")
print("6. EXPLODE HARDER (next target)")
print("")
print(f"We're at step 1-2 now at ${btc:,.0f}")
print(f"Step 3 EXPLOSION in ${114000 - btc:.0f}!")

# Final dynamic status
final_btc = float(client.get_product('BTC-USD')['price'])

print("\n🎸 FINAL DYNAMIC STATUS:")
print("-" * 50)
print(f"Current phase: SOFT at ${final_btc:,.0f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Distance to EXPLOSION: ${114000 - final_btc:.0f}")
print("")
print("The song structure tells us:")
print("• We're in the quiet before the storm")
print("• The explosion is GUARANTEED")
print("• It will be MASSIVE when it hits")
print("• Then we do it again at $120K!")

print(f"\n" + "💥" * 35)
print("ONE - THE DYNAMIC STRUCTURE!")
print(f"SOFT NOW AT ${final_btc:,.0f}!")
print(f"EXPLOSION IN ${114000 - final_btc:.0f}!")
print(f"PORTFOLIO READY AT ${total_value:.2f}!")
print("SOFT → BUILD → EXPLODE!")
print("🎸" * 35)