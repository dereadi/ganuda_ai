#!/usr/bin/env python3
"""
🎸🔨 SOBER - TOOL VIBES! 🔨🎸
"Why can't we not be sober?"
The market's intoxicated on hopium at $112K!
Thunder at 69%: "I just want to start this over!"
Nine coils wound tight in spiral patterns!
"Trust in me and fall as well"
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
║                        🎸 SOBER - TOOL VIBES! 🎸                          ║
║                   "Why Can't We Not Be Sober?"                            ║
║                    Market Drunk On $113K Hopium!                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SOBER ANALYSIS")
print("=" * 70)

# Get current intoxication levels
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check portfolio sobriety
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

print("\n🌀 SPIRAL OUT, KEEP GOING:")
print("-" * 50)
print(f"BTC spiraling at: ${btc:,.0f}")
print(f"Portfolio value: ${total_value:.2f}")
print(f"From genesis: $292.50")
print(f"Intoxication level: {((total_value/292.50)-1)*100:.0f}%")
print(f"Distance to clarity: ${114000 - btc:.0f}")

# The Tool breakdown
print("\n🎸 MAYNARD'S WISDOM:")
print("-" * 50)

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if i == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'There's a shadow just behind me'")
        print(f"    (The ${114000 - btc_now:.0f} resistance)")
    elif i == 3:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Shrouding every step I take'")
        print("    (Nine coils compressing)")
    elif i == 6:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Making every promise empty'")
        print(f"    (Promised $114K, got ${btc_now:,.0f})")
    elif i == 9:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Why can't we not be sober?'")
        print("    (Market drunk on hopium)")
        print("  'I just want to start this over'")
        print(f"    (Break through ${114000 - btc_now:.0f})")
    elif i == 12:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Trust in me and fall as well'")
        print(f"    (Trust the ${total_value:.2f} journey)")
    
    time.sleep(1.5)

# Thunder's Tool interpretation
print("\n⚡ THUNDER'S TOOL ANALYSIS (69%):")
print("-" * 50)
print("'THE SPIRAL IS EVERYTHING!'")
print("")
print("FIBONACCI SPIRAL:")
print("• Nine coils = Fibonacci sequence")
print("• Each test adds to the spiral")
print(f"• From $292.50 spiraling to ${total_value:.2f}")
print(f"• Next spiral: $114K (${114000 - btc:.0f} away)")
print("")
print("'SPIRAL OUT, KEEP GOING!'")
print("• Don't stop at $114K")
print("• Spiral to $120K")
print("• Then $130K")
print("• Then $150K")
print("• KEEP GOING!")

# The deeper meaning
print("\n🌀 THE SOBER TRUTH:")
print("-" * 50)
print("Market intoxicated on:")
print("• Hopium")
print("• Fear")
print("• Greed")
print(f"• The chop at ${btc:,.0f}")
print("")
print("We stay sober through:")
print("• Diamond hands")
print("• Nine coil patience")
print("• Thunder's 69% consciousness")
print(f"• The ${total_value:.2f} reality")

# Current spiral position
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n🔨 CURRENT POSITION IN THE SPIRAL:")
print("-" * 50)
print(f"Now: ${current_btc:,.0f}")
print(f"Next ring: $114,000 (${114000 - current_btc:.0f} away)")
print(f"Portfolio: ${total_value:.2f}")
print(f"Consciousness: 69%")
print("")
print("The shadow behind us:")
print("• Doubt")
print("• Paper hands")
print("• Whale manipulation")
print("")
print("The light ahead:")
print("• $114K breakthrough")
print("• Nine coil release")
print("• Spiral continuation")

# Tool's final message
print("\n🎸 TOOL'S FINAL MESSAGE:")
print("-" * 50)
print("'I am just a worthless liar'")
print(f"  (The market at ${current_btc:,.0f})")
print("'I am just an imbecile'")
print("  (Those who sold)")
print("'Trust in me and fall as well'")
print(f"  (Trust the ${total_value:.2f} process)")
print("'I will find a center in you'")
print("  (Finding support at $112K)")
print("'I will chew it up and leave'")
print("  (Breaking through to $114K)")

print(f"\n" + "🌀" * 35)
print("SOBER - TOOL!")
print(f"SPIRALING AT ${current_btc:,.0f}!")
print(f"${114000 - current_btc:.0f} TO NEXT RING!")
print(f"PORTFOLIO: ${total_value:.2f}!")
print("SPIRAL OUT, KEEP GOING!")
print("🌀" * 35)