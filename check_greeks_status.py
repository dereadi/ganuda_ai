#!/usr/bin/env python3
"""
🏛️ THE GREEKS STATUS CHECK - Are the Sacred Five Still Trading?
Delta, Gamma, Theta, Vega, Rho - The Elite Force
"""

import json
import os
from datetime import datetime, timedelta
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════╗
║            🏛️ THE GREEKS CONNECTION CHECK 🏛️                   ║
║                                                                 ║
║         "Delta, Gamma, Theta, Vega, Rho"                       ║
║         "We are the markets, we are eternal"                   ║
╚════════════════════════════════════════════════════════════════╝
""")

# Check API connection
try:
    with open('cdp_api_key_new.json', 'r') as f:
        api_data = json.load(f)
    
    client = RESTClient(
        api_key=api_data['name'].split('/')[-1],
        api_secret=api_data['privateKey']
    )
    
    # Test connection
    btc = client.get_product('BTC-USD')
    print(f"\n✅ COINBASE CONNECTION: ACTIVE")
    print(f"   BTC Price: ${float(btc['price']):,.2f}")
except Exception as e:
    print(f"\n❌ COINBASE CONNECTION: FAILED")
    print(f"   Error: {e}")

# Check Greeks' recent activity
print(f"\n📊 GREEKS TRADING ACTIVITY:")
print("=" * 50)

greek_logs = [
    ('delta_greek.log', 'Δ DELTA (Gap Hunter)'),
    ('gamma_greek.log', 'Γ GAMMA (Trend Rider)'),
    ('theta_greek.log', 'Θ THETA (Volatility Master)'),
    ('vega_greek.log', 'ν VEGA (Breakout Specialist)'),
    ('rho_greek.log', 'ρ RHO (Mean Reversion)')
]

for log_file, name in greek_logs:
    if os.path.exists(log_file):
        mod_time = os.path.getmtime(log_file)
        last_modified = datetime.fromtimestamp(mod_time)
        time_ago = datetime.now() - last_modified
        
        if time_ago < timedelta(hours=1):
            status = "🟢 ACTIVE"
        elif time_ago < timedelta(days=1):
            status = "🟡 IDLE"
        else:
            status = "🔴 DORMANT"
            
        print(f"{name}: {status}")
        print(f"  Last activity: {last_modified.strftime('%Y-%m-%d %H:%M')}")
        print(f"  ({time_ago.days}d {time_ago.seconds//3600}h ago)")
    else:
        print(f"{name}: ⚫ NO LOG FILE")

# Check last deployment
print(f"\n💰 LAST DEPLOYMENT:")
print("=" * 50)

if os.path.exists('greeks_cash_deployment.json'):
    with open('greeks_cash_deployment.json', 'r') as f:
        deployment = json.load(f)
    
    print(f"Time: {deployment['timestamp'][:16]}")
    print(f"Amount: ${deployment['cash_deployed']:.2f}")
    print(f"Allocation:")
    for coin, amount in deployment['allocation'].items():
        print(f"  {coin}: ${amount:.2f}")
    print(f"Status: {deployment['status']}")
    print(f"Message: '{deployment['greeks_message']}'")

# Check if Greeks need reactivation
print(f"\n🔧 SYSTEM STATUS:")
print("=" * 50)

all_dormant = True
for log_file, _ in greek_logs:
    if os.path.exists(log_file):
        mod_time = os.path.getmtime(log_file)
        if (datetime.now() - datetime.fromtimestamp(mod_time)) < timedelta(days=1):
            all_dormant = False
            break

if all_dormant:
    print("⚠️ GREEKS ARE DORMANT - NEED REACTIVATION!")
    print("\n🚀 TO REACTIVATE THE GREEKS:")
    print("1. python3 delta_greek.py &")
    print("2. python3 gamma_greek.py &")
    print("3. python3 theta_greek.py &")
    print("4. python3 vega_greek.py &")
    print("5. python3 rho_greek.py &")
    print("\nOr run: python3 deploy_specialist_army.py")
else:
    print("✅ GREEKS SYSTEM: Partially Active")
    print("💡 Some Greeks may need individual restart")

print(f"\n🔥 SACRED FIRE WISDOM:")
print("The Greeks never truly sleep - they wait")
print("When markets move, they awaken")
print("Your week away = Their meditation period")
print("Time to summon them back to battle!")
