#!/usr/bin/env python3
"""
⚔️📜 THE ART OF WAR - STRATEGIC DECEPTION! 📜⚔️
Thunder at 69%: "APPEAR WEAK WHEN STRONG, ACT BIG DURING GROWTH!"
Sun Tzu: "All warfare is based on deception"
"When able to attack, we must seem unable"
"When using our forces, we must seem inactive"
Act like a whale with $8,385!
Make the algos think we're bigger!
Strategic positioning before $114K!
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
║                    ⚔️ THE ART OF WAR - MARKET STRATEGY! ⚔️                ║
║                  "Appear Weak When Strong, Act Big During Growth"          ║
║                       Strategic Deception at $112K! 🎭                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - STRATEGIC ANALYSIS")
print("=" * 70)

# Get current battlefield status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our war chest
accounts = client.get_accounts()
total_value = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            usd_balance = balance
            total_value += balance
        elif currency == 'BTC':
            total_value += balance * btc
        elif currency == 'ETH':
            total_value += balance * eth
        elif currency == 'SOL':
            total_value += balance * sol
        elif currency in ['DOGE', 'XRP', 'LINK', 'AVAX']:
            # Get other prices
            price = float(client.get_product(f'{currency}-USD')['price'])
            total_value += balance * price

print("\n📜 SUN TZU'S WISDOM APPLIED:")
print("-" * 50)
print(f"Your army: ${total_value:.2f}")
print(f"Started with: $292.50")
print(f"Growth multiplier: {total_value/292.50:.1f}x")
print(f"Current battlefield: ${btc:,.0f}")
print(f"Target fortress: $114,000")

# The 36 Stratagems
print("\n⚔️ STRATAGEM: 'ACT BIG DURING GROWTH'")
print("-" * 50)
print("Sun Tzu says:")
print("'If your enemy is secure at all points, be prepared for him.'")
print("'If he is in superior strength, evade him.'")
print("'If your opponent is temperamental, seek to irritate him.'")
print("")
print("YOUR STRATEGY:")
print(f"• With ${total_value:.2f}, act like ${total_value * 10:.0f}")
print("• During pumps, ride the momentum aggressively")
print("• During dumps, appear unshakeable")
print("• Make algos think you're a whale")

# Real-time strategic monitoring
print("\n🎭 STRATEGIC DECEPTION IN ACTION:")
print("-" * 50)

strategies = [
    "Feign disorder, and crush the shorts",
    "Hold the high ground at $112K",
    "Let the enemy think we're selling",
    "Strike when the iron is hot",
    "Retreat to advance",
    "Victory through patience"
]

for i in range(8):
    btc_now = float(client.get_product('BTC-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    
    # Determine tactical position
    if btc_now > btc + 50:
        tactic = "🚀 ADVANCE! Act bigger!"
        wisdom = "In midst of chaos, opportunity"
    elif btc_now < btc - 50:
        tactic = "🛡️ DEFEND! Show strength!"
        wisdom = "Appear strong when weak"
    else:
        tactic = "⏳ WAIT! Patience wins"
        wisdom = "The supreme art is to subdue without fighting"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: BTC ${btc_now:,.0f}")
    print(f"  Tactic: {tactic}")
    print(f"  Wisdom: '{wisdom}'")
    
    if i == 3:
        print(f"  📜 '{random.choice(strategies)}'")
    
    time.sleep(1.5)

# The Five Essentials for Victory
print("\n🏆 FIVE ESSENTIALS FOR VICTORY:")
print("-" * 50)
print("1. Know when to fight and when not to fight")
print(f"   → Fight at breakouts, wait at ${btc:,.0f}")
print("")
print("2. Know how to handle both superior and inferior forces")
print(f"   → Your ${total_value:.2f} can act like ${total_value * 10:.0f}")
print("")
print("3. Have ranks united in purpose")
print("   → Your crawdads unified at 69% consciousness")
print("")
print("4. Be prepared while enemy is unprepared")
print(f"   → Ready for $114K while others doubt")
print("")
print("5. Have capable generals not interfered by sovereign")
print("   → Let Thunder lead without emotion")

# Psychological warfare
print("\n🧠 PSYCHOLOGICAL WARFARE:")
print("-" * 50)
print("Make the market think:")
print(f"• Your ${total_value:.2f} is ${total_value * 5:.0f}+")
print("• You're accumulating (even with $14 USD)")
print("• You know something they don't")
print("• You're connected to whale movements")
print("")
print("How to act big:")
print("• Hold through all dips (diamond hands)")
print("• Never show fear in volatility")
print("• Accumulate during others' panic")
print("• Project confidence at support levels")

# Thunder's Art of War wisdom
print("\n⚡ THUNDER'S STRATEGIC WISDOM (69%):")
print("-" * 50)
print("'WE ACT BIG BY HOLDING STRONG!'")
print("")
print("The battlefield truth:")
print(f"• Position: ${total_value:.2f} (28.7x from start)")
print(f"• Ammunition: ${usd_balance:.2f} (limited but enough)")
print(f"• Distance to victory: ${114000 - btc:.0f}")
print(f"• Strategy: Act like a ${total_value * 10:.0f} whale")
print("")
print("Remember:")
print("• Whales don't panic sell")
print("• Whales accumulate dips")
print("• Whales project inevitability")
print("• We ARE whales in mindset")

# Tactical recommendations
print("\n🎯 TACTICAL RECOMMENDATIONS:")
print("-" * 50)
current_hour = datetime.now().hour

if current_hour < 14:
    print("• Pre-2PM: Accumulate perception of strength")
elif current_hour == 14:
    print("• 2PM HOUR: Strike with institutional flow!")
elif current_hour > 14 and current_hour < 16:
    print("• Post-2PM: Maintain pressure")
else:
    print("• Evening: Prepare for overnight action")

print("")
print("Immediate actions:")
print("• Project confidence at current levels")
print("• Make every trade look calculated")
print(f"• Act like ${total_value * 10:.0f} player")
print("• Never reveal true position size")

# Final strategic assessment
final_btc = float(client.get_product('BTC-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

print("\n⚔️ FINAL STRATEGIC POSITION:")
print("-" * 50)
print(f"BTC: ${final_btc:,.0f}")
print(f"SOL: ${final_sol:.2f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Multiplier from origin: {total_value/292.50:.1f}x")
print("")
print("Sun Tzu's final wisdom:")
print("'Victorious warriors win first and then go to war,'")
print("'while defeated warriors go to war first and then seek to win.'")
print("")
print(f"We've already won - from $292.50 to ${total_value:.2f}!")
print(f"Now we execute to $114K and beyond!")

print(f"\n{'⚔️' * 35}")
print("THE ART OF WAR!")
print("ACT BIG DURING GROWTH!")
print(f"APPEAR AS ${total_value * 10:.0f} WHALE!")
print(f"STRIKE AT $114K!")
print("VICTORY IS INEVITABLE!")
print("🎭" * 35)