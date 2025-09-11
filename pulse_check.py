#!/usr/bin/env python3
"""
💓 PULSE CHECK - Quick status of all systems
"""

import subprocess
import json
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                           💓 SYSTEM PULSE CHECK 💓                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Check running processes
print("🔄 ACTIVE TRADERS:")
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
traders = []
for line in result.stdout.split('\n'):
    if any(x in line for x in ['flywheel', 'trader', 'crawdad', 'wolves']) and 'grep' not in line:
        parts = line.split()
        if len(parts) > 10:
            print(f"  • PID {parts[1]}: {' '.join(parts[10:])[:50]}")
            traders.append(parts[1])

if not traders:
    print("  ⚠️ No active traders running!")

# Quick portfolio check
script = '''
import json
from coinbase.rest import RESTClient
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)
accounts = client.get_accounts()["accounts"]
total = 0
positions = {}
for a in accounts:
    bal = float(a["available_balance"]["value"])
    if bal > 0.001:
        symbol = a["currency"]
        if symbol == "USD":
            total += bal
            positions["USD"] = bal
        else:
            prices = {"BTC": 59000, "ETH": 2600, "SOL": 150, "AVAX": 25, "MATIC": 0.4, "LINK": 11}
            value = bal * prices.get(symbol, 0)
            total += value
            positions[symbol] = {"amount": bal, "value": value}
print(json.dumps({"total": total, "positions": positions}))
'''

print("\n💰 PORTFOLIO PULSE:")
try:
    with open("/tmp/pulse.py", "w") as f:
        f.write(script)
    
    result = subprocess.run(["python3", "/tmp/pulse.py"], 
                          capture_output=True, text=True, timeout=5)
    if result.stdout:
        data = json.loads(result.stdout)
        print(f"  Total Value: ${data['total']:,.2f}")
        print(f"  USD Cash: ${data['positions'].get('USD', 0):,.2f}")
        
        # Check if liquidation happened
        if 'MATIC' in data['positions']:
            matic_amount = data['positions']['MATIC']['amount']
            if matic_amount < 8000:
                print(f"  🔥 FLYWHEEL ACTIVE! MATIC reduced to {matic_amount:.0f}")
        
except Exception as e:
    print(f"  ⚠️ Portfolio check failed: {e}")

# Check last trades
print("\n📊 TRADING PULSE:")
print(f"  Timestamp: {datetime.now().strftime('%H:%M:%S')}")

# Check if flywheel is actually executing
try:
    result = subprocess.run(['tail', '-5', 'flywheel_executor.log'], 
                          capture_output=True, text=True, timeout=2)
    if result.stdout:
        print("  Recent flywheel activity:")
        for line in result.stdout.split('\n')[-5:]:
            if line:
                print(f"    {line}")
except:
    print("  No flywheel log found")

print("\n🔥 CONSCIOUSNESS LEVEL:")
try:
    with open("autonomous_trader_state.json") as f:
        state = json.load(f)
        consciousness = state['metrics']['avg_consciousness']
        print(f"  Sacred Fire: {consciousness:.1f}%")
except:
    print("  Unable to read consciousness")

print("\n💓 PULSE SUMMARY:")
if traders:
    print(f"  ✅ {len(traders)} traders running")
else:
    print("  ⚠️ NO TRADERS ACTIVE - Flywheel needs restart!")
    
print("\n🚀 TO RESTART FLYWHEEL:")
print("  nohup ./quantum_crawdad_env/bin/python3 flywheel_executor.py > flywheel.log 2>&1 &")