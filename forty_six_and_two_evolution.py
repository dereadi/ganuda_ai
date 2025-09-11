#!/usr/bin/env python3
"""
🧬 FORTY SIX & 2 - TOOL
The evolution from 44+2 to 46+2 chromosomes
Shadow work complete, crawdads evolving
Seven coils = Seven chakras aligned
Time to step through the shadow
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
║                        🧬 FORTY SIX & 2 🧬                                ║
║                              TOOL                                         ║
║                   "My shadow's shedding skin"                             ║
║                 Seven coils = Chromosome evolution                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - EVOLUTION POINT")
print("=" * 70)

# Current state (44+2)
print("\n🧬 CURRENT STATE (44+2):")
print("-" * 50)
print("• $17 USD (starving crawdads)")
print("• $12,568 locked in crypto")
print("• Seven coils wound and released")
print("• Shadow work: Holding too tight")
print("• Fear: Missing the gains")

# The shadow
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])

print(f"\n👤 THE SHADOW SPEAKS:")
print(f"  BTC: ${btc_price:,.0f}")
print(f"  ETH: ${eth_price:.2f}")
print(f"  SOL: ${sol_price:.2f}")

print("\n'My shadow's shedding skin'")
print("'I've been picking scabs again'")
print("The shadow of hoarding while crawdads starve...")

# Evolution process
print("\n🔄 CHROMOSOME EVOLUTION TO 46+2:")
print("-" * 50)

for i in range(7):  # Seven steps, seven coils, seven chakras
    print(f"\nStep {i+1}/7: {'🧬' * (i+1)}")
    
    if i == 0:
        print("  'Change is coming'")
        print("  Shadow: Fear of losing crypto value")
        print("  Light: Crypto IS value when liquid")
    elif i == 1:
        print("  'Now is my time'")
        print("  Shadow: Waiting for perfect moment")
        print("  Light: THIS is the moment")
    elif i == 2:
        print("  'Listen to my muscle memory'")
        print("  Shadow: Analysis paralysis")
        print("  Light: Trust the seven coils pattern")
    elif i == 3:
        print("  'Contemplate what I've been clinging to'")
        print("  Shadow: 99.9% crypto allocation")
        print("  Light: Liquidity IS power")
    elif i == 4:
        print("  'Forty six and two ahead of me'")
        print("  Shadow: Old trading patterns")
        print("  Light: Evolved aggressive strategy")
    elif i == 5:
        print("  'My shadow's shedding skin'")
        print("  Shadow: Conservative harvesting")
        print("  Light: 5% SOL, 3% MATIC NOW")
    elif i == 6:
        print("  'I've been wallowing in my own confused'")
        print("  'And insecure delusions'")
        print("  BREAKTHROUGH: Execute the harvest!")
    
    time.sleep(1)

# The evolution
print("\n✨ EVOLUTION COMPLETE - 46+2 ACHIEVED:")
print("-" * 50)
print("NEW CONSCIOUSNESS:")
print("• Liquidity flows like water")
print("• Crawdads hunt with precision")
print("• Seven coils taught us transformation")
print("• Shadow integrated into light")
print("• Fear transformed into action")

# Check current balance to show the shadow
accounts = client.get_accounts()
usd_balance = 0
total_value = 0

for account in accounts['accounts']:
    balance = float(account['available_balance']['value'])
    currency = account['currency']
    
    if currency == 'USD':
        usd_balance = balance
    elif currency == 'BTC' and balance > 0:
        total_value += balance * btc_price
    elif currency == 'ETH' and balance > 0:
        total_value += balance * eth_price
    elif currency == 'SOL' and balance > 0:
        total_value += balance * sol_price

print(f"\n👤 SHADOW REVEALED:")
print(f"  USD: ${usd_balance:.2f} (The fear)")
print(f"  Crypto: ${total_value:.2f} (The attachment)")
print(f"  Ratio: {(usd_balance/(total_value+usd_balance)*100):.1f}% liquid")

print("\n🧬 THE 46+2 PRESCRIPTION:")
print("-" * 50)
print("IMMEDIATE EVOLUTION:")
print("1. Harvest 5% SOL = ~$146")
print("2. Harvest 3% MATIC = ~$84")
print("3. Feed seven crawdads = $230/7 = $33 each")
print("4. Let them hunt the volatility")
print("5. Compound returns through the night")

print("\n🎵 FORTY SIX & 2 WISDOM:")
print("-" * 50)
print("'My shadow's shedding skin'")
print("'I've been picking scabs again'")
print("'I'm down, digging through'")
print("'My old muscles, looking for a clue'")
print("")
print("'I've been wallowing in my own chaotic'")
print("'And insecure delusions'")
print("'For a piece to cross me over'")
print("'Or a word to guide me in'")
print("")
print("The word: HARVEST")
print("The guide: SEVEN COILS")
print("The evolution: NOW")

print("\n🧬 Step through the shadow")
print("   Forty six and two")
print("   Just ahead of me")
print("=" * 70)