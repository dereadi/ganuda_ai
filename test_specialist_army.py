#!/usr/bin/env python3
"""
🧪 TEST SPECIALIST ARMY V2
Quick test of the new unified system
"""

import subprocess
import time
import json
from coinbase.rest import RESTClient

print("🧪 TESTING SPECIALIST ARMY V2")
print("=" * 60)

# Check current portfolio state
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

accounts = client.get_accounts()
usd_balance = 0
total_value = 0

for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        total_value += usd_balance
    elif float(account['available_balance']['value']) > 0:
        try:
            currency = account['currency']
            balance = float(account['available_balance']['value'])
            ticker = client.get_product(f'{currency}-USD')
            price = float(ticker['price'])
            total_value += balance * price
        except:
            pass

print(f"Current Portfolio: ${total_value:,.2f}")
print(f"USD Balance: ${usd_balance:,.2f}")
print()

# Determine mode
if usd_balance < 250:
    mode = "RETRIEVE MODE (Need liquidity)"
elif usd_balance > 500:
    mode = "DEPLOY MODE (Have capital)"
else:
    mode = "BALANCED MODE"
    
print(f"Specialists will operate in: {mode}")
print()

# Test one specialist first
print("🧪 Testing Mean Reversion Specialist V2...")
print("-" * 40)

# Start mean reversion specialist
proc = subprocess.Popen(
    ['python3', 'mean_reversion_specialist_v2.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd='/home/dereadi/scripts/claude'
)

# Monitor for 30 seconds
print("Monitoring for 30 seconds...")
start_time = time.time()

while time.time() - start_time < 30:
    # Check if process is still alive
    if proc.poll() is not None:
        print("❌ Specialist crashed!")
        stdout, stderr = proc.communicate()
        print("Error:", stderr[:500])
        break
        
    # Read output if available
    try:
        proc.stdout.flush()
    except:
        pass
        
    time.sleep(5)
    print(".", end="", flush=True)

# Stop the test
if proc.poll() is None:
    print("\n✅ Specialist running successfully!")
    proc.terminate()
    time.sleep(1)
    if proc.poll() is None:
        proc.kill()
else:
    print("\n❌ Specialist failed")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print()
print("Next steps:")
print("1. Fix any errors shown above")
print("2. Run: python3 specialist_army_controller.py")
print("3. Use 'START' command to deploy all specialists")
print("4. Use 'MONITOR' for auto-restart mode")