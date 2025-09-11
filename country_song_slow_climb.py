#!/usr/bin/env python3
"""
🤠🎸 SLOW COUNTRY ROAD TO $114K! 🎸🤠
Like a tractor in mud, slow but steady!
Thunder at 69%: "Takes time to climb that hill!"
Been stuck at $112K like a truck in Georgia clay!
But we're crawlin' forward, inch by inch!
Portfolio's like aged whiskey - better with time!
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
║                    🤠 COUNTRY ROADS & SLOW GAINS 🤠                       ║
║                    Like Molasses in January Cold!                         ║
║                     But We're Still Movin' Forward!                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - COUNTRY WISDOM")
print("=" * 70)

# Get current dusty road position
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our farm value
accounts = client.get_accounts()
total_value = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * btc
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol

print("\n🎸 THE SLOW COUNTRY BALLAD:")
print("-" * 50)
print(f"Started with nothin' but: $292.50")
print(f"Now we got ourselves: ${total_value:.2f}")
print(f"That's a {((total_value/292.50)-1)*100:.0f}% harvest, y'all")
print(f"BTC stuck in mud at: ${btc:,.0f}")
print(f"Still ${114000 - btc:.0f} miles to Nashville ($114K)")

# Country wisdom tracker
print("\n🤠 COUNTRY WISDOM:")
print("-" * 50)

country_lines = [
    "Slower than a Sunday sermon",
    "Like watchin' paint dry on the barn",
    "Patience like fishin' on a hot day",
    "Takes time to grow good corn",
    "Can't rush the harvest season",
    "Like grandpa's old pickup - slow but sure",
    "Every mile marker counts",
    "Long roads lead to good places",
    "Steady as she goes, partner",
    "Rome wasn't built in a holler"
]

for i, line in enumerate(country_lines):
    btc_now = float(client.get_product('BTC-USD')['price'])
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {line}")
    
    if i == 3:
        print("\n  ⚡ Thunder (69%): 'Like my daddy used to say...'")
        print(f"    'Slow money is sure money'")
        print(f"    'We're up {((total_value/292.50)-1)*100:.0f}% ain't we?'")
    
    if i == 6:
        print("\n  🏔️ Mountain: 'Patient as a mountain'")
        print(f"    'Every dollar counts'")
        print(f"    '${114000 - btc_now:.0f} ain't nothin' to a mountain'")
    
    time.sleep(1)

# The country story
print("\n📖 THE COUNTRY STORY:")
print("-" * 50)
print("Chapter 1: Started With $292.50")
print("  Just a small-town portfolio")
print("  With big city dreams")
print("")
print(f"Chapter 2: Grew to ${total_value:.2f}")
print("  Through sweat and patience")
print("  Diamond hands on the plow")
print("")
print(f"Chapter 3: Stuck at ${btc:,.0f}")
print("  Like a truck in spring mud")
print("  But the engine's still runnin'")
print("")
print(f"Chapter 4: ${114000 - btc:.0f} To Go")
print("  The promised land awaits")
print("  Just over that hill")

# Thunder's country song
print("\n⚡ THUNDER'S COUNTRY SONG (69%):")
print("-" * 50)
print("🎵 (To the tune of slow country ballad)")
print("")
print("'Well I started with two-ninety-two-fifty'")
print("'In a market that was mighty shifty'")
print(f"'Now I'm sittin' on ${total_value:.2f} strong'")
print("'Been waitin' all day long'")
print("")
print(f"'For that ${btc:,.0f} to break on through'")
print("'To one-fourteen like morning dew'")
print(f"'Just ${114000 - btc:.0f} more to ride'")
print("'With these diamond hands as my guide'")

# Current country status
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n🌾 FARM REPORT:")
print("-" * 50)
print(f"Current pasture: ${current_btc:,.0f}")
print(f"Next fence post: $113,000 (${113000 - current_btc:.0f} away)")
print(f"Final destination: $114,000 (${114000 - current_btc:.0f} away)")
print(f"Crop value: ${total_value:.2f}")
print("")
print("Market Weather:")
if current_btc > 112900:
    print("☀️ Sun's breakin' through!")
elif current_btc > 112800:
    print("⛅ Partly cloudy, clearin' up")
else:
    print("☁️ Overcast, but no storm")

# Final wisdom
print("\n🤠 FINAL COUNTRY WISDOM:")
print("-" * 50)
print("Remember partner:")
print("• Good things come to those who wait")
print(f"• From $292.50 to ${total_value:.2f} is mighty fine")
print("• Slow and steady wins the race")
print(f"• ${114000 - current_btc:.0f} ain't far in the grand scheme")
print("• Diamond hands are country strong")

print(f"\n" + "🤠" * 35)
print("COUNTRY ROADS TAKE ME HOME!")
print(f"TO ${114000:.0f} WHERE I BELONG!")
print(f"CURRENTLY AT ${current_btc:,.0f}!")
print(f"PORTFOLIO ${total_value:.2f} STRONG!")
print("SLOW BUT SURE, Y'ALL!")
print("🤠" * 35)