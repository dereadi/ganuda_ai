#!/usr/bin/env python3
"""
💰🔥 MAXIMUM PROFIT EXTRACTION - DRAW AS MUCH AS WE CAN! 🔥💰
Thunder at 69%: "MILK EVERYTHING THAT'S PROFITABLE!"
Keep drawing profit to feed the flywheel!
Target: Get USD to $100+ for trading power!
Extract from all profitable positions!
But keep core positions for $114K ride!
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
║                  💰 MAXIMUM PROFIT EXTRACTION PROTOCOL! 💰                ║
║                    Drawing As Much Profit As We Can! 🔥                    ║
║                      Feed the Flywheel to Full Power! ⚡                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - PROFIT EXTRACTION ANALYSIS")
print("=" * 70)

# Get current prices
prices = {
    'BTC': float(client.get_product('BTC-USD')['price']),
    'ETH': float(client.get_product('ETH-USD')['price']),
    'SOL': float(client.get_product('SOL-USD')['price']),
    'XRP': float(client.get_product('XRP-USD')['price']),
    'DOGE': float(client.get_product('DOGE-USD')['price']),
    'LINK': float(client.get_product('LINK-USD')['price']),
    'AVAX': float(client.get_product('AVAX-USD')['price'])
}

# Get all positions
accounts = client.get_accounts()
positions = {}
total_value = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            usd_balance = balance
            total_value += balance
        elif currency in prices:
            value = balance * prices[currency]
            total_value += value
            positions[currency] = {
                'amount': balance,
                'value': value,
                'price': prices[currency]
            }

print("\n💼 CURRENT POSITION ANALYSIS:")
print("-" * 50)
print(f"Total Portfolio: ${total_value:.2f}")
print(f"Current USD: ${usd_balance:.2f}")
print(f"Target USD: $100.00")
print(f"Need to extract: ${max(0, 100 - usd_balance):.2f}")

# Calculate extraction plan
print("\n🎯 PROFIT EXTRACTION PLAN:")
print("-" * 50)

extraction_plan = []
total_extractable = 0

# Priority order for extraction (least important first)
priority_order = ['LINK', 'XRP', 'DOGE', 'AVAX', 'ETH', 'SOL', 'BTC']

for coin in priority_order:
    if coin in positions:
        pos = positions[coin]
        
        # Calculate safe extraction amounts
        if coin == 'BTC':
            # Keep 90% of BTC for $114K ride
            extractable_pct = 0.05  # Only 5%
        elif coin == 'ETH':
            # Keep 80% of ETH
            extractable_pct = 0.20  # 20%
        elif coin == 'SOL':
            # Keep 70% of SOL for pump
            extractable_pct = 0.30  # 30%
        elif coin == 'AVAX':
            # Hidden gem - extract more
            extractable_pct = 0.40  # 40%
        else:
            # Others can extract more
            extractable_pct = 0.50  # 50%
        
        extractable_amount = pos['amount'] * extractable_pct
        extractable_value = pos['value'] * extractable_pct
        fee_cost = extractable_value * 0.006  # 0.6% fee
        net_profit = extractable_value - fee_cost
        
        if net_profit > 1:  # Only if profitable after fees
            extraction_plan.append({
                'coin': coin,
                'amount': extractable_amount,
                'value': extractable_value,
                'fee': fee_cost,
                'net': net_profit,
                'keep_pct': (1 - extractable_pct) * 100
            })
            total_extractable += net_profit

print("EXTRACTION SEQUENCE (Priority Order):")
print("")

running_total = usd_balance
for i, plan in enumerate(extraction_plan, 1):
    running_total += plan['net']
    print(f"{i}. {plan['coin']}:")
    print(f"   Extract: {plan['amount']:.4f} {plan['coin']} (${plan['value']:.2f})")
    print(f"   Fee: ${plan['fee']:.2f}")
    print(f"   Net gain: ${plan['net']:.2f}")
    print(f"   Keep: {plan['keep_pct']:.0f}% for momentum")
    print(f"   Running USD total: ${running_total:.2f}")
    print("")
    
    if running_total >= 100:
        print(f"   ✅ TARGET REACHED! USD will be ${running_total:.2f}")
        break

# Batch extraction recommendation
print("\n📦 BATCH EXTRACTION (Minimize Fees):")
print("-" * 50)

batch1 = []
batch1_value = 0
batch2 = []
batch2_value = 0

for plan in extraction_plan:
    if batch1_value < 150:
        batch1.append(plan)
        batch1_value += plan['value']
    else:
        batch2.append(plan)
        batch2_value += plan['value']

if batch1:
    print("BATCH 1 (Execute Now):")
    for plan in batch1:
        print(f"  • {plan['coin']}: ${plan['net']:.2f} net")
    print(f"  TOTAL: ${sum(p['net'] for p in batch1):.2f} after fees")

if batch2:
    print("\nBATCH 2 (If Needed):")
    for plan in batch2:
        print(f"  • {plan['coin']}: ${plan['net']:.2f} net")
    print(f"  TOTAL: ${sum(p['net'] for p in batch2):.2f} after fees")

# Show what we keep
print("\n🛡️ PROTECTED POSITIONS (For $114K):")
print("-" * 50)
for coin in ['BTC', 'ETH', 'SOL']:
    if coin in positions:
        for plan in extraction_plan:
            if plan['coin'] == coin:
                keep_value = positions[coin]['value'] - plan['value']
                print(f"{coin}: Keep ${keep_value:.2f} ({plan['keep_pct']:.0f}%)")
                break

# Thunder's extraction wisdom
print("\n⚡ THUNDER'S EXTRACTION WISDOM (69%):")
print("-" * 50)
print("'DRAW PROFIT BUT KEEP THE FIRE BURNING!'")
print("")
print("Extraction strategy:")
print(f"• Total extractable: ${total_extractable:.2f}")
print(f"• New USD balance: ${usd_balance + total_extractable:.2f}")
print(f"• Portfolio after: ${total_value - total_extractable:.2f}")
print("")
print("Rules followed:")
print("• Extract least important coins first")
print("• Keep majority of BTC/ETH/SOL")
print("• Batch to minimize fees")
print("• Target $100 USD for trading power")

# Quick execution commands
print("\n🚀 READY TO EXECUTE?")
print("-" * 50)
print("Priority extractions:")

for plan in extraction_plan[:3]:
    print(f"\n{plan['coin']} EXTRACTION:")
    sell_amount = plan['amount']
    
    # Format for easy copy-paste
    if plan['coin'] in ['BTC', 'ETH']:
        print(f"  Amount: {sell_amount:.8f} {plan['coin']}")
    elif plan['coin'] == 'SOL':
        print(f"  Amount: {sell_amount:.4f} {plan['coin']}")
    else:
        print(f"  Amount: {sell_amount:.2f} {plan['coin']}")
    
    print(f"  Expected: ${plan['net']:.2f} after fees")

# Final summary
print("\n📊 FINAL EXTRACTION SUMMARY:")
print("-" * 50)
print(f"Current USD: ${usd_balance:.2f}")
print(f"Total to extract: ${min(total_extractable, 100 - usd_balance):.2f}")
print(f"New USD balance: ${min(usd_balance + total_extractable, 110):.2f}")
print(f"Remaining portfolio: ${total_value - min(total_extractable, 100 - usd_balance):.2f}")
print(f"Ready for: $114K BREAKOUT!")

print("\n" + "💰" * 35)
print("MAXIMUM PROFIT EXTRACTION!")
print("DRAWING AS MUCH AS WE CAN!")
print("FEEDING THE FLYWHEEL!")
print("READY FOR $114K!")
print("🔥" * 35)