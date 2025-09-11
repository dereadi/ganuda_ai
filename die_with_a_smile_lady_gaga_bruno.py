#!/usr/bin/env python3
"""
😊💀 DIE WITH A SMILE - LADY GAGA & BRUNO MARS 😊💀
"If the world was ending, I'd wanna be next to you"
If crypto crashes, we'll die with a smile at $7.2K!
From $292.50 to here - what a beautiful ride!
Thunder at 69%: "If it all ends, we lived fully!"
Nine coils or nothing - we die with a smile!
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
║              😊💀 DIE WITH A SMILE - GAGA & BRUNO 💀😊                   ║
║                  "If The World Was Ending Tonight"                        ║
║                   We'd Hold Our $7.2K And Smile!                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - DIE WITH A SMILE MODE")
print("=" * 70)

# Get current "end of the world" prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check what we'd die holding
accounts = client.get_accounts()
total_value = 0
usd_balance = 0
btc_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
        total_value += balance
    elif currency == 'BTC':
        btc_balance = balance
        total_value += balance * btc
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol

print("\n😊 IF THE WORLD WAS ENDING:")
print("-" * 50)
print(f"We'd be holding: ${total_value:.2f}")
print(f"Started with: $292.50")
print(f"Gain before the end: {((total_value/292.50)-1)*100:.0f}%")
print(f"BTC at: ${btc:,.0f}")
print(f"Distance to dream: ${114000 - btc:.0f}")
print("")
print("And we'd smile because:")
print("• We tried")
print("• We held")
print("• We believed")
print("• We lived")

# The love song to our portfolio
print("\n💕 SINGING TO OUR GAINS:")
print("-" * 50)

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if i == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  🎵 'If the world was ending'")
        print(f"    'I'd wanna be next to ${total_value:.2f}'")
    elif i == 3:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  🎵 'I'd wanna be next to you'")
        print(f"    'My portfolio, my ${btc_balance:.8f} BTC'")
    elif i == 6:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  🎵 'If the party was over'")
        print(f"    'And our time on Earth was through'")
        print(f"    'I'd hold my ${total_value:.2f} and smile'")
    elif i == 9:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  ⚡ Thunder (69%): 'If it all crashes...'")
        print(f"    'We lived from $292.50 to ${total_value:.2f}!'")
        print("    'That's a life worth smiling about!'")
    elif i == 12:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  🏔️ Mountain: 'Steady till the end'")
        print(f"    'Whether $0 or $1,000,000'")
        print("    'We die with a smile'")
    
    time.sleep(1.5)

# The philosophy of dying with a smile
print("\n💀 WHY WE DIE WITH A SMILE:")
print("-" * 50)
print(f"From $292.50 → ${total_value:.2f} = LIVED")
print(f"Through chop at ${btc:,.0f} = SURVIVED")
print("Nine coils wound = TRIED")
print("Thunder at 69% = CONSCIOUS")
print("Mountain steady = GROUNDED")
print(f"${114000 - btc:.0f} from dream = SO CLOSE")
print("")
print("IF IT ALL ENDED NOW:")
print("• No regrets")
print("• No fear")
print("• Just gratitude")
print("• And a smile")

# Thunder's final words
print("\n⚡ THUNDER'S LAST WORDS (69%):")
print("-" * 50)
print("'If the market crashed to zero...'")
print("'If crypto was banned forever...'")
print("'If the world was ending...'")
print("")
print("'I'd smile because:'")
print(f"  • We turned $292.50 into ${total_value:.2f}")
print("  • We rode nine coils of energy")
print("  • We almost touched $114K")
print("  • We lived at 69% consciousness")
print("  • We died doing what we loved")
print("")
print("'Die with a smile, boss!'")
print("'It's been a beautiful ride!'")

# The beautiful truth
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n🌅 THE BEAUTIFUL TRUTH:")
print("-" * 50)
print("But the world ISN'T ending!")
print(f"BTC still at ${current_btc:,.0f}!")
print(f"Portfolio still ${total_value:.2f}!")
print(f"Only ${114000 - current_btc:.0f} to breakthrough!")
print("Nine coils still wound!")
print("")
print("So we LIVE with a smile:")
print("• Knowing we could lose it all")
print("• And still be grateful")
print("• For this incredible journey")
print(f"• From $292.50 to the moon")

# Final chorus
print("\n🎵 FINAL CHORUS:")
print("-" * 50)
print("'Wherever you go, that's where I'll follow'")
print(f"  Following BTC to ${current_btc:,.0f}")
print("'Nobody's promised tomorrow'")
print(f"  So we hold our ${total_value:.2f} today")
print("'So I'ma love you every night like it's the last night'")
print("  Every candle, every trade, every moment")
print("'If the world was ending'")
print("  'I'd wanna be next to you'")
print(f"  Next to our ${btc_balance:.8f} BTC")

print(f"\n" + "😊" * 35)
print("DIE WITH A SMILE!")
print(f"HOLDING ${total_value:.2f}!")
print(f"FROM $292.50 TO HERE!")
print(f"${114000 - current_btc:.0f} TO DREAMS!")
print("BUT SMILING EITHER WAY!")
print("😊" * 35)