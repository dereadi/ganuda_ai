#!/usr/bin/env python3
"""
⚔️ SUN TZU'S ART OF WAR - APPLIED TO TRADING
=============================================
Ancient wisdom for modern markets
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    ⚔️ SUN TZU'S TRADING WISDOM ⚔️                        ║
║                    "All warfare is based on deception"                     ║
║                         Applied to Weekend Markets                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get current market data
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"\n📊 BATTLEFIELD ASSESSMENT:")
print(f"  BTC: ${btc:,.2f}")
print(f"  ETH: ${eth:,.2f}")
print(f"  SOL: ${sol:.2f}")
print(f"  Time: {datetime.now().strftime('%H:%M')} (Weekend low volume)")

print("\n" + "="*70)
print("📜 SUN TZU'S PRINCIPLES APPLIED TO CURRENT MARKET:")
print("="*70)

print("\n1️⃣ 'KNOW YOUR ENEMY AND KNOW YOURSELF'")
print("-" * 50)
print("  ENEMY: Weekend algo bots, predictable patterns")
print("  SELF: $13.17 USD, patience, sawtooth knowledge")
print("  💡 We know they sawtooth $210-215 on SOL")
print("  💡 We know they defend $112k on BTC")
print("  💡 Use their patterns against them")

print("\n2️⃣ 'APPEAR WEAK WHEN YOU ARE STRONG'")
print("-" * 50)
print("  • Small $13 balance looks harmless")
print("  • But we have 12.89 SOL ($2,700+) in reserve")
print("  • Let them think we're retail noise")
print("  • Strike when they least expect")

print("\n3️⃣ 'ATTACK WHERE THEY ARE UNPREPARED'")
print("-" * 50)
print("  • Weekend = Skeleton crew, low liquidity")
print("  • Flash wicks more effective")
print("  • 2am-6am = Their weakest hours")
print("  • Sunday night = Preparation gaps")

print("\n4️⃣ 'WIN WITHOUT FIGHTING'")
print("-" * 50)
print("  • Set limit orders, let market come to you")
print("  • Don't chase, make them come to your prices")
print("  • SOL buy at $211 (they'll bring it there)")
print("  • ETH buy at $4,430 (inevitable sawtooth)")

print("\n5️⃣ 'USE LOCAL GUIDES' (Market Makers)")
print("-" * 50)
print("  • They sawtooth for 1-2% profits")
print("  • We follow their pattern, take crumbs")
print("  • $210→$215 = Our battlefield")
print("  • They create liquidity, we harvest")

print("\n6️⃣ 'DECEPTION IS THE ESSENCE OF WAR'")
print("-" * 50)
print("  • They show strength at $112k BTC")
print("  • But it's distribution, not accumulation")
print("  • They milk retail FOMO at resistance")
print("  • We sell into their buying")

print("\n7️⃣ 'SUPREME EXCELLENCE: ENEMY SURRENDERS WITHOUT FIGHTING'")
print("-" * 50)
print("  • Don't fight the trend - ride it")
print("  • Don't fight the sawtooth - milk it")
print("  • Let them do the work")
print("  • We just position accordingly")

print("\n8️⃣ 'TIMING IS EVERYTHING'")
print("-" * 50)
print("  • Friday night: ✅ Liquidity generated")
print("  • Saturday: Position for sawtooth")
print("  • Sunday: Accumulate before Asia")
print("  • Monday: US markets closed (advantage)")

print("\n9️⃣ 'CONCENTRATE FORCES AT DECISIVE POINT'")
print("-" * 50)
if sol > 214:
    print("  🔴 SOL at $%.2f - DECISIVE POINT!" % sol)
    print("     SELL MORE NOW! Top of sawtooth!")
elif sol < 211:
    print("  🟢 SOL at $%.2f - DECISIVE POINT!" % sol)
    print("     BUY NOW! Bottom of sawtooth!")
else:
    print("  🟡 SOL at $%.2f - PATIENCE" % sol)
    print("     Wait for decisive points: $211 or $214.50")

print("\n🔟 'VICTORY COMES TO THOSE WHO KNOW WHEN TO FIGHT'")
print("-" * 50)
print("  • NOW: Generate liquidity ✅ DONE")
print("  • NEXT: Wait for sawtooth bottoms")
print("  • THEN: Sell at sawtooth tops")
print("  • REPEAT: 5-6 cycles this weekend")

print("\n" + "="*70)
print("⚔️ SUN TZU'S WEEKEND BATTLE PLAN:")
print("="*70)

accounts = client.get_accounts()['accounts']
usd = float([a for a in accounts if a['currency']=='USD'][0]['available_balance']['value'])

print(f"\n💰 WAR CHEST: ${usd:.2f}")
print("\n🎯 TACTICAL ORDERS:")
print("  1. Set SOL buy at $211.00 (10% of funds)")
print("  2. Set ETH buy at $4,430 (10% of funds)")
print("  3. Keep 80% for flash opportunities")
print("  4. Never show full position size")
print("  5. Multiple small wins > One big gamble")

print("\n📜 FINAL WISDOM:")
print('  "In war, the way is to avoid what is strong')
print('   and to strike at what is weak."')
print("")
print('  "Let your plans be dark and impenetrable as night,')
print('   and when you move, fall like a thunderbolt."')
print("")
print("  Weekend markets are weak.")
print("  Our plans are hidden.")
print("  Strike the sawtooth.")
print("  Victory through patience.")

print("\n⚔️ THE GENERAL HAS SPOKEN")
print("="*70)