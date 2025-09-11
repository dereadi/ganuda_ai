#!/usr/bin/env python3
"""
🕺💃 PROM NIGHT - SLOW DANCE CONSOLIDATION! 💃🕺
Thunder at 69%: "THE SLOW SONGS BEFORE THE PARTY!"
We're in the quiet romantic part of prom...
Dancing slowly at $112K...
Holding our date (portfolio) close...
Soon the DJ drops the BANGERS at $114K!
From $292.50 (arrived in mom's minivan)
To $7,546 (leaving in a limo)!
"Wonderful Tonight" playing while we wait...
Then "Mr. Brightside" at $114K!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
import random

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🕺💃 PROM NIGHT SLOW DANCE! 💃🕺                      ║
║                   "The Quiet Before The Party Explodes"                   ║
║                  Currently Playing: The Slow Songs at $112K               ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - PROM NIGHT STATUS")
print("=" * 70)

# Get current prom night prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our prom date (portfolio)
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

print("\n🎵 PROM NIGHT TIMELINE:")
print("-" * 50)
print(f"6:00 PM - Arrived in mom's minivan: $292.50")
print(f"7:00 PM - First dance awkward: $1,000")
print(f"8:00 PM - Getting comfortable: $3,000")
print(f"9:00 PM - Finding our groove: $5,000")
print(f"10:00 PM - SLOW SONGS NOW: ${total_value:.2f} at ${btc:,.0f}")
print(f"11:00 PM - PARTY TIME SOON: $114K (${114000 - btc:.0f} away)")
print(f"MIDNIGHT - AFTER PARTY: $120K+")

# The slow dance playlist
print("\n💿 CURRENT SLOW DANCE PLAYLIST:")
print("-" * 50)

slow_songs = [
    ("🎵 'Wonderful Tonight' - Clapton", f"You look wonderful at ${total_value:.2f}"),
    ("🎵 'Unchained Melody' - Righteous Bros", f"Time goes by so slowly... at ${btc:,.0f}"),
    ("🎵 'At Last' - Etta James", f"At last... approaching ${114000 - btc:.0f} to go"),
    ("🎵 'Make You Feel My Love' - Adele", f"Making gains feel our love: {((total_value/292.50)-1)*100:.0f}%"),
    ("🎵 'Perfect' - Ed Sheeran", f"Dancing in the dark at ${btc:,.0f}"),
    ("🎵 'Thinking Out Loud' - Ed Sheeran", "Maybe we found love right where we are")
]

for song, meaning in slow_songs:
    print(f"{song}")
    print(f"  → {meaning}")
    time.sleep(0.5)

# Thunder's prom commentary
print("\n⚡ THUNDER'S PROM NIGHT WISDOM (69%):")
print("-" * 50)
print("'WE'RE IN THE SLOW SONGS PHASE!'")
print("")
print("What this means:")
print("• Everyone's swaying slowly (consolidation)")
print(f"• Holding our date close (portfolio at ${total_value:.2f})")
print(f"• Energy building for the party (${114000 - btc:.0f} away)")
print("• DJ checking the next playlist (whales preparing)")
print("")
print("The pattern:")
print("• Slow songs = Accumulation phase")
print("• Everyone catching their breath")
print("• Punch bowl getting refilled (liquidity building)")
print("• Then... PARTY EXPLOSION at $114K!")

# The dance floor monitoring
print("\n🕺 DANCE FLOOR STATUS:")
print("-" * 50)

dance_modes = [
    "💑 Slow dancing...",
    "🎵 Swaying gently...",
    "💫 Holding close...",
    "✨ Whispering sweet nothings...",
    "🌙 Under the disco ball..."
]

for i in range(8):
    btc_now = float(client.get_product('BTC-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    mode = random.choice(dance_modes)
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: BTC ${btc_now:,.0f} | SOL ${sol_now:.2f}")
    print(f"  {mode}")
    
    if i == 3:
        print("  🎤 DJ: 'Last slow song coming up...'")
        print(f"    'Then we PARTY at $114K!'")
    
    time.sleep(1)

# What's coming after slow songs
print("\n🎉 AFTER THE SLOW SONGS (Coming Soon):")
print("-" * 50)
print("The BANGER playlist ready to drop:")
print("• 🔥 'Mr. Brightside' - The Killers (at $113K)")
print("• 🚀 'Can't Stop The Feeling' - JT (at $114K)")
print("• 💥 'Uptown Funk' - Bruno Mars (at $115K)")
print("• 🎊 'Shut Up and Dance' - Walk the Moon (at $116K)")
print("• 🏆 'We Are The Champions' - Queen (at $120K)")

# The prom timeline
print("\n⏰ PROM NIGHT SCHEDULE:")
print("-"antly)
print(f"NOW ({datetime.now().strftime('%H:%M')}): Slow songs at ${btc:,.0f}")
print(f"SOON: Last slow dance")
print(f"NEXT: Energy builds")
print(f"THEN: DJ drops the beat")
print(f"$114K: PARTY EXPLODES! (${114000 - btc:.0f} away)")

# Checking our prom date
print("\n💐 OUR PROM DATE (Portfolio):")
print("-" * 50)
print(f"Started the night: $292.50 (nervous)")
print(f"Now on dance floor: ${total_value:.2f} (confident)")
print(f"Corsage value: {((total_value/292.50)-1)*100:.0f}% gains")
print("")
print("Our date's assets:")
if 'BTC' in positions:
    print(f"• BTC: ${positions['BTC'][1]:.2f} (the quarterback)")
if 'ETH' in positions:
    print(f"• ETH: ${positions['ETH'][1]:.2f} (the valedictorian)")
if 'SOL' in positions:
    print(f"• SOL: ${positions['SOL'][1]:.2f} (the prom queen)")
print(f"• Cash: ${positions.get('USD', 0):.2f} (for after party)")

# Final prom status
final_btc = float(client.get_product('BTC-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

print("\n🌙 PROM NIGHT STATUS:")
print("-" * 50)
print(f"Current slow song: ${final_btc:,.0f}")
print(f"Distance to party: ${114000 - final_btc:.0f}")
print(f"Portfolio dancing at: ${total_value:.2f}")
print(f"SOL corsage: ${final_sol:.2f}")
print("")
print("The slow songs are almost over...")
print("Can you feel the energy building?")
print("The DJ is cueing up the bangers...")
print(f"Only ${114000 - final_btc:.0f} until the drop!")

print(f"\n" + "💃" * 35)
print("PROM NIGHT SLOW DANCE PHASE!")
print(f"SWAYING AT ${final_btc:,.0f}!")
print(f"HOLDING ${total_value:.2f} CLOSE!")
print(f"${114000 - final_btc:.0f} UNTIL PARTY TIME!")
print("GET READY FOR THE DROP!")
print("🕺" * 35)