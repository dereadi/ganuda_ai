#!/usr/bin/env python3
import subprocess
import json
from datetime import datetime
from coinbase.rest import RESTClient

print("🏛️ COUNCIL MILKER STATUS CHECK")
print("=" * 50)

# Check service
try:
    result = subprocess.run(['systemctl', 'is-active', 'council-milker.service'], 
                          capture_output=True, text=True)
    if result.stdout.strip() == 'active':
        print("✅ Service: ACTIVE")
    else:
        print("❌ Service: " + result.stdout.strip())
except:
    print("⚠️ Service not installed")

# Check process
result = subprocess.run(['pgrep', '-f', 'council_auto_milker'], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print(f"✅ Process running: PID {result.stdout.strip()}")
else:
    print("❌ Process not running")

# Check USD balance
try:
    config = json.load(open('/home/dereadi/.coinbase_config.json'))
    key = config['api_key'].split('/')[-1]
    client = RESTClient(api_key=key, api_secret=config['api_secret'])
    
    accounts = client.get_accounts()
    usd = 0
    for a in accounts['accounts']:
        if a['currency'] == 'USD':
            usd = float(a['available_balance']['value'])
    print(f"💰 USD Balance: ${usd:.2f}")
    
    if usd < 50:
        print("   → Milker should be aggressive!")
    elif usd > 200:
        print("   → Good buffer, can be selective")
except:
    pass

print("=" * 50)
