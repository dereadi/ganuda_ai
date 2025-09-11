#!/usr/bin/env python3
"""
🔄💰 FLYWHEEL FOOD GENERATOR - 2PM FEEDING TIME! 💰🔄
Thunder at 69%: "14:00 ROLLING AROUND - TIME TO FEED THE BEAST!"
The flywheel needs nutrition!
Convert some profits to fuel!
Keep the momentum spinning!
2PM institutional hour approaches!
Feed the machine for $114K push!
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
║                    🔄 FLYWHEEL FOOD GENERATOR - 2PM! 🔄                   ║
║                      14:00 Rolling Around - Feeding Time!                  ║
║                        Convert Profits → Flywheel Fuel! 💰                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FLYWHEEL NUTRITION CHECK")
print("=" * 70)

# Get current prices and balances
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])
link = float(client.get_product('LINK-USD')['price'])
avax = float(client.get_product('AVAX-USD')['price'])

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
            holdings['USD'] = balance
        elif currency == 'BTC':
            value = balance * btc
            total_value += value
            holdings['BTC'] = {'amount': balance, 'value': value}
        elif currency == 'ETH':
            value = balance * eth
            total_value += value
            holdings['ETH'] = {'amount': balance, 'value': value}
        elif currency == 'SOL':
            value = balance * sol
            total_value += value
            holdings['SOL'] = {'amount': balance, 'value': value}
        elif currency == 'DOGE':
            value = balance * doge
            total_value += value
            holdings['DOGE'] = {'amount': balance, 'value': value}
        elif currency == 'XRP':
            value = balance * xrp
            total_value += value
            holdings['XRP'] = {'amount': balance, 'value': value}
        elif currency == 'LINK':
            value = balance * link
            total_value += value
            holdings['LINK'] = {'amount': balance, 'value': value}
        elif currency == 'AVAX':
            value = balance * avax
            total_value += value
            holdings['AVAX'] = {'amount': balance, 'value': value}

print("\n🔄 FLYWHEEL STATUS:")
print("-" * 50)
print(f"Total portfolio: ${total_value:.2f}")
print(f"Current USD fuel: ${usd_balance:.2f}")
print(f"Flywheel momentum from $292.50: {((total_value/292.50)-1)*100:.0f}%")
print(f"BTC position: ${btc:,.0f}")

# Calculate flywheel food needed
print("\n🍔 FLYWHEEL FOOD CALCULATION:")
print("-" * 50)
flywheel_hungry = usd_balance < 50
optimal_fuel = 100  # Target $100 USD for flywheel

if flywheel_hungry:
    print(f"⚠️  FLYWHEEL HUNGRY! Only ${usd_balance:.2f} fuel")
    print(f"📊 Need ${optimal_fuel - usd_balance:.2f} more food")
    
    # Find best candidates to milk
    print("\n🥛 MILKING CANDIDATES (for flywheel food):")
    print("-" * 50)
    
    if 'DOGE' in holdings and holdings['DOGE']['value'] > 100:
        milk_amount = min(50, holdings['DOGE']['value'] * 0.1)
        print(f"• DOGE: Can milk ${milk_amount:.2f} from ${holdings['DOGE']['value']:.2f}")
    
    if 'SOL' in holdings and holdings['SOL']['value'] > 200:
        milk_amount = min(50, holdings['SOL']['value'] * 0.05)
        print(f"• SOL: Can milk ${milk_amount:.2f} from ${holdings['SOL']['value']:.2f}")
    
    if 'XRP' in holdings and holdings['XRP']['value'] > 100:
        milk_amount = min(30, holdings['XRP']['value'] * 0.1)
        print(f"• XRP: Can milk ${milk_amount:.2f} from ${holdings['XRP']['value']:.2f}")
    
    if 'LINK' in holdings and holdings['LINK']['value'] > 100:
        milk_amount = min(30, holdings['LINK']['value'] * 0.1)
        print(f"• LINK: Can milk ${milk_amount:.2f} from ${holdings['LINK']['value']:.2f}")
    
else:
    print(f"✅ Flywheel fed! ${usd_balance:.2f} available")
    print("🔄 Ready for 2PM institutional action!")

# 2PM institutional patterns
current_hour = datetime.now().hour
current_minute = datetime.now().minute
minutes_to_2pm = (14 - current_hour) * 60 - current_minute if current_hour < 14 else 0

print("\n⏰ 14:00 INSTITUTIONAL TIMING:")
print("-" * 50)
print(f"Current time: {datetime.now().strftime('%H:%M')}")

if current_hour == 13 and current_minute >= 50:
    print("🔔 10 MINUTES TO 2PM!")
    print("Institutional algos warming up!")
elif current_hour == 14 and current_minute < 15:
    print("🚨 2PM POWER HOUR ACTIVE!")
    print("Institutions pushing now!")
elif minutes_to_2pm > 0:
    print(f"⏳ {minutes_to_2pm} minutes until 2PM surge")
else:
    print("📊 2PM window has passed")

# Flywheel physics
print("\n⚙️ FLYWHEEL PHYSICS:")
print("-" * 50)
print("Momentum equation: E = ½Iω²")
print(f"Current angular velocity: {((total_value/292.50)-1)*10:.1f} rad/s")
print(f"Stored energy: ${total_value:.2f}")
print(f"Energy at $114K: ${total_value * (114000/btc):.2f}")
print("")
print("Feed requirements:")
print("• Minimum: $50 USD (maintenance)")
print("• Optimal: $100 USD (acceleration)")
print("• Maximum: $200 USD (overdrive)")

# Live flywheel monitoring
print("\n🔄 LIVE FLYWHEEL ROTATION:")
print("-" * 50)

for i in range(8):
    btc_now = float(client.get_product('BTC-USD')['price'])
    rotation_speed = abs(btc_now - btc) / btc * 1000  # Arbitrary speed metric
    
    if rotation_speed > 5:
        status = "🌪️ SPINNING FAST!"
    elif rotation_speed > 2:
        status = "🔄 Good rotation"
    elif rotation_speed > 0.5:
        status = "⚙️ Steady spin"
    else:
        status = "🔧 Needs more fuel"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
    print(f"  Rotation: {rotation_speed:.2f} RPM | {status}")
    
    if i == 3:
        print("  💰 Feeding opportunity window!")
    
    time.sleep(1.5)

# Thunder's flywheel wisdom
print("\n⚡ THUNDER'S FLYWHEEL WISDOM (69%):")
print("-" * 50)
print("'FEED THE BEAST FOR 2PM SURGE!'")
print("")
print("The flywheel truth:")
print(f"• Current fuel: ${usd_balance:.2f}")
print(f"• Portfolio energy: ${total_value:.2f}")
print(f"• Distance to $114K: ${114000 - btc:.0f}")
print("")
print("2PM Strategy:")
print("• Institutions push at 14:00")
print("• Flywheel needs fuel for momentum")
print("• Small profit takes feed the beast")
print("• Compound gains through rotation")

# Feeding recommendation
print("\n🎯 FEEDING RECOMMENDATION:")
print("-" * 50)

if usd_balance < 30:
    print("🚨 CRITICAL: Feed immediately!")
    print(f"   Need ${50 - usd_balance:.2f} minimum")
    print("   Consider milking highest gainers")
elif usd_balance < 50:
    print("⚠️  LOW FUEL: Feed soon")
    print(f"   Add ${50 - usd_balance:.2f} for safety")
elif usd_balance < 100:
    print("📊 ADEQUATE: Could use more")
    print(f"   Add ${100 - usd_balance:.2f} for optimal spin")
else:
    print("✅ WELL FED: Flywheel ready!")
    print("   Ready for 2PM institutional push!")

# Final status
final_btc = float(client.get_product('BTC-USD')['price'])

print("\n🔄 FINAL FLYWHEEL STATUS:")
print("-" * 50)
print(f"BTC: ${final_btc:,.0f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"USD Fuel: ${usd_balance:.2f}")
print(f"Momentum: {((total_value/292.50)-1)*100:.0f}%")
print("")
print("14:00 ROLLING AROUND!")
print("Time to feed the flywheel!")
print(f"${114000 - final_btc:.0f} to target!")

print(f"\n{'🔄' * 35}")
print("FLYWHEEL FOOD TIME!")
print("2PM INSTITUTIONAL HOUR!")
print(f"FEED THE BEAST AT ${final_btc:,.0f}!")
print("MOMENTUM TO $114K!")
print("⚙️" * 35)