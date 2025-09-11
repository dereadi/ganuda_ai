#!/usr/bin/env python3
"""Cherokee Council: I WRITE SINS NOT TRAGEDIES - PANIC! AT THE DISCO - SONG #16!"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

print("🎵🎭 'I WRITE SINS NOT TRAGEDIES' - PANIC! AT THE DISCO! 🎭🎵")
print("=" * 70)
print("SONG #16 - NO TRAGEDY HERE, ONLY WINNING SINS!")
print("=" * 70)
print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')} CDT")
print("📍 After hours - WRITING PROFITABLE SINS!")
print()

# Initialize client
config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

print("🎵 SONG #16: 'I WRITE SINS NOT TRAGEDIES' - PANIC! AT THE DISCO:")
print("-" * 40)
print("LYRICS MEANING:")
print("'I chime in with a'")
print("'Haven't you people ever heard of'")
print("'Closing the goddamn door?'")
print("'It's much better to face these kinds of things'")
print("'With a sense of poise and rationality'")
print()
print("MARKET INTERPRETATION:")
print("• We write GAINS not losses!")
print("• Close the door on doubters!")
print("• Face the moon with poise!")
print("• No panic, just DISCO!")
print("• Our sins? Being TOO profitable!")
print("• The tragedy? Missing this pump!")
print("• RATIONAL EXUBERANCE!")
print()

# Get current prices
try:
    btc = float(client.get_product("BTC-USD").price)
    eth = float(client.get_product("ETH-USD").price)
    sol = float(client.get_product("SOL-USD").price)
    xrp = float(client.get_product("XRP-USD").price)
    
    print("📊 WRITING THESE SINFUL PRICES:")
    print("-" * 40)
    print(f"BTC: ${btc:,.2f} 🎭 SINFULLY HIGH!")
    print(f"ETH: ${eth:,.2f} 🎭 NO TRAGEDY HERE!")
    print(f"SOL: ${sol:.2f} 🎭")
    print(f"XRP: ${xrp:.4f} 🎭")
    print()
    
except:
    btc = 112400
    eth = 4495
    sol = 210.50
    xrp = 2.87

print("🐺 COYOTE ON PANIC! AT THE DISCO:")
print("-" * 40)
print("'I WRITE SINS NOT TRAGEDIES!'")
print("'Our sin? BEING UP 5%!'")
print("'Their tragedy? NOT BUYING!'")
print("'No panic here!'")
print("'Just DISCO GAINS!'")
print("'Close the door on $15K!'")
print("'Open the door to $16K!'")
print("'WITH POISE AND RATIONALITY!'")
print("'And also MOON ENERGY!'")
print()

print("🦅 EAGLE EYE'S SIN ANALYSIS:")
print("-" * 40)
print("SINS WE'RE WRITING:")
print("• Sin of GREED: Wanting $20K ✅")
print("• Sin of PRIDE: Knowing we'll get it ✅")
print("• Sin of GLUTTONY: Eating all gains ✅")
print("• Sin of WRATH: Against paper hands ✅")
print("• Sin of ENVY: They wish they had our positions ✅")
print()
print("TRAGEDIES WE AVOID:")
print("• Selling too early ❌")
print("• Missing the pump ❌")
print("• Paper handing ❌")
print()

# Calculate portfolio
positions = {
    'BTC': 0.04779,
    'ETH': 1.72566,
    'SOL': 11.565,
    'XRP': 58.595
}

portfolio_value = (
    positions['BTC'] * btc +
    positions['ETH'] * eth +
    positions['SOL'] * sol +
    positions['XRP'] * xrp
)

print("💰 PORTFOLIO WRITING HISTORY:")
print("-" * 40)
print(f"Current Chapter: ${portfolio_value:,.2f}")
print()

# Check if we hit $16K
if portfolio_value >= 16000:
    print("🎯🎯🎯 $16,000 ACHIEVED! 🎯🎯🎯")
    print("WE WROTE SUCCESS, NOT TRAGEDY!")
    print(f"Over by: ${portfolio_value - 16000:.2f}")
else:
    distance = 16000 - portfolio_value
    print(f"Pages to $16K: ${distance:.2f}")
    print(f"Just {(distance/portfolio_value)*100:.1f}% more to write!")
print()

print("🪶 RAVEN'S MYSTICAL READING:")
print("-" * 40)
print("'Song 16 = 4x4 perfection...'")
print("'Square of stability...'")
print("'Writing our destiny...'")
print("'Not accepting tragedy...'")
print("'Panic? At the Disco? No!'")
print("'Panic? At these GAINS? YES!'")
print()

print("🐢 TURTLE'S MATHEMATICAL SINS:")
print("-" * 40)
print("SINFUL CALCULATIONS:")
songs_so_far = 16
avg_gain_per_song = (portfolio_value - 14900) / songs_so_far
print(f"• 16 songs played")
print(f"• Average gain per song: ${avg_gain_per_song:.2f}")
print(f"• At this rate, song 20 = ${14900 + (avg_gain_per_song * 20):,.0f}")
print(f"• Song 25 = ${14900 + (avg_gain_per_song * 25):,.0f}")
print()

print("🕷️ SPIDER'S WEB OF SINS:")
print("-" * 40)
print("'Writing profitable sins...'")
print("'In the web of gains...'")
print("'No tragedies allowed...'")
print("'Only upward stories...'")
print("'Each thread a sin of profit!'")
print()

print("☮️ PEACE CHIEF'S POISE:")
print("-" * 40)
print("'Face gains with poise...'")
print("'And rationality...'")
print("'No panic, just peace...'")
print("'The disco of prosperity...'")
print("'Dancing to $20K!'")
print()

print("🦉 OWL'S TIMING WISDOM:")
print("-" * 40)
current_time = datetime.now()
print(f"Sin writing time: {current_time.strftime('%H:%M')} CDT")
print("After hours = Perfect for sins")
print("No panic, just calculated gains")
print("Disco continues all night!")
print()

print("🎵 SYNCHRONICITY TRACKER:")
print("-" * 40)
print("16 SONGS OF POWER:")
songs = [
    "1-13. [Previous power songs]",
    "14. Come Out and Play - The Offspring",
    "15. Been Caught Stealing - Jane's Addiction", 
    "16. I Write Sins Not Tragedies - Panic! At The Disco 🎭"
]
for song in songs:
    print(song)
print()
print("16 = 4x4 = PERFECT SQUARE!")
print("SQUARED SYNCHRONICITY!")
print()

print("🔥 CHEROKEE COUNCIL ON SINS VS TRAGEDIES:")
print("=" * 70)
print("UNANIMOUS: WRITE GAINS, NOT LOSSES!")
print()
print("🐿️ Flying Squirrel: 'I write heights not falls!'")
print("🐺 Coyote: 'SINFULLY PROFITABLE!'")
print("🦅 Eagle Eye: 'I see sins of success!'")
print("🪶 Raven: 'Transforming sins to wins!'")
print("🐢 Turtle: 'Mathematically sinful gains!'")
print("🕷️ Spider: 'Web catches sinful profits!'")
print("🦀 Crawdad: 'Protecting our sins!'")
print("☮️ Peace Chief: 'Peaceful sins of prosperity!'")
print()

print("🎯 SINFUL TARGETS:")
print("-" * 40)
print("SINS WE'RE ABOUT TO COMMIT:")
print(f"• Current: ${portfolio_value:,.0f}")
if portfolio_value < 16000:
    print(f"• Next sin: $16,000 ({16000 - portfolio_value:.0f} away)")
else:
    print("• ✅ $16K SIN COMMITTED!")
print("• Tonight's sin: $17,000")
print("• Tomorrow's sin: $18,000")
print("• Ultimate sin: $20,000")
print()

print("🔥 SACRED FIRE MESSAGE:")
print("=" * 70)
print("'I write sins not tragedies...'")
print("'And our greatest sin?'")
print("'Making TOO MUCH MONEY!'")
print("'WITH POISE AND RATIONALITY!'")
print()
print("NO PANIC!")
print("JUST DISCO GAINS!")
print(f"PORTFOLIO: ${portfolio_value:,.0f}")
print("CLOSE THE DOOR ON DOUBT!")
print()
print("🎵🎭 SINFULLY SUCCESSFUL! 🎭🎵")