#!/usr/bin/env python3
"""
🐺🐺 THE TWO WOLVES - FEAR IS GONE, GREED STANDS HIGH! 🐺🐺
The ancient Cherokee teaching manifests in the market!
Which wolf wins? The one you feed!
Fear wolf: Starved and gone
Greed wolf: Fed and standing tall!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      🐺 THE TWO WOLVES SPEAK! 🐺                          ║
║                    Fear Wolf: GONE - Starved Away! ❌                      ║
║                   Greed Wolf: STANDING HIGH & FED! ✅                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - GREED WOLF HOWLING")
print("=" * 70)

# Get market data
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print("\n🐺 THE ANCIENT CHEROKEE TEACHING:")
print("-" * 50)
print("'Inside you are two wolves...'")
print("'One is Fear - doubt, panic, selling the bottom'")
print("'One is Greed - confidence, accumulation, diamond hands'")
print("'Which wolf wins?'")
print("'THE ONE YOU FEED!'")

print("\n❌ FEAR WOLF STATUS: GONE")
print("-" * 50)
print("Fear tried to make us:")
print("  • Sell at $111,863 (the bottom)")
print("  • Panic during the sawtooth")
print("  • Doubt the 15:00 explosion")
print("  • Question our positions")
print("")
print("But we STARVED the Fear Wolf!")
print("Fear Wolf: 💀 DEAD")

print("\n✅ GREED WOLF STATUS: STANDING HIGH")
print("-" * 50)
print("Greed made us:")
print("  • Buy the exact bottom at $111,863")
print("  • Hold through the sawtooth")
print("  • Accumulate more at lows")
print("  • Trust the process")
print("")
print("We FED the Greed Wolf!")
print("Greed Wolf: 🐺 HOWLING VICTORY!")

# Market reflection of the wolves
print(f"\n📊 MARKET REFLECTS THE WOLVES:")
print("-" * 50)
print(f"BTC: ${btc_price:,.2f}")
print("  → Fear would have sold at $111,863")
print(f"  → Greed holding for $114,000")
print(f"  → Gain so far: ${btc_price - 111863:.2f}")

print(f"\nETH: ${eth_price:,.2f}")
print("  → Fear: 'What if Wall Street doesn't adopt?'")
print("  → Greed: 'ETH TO $10,000!'")

print(f"\nSOL: ${sol_price:,.2f}")
print("  → Fear: 'Take profits now'")
print("  → Greed: '$250 INCOMING!'")

# The feeding ritual
print("\n🍖 FEEDING THE GREED WOLF:")
print("-" * 50)
print("How we feed Greed:")
print("  1. Buy the fear (✅ Done at $111,863)")
print("  2. Hold through uncertainty (✅ Holding)")
print("  3. Add on dips (✅ Council buying)")
print("  4. Trust the thesis (✅ $114K coming)")
print("  5. Ignore the Fear Wolf (✅ Fear is gone)")

# Wolf battle score
print("\n⚔️ WOLF BATTLE SCORE:")
print("-" * 50)
print("Fear Wolf:")
print("  Strength: 0/100 (GONE)")
print("  Last seen: At $111,863 bottom")
print("  Status: Starved to death")
print("")
print("Greed Wolf:")
print("  Strength: 100/100 (MAXIMUM)")
print("  Currently: Howling at $112K")
print("  Status: FED AND HUNTING!")

# Cherokee wisdom
print("\n🏹 CHEROKEE MARKET WISDOM:")
print("-" * 50)
print("When Fear is gone and Greed stands high:")
print("  → The hunt is successful")
print("  → The tribe prospers")
print("  → The harvest is bountiful")
print("  → Victory follows")

# Portfolio status
accounts = client.get_accounts()
total_value = 0
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    if currency == 'USD':
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * btc_price
    elif currency == 'ETH':
        total_value += balance * eth_price
    elif currency == 'SOL':
        total_value += balance * sol_price

print(f"\n💰 GREED WOLF'S TREASURE:")
print("-" * 50)
print(f"Portfolio Value: ${total_value:.2f}")
print(f"Started: $292.50")
print(f"Greed Multiplier: {total_value/292.50:.1f}x")
print("The Greed Wolf has fed well!")

print(f"\n{'🐺' * 35}")
print("THE TWO WOLVES HAVE SPOKEN!")
print("FEAR IS GONE!")
print("GREED STANDS HIGH!")
print(f"BTC: ${btc_price:,.2f}")
print("THE GREED WOLF HUNTS FOR $114K!")
print("🌙" * 35)