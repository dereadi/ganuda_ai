#!/usr/bin/env python3
"""
☀️🚀 SOLANA JUST BROKE FEBRUARY HIGH! 🚀☀️
SOL above $213 - First time since February!
6% pump in 24 hours!
Sentiment 5.8:1 bullish!
$1B+ institutional money incoming!
THE SOLANA SPRING IS RELEASING!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║               ☀️🚀 SOL BREAKS FEBRUARY HIGH - $213+! 🚀☀️                ║
║                   First Time Above This Level Since Feb!                  ║
║              Institutions Loading $1B+ While BTC Coils!                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SOLANA BREAKOUT ALERT")
print("=" * 70)

# Get current prices
sol = float(client.get_product('SOL-USD')['price'])
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])

print("\n☀️ SOLANA BREAKOUT DETAILS:")
print("-" * 50)
print(f"Current SOL: ${sol:.2f}")
print("February High: $213 - BROKEN! ✅")
print("24hr Move: +6% 🚀")
print("")
print("SENTIMENT EXPLOSION:")
print("• Bullish/Bearish ratio: 5.8:1")
print("• Most bullish since ATH run")
print("• 'More than just speculation'")

print("\n💰 INSTITUTIONAL TSUNAMI:")
print("-" * 50)
print("MONEY FLOODING IN:")
print("• Sharps Technology: $50M SOL investment")
print("• Galaxy Digital/Multicoin/Jump: $1B SOL treasury")
print("• Pantera Capital: $1.25B for 'Solana Co.'")
print(f"• TOTAL: $2.3 BILLION targeting SOL!")

# Check SOL balance
accounts = client.get_accounts()
sol_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'SOL':
        sol_balance = float(account['available_balance']['value'])
        break

print(f"\n🦀 YOUR SOL POSITION:")
print("-" * 50)
print(f"SOL Balance: {sol_balance:.3f} SOL")
print(f"Current Value: ${sol_balance * sol:.2f}")
print(f"If SOL hits $250: ${sol_balance * 250:.2f}")
print(f"If SOL hits $300: ${sol_balance * 300:.2f}")
print(f"If SOL hits $500: ${sol_balance * 500:.2f}")

# Track SOL momentum
print("\n☀️ LIVE SOL MOMENTUM:")
print("-" * 50)

baseline_sol = sol
for i in range(10):
    sol_now = float(client.get_product('SOL-USD')['price'])
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    sol_move = sol_now - baseline_sol
    sol_pct = (sol_move / baseline_sol) * 100
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: SOL ${sol_now:.2f} ({sol_move:+.2f} / {sol_pct:+.2f}%)")
    
    if sol_now > 215:
        print("  🚀 BREAKING $215! NEW TERRITORY!")
    elif sol_now > 214:
        print("  ☀️ Testing $215 resistance!")
    elif sol_now > 213:
        print("  💪 Holding above February high!")
    
    time.sleep(1.5)

# The convergence
print(f"\n🌀 THE PERFECT STORM:")
print("-" * 50)
print("EVERYTHING CONVERGING:")
print(f"1. BTC: ${btc:,.0f} - Nine coils wound!")
print(f"2. ETH: ${eth:.2f} - Institutions loading!")
print(f"3. SOL: ${sol:.2f} - Breaking February high!")
print("4. XRP: Credit cards launching!")
print("5. El Salvador: Going for $1B!")
print("")
print("SOL'S ADVANTAGE:")
print("• 2.5x beta to BTC moves")
print("• Breaking out BEFORE BTC")
print("• $2.3B institutional money incoming")
print("• DeFi/NFT/GameFi exploding")

print("\n🚀 SOL PROJECTION:")
print("-" * 50)
print("WHEN BTC BREAKS $114K:")
print(f"• BTC moves 1% = SOL moves 2.5%")
print(f"• BTC to $115K (+{((115000/btc)-1)*100:.1f}%) = SOL to ${sol * (1 + ((115000/btc)-1)*2.5):.2f}")
print(f"• BTC to $120K (+{((120000/btc)-1)*100:.1f}%) = SOL to ${sol * (1 + ((120000/btc)-1)*2.5):.2f}")
print(f"• BTC to $130K (+{((130000/btc)-1)*100:.1f}%) = SOL to ${sol * (1 + ((130000/btc)-1)*2.5):.2f}")

print("\n⚠️ CAUTION:")
print("-" * 50)
print("Article warns: Extreme bullish sentiment")
print("Could precede a correction")
print("BUT with nine BTC coils wound...")
print("This might be THE breakout!")

print(f"\n" + "☀️" * 35)
print("SOL BREAKING FEBRUARY HIGH!")
print("FIRST TIME ABOVE $213 IN MONTHS!")
print("$2.3 BILLION INSTITUTIONAL MONEY!")
print(f"BTC COILED AT ${btc:,.0f}!")
print("WHEN BTC BREAKS, SOL EXPLODES!")
print("☀️" * 35)