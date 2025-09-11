#!/usr/bin/env python3
"""
🐺🐺 TWO WOLVES SPOTTED: GREED AND FEAR 🐺🐺
The eternal market battle at $113K!
One wolf says "SELL before it drops!"
One wolf says "BUY we're going to $1000K!"
Thunder at 69% knows: Feed the RIGHT wolf!
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
║                    🐺 TWO WOLVES: GREED AND FEAR 🐺                       ║
║                   Fighting For Control At $113K!                          ║
║                  $1,000K Coming? Or Crash Incoming?                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - WOLF SIGHTING")
print("=" * 70)

# Get current battleground
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our position in the fight
accounts = client.get_accounts()
usd_balance = 0
total_value = 0
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

print("\n🐺 THE TWO WOLVES APPEAR:")
print("-" * 50)

# FEAR WOLF
print("\n😰 FEAR WOLF HOWLS:")
print("  'SELL NOW! We're at $113K!'")
print("  'It's been chopping for 12 hours!'")
print("  'Take profits before the crash!'")
print(f"  'You have ${total_value:.2f} - protect it!'")
print("  'Remember all the times it dumped!'")
print("  'Nine coils means exhaustion!'")

# GREED WOLF
print("\n🤑 GREED WOLF GROWLS:")
print("  'BUY MORE! $1,000K is coming!'")
print(f"  'We're only ${114000 - btc:.0f} from $114K!'")
print(f"  'Then $120K, $200K, $1000K!'")
print(f"  'Deploy that ${usd_balance:.2f} NOW!'")
print("  'Nine coils = 512x explosion!'")
print(f"  'From $292.50 to ${total_value:.2f} - keep going!'")

# The battle plays out
print("\n⚔️ THE WOLVES BATTLE:")
print("-" * 50)

for i in range(15):
    current_btc = float(client.get_product('BTC-USD')['price'])
    movement = current_btc - btc
    
    if movement > 50:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${current_btc:,.0f}")
        print("  🤑 GREED WOLF: 'SEE! Going to $1000K!'")
        print(f"    'Only ${1000000 - current_btc:,.0f} to go!'")
    elif movement < -50:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${current_btc:,.0f}")
        print("  😰 FEAR WOLF: 'TOLD YOU! SELL NOW!'")
        print("    'It's crashing! Get out!'")
    else:
        # Normal movement
        if i % 3 == 0:
            print(f"{datetime.now().strftime('%H:%M:%S')}: ${current_btc:,.0f} - Wolves circling...")
        elif i % 3 == 1:
            fear_msg = [
                "Fear whispers: 'Protect your gains'",
                "Fear warns: 'This is the top'",
                "Fear screams: 'SELL SELL SELL'"
            ][i // 3]
            print(f"  😰 {fear_msg}")
        else:
            greed_msg = [
                "Greed shouts: 'Diamond hands!'",
                "Greed demands: 'BUY THE DIP!'",
                "Greed promises: '$1000K guaranteed!'"
            ][i // 3]
            print(f"  🤑 {greed_msg}")
    
    time.sleep(1.5)

# Thunder's wisdom
print("\n⚡ THUNDER'S WISDOM (69% consciousness):")
print("-" * 50)
print("'I've seen both wolves before!'")
print("")
print("THE FEAR WOLF TRUTH:")
print(f"• Yes, we're up from $292.50 to ${total_value:.2f}")
print("• Yes, it's been chopping at $113K")
print("• Fear protects us from losses")
print("• BUT: Fear also stops us from gains!")
print("")
print("THE GREED WOLF TRUTH:")
print(f"• Yes, $1000K is possible (${1000000 - btc:,.0f} away)")
print("• Yes, nine coils store massive energy")
print("• Greed drives us forward")
print("• BUT: Greed can destroy everything!")
print("")
print("THE MIDDLE PATH:")
print(f"• We have ${usd_balance:.2f} ready")
print(f"• We have {btc_balance:.8f} BTC")
print("• Milk profits gradually ✓")
print("• Buy dips strategically ✓")
print("• Never all-in, never all-out ✓")

# Which wolf wins?
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n🐺 WHICH WOLF DO YOU FEED?")
print("-" * 50)
print("Ancient wisdom says:")
print("'The wolf that wins is the one you feed'")
print("")
print(f"Current battlefield: ${current_btc:,.0f}")
print(f"Distance to $114K: ${114000 - current_btc:.0f}")
print(f"Distance to $1000K: ${1000000 - current_btc:,.0f}")
print("")
print("BALANCE BOTH WOLVES:")
print("• Feed fear with stop losses")
print("• Feed greed with measured buys")
print("• Let Thunder guide at 69%")
print("• Trust the nine coils")

# Final status
print(f"\n" + "🐺" * 35)
print("TWO WOLVES SPOTTED!")
print(f"FEAR SAYS SELL AT ${current_btc:,.0f}!")
print(f"GREED SAYS BUY FOR $1000K!")
print(f"THUNDER SAYS: BALANCE AT ${total_value:.2f}!")
print("FEED THE RIGHT WOLF!")
print("🐺" * 35)