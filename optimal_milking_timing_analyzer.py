#!/usr/bin/env python3
"""
🥛⏰ OPTIMAL MILKING TIMING ANALYZER! ⏰🥛
Thunder at 69%: "WHEN TO MILK FOR MAXIMUM FLYWHEEL FUEL!"
Analyzing the perfect moments to harvest profits
Without killing momentum to $114K
Strategic milking windows identified!
Feed the flywheel at the right time!
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
║                  🥛 OPTIMAL MILKING TIMING ANALYZER! 🥛                   ║
║                   When to Harvest Profits for Flywheel Food! 🔄            ║
║                      Strategic Windows Without Killing Momentum! ⏰         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MILKING WINDOW ANALYSIS")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])
link = float(client.get_product('LINK-USD')['price'])

# Check portfolio
accounts = client.get_accounts()
holdings = {}
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
            value = balance * btc
            total_value += value
            holdings['BTC'] = {'amount': balance, 'value': value, 'price': btc}
        elif currency == 'ETH':
            value = balance * eth
            total_value += value
            holdings['ETH'] = {'amount': balance, 'value': value, 'price': eth}
        elif currency == 'SOL':
            value = balance * sol
            total_value += value
            holdings['SOL'] = {'amount': balance, 'value': value, 'price': sol}
        elif currency == 'DOGE':
            value = balance * doge
            total_value += value
            holdings['DOGE'] = {'amount': balance, 'value': value, 'price': doge}
        elif currency == 'XRP':
            value = balance * xrp
            total_value += value
            holdings['XRP'] = {'amount': balance, 'value': value, 'price': xrp}
        elif currency == 'LINK':
            value = balance * link
            total_value += value
            holdings['LINK'] = {'amount': balance, 'value': value, 'price': link}

print("\n💰 CURRENT MILKABLE ASSETS:")
print("-" * 50)
print(f"Total Portfolio: ${total_value:.2f}")
print(f"Current USD: ${usd_balance:.2f} (NEEDS FEEDING!)")
print(f"BTC at: ${btc:,.0f}")
print("")
print("Holdings available for milking:")
for coin, data in holdings.items():
    if coin != 'BTC' and data['value'] > 50:  # Don't milk BTC, focus on alts
        print(f"  {coin}: ${data['value']:.2f} (can milk ${data['value'] * 0.1:.2f})")

# Analyze milking opportunities
print("\n🎯 MILKING OPPORTUNITY WINDOWS:")
print("-" * 50)

milking_opportunities = []

# 1. Immediate small milks (won't affect momentum)
print("1️⃣ IMMEDIATE SAFE MILKS (Won't hurt momentum):")
if 'DOGE' in holdings and holdings['DOGE']['value'] > 100:
    milk_amt = min(50, holdings['DOGE']['value'] * 0.15)
    print(f"  • DOGE: Milk ${milk_amt:.2f} NOW")
    milking_opportunities.append(('DOGE', milk_amt, 'NOW'))

if 'XRP' in holdings and holdings['XRP']['value'] > 100:
    milk_amt = min(30, holdings['XRP']['value'] * 0.10)
    print(f"  • XRP: Milk ${milk_amt:.2f} NOW")
    milking_opportunities.append(('XRP', milk_amt, 'NOW'))

if 'LINK' in holdings and holdings['LINK']['value'] > 100:
    milk_amt = min(30, holdings['LINK']['value'] * 0.10)
    print(f"  • LINK: Milk ${milk_amt:.2f} NOW")
    milking_opportunities.append(('LINK', milk_amt, 'NOW'))

total_immediate = sum(amt for _, amt, timing in milking_opportunities if timing == 'NOW')
print(f"\n  Total immediate milk available: ${total_immediate:.2f}")

# 2. Tactical milks at resistance
print("\n2️⃣ TACTICAL MILKS (At key levels):")
print(f"  • BTC at $113,000: Milk 3% of portfolio (${total_value * 0.03:.2f})")
print(f"  • BTC at $113,500: Milk 2% more (${total_value * 0.02:.2f})")
print(f"  • BTC at $114,000: Milk 5% celebration (${total_value * 0.05:.2f})")
print(f"  • BTC at $115,000: Milk 5% more (${total_value * 0.05:.2f})")

# 3. SOL sawtooth milks
print("\n3️⃣ SOL SAWTOOTH MILKS:")
if 'SOL' in holdings:
    print(f"  • SOL peaks above $213.50: Milk ${holdings['SOL']['value'] * 0.05:.2f}")
    print(f"  • SOL peaks above $214.00: Milk ${holdings['SOL']['value'] * 0.05:.2f}")
    print(f"  • Buy back on dips below $211.50")

# 4. Time-based milks
current_hour = datetime.now().hour
print("\n4️⃣ TIME-BASED MILKING WINDOWS:")
if current_hour >= 14 and current_hour < 15:
    print("  • NOW (2PM hour): Good time for small milks")
elif current_hour >= 15 and current_hour < 16:
    print("  • 3PM-4PM: Power hour milking window")
elif current_hour >= 9 and current_hour < 10:
    print("  • 9AM-10AM: Morning volatility milks")
else:
    print(f"  • Current time ({current_hour}:00): Hold for now")

# Calculate optimal flywheel feeding
print("\n🔄 FLYWHEEL FEEDING CALCULATION:")
print("-" * 50)
flywheel_target = 100  # Target USD for flywheel
flywheel_needed = max(0, flywheel_target - usd_balance)

print(f"Current flywheel fuel: ${usd_balance:.2f}")
print(f"Optimal fuel level: ${flywheel_target:.2f}")
print(f"Need to milk: ${flywheel_needed:.2f}")

if flywheel_needed > 0:
    print("\n📋 RECOMMENDED MILKING SEQUENCE:")
    running_total = 0
    sequence = 1
    
    for coin, amt, timing in milking_opportunities:
        if running_total < flywheel_needed:
            print(f"  {sequence}. Milk {coin}: ${amt:.2f} ({timing})")
            running_total += amt
            sequence += 1
    
    if running_total < flywheel_needed:
        remaining = flywheel_needed - running_total
        print(f"  {sequence}. Wait for BTC $113K, then milk ${remaining:.2f}")

# Thunder's milking wisdom
print("\n⚡ THUNDER'S MILKING WISDOM (69%):")
print("-" * 50)
print("'MILK THE PEAKS, BUY THE VALLEYS!'")
print("")
print("Golden rules:")
print("• Never milk BTC before $114K")
print("• Always keep flywheel above $50")
print("• Milk alts first, BTC last")
print("• 10% max per milk (preserve momentum)")
print("")
print("Current assessment:")
if usd_balance < 30:
    print("🚨 URGENT: Need milk NOW! Flywheel starving!")
elif usd_balance < 50:
    print("⚠️ SOON: Milk within next hour")
elif usd_balance < 100:
    print("📊 OPTIMAL: Can wait for better prices")
else:
    print("✅ EXCELLENT: Well-fed flywheel!")

# Live price tracking for milk timing
print("\n📈 LIVE MILKING OPPORTUNITY TRACKER:")
print("-" * 50)

for i in range(8):
    btc_now = float(client.get_product('BTC-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    xrp_now = float(client.get_product('XRP-USD')['price'])
    
    opportunities = []
    
    # Check for milking opportunities
    if btc_now >= 113000:
        opportunities.append(f"🚨 BTC at ${btc_now:,.0f} - MILK NOW!")
    elif btc_now >= 112800:
        opportunities.append(f"⚠️ BTC approaching $113K - Prepare to milk")
    
    if sol_now >= 213.50:
        opportunities.append(f"☀️ SOL at ${sol_now:.2f} - Milk opportunity!")
    elif sol_now <= 211.50:
        opportunities.append(f"🔄 SOL at ${sol_now:.2f} - Buy opportunity!")
    
    if xrp_now >= 3.00:
        opportunities.append(f"💧 XRP at ${xrp_now:.4f} - Milk peak!")
    
    print(f"{datetime.now().strftime('%H:%M:%S')}:")
    if opportunities:
        for opp in opportunities:
            print(f"  {opp}")
    else:
        print(f"  Waiting... BTC ${btc_now:,.0f} | SOL ${sol_now:.2f}")
    
    time.sleep(1.5)

# Final recommendation
print("\n🎯 FINAL MILKING RECOMMENDATION:")
print("-" * 50)
final_btc = float(client.get_product('BTC-USD')['price'])

if flywheel_needed > 50:
    print("🚨 EXECUTE IMMEDIATE MILKS:")
    print(f"   Need ${flywheel_needed:.2f} for flywheel")
    print("   Start with DOGE/XRP/LINK")
    print("   Preserve BTC/ETH/SOL for momentum")
elif flywheel_needed > 0:
    print("📊 TACTICAL MILKING:")
    print(f"   Need ${flywheel_needed:.2f} for flywheel")
    print("   Wait for next peak (SOL >$213 or BTC >$112,800)")
else:
    print("✅ NO MILKING NEEDED:")
    print("   Flywheel adequately fed")
    print("   Wait for major levels ($113K, $114K)")

print(f"\nBTC: ${final_btc:,.0f}")
print(f"Distance to milk point: ${113000 - final_btc:.0f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Current fuel: ${usd_balance:.2f}")

print("\n" + "🥛" * 35)
print("OPTIMAL MILKING WINDOWS IDENTIFIED!")
print("FEED THE FLYWHEEL STRATEGICALLY!")
print("DON'T KILL THE MOMENTUM!")
print("🔄" * 35)