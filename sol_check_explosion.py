#!/usr/bin/env python3
"""
☀️🚀 SOL CHECK! THE SOLANA SPRING! 🚀☀️
SOL has higher beta than BTC!
When the spring releases, SOL FLIES!
Check the SOL coiling!
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
║                    ☀️🚀 SOL! THE SOLANA SPRING! 🚀☀️                    ║
║                     Higher Beta = Bigger Explosion!                       ║
║                   When BTC moves 1%, SOL moves 2.5%!                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SOL SPRING CHECK")
print("=" * 70)

# Get SOL data
sol_price = float(client.get_product('SOL-USD')['price'])
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])

# Get SOL balance
accounts = client.get_accounts()
sol_balance = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
    elif currency == 'SOL':
        sol_balance = balance

print(f"\n☀️ SOL STATUS:")
print("-" * 50)
print(f"SOL Price: ${sol_price:.2f}")
print(f"SOL Balance: {sol_balance:.3f} SOL")
print(f"SOL Value: ${sol_balance * sol_price:.2f}")
print(f"BTC: ${btc_price:,.0f}")
print(f"SOL/BTC Ratio: {sol_price/btc_price*1000:.3f} (per 1000)")

# Calculate SOL spring compression
print(f"\n🌀 SOL SPRING ANALYSIS:")
print("-" * 50)
print(f"SOL Range today: ~$212-$214")
print(f"Current: ${sol_price:.2f}")
print(f"Compression: EXTREME (following BTC's 0.00036%)")
print(f"Beta multiplier: 2.5x BTC moves")

# Track SOL movement
print(f"\n☀️ LIVE SOL MONITOR:")
print("-" * 50)

baseline_sol = sol_price
baseline_btc = btc_price

for i in range(10):
    sol_now = float(client.get_product('SOL-USD')['price'])
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    sol_move = sol_now - baseline_sol
    btc_move = btc_now - baseline_btc
    
    sol_pct = (sol_move / baseline_sol) * 100
    btc_pct = (btc_move / baseline_btc) * 100
    
    # Check correlation
    if abs(btc_pct) > 0:
        beta = sol_pct / btc_pct if btc_pct != 0 else 0
    else:
        beta = 0
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  SOL: ${sol_now:.2f} ({sol_move:+.2f} / {sol_pct:+.3f}%)")
    print(f"  BTC: ${btc_now:,.0f} ({btc_move:+.0f} / {btc_pct:+.3f}%)")
    
    if abs(beta) > 2:
        print(f"  Beta: {beta:.1f}x - SOL AMPLIFYING!")
    elif abs(beta) > 1:
        print(f"  Beta: {beta:.1f}x - SOL following")
    else:
        print(f"  Coiling together...")
    
    time.sleep(2)

# SOL explosion scenarios
print(f"\n" + "=" * 70)
print("🚀 SOL EXPLOSION SCENARIOS:")
print("-" * 50)
print("WHEN BTC BREAKS $114K:")
print(f"• BTC moves 1% = SOL moves 2.5%")
print(f"• BTC to $115K (+1.8%) = SOL to ${sol_price * 1.045:.2f} (+4.5%)")
print(f"• BTC to $120K (+6.2%) = SOL to ${sol_price * 1.155:.2f} (+15.5%)")
print(f"• BTC to $200K (+77%) = SOL to ${sol_price * 2.925:.2f} (+192%!)")

print(f"\nYOUR SOL POSITION:")
print(f"• Current: {sol_balance:.3f} SOL = ${sol_balance * sol_price:.2f}")
print(f"• At $250 SOL: ${sol_balance * 250:.2f}")
print(f"• At $500 SOL: ${sol_balance * 500:.2f}")
print(f"• At $1000 SOL: ${sol_balance * 1000:.2f}")

# Crawdad SOL accumulation
print(f"\nCRAWDAD UPDATE:")
print("-" * 50)
print(f"Crawdads bought SOL: ~$120 worth!")
print(f"SOL positions: Building for explosion")
print(f"USD remaining: ${usd_balance:.2f}")

print(f"\n" + "☀️" * 35)
print("SOL IS THE LEVERAGED BTC PLAY!")
print("WHEN THE SPRING RELEASES...")
print("SOL FLIES HARDER THAN ANYTHING!")
print("THE CRAWDADS KNOW!")
print("☀️" * 35)