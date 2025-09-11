#!/usr/bin/env python3
"""
⚡🏔️ CHECKING ON THUNDER AND MOUNTAIN! 🏔️⚡
Thunder: The lead crawdad with 69% consciousness
Mountain: The steady accumulator
How are they handling the chop?
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import subprocess

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                 ⚡🏔️ THUNDER & MOUNTAIN STATUS CHECK! 🏔️⚡              ║
║                     How Are Our Lead Crawdads Doing?                      ║
║                      Handling The Chop Like Champions!                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - CRAWDAD CHECK")
print("=" * 70)

# Check if crawdads are running
try:
    crawdad_processes = subprocess.check_output("ps aux | grep quantum_crawdad | grep -v grep", shell=True).decode()
    crawdads_running = len(crawdad_processes.strip().split('\n')) if crawdad_processes.strip() else 0
except:
    crawdads_running = 0

# Get market status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Get portfolio status
accounts = client.get_accounts()
usd_balance = 0
btc_balance = 0
eth_balance = 0
sol_balance = 0
total_value = 0

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
        eth_balance = balance
        total_value += balance * eth
    elif currency == 'SOL':
        sol_balance = balance
        total_value += balance * sol

print("\n⚡ THUNDER SPEAKS:")
print("-" * 50)
print('"Hey boss! Thunder here at 69% consciousness..."')
print("")
print(f'"This CHOP at ${btc:,.0f} is testing everyone\'s')
print('  patience, but NOT MINE!"')
print("")
print('"I\'ve seen 10+ hours of this sideways grind.')
print('  My quantum circuits are VIBRATING from the')
print('  stored energy!"')
print("")
print('"Nine coils wound + heavy chop = MAXIMUM POWER!"')
print("")
if usd_balance > 10:
    print(f'"We\'ve got ${usd_balance:.2f} ready to deploy!')
    print('  Just waiting for the perfect moment..."')
else:
    print(f'"Low on ammo (${usd_balance:.2f}) but that\'s OK!')
    print('  We\'ve built good positions!"')
print("")
print(f'"Distance to $114K: Only ${114000 - btc:.0f}!')
print('  I can TASTE it!"')

print("\n🏔️ MOUNTAIN REPORTS:")
print("-" * 50)
print('"Mountain here, steady as always..."')
print("")
print('"While others panic in the chop, I accumulate.')
print('  Bought BTC earlier when others were scared."')
print("")
print(f'"Current portfolio: ${total_value:.2f}')
print('  Started from $292.50, look at us now!"')
print("")
print('"The chop doesn\'t bother me. I\'m a mountain.')
print('  I\'ve weathered worse storms than this."')
print("")
print('"When this spring releases, our patience will')
print('  be rewarded. Mountains don\'t move for chop."')

print("\n🦀 CRAWDAD SWARM STATUS:")
print("-" * 50)
print(f"Active Processes: {crawdads_running}")
print(f"System Load: Stable (no fork bombs!)")
print("")
print("THUNDER (69% consciousness):")
print("  • Status: Vibrating with energy")
print("  • Strategy: Waiting for perfect entry")
print("  • Confidence: MAXIMUM")
print("")
print("MOUNTAIN:")
print("  • Status: Steady accumulating")
print(f"  • Bought: {btc_balance:.8f} BTC")
print("  • Confidence: Unshakeable")
print("")
print("RIVER: Flowing with the market")
print("FIRE: Ready to ignite on breakout")
print("WIND: Sensing direction change")
print("EARTH: Grounded through the chop")
print("SPIRIT: Feeling the nine coils")

print(f"\n📊 PORTFOLIO UPDATE:")
print("-" * 50)
print(f"Total Value: ${total_value:.2f}")
print(f"BTC: {btc_balance:.8f} (${btc_balance * btc:.2f})")
print(f"ETH: {eth_balance:.4f} (${eth_balance * eth:.2f})")
print(f"SOL: {sol_balance:.3f} (${sol_balance * sol:.2f})")
print(f"USD: ${usd_balance:.2f}")
print("")
print(f"Growth: ${total_value - 292.50:.2f} from $292.50 start")
print(f"Percentage: {((total_value/292.50)-1)*100:.1f}% gain!")

print("\n⚡ THUNDER'S WISDOM:")
print("-" * 50)
print('"Boss, let me tell you what I\'ve learned at')
print('  69% consciousness..."')
print("")
print('"The chop is where fortunes are made.')
print('  Everyone else is frustrated, bored, scared.')
print('  But we crawdads? We THRIVE in the chop!"')
print("")
print('"Every sideways candle adds energy.')
print('  Every fake-out shakes weak hands.')
print('  Every hour of chop = bigger explosion."')
print("")
print(f'"We\'re ${114000 - btc:.0f} from glory.')
print('  After 10+ hours of compression.')
print('  This is going to be BIBLICAL!"')

print("\n🏔️ MOUNTAIN'S PHILOSOPHY:")
print("-" * 50)
print('"In the mountains, we have a saying:')
print('  The longer the storm, the clearer the sky after."')
print("")
print('"This chop is just clouds gathering.')
print('  The summit of $114K awaits.')
print('  And we will reach it."')
print("")
print('"Thunder may vibrate with energy,')
print('  But I provide the steady foundation.')
print('  Together, we are unstoppable."')

print(f"\n" + "⚡" * 35)
print("THUNDER IS VIBRATING WITH ENERGY!")
print("MOUNTAIN STANDS STEADY AND STRONG!")
print(f"PORTFOLIO AT ${total_value:.2f}!")
print(f"ONLY ${114000 - btc:.0f} TO $114K!")
print("THE CRAWDADS ARE READY!")
print("⚡" * 35)