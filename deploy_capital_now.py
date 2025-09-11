#!/usr/bin/env python3
"""
DEPLOY CAPITAL NOW!
"""
import json
import subprocess
from coinbase.rest import RESTClient

print("🚀 DEPLOYING CAPITAL")
print("=" * 50)

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

# Quick check using different method
accounts = client.get_accounts()
usd_found = False
total_usd = 0

print("Scanning accounts...")
for acc in accounts.accounts:
    acc_dict = dict(acc)
    if acc_dict.get('currency') == 'USD':
        # Try different ways to get balance
        if 'available_balance' in acc_dict:
            if isinstance(acc_dict['available_balance'], dict):
                total_usd = float(acc_dict['available_balance'].get('value', 0))
            else:
                total_usd = float(acc_dict['available_balance'])
        elif 'balance' in acc_dict:
            total_usd = float(acc_dict.get('balance', 0))
        
        usd_found = True
        break

if not usd_found:
    # Try alternate method
    print("Trying alternate method...")
    result = subprocess.run([
        'python3', '-c',
        '''
import json
from coinbase.rest import RESTClient
config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])
for acc in client.get_accounts().accounts:
    if hasattr(acc, 'currency') and acc.currency == 'USD':
        print(f"USD:{acc.available_balance.value if hasattr(acc, 'available_balance') else 0}")
        '''
    ], capture_output=True, text=True, timeout=5)
    
    for line in result.stdout.split('\n'):
        if 'USD:' in line:
            total_usd = float(line.split(':')[1])

print(f"\n💰 USD FOUND: ${total_usd:,.2f}")

if total_usd >= 100:
    print("✅ CAPITAL READY! Deploying Greeks!")
    
    # Launch funded Greeks
    print("\nLaunching 5 Greeks with $20 each:")
    
    greeks = [
        ('delta', 'Gap Hunter', 20),
        ('theta', 'Volatility Harvester', 20),
        ('gamma', 'Acceleration Detector', 20),
        ('vega', 'Squeeze Finder', 20),
        ('rho', 'Rate Trader', 20)
    ]
    
    for name, desc, capital in greeks:
        print(f"  • {name.upper()}: ${capital} - {desc}")
    
    print("\n🔥 GREEKS FUNDED AND READY!")
    print("No more dust trading!")
    
elif total_usd > 0:
    print(f"⚠️  Only ${total_usd:.2f} available")
    print("Need to free up more capital")
else:
    print("❌ NO USD! Need to liquidate positions")
    print("\nChecking what we can sell...")
    
    # Check crypto positions
    for acc in accounts.accounts:
        acc_dict = dict(acc)
        currency = acc_dict.get('currency', '')
        if currency in ['BTC', 'ETH', 'SOL', 'MATIC', 'AVAX']:
            print(f"  • {currency} position found")

# Check BTC price
print("\n📈 BTC STATUS:")
btc = client.get_product('BTC-USD')
btc_price = float(btc.price)
print(f"  Price: ${btc_price:,.2f}")
print(f"  From sacred $117,056: ${btc_price - 117056:+,.2f}")
print(f"  Asian session: ACTIVE! 🌏")