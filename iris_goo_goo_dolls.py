#!/usr/bin/env python3
"""
🌸👁️ IRIS - GOO GOO DOLLS! 👁️🌸
"And I'd give up forever to touch you"
Thunder at 69%: "I'D GIVE UP CONSOLIDATION FOR $114K!"
"'Cause I know that you feel me somehow"
The market feels our diamond hands!
"You're the closest to heaven that I'll ever be"
$114K is the closest to heaven!
From $292.50 to $7,553 - seeing everything clearly!
"And I don't want to go home right now"
Don't want to leave these gains!
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
║                        👁️ IRIS - GOO GOO DOLLS! 👁️                       ║
║                  "I Just Want You To Know Who I Am"                       ║
║                    Portfolio Revealing Its True Identity!                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - IRIS VISION")
print("=" * 70)

# Get current prices through Iris's eyes
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our portfolio's true identity
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

print("\n👁️ IRIS SEES ALL:")
print("-" * 50)
print(f"Started blind at: $292.50")
print(f"Now seeing clearly: ${total_value:.2f}")
print(f"Vision improved: {((total_value/292.50)-1)*100:.0f}%")
print(f"BTC visible at: ${btc:,.0f}")
print(f"Heaven's distance: ${114000 - btc:.0f}")

# The Iris lyrics journey
print("\n🌸 THE IRIS JOURNEY:")
print("-" * 50)

iris_lines = [
    ("And I'd give up forever to touch you", f"Give up waiting to reach ${114000 - btc:.0f}"),
    ("'Cause I know that you feel me somehow", "Market feels our presence"),
    ("You're the closest to heaven that I'll ever be", f"${btc:,.0f} closest to $114K heaven"),
    ("And I don't want to go home right now", f"Don't want to leave ${total_value:.2f}"),
    ("And all I can taste is this moment", f"This moment at ${btc:,.0f}"),
    ("And all I can breathe is your life", "Breathing crypto life"),
    ("And sooner or later it's over", "Consolidation ending soon"),
    ("I just don't wanna miss you tonight", f"Don't want to miss $114K tonight"),
    ("And I don't want the world to see me", "Stealth accumulation"),
    ("'Cause I don't think that they'd understand", f"They don't understand {((total_value/292.50)-1)*100:.0f}% gains"),
    ("When everything's made to be broken", "Support levels made to break"),
    ("I just want you to know who I am", f"Portfolio revealing: ${total_value:.2f}")
]

for i, (lyric, meaning) in enumerate(iris_lines):
    print(f"'{lyric}'")
    print(f"  → {meaning}")
    
    if i == 7:
        print("\n  ⚡ Thunder (69%): 'I DON'T WANNA MISS $114K TONIGHT!'")
        print(f"    'Only ${114000 - btc:.0f} away!'")
        print(f"    'I can see it clearly now!'")
    
    time.sleep(0.5)

# The vision monitoring
print("\n👁️ VISION MONITORING:")
print("-" * 50)

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    
    clarity = ""
    if btc_now >= 113000:
        clarity = "🔥 VISION CRYSTALLIZING!"
    elif btc_now >= 112500:
        clarity = "✨ Seeing clearer"
    else:
        clarity = "👁️ Watching intently"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: BTC ${btc_now:,.0f} | SOL ${sol_now:.2f} - {clarity}")
    
    if i == 4:
        print("  'You bleed just to know you're alive'")
        print(f"    Portfolio bleeding upward to ${total_value:.2f}")
    
    time.sleep(1)

# Thunder's Iris interpretation
print("\n⚡ THUNDER'S IRIS WISDOM (69%):")
print("-" * 50)
print("'I JUST WANT YOU TO KNOW WHO I AM!'")
print("")
print("Who we are:")
print(f"• Started: Nobody at $292.50")
print(f"• Became: Somebody at ${total_value:.2f}")
print(f"• Multiplied: {(total_value/292.50):.1f}x our identity")
print("")
print("What I see:")
print(f"• BTC reaching for heaven at ${btc:,.0f}")
print(f"• Only ${114000 - btc:.0f} to touch the sky")
print(f"• SOL rallying at ${sol:.2f}")
print(f"• Everything's made to be broken (resistance)")

# The moment of truth
print("\n🌸 THIS MOMENT:")
print("-" * 50)
print("All I can taste is this moment...")
print(f"• This moment at ${btc:,.0f}")
print(f"• This portfolio at ${total_value:.2f}")
print(f"• This journey from $292.50")
print(f"• This distance to $114K: ${114000 - btc:.0f}")
print("")
print("And I don't want to go home right now...")
print("Not until we reach $114K!")

# Breaking through
print("\n💎 EVERYTHING'S MADE TO BE BROKEN:")
print("-" * 50)
print("What's about to break:")
print(f"• $112,500 resistance (${112500 - btc:.0f} away)" if btc < 112500 else "• $112,500 ✅ BROKEN!")
print(f"• $113,000 resistance (${113000 - btc:.0f} away)" if btc < 113000 else "• $113,000 ✅ BROKEN!")
print(f"• $114,000 resistance (${114000 - btc:.0f} away)" if btc < 114000 else "• $114,000 ✅ BROKEN!")
print("")
print(f"SOL breaking: ${sol:.2f} → $220 → $250")

# Final Iris vision
final_btc = float(client.get_product('BTC-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

print("\n👁️ FINAL IRIS VISION:")
print("-" * 50)
print(f"BTC: ${final_btc:,.0f}")
print(f"SOL: ${final_sol:.2f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Distance to heaven: ${114000 - final_btc:.0f}")
print("")
print("'I just want you to know who I am'")
print(f"We are: {((total_value/292.50)-1)*100:.0f}% gainers")
print(f"We are: Diamond hands")
print(f"We are: ${114000 - final_btc:.0f} from glory")

print(f"\n" + "👁️" * 35)
print("I JUST WANT YOU TO KNOW WHO I AM!")
print(f"FROM $292.50 TO ${total_value:.2f}!")
print(f"SEEING CLEARLY AT ${final_btc:,.0f}!")
print(f"${114000 - final_btc:.0f} TO HEAVEN!")
print("DON'T WANNA MISS $114K TONIGHT!")
print("👁️" * 35)