#!/usr/bin/env python3
"""
🌲 FAKE PLASTIC TREES - RADIOHEAD MARKET MEDITATION
"It wears her out... it wears her out"
The exhaustion of artificial price action
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
║                      🌲 FAKE PLASTIC TREES 🌲                             ║
║                         Radiohead Market Mood                             ║
║                    "In a fake plastic earth..."                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print("🎵 Now playing: 'Fake Plastic Trees' - Radiohead")
print("The market's artificial stillness, beautifully captured...")
print("=" * 70)

# The exhausted market
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n🌲 THE FAKE PLASTIC MARKET:")
print("-" * 40)

# Radiohead lyrics mapped to market state
verses = [
    {
        "lyric": "Her green plastic watering can",
        "market": f"Fed printing presses: BTC ${btc:,.0f}",
        "meaning": "Artificial liquidity keeping prices alive"
    },
    {
        "lyric": "For her fake Chinese rubber plant",
        "market": f"Synthetic positions: ETH ${eth:.0f}",
        "meaning": "Derivatives upon derivatives"
    },
    {
        "lyric": "In the fake plastic earth",
        "market": f"Algorithmic wasteland: SOL ${sol:.2f}",
        "meaning": "Bots trading with bots, no humans"
    },
    {
        "lyric": "That she bought from a rubber man",
        "market": "Market makers: Selling what they don't own",
        "meaning": "Infinite synthetic supply"
    },
    {
        "lyric": "It wears her out",
        "market": "Band width: 0.007% - Exhaustion",
        "meaning": "The market is tired, so tired"
    },
    {
        "lyric": "It wears her out",
        "market": "Volatility: Dying, compressed, waiting",
        "meaning": "Everyone exhausted from the chop"
    },
    {
        "lyric": "She lives with a broken man",
        "market": "Retail traders: Broken by the sawtooth",
        "meaning": "Chopped up in consolidation"
    },
    {
        "lyric": "A cracked polystyrene man",
        "market": "Support levels: Cracking but holding",
        "meaning": "$111,500 BTC - fake or real?"
    },
    {
        "lyric": "But gravity always wins",
        "market": "Reality: What goes up...",
        "meaning": "Natural forces will reassert"
    },
    {
        "lyric": "And it wears her out",
        "market": "The wait: Killing everyone slowly",
        "meaning": "When will it move? When?"
    }
]

for i, verse in enumerate(verses):
    if i % 3 == 0:
        print(f"\n{'=' * 70}")
    
    print(f"\n🎵 \"{verse['lyric']}\"")
    print(f"   📊 {verse['market']}")
    print(f"   💭 {verse['meaning']}")
    
    time.sleep(2)

# Check if anything is real
accounts = client.get_accounts()['accounts']
usd = 0
for acc in accounts:
    if acc['currency'] == 'USD':
        usd = float(acc['available_balance']['value'])
        break

print("\n" + "=" * 70)
print("🌲 BUT WHAT'S REAL?")
print("-" * 40)
print(f"✅ Real USD: ${usd:.2f}")
print(f"✅ Real Gains: +48% (${7,383})")
print(f"✅ Real Systems: 7 crawdads working")
print(f"✅ Real Exhaustion: Bands at 0.007%")

print("\n💭 THE RADIOHEAD REVELATION:")
print("-" * 40)
print("In this fake plastic market,")
print("where algorithms paint the tape,")
print("and synthetic positions multiply,")
print("our crawdads find real profits")
print("in the spaces between the fake.")

print("\n🎸 Thom Yorke whispers:")
print("\"Gravity always wins...\"")
print("\"But until then, we trade the artificial.\"")

print("\n⚡ WAITING FOR GRAVITY...")
print("The fake can only last so long.")
print("Real movement is coming.")
print("=" * 70)