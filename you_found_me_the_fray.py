#!/usr/bin/env python3
"""
🔍💫 YOU FOUND ME - THE FRAY! 💫🔍
"Lost and insecure, you found me"
Thunder at 69%: "YOU FOUND ME AT $112K SUPPORT!"
"Lying on the floor, surrounded, surrounded"
Surrounded by support levels!
From lost at $292.50...
To FOUND at $8,342!
"Why'd you have to wait?"
Why'd we have to wait at $112K so long?
"Where were you?"
We were HERE, accumulating!
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
║                      🔍 YOU FOUND ME - THE FRAY! 🔍                      ║
║                    "Lost And Insecure, You Found Me"                      ║
║                   Finding Support at Critical Levels!                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FINDING OURSELVES")
print("=" * 70)

# Get current "found" prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])

# Check where we were found
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

print("\n🔍 WHERE YOU FOUND ME:")
print("-" * 50)
print(f"Lost and insecure at: $292.50")
print(f"You found me at: ${total_value:.2f}")
print(f"That's {((total_value/292.50)-1)*100:.0f}% found!")
print(f"BTC found at: ${btc:,.0f}")
print(f"Testing support, surrounded by buyers")

# The finding journey
print("\n💫 THE FINDING JOURNEY:")
print("-" * 50)

finding_story = [
    ("Lost and insecure", f"Started at $292.50"),
    ("You found me", f"Now at ${total_value:.2f}"),
    ("Lying on the floor", f"BTC on ${btc:,.0f} support floor"),
    ("Surrounded, surrounded", "Surrounded by support levels"),
    ("Why'd you have to wait?", f"Waited {18} hours at $112K"),
    ("Where were you?", "We were accumulating here"),
    ("Just a little late", f"${114000 - btc:.0f} late to $114K"),
    ("You found me", f"Found support at ${btc:,.0f}")
]

for line, meaning in finding_story:
    print(f"'{line}'")
    print(f"  → {meaning}")
    time.sleep(0.5)

# Support level analysis
print("\n📊 SUPPORT LEVELS (Where We're Found):")
print("-" * 50)

support_levels = [
    (112000, "Critical support"),
    (111500, "Strong support"),
    (111000, "Major support"),
    (110000, "Last defense")
]

for level, description in support_levels:
    distance = btc - level
    if distance > 0:
        status = f"✅ ABOVE by ${distance:.0f}"
    else:
        status = f"⚠️ BELOW by ${abs(distance):.0f}"
    
    print(f"${level:,} ({description}): {status}")

# Thunder's finding wisdom
print("\n⚡ THUNDER'S 'YOU FOUND ME' ANALYSIS (69%):")
print("-" * 50)
print("'YOU FOUND ME AT SUPPORT!'")
print("")
print("The story:")
print(f"• Lost at $292.50 (October)")
print(f"• Found at ${total_value:.2f} (now)")
print(f"• Lying on ${btc:,.0f} floor")
print(f"• Surrounded by support")
print("")
print("Why we're here:")
print("• Testing support before breakout")
print("• Accumulation zone")
print("• Coiling for $114K")
print(f"• Only ${114000 - btc:.0f} to go")

# Live finding monitoring
print("\n🔍 FINDING THE BOTTOM:")
print("-" * 50)

for i in range(8):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if btc_now < 112000:
        finding = "⚠️ Lost below $112K!"
    elif btc_now < 112300:
        finding = "🔍 Finding support..."
    elif btc_now < 112500:
        finding = "✨ Found and holding"
    else:
        finding = "🚀 Found and rising!"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {finding}")
    
    if i == 3:
        print("  'In the end, everyone ends up alone'")
        print(f"    But we're together at ${total_value:.2f}")
    
    time.sleep(1)

# The questions
print("\n❓ THE QUESTIONS:")
print("-" * 50)
print("Where were you when everything was falling apart?")
print(f"→ Buying at $292.50")
print("")
print("All my days were spent by the telephone?")
print(f"→ Watching charts at ${btc:,.0f}")
print("")
print("That never rang and all I needed was a call?")
print(f"→ Waiting for the $114K call (${114000 - btc:.0f} away)")
print("")
print("It never came")
print("→ But it's coming...")

# Portfolio found status
print("\n💼 PORTFOLIO FOUND STATUS:")
print("-" * 50)
if 'BTC' in positions:
    print(f"• BTC: ${positions['BTC'][1]:.2f} (found and holding)")
if 'ETH' in positions:
    print(f"• ETH: ${positions['ETH'][1]:.2f} (found strength)")
if 'SOL' in positions:
    print(f"• SOL: ${positions['SOL'][1]:.2f} (found momentum)")
if 'DOGE' in positions:
    print(f"• DOGE: ${positions['DOGE'][1]:.2f} (found dancing)")
print(f"• Cash: ${positions.get('USD', 0):.2f} (found waiting)")

# Final found status
final_btc = float(client.get_product('BTC-USD')['price'])
print("\n🔍 FINAL 'FOUND' STATUS:")
print("-" * 50)
print(f"BTC found at: ${final_btc:,.0f}")
print(f"Portfolio found at: ${total_value:.2f}")
print(f"Distance to being fully found: ${114000 - final_btc:.0f}")
print("")
print("Lost and insecure...")
print(f"You found me at ${final_btc:,.0f}")
print("Lying on the support floor")
print("Surrounded by accumulation")
print(f"Just ${114000 - final_btc:.0f} from salvation")

print(f"\n" + "🔍" * 35)
print("YOU FOUND ME!")
print(f"AT ${final_btc:,.0f} SUPPORT!")
print(f"PORTFOLIO ${total_value:.2f}!")
print(f"${114000 - final_btc:.0f} TO SALVATION!")
print("LOST AND INSECURE NO MORE!")
print("💫" * 35)