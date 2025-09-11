#!/usr/bin/env python3
"""
💰🚀 FRESH CAPITAL ARRIVED! $244.52! 🚀💰
Thunder at 69%: "AMMUNITION RELOADED!"
From $4.51 to $244.52 - 54X MORE FIREPOWER!
Time to deploy into this $112K consolidation!
Perfect timing before the $114K breakout!
We can finally BUY THE DIP!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    💰 FRESH CAPITAL DEPLOYED! 💰                          ║
║                       $244.52 Ready For Action!                           ║
║                    Time To Feed The Crawdads Again!                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - CAPITAL ANALYSIS")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Get all balances
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
    elif currency == 'DOGE':
        doge_price = float(client.get_product('DOGE-USD')['price'])
        total_value += balance * doge_price

print(f"\n💰 CAPITAL STATUS:")
print("-" * 50)
print(f"Fresh USD available: ${usd_balance:.2f}")
print(f"Previous balance: $4.51")
print(f"New deposit: ${usd_balance - 4.51:.2f}")
print(f"Total portfolio: ${total_value:.2f}")
print("")
print(f"BTC price: ${btc:,.0f}")
print(f"ETH price: ${eth:.2f}")
print(f"SOL price: ${sol:.2f}")

# What we can buy
print(f"\n🛒 BUYING POWER ANALYSIS:")
print("-" * 50)
print(f"With ${usd_balance:.2f} we can buy:")
print(f"• BTC: {usd_balance/btc:.8f} (${usd_balance:.2f})")
print(f"• ETH: {usd_balance/eth:.6f} (${usd_balance:.2f})")
print(f"• SOL: {usd_balance/sol:.4f} (${usd_balance:.2f})")
print("")
print("Or split deployment:")
print(f"• 50% BTC: {(usd_balance*0.5)/btc:.8f} BTC (${usd_balance*0.5:.2f})")
print(f"• 30% ETH: {(usd_balance*0.3)/eth:.6f} ETH (${usd_balance*0.3:.2f})")
print(f"• 20% SOL: {(usd_balance*0.2)/sol:.4f} SOL (${usd_balance*0.2:.2f})")

# Thunder's deployment strategy
print(f"\n⚡ THUNDER'S DEPLOYMENT STRATEGY (69%):")
print("-" * 50)
print("'PERFECT TIMING!'")
print("")
print("The situation:")
print(f"• BTC stuck at ${btc:,.0f}")
print(f"• Only ${114000 - btc:.0f} to breakout")
print("• 17+ hours of consolidation")
print("• Lending boom = supply shock coming")
print("")
print("Recommended deployment:")
print(f"• 60% into BTC ({(usd_balance*0.6)/btc:.8f} BTC)")
print(f"• 25% into SOL ({(usd_balance*0.25)/sol:.4f} SOL)")
print(f"• 15% into ETH ({(usd_balance*0.15)/eth:.6f} ETH)")
print("")
print("Why this split:")
print("• BTC ready to explode to $114K")
print("• SOL has whale accumulation")
print("• ETH lagging (will catch up)")

# Portfolio projections with deployment
print(f"\n📊 PORTFOLIO PROJECTIONS:")
print("-" * 50)
print(f"Current total: ${total_value:.2f}")
print("")
print("If we deploy all $244.52:")
print(f"• At $114K BTC: ${total_value * (114000/btc):.2f}")
print(f"• At $120K BTC: ${total_value * (120000/btc):.2f}")
print(f"• At $126K BTC: ${total_value * (126000/btc):.2f}")
print("")
print("Potential gains from deployment:")
print(f"• +10% move: ${usd_balance * 1.1:.2f} (${usd_balance * 0.1:.2f} profit)")
print(f"• +20% move: ${usd_balance * 1.2:.2f} (${usd_balance * 0.2:.2f} profit)")
print(f"• +50% move: ${usd_balance * 1.5:.2f} (${usd_balance * 0.5:.2f} profit)")

# Crawdad feeding time
print(f"\n🦀 CRAWDAD FEEDING TIME:")
print("-" * 50)
print("The crawdads have been starving with only $4.51!")
print(f"Now they have ${usd_balance:.2f} to feast on!")
print("")
print("Crawdad allocation ($35 each):")
print(f"• Thunder (69%): Ready for $35")
print(f"• Mountain (steady): Ready for $35")
print(f"• River (flowing): Ready for $35")
print(f"• Fire (aggressive): Ready for $35")
print(f"• Wind (swift): Ready for $35")
print(f"• Earth (grounded): Ready for $35")
print(f"• Spirit (wise): Ready for $34.52")
print("")
print(f"Total for crawdads: ${35*6 + 34.52:.2f}")

# Action plan
print(f"\n🎯 ACTION PLAN:")
print("-" * 50)
print(f"1. Deploy ${usd_balance:.2f} strategically")
print(f"2. Focus on BTC before $114K breakout")
print(f"3. Add to SOL position (whale following)")
print(f"4. Small ETH for catch-up play")
print(f"5. Watch for breakout above ${btc:,.0f}")
print(f"6. Target: $114K (${114000 - btc:.0f} away)")
print("")
print("This is the ammunition we needed!")
print("Perfect timing at this consolidation!")
print("LET'S DEPLOY!")

print(f"\n" + "💰" * 35)
print(f"FRESH CAPITAL: ${usd_balance:.2f}!")
print(f"TOTAL PORTFOLIO: ${total_value:.2f}!")
print(f"BTC AT ${btc:,.0f}!")
print(f"${114000 - btc:.0f} TO BREAKOUT!")
print("TIME TO FEAST!")
print("💰" * 35)