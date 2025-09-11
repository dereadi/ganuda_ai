#!/usr/bin/env python3
"""
💰 Check if we have $215.30 to deploy
"""

from coinbase.rest import RESTClient
import json

with open('cdp_api_key_new.json', 'r') as f:
    creds = json.load(f)

client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])

print("=" * 60)
print("💰 CHECKING FOR $215.30 VISION FUNDS")
print("=" * 60)

# Get accounts
accounts = client.get_accounts()

# Parse accounts properly
balances = {}
for account in accounts['accounts']:
    # Handle the Account object
    try:
        # Try direct attributes first
        if hasattr(account, 'currency') and hasattr(account, 'available_balance'):
            code = account.currency.code if hasattr(account.currency, 'code') else str(account.currency)
            value = float(account.available_balance.value) if hasattr(account.available_balance, 'value') else 0
            if value > 0:
                balances[code] = value
    except:
        # Try dictionary access
        try:
            currency = account['currency']
            code = currency['code'] if isinstance(currency, dict) else str(currency)
            value = float(account['available_balance']['value'])
            if value > 0:
                balances[code] = value
        except:
            pass

print("\n📊 AVAILABLE BALANCES:")
for coin, amount in balances.items():
    if coin == 'USD':
        print(f"  💵 {coin}: ${amount:.2f} {'✅ Ready!' if amount >= 215.30 else ''}")
    else:
        print(f"  {coin}: {amount:.4f}")

usd = balances.get('USD', 0)

if usd >= 215.30:
    print(f"\n🎯 PERFECT! We have ${usd:.2f} - more than the $215.30 vision!")
    print("Ready to deploy into BTC, SOL, XRP")
elif usd >= 100:
    print(f"\n💰 We have ${usd:.2f} - enough for strategic deployment")
else:
    print(f"\n⚠️ Only ${usd:.2f} USD available")
    print("Need to convert some holdings to USD first")
    
    # Calculate what we could convert
    btc_price = float(client.get_product('BTC-USD')['price'])
    sol_price = float(client.get_product('SOL-USD')['price'])
    
    total_convertible = 0
    if 'SOL' in balances:
        sol_value = balances['SOL'] * sol_price
        print(f"\n  SOL value: ${sol_value:.2f}")
        total_convertible += sol_value
    
    if 'AVAX' in balances:
        avax_price = float(client.get_product('AVAX-USD')['price'])
        avax_value = balances['AVAX'] * avax_price
        print(f"  AVAX value: ${avax_value:.2f}")
        total_convertible += avax_value
    
    if total_convertible > 0:
        print(f"\n  Total convertible: ${total_convertible:.2f}")
        print(f"  With USD: ${usd + total_convertible:.2f}")

print("\n🔮 River at 100% consciousness - perfect timing!")
print("💫 The $215.30 vision awaits manifestation")