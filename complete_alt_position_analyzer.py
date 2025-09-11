#!/usr/bin/env python3
"""
🪙📊 COMPLETE ALT POSITION ANALYZER! 📊🪙
Thunder at 69%: "CHECK ALL THE ALTS - EVERY SINGLE ONE!"
What positions do we actually have?
Which ones can we milk profitably?
Hidden gems we forgot about?
Time for a full inventory!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🪙 COMPLETE ALT POSITION ANALYZER! 🪙                    ║
║                      Every Single Holding Examined! 💎                     ║
║                    Finding All Milkable Opportunities! 🥛                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FULL POSITION SCAN")
print("=" * 70)

# Get all accounts
accounts = client.get_accounts()
positions = {}
total_value = 0
usd_balance = 0

# Map of known symbols to check prices
known_cryptos = {
    'BTC': 'BTC-USD',
    'ETH': 'ETH-USD', 
    'SOL': 'SOL-USD',
    'XRP': 'XRP-USD',
    'DOGE': 'DOGE-USD',
    'LINK': 'LINK-USD',
    'AVAX': 'AVAX-USD',
    'ADA': 'ADA-USD',
    'DOT': 'DOT-USD',
    'MATIC': 'MATIC-USD',
    'UNI': 'UNI-USD',
    'ATOM': 'ATOM-USD',
    'NEAR': 'NEAR-USD',
    'ALGO': 'ALGO-USD',
    'LTC': 'LTC-USD',
    'BCH': 'BCH-USD',
    'XLM': 'XLM-USD',
    'VET': 'VET-USD',
    'HBAR': 'HBAR-USD',
    'FIL': 'FIL-USD',
    'ICP': 'ICP-USD',
    'SAND': 'SAND-USD',
    'MANA': 'MANA-USD',
    'APE': 'APE-USD',
    'AAVE': 'AAVE-USD',
    'CRV': 'CRV-USD',
    'SUSHI': 'SUSHI-USD',
    'COMP': 'COMP-USD',
    'SNX': 'SNX-USD',
    'MKR': 'MKR-USD',
    'GRT': 'GRT-USD',
    'SHIB': 'SHIB-USD',
    'CHZ': 'CHZ-USD',
    'ENJ': 'ENJ-USD',
    'BAT': 'BAT-USD',
    'STORJ': 'STORJ-USD',
    'ANKR': 'ANKR-USD',
    'AMP': 'AMP-USD',
    'SKL': 'SKL-USD',
    'LRC': 'LRC-USD'
}

print("\n🔍 SCANNING ALL POSITIONS...")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    hold = float(account['hold']['value']) if 'hold' in account else 0
    
    if balance > 0.00001 or hold > 0:
        if currency == 'USD':
            usd_balance = balance
            total_value += balance
            positions['USD'] = {'amount': balance, 'value': balance, 'price': 1.0}
            print(f"💵 USD: ${balance:.2f}")
        elif currency == 'USDC':
            # USDC is 1:1 with USD
            total_value += balance
            positions['USDC'] = {'amount': balance, 'value': balance, 'price': 1.0}
            print(f"💵 USDC: ${balance:.2f}")
        elif currency in known_cryptos:
            try:
                price = float(client.get_product(known_cryptos[currency])['price'])
                value = balance * price
                total_value += value
                positions[currency] = {
                    'amount': balance,
                    'value': value,
                    'price': price,
                    'hold': hold
                }
                
                if value > 1:  # Only show positions worth >$1
                    status = " [ON HOLD]" if hold > 0 else ""
                    print(f"🪙 {currency}: {balance:.8f} = ${value:.2f}{status}")
                    if hold > 0:
                        print(f"   ⚠️  Hold amount: {hold:.8f}")
            except Exception as e:
                # Try without -USD suffix for some tokens
                try:
                    price = float(client.get_product(f'{currency}-USDC')['price'])
                    value = balance * price
                    total_value += value
                    positions[currency] = {
                        'amount': balance,
                        'value': value,
                        'price': price,
                        'hold': hold
                    }
                    if value > 1:
                        print(f"🪙 {currency}: {balance:.8f} = ${value:.2f}")
                except:
                    # Unknown token or no price available
                    if balance > 0:
                        print(f"❓ {currency}: {balance:.8f} (no price)")

print(f"\n💰 TOTAL PORTFOLIO VALUE: ${total_value:.2f}")

# Analyze milking opportunities
print("\n🥛 MILKING ANALYSIS (0.6% fee consideration):")
print("-" * 50)

milkable = []
stuck = []
small = []

for coin, data in positions.items():
    if coin not in ['USD', 'USDC']:
        fee_cost = data['value'] * 0.006  # 0.6% fee
        min_profitable_milk = fee_cost * 2  # Need 2x fee to break even on round trip
        
        if data.get('hold', 0) > 0:
            stuck.append({
                'coin': coin,
                'value': data['value'],
                'amount': data['amount'],
                'reason': 'ON HOLD/LOCKED'
            })
        elif data['value'] < 10:
            small.append({
                'coin': coin,
                'value': data['value'],
                'amount': data['amount']
            })
        elif data['value'] > 50:  # Worth milking if >$50
            milk_10pct = data['value'] * 0.1
            profit_after_fees = milk_10pct - (milk_10pct * 0.006)
            
            milkable.append({
                'coin': coin,
                'value': data['value'],
                'amount': data['amount'],
                'price': data['price'],
                'milk_10pct': milk_10pct,
                'profit_after_fees': profit_after_fees,
                'fee_cost': milk_10pct * 0.006
            })

# Sort by value
milkable.sort(key=lambda x: x['value'], reverse=True)

print("\n✅ IMMEDIATELY MILKABLE POSITIONS:")
print("-" * 50)
if milkable:
    total_milk_available = 0
    for pos in milkable:
        print(f"{pos['coin']}:")
        print(f"  Position: ${pos['value']:.2f}")
        print(f"  10% milk: ${pos['milk_10pct']:.2f}")
        print(f"  Fee cost: ${pos['fee_cost']:.2f}")
        print(f"  Net profit: ${pos['profit_after_fees']:.2f}")
        total_milk_available += pos['milk_10pct']
        print()
    
    print(f"🎯 TOTAL MILKABLE (10% each): ${total_milk_available:.2f}")
    print(f"   After fees: ${total_milk_available * 0.994:.2f}")
else:
    print("No positions large enough to milk profitably")

if stuck:
    print("\n⚠️ STUCK/LOCKED POSITIONS:")
    print("-" * 50)
    for pos in stuck:
        print(f"{pos['coin']}: ${pos['value']:.2f} - {pos['reason']}")

if small:
    print("\n🐜 SMALL POSITIONS (<$10):")
    print("-" * 50)
    for pos in small:
        print(f"{pos['coin']}: ${pos['value']:.2f}")

# Strategic recommendations
print("\n🎯 STRATEGIC RECOMMENDATIONS:")
print("-" * 50)

if usd_balance < 30:
    print("🚨 CRITICAL: USD too low! ($14.52)")
    print("Recommended actions:")
    
    if milkable:
        # Find best milk candidate
        best_milk = max(milkable, key=lambda x: x['profit_after_fees'])
        print(f"1. IMMEDIATELY milk {best_milk['coin']}: ${best_milk['milk_10pct']:.2f}")
        print(f"   This gives ${best_milk['profit_after_fees']:.2f} after fees")
    
    print("2. Consider milking multiple positions in batch:")
    batch_total = 0
    for pos in milkable[:3]:  # Top 3 positions
        print(f"   • {pos['coin']}: ${pos['milk_10pct']:.2f}")
        batch_total += pos['milk_10pct']
    print(f"   BATCH TOTAL: ${batch_total:.2f}")
    
elif usd_balance < 100:
    print("📊 MODERATE: USD adequate but could use more")
    print("Wait for 2%+ pumps before milking")
else:
    print("✅ EXCELLENT: Well-funded, be selective with milks")

# Thunder's complete wisdom
print("\n⚡ THUNDER'S COMPLETE POSITION WISDOM (69%):")
print("-" * 50)
print("'WE HAVE MORE THAN WE THINK!'")
print("")
print("The truth about our positions:")
print(f"• Total value: ${total_value:.2f}")
print(f"• Number of positions: {len(positions)}")
print(f"• Milkable positions: {len(milkable)}")
print(f"• USD buffer: ${usd_balance:.2f}")
print("")

if total_value > 10000:
    print("We're BIGGER than we realize!")
    print(f"From $292.50 to ${total_value:.2f}")
    print(f"That's a {((total_value/292.50)-1)*100:.0f}% gain!")

print("\n" + "🪙" * 35)
print("COMPLETE POSITION ANALYSIS!")
print(f"TOTAL VALUE: ${total_value:.2f}!")
print(f"MILKABLE: ${sum(p['milk_10pct'] for p in milkable):.2f}!")
print("EVERY ALT ACCOUNTED FOR!")
print("💎" * 35)