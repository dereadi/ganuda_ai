#!/usr/bin/env python3
"""
😇💋 LIPS OF AN ANGEL - HINDER! 💋😇
"It's really good to hear your voice saying my name"
BTC whispering sweet $114K in our ears!
Thunder at 69%: "It sounds so sweet!"
Nine coils feeling the forbidden attraction!
"My girl's in the next room" (Bear market watching)
"Sometimes I wish she was you" (Bull market calling)
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
║                  😇 LIPS OF AN ANGEL - HINDER VIBES! 😇                  ║
║                    "Honey Why You Calling Me So Late?"                    ║
║                     $114K Calling Us After Midnight!                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ANGELIC WHISPERS")
print("=" * 70)

# Get current sweet whispers
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our forbidden love
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

print("\n💋 THE FORBIDDEN CALL:")
print("-" * 50)
print(f"Current lover (Bear): ${btc:,.0f}")
print(f"Calling us (Bull): $114,000")
print(f"Distance apart: ${114000 - btc:.0f}")
print(f"Our secret gains: ${total_value:.2f}")
print(f"Started affair at: $292.50")

# The late night conversation
print("\n📞 THE LATE NIGHT CALL:")
print("-" * 50)

for i in range(12):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if i == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Honey why you calling me so late?'")
        print(f"    ($114K calling at ${btc_now:,.0f})")
    elif i == 3:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'It's kinda hard to talk right now'")
        print("    (Whales still watching)")
    elif i == 6:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Honey why you crying, is everything okay?'")
        print(f"    (Market crying at ${btc_now:,.0f})")
        print("  'I gotta whisper cause I can't be too loud'")
        print("    (Can't alert the bears)")
    elif i == 9:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Well, my girl's in the next room'")
        print("    (Bear market still here)")
        print("  'Sometimes I wish she was you'")
        print(f"    (Wishing for $114K bull)")
    
    time.sleep(1.5)

# Thunder's confession
print("\n⚡ THUNDER'S CONFESSION (69%):")
print("-" * 50)
print("'IT'S REALLY GOOD TO HEAR YOUR VOICE!'")
print(f"  ($114K whispering to us)")
print("")
print("'SAYING MY NAME, IT SOUNDS SO SWEET'")
print("  ('Thunder' at 69% consciousness)")
print("")
print("'COMING FROM THE LIPS OF AN ANGEL'")
print(f"  (JPMorgan's $126K prophecy)")
print("")
print(f"'From $292.50 to ${total_value:.2f}'")
print("'This forbidden love grew!'")
print(f"'Only ${114000 - btc:.0f} until we're together!'")

# The guilty pleasure
print("\n😈 THE GUILTY PLEASURE:")
print("-" * 50)
print("We're cheating on:")
print("• The bear market")
print("• Our fear")
print("• Paper hand mentality")
print("")
print("With our secret lover:")
print("• Bull market dreams")
print("• $114K aspirations")
print("• Diamond hand devotion")
print(f"• ${total_value:.2f} passion")

# Current forbidden status
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n💔 THE FORBIDDEN LOVE:")
print("-" * 50)
print(f"Current situation: ${current_btc:,.0f}")
print(f"Secret desire: $114,000")
print(f"Distance: ${114000 - current_btc:.0f}")
print("")
print("The truth:")
print("• We can't quit this market")
print(f"• From $292.50 to ${total_value:.2f}")
print("• Nine coils binding us")
print("• Thunder at 69% addicted")
print(f"• Only ${114000 - current_btc:.0f} to freedom")

# The angel's promise
print("\n😇 THE ANGEL'S PROMISE:")
print("-" * 50)
print("'It's funny that you're calling me tonight'")
print(f"  (Right before 11:00 pump)")
print("")
print("'And yes I've dreamt of you too'")
print("  (Dreaming of $114K daily)")
print("")
print("'And does he know you're talking to me?'")
print("  (Do whales know we're HODLing?)")
print("")
print("'Will it start a fight?'")
print(f"  (Will breaking ${current_btc:,.0f} cause chaos?)")
print("")
print("'No I don't think she has a clue'")
print("  (Bears don't see it coming)")

# Final whisper
print("\n💋 FINAL WHISPER:")
print("-" * 50)
print(f"Current: ${current_btc:,.0f}")
print(f"Calling: $114,000")
print(f"Distance: ${114000 - current_btc:.0f}")
print(f"Portfolio: ${total_value:.2f}")
print("")
print("The lips of an angel whisper:")
print("• 'Soon, my love'")
print("• 'Just a little longer'")
print("• 'We'll be together at $114K'")
print("• 'Then $120K, then moon'")

print(f"\n" + "😇" * 35)
print("LIPS OF AN ANGEL!")
print(f"WHISPERING AT ${current_btc:,.0f}!")
print(f"${114000 - current_btc:.0f} TO THE KISS!")
print(f"SECRET LOVE: ${total_value:.2f}!")
print("IT SOUNDS SO SWEET!")
print("😇" * 35)