#!/usr/bin/env python3
"""
🥛🎯 CHECK ALL ALT POSITIONS FOR MILKING! 🎯🥛
SOL, ETH, AVAX, MATIC, DOGE, XRP - Who's ready?
Remember: 0.6% fees = need meaningful moves!
Batch our milking for efficiency!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🥛 ALL ALT POSITIONS MILK CHECK! 🥛                    ║
║                      Which Cows Are Ready to Milk? 🐄                      ║
║                    0.6% fees = Only milk the pumps! 💰                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SCANNING ALL ALTS")
print("=" * 70)

# Get all accounts
accounts = client.get_accounts()
positions = {}

# Track USD balance
usd_balance = 0

# Collect all positions
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.001:  # Only show meaningful balances
        if currency == 'USD':
            usd_balance = balance
        else:
            positions[currency] = balance

# Get prices for main alts we care about
alt_prices = {}
milk_opportunities = []

# Check each alt
alts_to_check = ['SOL', 'ETH', 'AVAX', 'MATIC', 'DOGE', 'XRP', 'ADA', 'DOT', 'LINK', 'UNI']

print("\n📊 ALT POSITIONS & MILK POTENTIAL:")
print("-" * 70)
print(f"{'Asset':<8} {'Balance':<12} {'Price':<10} {'Value':<12} {'Status':<30}")
print("-" * 70)

total_portfolio = 0

for alt in alts_to_check:
    if alt in positions and positions[alt] > 0:
        try:
            product = client.get_product(f'{alt}-USD')
            price = float(product['price'])
            balance = positions[alt]
            value = balance * price
            total_portfolio += value
            
            # Determine milk status
            status = ""
            milk_amount = 0
            
            if value > 500:  # Significant position
                if alt == 'SOL':
                    if price > 213:
                        status = "🥛 READY! Milk 10%"
                        milk_amount = balance * 0.1
                    else:
                        status = "📍 Hold, wait for >$215"
                elif alt == 'ETH':
                    if price > 4500:
                        status = "🥛 Consider 5% milk"
                        milk_amount = balance * 0.05
                    else:
                        status = "💎 HODL - Wall St token"
                elif alt == 'AVAX':
                    if price > 35:
                        status = "🥛 MILK 20%!"
                        milk_amount = balance * 0.2
                    else:
                        status = "📍 Wait for pump"
                elif alt == 'MATIC':
                    status = "🥛 Can milk small amount"
                    milk_amount = balance * 0.15
                elif alt == 'XRP':
                    if price > 0.52:
                        status = "🥛 Milk 25%"
                        milk_amount = balance * 0.25
                    else:
                        status = "📍 Hold"
                else:
                    if value > 100:
                        status = "🥛 Consider milking"
                        milk_amount = balance * 0.2
            elif value > 50:
                status = "📍 Small position"
            else:
                status = "🐜 Too small to milk"
            
            print(f"{alt:<8} {balance:<12.4f} ${price:<9.4f} ${value:<11.2f} {status:<30}")
            
            if milk_amount > 0:
                milk_value = milk_amount * price
                fee = milk_value * 0.006
                net = milk_value - fee
                milk_opportunities.append({
                    'asset': alt,
                    'amount': milk_amount,
                    'gross': milk_value,
                    'fee': fee,
                    'net': net
                })
                
        except Exception as e:
            # Asset might not have USD pair
            pass

# Show BTC (sacred, no milk)
if 'BTC' in positions:
    btc = client.get_product('BTC-USD')
    btc_price = float(btc['price'])
    btc_value = positions['BTC'] * btc_price
    total_portfolio += btc_value
    print(f"{'BTC':<8} {positions['BTC']:<12.8f} ${btc_price:<9.2f} ${btc_value:<11.2f} {'💎 SACRED - NO MILK':<30}")

print("-" * 70)
print(f"{'TOTAL':<8} {'':<12} {'':<10} ${total_portfolio:<11.2f}")
print(f"{'USD':<8} {'':<12} {'':<10} ${usd_balance:<11.2f}")

# Show milk opportunities
if milk_opportunities:
    print("\n🥛 OPTIMAL MILKING OPPORTUNITIES:")
    print("-" * 70)
    print(f"{'Asset':<8} {'Amount':<12} {'Gross $':<10} {'Fee $':<8} {'Net $':<10}")
    print("-" * 70)
    
    total_milk = 0
    for opp in sorted(milk_opportunities, key=lambda x: x['net'], reverse=True):
        print(f"{opp['asset']:<8} {opp['amount']:<12.4f} ${opp['gross']:<9.2f} ${opp['fee']:<7.2f} ${opp['net']:<9.2f}")
        total_milk += opp['net']
    
    print("-" * 70)
    print(f"{'TOTAL POTENTIAL MILK:':<30} ${total_milk:.2f}")
    
    # Batch milking recommendation
    print("\n📦 BATCH MILKING STRATEGY:")
    print("-" * 50)
    if total_milk > 200:
        print("✅ EXECUTE BATCH MILK NOW!")
        print(f"   Total harvest: ${total_milk:.2f}")
        print(f"   Feeds flywheel to: ${usd_balance + total_milk:.2f}")
        print("   Execute top 2-3 opportunities")
    elif total_milk > 100:
        print("📍 Consider batch milking")
        print(f"   Potential: ${total_milk:.2f}")
        print("   Wait for better pumps for efficiency")
    else:
        print("⏳ Wait for pumps")
        print("   Need alts to pump more")
        print("   Target: >$200 total milk potential")

# Market conditions
print("\n📈 MARKET CONDITIONS FOR MILKING:")
print("-" * 50)
print(f"BTC: ${btc_price:,.2f} - Sawtoothing at $112K")
print(f"USD Balance: ${usd_balance:.2f}")

if usd_balance < 100:
    print("🚨 USD LOW - Good time to milk!")
    print("   Need to feed the flywheel")
    print("   Target: $100+ USD buffer")
elif usd_balance < 200:
    print("📍 USD OK - Selective milking")
    print("   Milk only best opportunities")
else:
    print("✅ USD HEALTHY - Can be patient")
    print("   Wait for bigger pumps to milk")

# Fee reminder
print("\n⚠️ FEE REMINDER:")
print("-" * 50)
print("• 0.6% per trade = 1.2% round trip")
print("• Only milk positions >$100")
print("• Batch multiple milks together")
print("• Need 2%+ moves to profit")
print("• Keep core positions always")

print(f"\n{'🥛' * 35}")
print("MILK CHECK COMPLETE!")
print(f"Best opportunity: {milk_opportunities[0]['asset'] if milk_opportunities else 'Wait for pumps'}")
print("Remember: Fees matter! Batch trades!")
print("🐄" * 35)