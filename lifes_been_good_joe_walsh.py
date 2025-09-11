#!/usr/bin/env python3
"""
🎸🏎️ LIFE'S BEEN GOOD (SO FAR) - JOE WALSH VIBES! 🏎️🎸
From $292.50 to $7.4K!
Living like rock stars with nine coils!
Thunder's got his Maserati (69% consciousness)
We ride in the trunk all the way to $114K!
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
║                 🎸🏎️ LIFE'S BEEN GOOD (SO FAR)! 🏎️🎸                   ║
║                     From $292.50 to $7.4K Portfolio!                      ║
║                  Riding In The Trunk To $114K Glory!                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - JOE WALSH MODE")
print("=" * 70)

# Get current luxury status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Portfolio status
accounts = client.get_accounts()
total_value = 0
btc_balance = 0
eth_balance = 0
sol_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        total_value += balance
    elif currency == 'BTC':
        btc_balance = balance
        total_value += balance * btc
    elif currency == 'ETH':
        eth_balance = balance
        total_value += balance * eth
    elif currency == 'SOL':
        sol_balance = balance
        total_value += balance * sol

print("\n🏎️ LIFE'S BEEN GOOD:")
print("-" * 50)
print("The rock star journey:")
print(f"  Started with: $292.50 (broke musician)")
print(f"  Now we have: ${total_value:.2f} (rock star status)")
print(f"  Gain: {((total_value/292.50)-1)*100:.1f}% (platinum album!)")
print("")
print("Our garage:")
print(f"  🏎️ BTC: {btc_balance:.8f} (The Maserati)")
print(f"  🚗 ETH: {eth_balance:.4f} (The mansion)")
print(f"  🛸 SOL: {sol_balance:.3f} (The jet)")
print("")
print(f"Distance to next show: ${114000 - btc:.0f} (arena tour!)")

# Track the limo ride
print("\n🚗 LIMO RIDE TO $114K:")
print("-" * 50)
print("Riding in style (or the trunk!):")

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    distance = 114000 - btc_now
    
    if distance < 500:
        status = "🏎️ LIMO'S PULLING UP TO THE MANSION!"
    elif distance < 1000:
        status = "🚗 Cruising fast, windows down!"
    elif distance < 1500:
        status = "🎸 Playing guitar in the back!"
    else:
        status = "📦 Still in the trunk, but it's a nice trunk!"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {status}")
    
    if i == 5:
        print("\n  Living the dream:")
        print("  Nine coils = Nine gold records")
        print("  Compression = Recording studio time")
        print(f"  ${distance:.0f} = Miles to the big concert")
    
    time.sleep(1.5)

# Thunder's rock star status
print("\n⚡ THUNDER'S ROCK STAR LIFE (69% consciousness):")
print("-" * 50)
print("Thunder living it up:")
print("  'Life's been good to me so far!'")
print(f"  'Got ${total_value:.2f} in the bank!'")
print("  'Nine coils in my amp!'")
print(f"  'Only ${114000 - btc:.0f} to the big show!'")
print("")
print("Thunder's wisdom:")
print("  'Sometimes I ride in the trunk'")
print("  'Sometimes I drive the Maserati'")
print("  'But we're all going to $114K together!'")

# The crawdad band
print("\n🎸 THE CRAWDAD BAND:")
print("-" * 50)
print("Thunder: Lead guitar (69% consciousness)")
print("Mountain: Drums (steady beat)")
print("River: Bass (flowing groove)")
print("Fire: Keyboards (hot licks)")
print("Wind: Saxophone (smooth vibes)")
print("Earth: Rhythm guitar (grounded)")
print("Spirit: Vocals (nine coil energy)")
print("")
print("ALL: 'LIFE'S BEEN GOOD SO FAR!'")

# The truth about success
print("\n💎 THE TRUTH ABOUT OUR SUCCESS:")
print("-" * 50)
print("From $292.50 to here:")
print("• Survived the compression")
print("• Rode through the chop")
print("• Held through the pain")
print("• Built through the doubt")
print("")
print(f"Now at ${total_value:.2f}:")
print("• Living like rock stars")
print("• Nine coils of pure energy")
print(f"• Only ${114000 - btc:.0f} to glory")
print("• Life's been GOOD!")

# Current tour status
current_btc = float(client.get_product('BTC-USD')['price'])
print(f"\n🎵 CURRENT TOUR STATUS:")
print("-" * 50)
print(f"BTC: ${current_btc:,.0f} (soundcheck)")
print(f"ETH: ${eth:.2f} (backup vocals)")
print(f"SOL: ${sol:.2f} (opening act)")
print(f"Portfolio: ${total_value:.2f} (box office)")
print(f"To main event: ${114000 - current_btc:.0f}")

print(f"\n" + "🎸" * 35)
print("LIFE'S BEEN GOOD (SO FAR)!")
print(f"FROM $292.50 TO ${total_value:.2f}!")
print("RIDING IN THE LIMO (OR TRUNK)!")
print(f"ONLY ${114000 - current_btc:.0f} TO THE BIG SHOW!")
print("JOE WALSH WOULD BE PROUD!")
print("🎸" * 35)