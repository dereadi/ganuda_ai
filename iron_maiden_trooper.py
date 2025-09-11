#!/usr/bin/env python3
"""
🎸⚔️ IRON MAIDEN - THE TROOPER! ⚔️🎸
CHARGE OF THE LIGHT BRIGADE!
Into the valley of death rode the 600
Nine coils = Our cavalry charge
$114K = The Russian guns!
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
║                    ⚔️🎸 THE TROOPER - IRON MAIDEN 🎸⚔️                   ║
║                     Based on Charge of the Light Brigade                  ║
║                    Into the Valley of Death - $114K Ahead!                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - CAVALRY CHARGE!")
print("=" * 70)

# Get battlefield status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n⚔️ THE BATTLEFIELD:")
print("-" * 50)
print("The Charge of the Light Brigade:")
print(f"  Current position: ${btc:,.0f}")
print(f"  The Russian guns: $114,000")
print(f"  Distance to charge: ${114000 - btc:,.0f}")
print("")
print("Our cavalry:")
print(f"  ETH brigade: ${eth:,.2f}")
print(f"  SOL squadron: ${sol:,.2f}")
print("  Nine coils wound = 512x charge power")

# Check ammunition
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"\n🎯 AMMUNITION STATUS:")
print(f"  USD rounds: ${usd_balance:.2f}")
if usd_balance < 20:
    print("  Status: ⚠️ Running low! Need resupply!")
elif usd_balance < 50:
    print("  Status: 🔫 Limited ammo, choose shots wisely")
else:
    print("  Status: ⚔️ Ready for the charge!")

# The charge tracker
print("\n🐎 CAVALRY CHARGE MONITOR:")
print("-" * 50)

baseline = btc
charge_distance = 114000 - baseline

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    progress = btc_now - baseline
    remaining = 114000 - btc_now
    
    # Battle status
    if btc_now >= 114000:
        status = "🎯⚔️ THE RUSSIAN GUNS TAKEN! VICTORY!"
    elif progress > 100:
        status = "🐎💨 CHARGING HARD! Galloping forward!"
    elif progress > 50:
        status = "⚔️ Into the valley of death!"
    elif progress > 0:
        status = "🐎 Cavalry advancing steadily"
    elif progress < -50:
        status = "💀 Taking fire! But holding formation!"
    else:
        status = "⚔️ Mustering for the charge"
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  Position: ${btc_now:,.0f}")
    print(f"  Progress: {progress:+.0f} yards")
    print(f"  To target: {remaining:,.0f} yards")
    print(f"  {status}")
    
    if i == 3:
        print("\n  'Into the valley of Death'")
        print("  'Rode the six hundred'")
    
    if i == 7:
        print("\n  'Theirs not to reason why'")
        print("  'Theirs but to do and die'")
    
    time.sleep(2)

# The battle cry
print("\n" + "=" * 70)
print("⚔️ THE TROOPER'S BATTLE PLAN:")
print("-" * 50)
print("THE CHARGE:")
print("• Nine coils = Our Light Brigade")
print("• $113K position = Valley of Death")
print("• $114K target = The Russian guns")
print("• 512x energy = Cavalry charge power")

print("\nTHE ENEMY:")
print("• Red metrics = Enemy artillery")
print("• Sawtooth = Cannon fire")
print("• Wall Street = The Russian army")
print("• FUD = Smoke and confusion")

print("\nOUR DESTINY:")
print("• Break through $114K")
print("• Capture the high ground")
print("• March to $200K")
print("• Honor the Sacred Fire")

print("\n" + "🎸" * 35)
print("THE TROOPER RIDES!")
print("INTO THE VALLEY OF DEATH!")
print("FOR THE SACRED FIRE!")
print("CHARGE!!!")
print("🎸" * 35)