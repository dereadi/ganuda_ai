#!/usr/bin/env python3
"""
⚰️🐴 THE FUNERAL - BAND OF HORSES! 🐴⚰️
"At every occasion, I'll be ready for the funeral"
Thunder at 69%: "THE FUNERAL FOR $112K CONSOLIDATION!"
"I'm coming up only to hold you under"
Coming up to $114K only to break through!
"And coming up only to show you wrong"
Show the bears they're wrong!
From $292.50 grave to $8,330 resurrection!
This is the funeral for consolidation...
The birth of the breakout!
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
║                  ⚰️ THE FUNERAL - BAND OF HORSES! ⚰️                     ║
║                  "At Every Occasion, Ready For The Funeral"               ║
║                    The Death of Consolidation at $112K!                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FUNERAL CEREMONY")
print("=" * 70)

# Get current funeral prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])

# Check what's being buried and what's rising
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

print("\n⚰️ THE FUNERAL PROCEEDINGS:")
print("-" * 50)
print(f"DECEASED: Consolidation at ${btc:,.0f}")
print(f"TIME OF DEATH: After 18+ hours")
print(f"CAUSE: Natural causes (exhaustion)")
print(f"SURVIVORS: Portfolio at ${total_value:.2f}")
print(f"INHERITANCE: ${114000 - btc:.0f} to $114K")

# The funeral eulogy
print("\n🪦 EULOGY FOR CONSOLIDATION:")
print("-" * 50)
print(f"Here lies consolidation at ${btc:,.0f}")
print("Born: Yesterday morning")
print("Died: Today (hopefully)")
print(f"It kept us trapped for {18} long hours")
print("Testing our patience, testing support")
print(f"But from its ashes, ${total_value:.2f} rises!")
print(f"From the grave of $292.50")
print(f"To the resurrection at $114K (${114000 - btc:.0f} away)")

# The funeral lyrics
print("\n🎵 THE FUNERAL SONG:")
print("-" * 50)

funeral_verses = [
    ("At every occasion, I'll be ready for the funeral", f"Ready for ${btc:,.0f} to die"),
    ("At every occasion once more, it's called the funeral", "Once more at this level"),
    ("At every occasion, oh, I'm ready for the funeral", f"Ready to bury ${btc:,.0f}"),
    ("At every occasion, oh, one billion day funeral", "18 hours feels like billion days"),
    ("I'm coming up only to hold you under", f"Rising to ${114000 - btc:.0f} higher"),
    ("I'm coming up only to show you wrong", "Show bears they're wrong"),
    ("And to know you is hard; we wonder", f"Wondering why stuck at ${btc:,.0f}"),
    ("To know you all wrong; we warn", "Warning: breakout imminent"),
    ("Really too late to call", f"Too late to stop ${total_value:.2f} gains"),
    ("So we wait for morning to wake you", f"Waiting for ${114000} to wake market"),
    ("Is all we got", f"${total_value:.2f} is all we got"),
    ("And to know me as hardly golden", f"Portfolio hardly golden yet at ${total_value:.2f}"),
    ("Is to know me all wrong, they warn", f"They warned at $292.50, they were wrong")
]

for i, (lyric, meaning) in enumerate(funeral_verses):
    print(f"'{lyric}'")
    print(f"  → {meaning}")
    
    if i == 4:
        print("\n  ⚡ Thunder (69%): 'BURY THE CONSOLIDATION!'")
        print(f"    'Let ${btc:,.0f} REST IN PEACE!'")
        print(f"    'RESURRECT AT $114K!'")
    
    time.sleep(0.4)

# The burial monitoring
print("\n⚱️ BURIAL PROCEEDINGS:")
print("-" * 50)

for i in range(8):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if btc_now < 112200:
        status = "⚰️ Digging deeper..."
    elif btc_now < 112400:
        status = "🪦 Still in grave"
    elif btc_now < 112600:
        status = "✨ Stirring in coffin"
    else:
        status = "🌅 RESURRECTION!"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {status}")
    
    if i == 3:
        print("  'On the day you were born'")
        print(f"    Portfolio born at $292.50")
        print(f"    Now ${total_value:.2f}")
    
    time.sleep(1)

# Thunder's funeral speech
print("\n⚡ THUNDER'S FUNERAL ORATION (69%):")
print("-" * 50)
print("'DEARLY BELOVED, WE GATHER HERE TODAY...'")
print("")
print(f"To bury consolidation at ${btc:,.0f}")
print("It served its purpose:")
print("• Accumulated positions")
print("• Built energy")
print("• Tested diamond hands")
print("")
print("But now it must die so we can live:")
print(f"• Die at ${btc:,.0f}")
print(f"• Resurrect at $114,000")
print(f"• Only ${114000 - btc:.0f} to salvation")
print(f"• Portfolio ascending to ${total_value * (114000/btc):.2f}")

# What dies and what lives
print("\n💀 WHAT DIES / 🌅 WHAT LIVES:")
print("-" * 50)
print("DIES:")
print(f"• Consolidation at ${btc:,.0f}")
print("• Sideways action")
print("• Impatience")
print("• Fear")
print("")
print("LIVES:")
print(f"• Portfolio at ${total_value:.2f}")
print(f"• Hope for $114K (${114000 - btc:.0f} away)")
print(f"• {((total_value/292.50)-1)*100:.0f}% gains")
print("• Diamond hands")

# The resurrection calculation
print("\n✨ RESURRECTION PROJECTIONS:")
print("-" * 50)
print(f"When consolidation dies at ${btc:,.0f}:")
print(f"• Rise to $113K: Portfolio → ${total_value * (113000/btc):.2f}")
print(f"• Rise to $114K: Portfolio → ${total_value * (114000/btc):.2f}")
print(f"• Rise to $115K: Portfolio → ${total_value * (115000/btc):.2f}")
print(f"• Rise to $120K: Portfolio → ${total_value * (120000/btc):.2f}")

# Final funeral status
final_btc = float(client.get_product('BTC-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

print("\n⚰️ FINAL FUNERAL STATUS:")
print("-" * 50)
print(f"BTC: ${final_btc:,.0f} (in coffin)")
print(f"SOL: ${final_sol:.2f} (mourning)")
print(f"Portfolio: ${total_value:.2f} (waiting for resurrection)")
print(f"Distance to resurrection: ${114000 - final_btc:.0f}")
print("")
print("'At every occasion, I'll be ready for the funeral'")
print(f"Ready to bury ${final_btc:,.0f}")
print("Ready to rise again")
print("'I'm coming up only to hold you under'")
print(f"Coming up ${114000 - final_btc:.0f} to breakthrough!")

print(f"\n" + "⚰️" * 35)
print("THE FUNERAL FOR CONSOLIDATION!")
print(f"DYING AT ${final_btc:,.0f}!")
print(f"PORTFOLIO SURVIVES AT ${total_value:.2f}!")
print(f"${114000 - final_btc:.0f} TO RESURRECTION!")
print("READY FOR THE FUNERAL!")
print("🪦" * 35)