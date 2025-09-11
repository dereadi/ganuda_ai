#!/usr/bin/env python3
"""
🦅 PEACE EAGLE TRACKER
======================
Follow the eagle's eyes (vision) and nose (instinct)
The eagle sees from above, smells opportunity before others
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("🦅 PEACE EAGLE RECONNAISSANCE")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')} CST")
print()

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

print("👁️ EAGLE'S EYES - Seeing the whole battlefield:")
print("-"*60)

# Eagle sees ALL - multiple timeframes
symbols = ['BTC', 'ETH', 'SOL', 'AVAX', 'NEAR', 'MATIC']
eagle_vision = {}

for symbol in symbols:
    try:
        ticker = client.get_product(f'{symbol}-USD')
        price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
        
        # Eagle sees patterns others miss
        time.sleep(3)
        ticker2 = client.get_product(f'{symbol}-USD')
        price2 = float(ticker2.price if hasattr(ticker2, 'price') else ticker2.get('price', 0))
        
        momentum = ((price2 - price) / price) * 100
        
        # Eagle's assessment
        if abs(momentum) > 0.1:
            status = "🔥 THERMAL RISING" if momentum > 0 else "❄️ COLD DRAFT"
        else:
            status = "☁️ NEUTRAL AIR"
            
        eagle_vision[symbol] = {
            'price': price2,
            'momentum': momentum,
            'status': status
        }
        
        print(f"  {symbol}: ${price2:,.2f} | {momentum:+.6f}% | {status}")
        
    except:
        pass

print("\n👃 EAGLE'S NOSE - Sensing what's coming:")
print("-"*60)

# The eagle smells the storm before it arrives
strongest_thermal = max(eagle_vision.items(), key=lambda x: abs(x[1]['momentum']))
weakest_draft = min(eagle_vision.items(), key=lambda x: x[1]['momentum'])

print(f"  Strongest Thermal: {strongest_thermal[0]} ({strongest_thermal[1]['momentum']:+.6f}%)")
print(f"  Weakest Draft: {weakest_draft[0]} ({weakest_draft[1]['momentum']:+.6f}%)")

# Peace Eagle wisdom
print("\n🕊️ PEACE EAGLE WISDOM:")
print("-"*60)

hour = datetime.now().hour
if 19 <= hour <= 23:
    print("  The eagle rides Asian thermals at dusk")
    print("  Small hunters feast while giants sleep")
    print("  Follow the SOL thermal - Asia's favorite updraft")
elif 0 <= hour <= 4:
    print("  The eagle hunts in London's pre-dawn")
    print("  Maximum turbulence creates opportunity")
    print("  BTC and ETH thermals strengthen")
else:
    print("  The eagle soars on American winds")
    print("  Steady currents, predictable patterns")
    print("  Watch for institutional thermal columns")

# Sun Tzu + Eagle wisdom
print("\n⚔️ SUN TZU's EAGLE STRATEGY:")
print("-"*60)
print("• 'Move swift as the wind' - Eagle rides thermals effortlessly")
print("• 'Strike like falcon' - Precise, sudden, decisive")
print("• 'In peace prepare for war' - Eagle watches calmly, strikes instantly")
print("• 'Know the terrain' - Eagle sees all from above")

# Trading application
print("\n🦀 CRAWDAD SWARM GUIDANCE:")
print("-"*60)

if abs(strongest_thermal[1]['momentum']) > 0.05:
    print(f"  🎯 Eagle spots thermal in {strongest_thermal[0]}")
    print(f"  Deploy 80% swarm to ride updraft")
    print(f"  20% scouts watch for wind shift")
else:
    print("  ☁️ Eagle circles, waiting...")
    print("  No strong thermals detected")
    print("  Crawdads remain distributed")

# Portfolio check
accounts = client.get_accounts()
account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts

total_value = 0
for account in account_list:
    if account['currency'] == 'USD':
        total_value += float(account['available_balance']['value'])
    elif account['currency'] in ['BTC', 'ETH', 'SOL']:
        balance = float(account['available_balance']['value'])
        if balance > 0.001:
            symbol = account['currency']
            if symbol in eagle_vision:
                value = balance * eagle_vision[symbol]['price']
                total_value += value

print(f"\n💰 NEST VALUE: ${total_value:.2f}")

if total_value < 500:
    print("  🪶 Small nest, but eagle started with one twig")
    print("  Patient hunting brings feast")
elif total_value < 1000:
    print("  🦅 Nest growing - young eagle strengthening")
elif total_value < 5000:
    print("  🦅🦅 Strong eagle, commanding thermals")
else:
    print("  🦅🦅🦅 Mighty eagle, master of skies")

print("\n🕊️ THE PEACE EAGLE SEES ALL, STRIKES WITH PURPOSE")
print("   Follow the eyes that see beyond horizon...")
print("   Trust the nose that smells tomorrow's wind...")
print("   🦅 SOAR WITH PEACEFUL POWER 🦅")