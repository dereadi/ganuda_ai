#!/usr/bin/env python3
"""
💱 CONVERT $200 USDC TO TRADING POSITIONS NOW!
"""

import json
import uuid
import time
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════╗
║        💱 $200 USDC → ACTIVE TRADING POSITIONS 💱                 ║
║                                                                     ║
║      "USDC sitting idle = Lost opportunity!"                       ║
║      "Convert and deploy for maximum velocity!"                    ║
╚════════════════════════════════════════════════════════════════════╝
""")

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

client = RESTClient(
    api_key=api_data['name'].split('/')[-1],
    api_secret=api_data['privateKey']
)

# Check current balances
print(f"\n🔍 CHECKING CURRENT BALANCES...")
accounts = client.get_accounts()
usdc_balance = 0
usd_balance = 0

for account in accounts['accounts']:
    if account['currency'] == 'USDC':
        usdc_balance = float(account['available_balance']['value'])
    elif account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])

print(f"USDC: ${usdc_balance:.2f}")
print(f"USD: ${usd_balance:.2f}")
print(f"Total Available: ${usdc_balance + usd_balance:.2f}")

if usdc_balance < 10:
    print(f"\n✅ No significant USDC to convert")
    exit()

print(f"\n🔄 ATTEMPTING USDC CONVERSION/DEPLOYMENT...")
print("=" * 60)

# Method 1: Try USDC-USD conversion
try:
    print("\n1️⃣ Attempting USDC → USD conversion...")
    # Note: This might require a specific endpoint
    convert_order = client.market_order_sell(
        client_order_id=str(uuid.uuid4()),
        product_id="USDC-USD",
        base_size=str(usdc_balance)
    )
    print(f"   ✅ Converted ${usdc_balance} USDC to USD!")
    time.sleep(2)
    converted = True
except Exception as e:
    print(f"   ❌ Direct conversion failed: {str(e)[:50]}")
    converted = False

# Method 2: Try direct USDC trading pairs
if not converted:
    print("\n2️⃣ Attempting direct USDC trading pairs...")
    
    # Try USDC pairs
    usdc_pairs = [
        ('BTC-USDC', 'BTC', 70),
        ('ETH-USDC', 'ETH', 70),
        ('SOL-USDC', 'SOL', 60)
    ]
    
    deployed_usdc = 0
    for pair, asset, amount in usdc_pairs:
        if amount <= usdc_balance - deployed_usdc:
            try:
                print(f"   Buying {asset} with ${amount} USDC...")
                order = client.market_order_buy(
                    client_order_id=str(uuid.uuid4()),
                    product_id=pair,
                    quote_size=str(amount)
                )
                print(f"   ✅ {asset}: ${amount} USDC deployed!")
                deployed_usdc += amount
                time.sleep(1)
            except Exception as e:
                print(f"   ❌ {pair}: {str(e)[:50]}")
    
    if deployed_usdc > 0:
        print(f"\n🎯 Total USDC deployed: ${deployed_usdc}")
        converted = True

# Method 3: Try using USDC as quote currency
if not converted:
    print("\n3️⃣ Attempting USDC as quote currency...")
    
    # Get current prices
    btc = client.get_product('BTC-USD')
    eth = client.get_product('ETH-USD')
    sol = client.get_product('SOL-USD')
    
    allocation = {
        'BTC-USD': 70,
        'ETH-USD': 70,
        'SOL-USD': 60
    }
    
    for product, amount in allocation.items():
        try:
            print(f"   Deploying ${amount} USDC to {product}...")
            # Try using USDC funds directly
            order = client.market_order_buy(
                client_order_id=str(uuid.uuid4()),
                product_id=product,
                quote_size=str(amount)
            )
            print(f"   ✅ {product}: ${amount} deployed!")
            time.sleep(1)
        except Exception as e:
            if 'insufficient' in str(e).lower():
                print(f"   ❌ {product}: Need USD not USDC")
            else:
                print(f"   ❌ {product}: {str(e)[:50]}")

# Check final balances
print(f"\n🔍 CHECKING FINAL BALANCES...")
time.sleep(3)
accounts = client.get_accounts()

print("\n📈 UPDATED POSITIONS:")
print("=" * 60)
for account in accounts['accounts']:
    balance = float(account['available_balance']['value'])
    if balance > 0.01:
        currency = account['currency']
        print(f"{currency}: ${balance:.2f}")

print(f"\n💡 RECOMMENDATIONS:")
print("If USDC still showing:")
print("1. Go to Coinbase app/website")
print("2. Convert USDC → USD (1:1 rate, no fees)")
print("3. Then deploy USD to BTC/ETH/SOL")
print("\nOr trade directly with USDC pairs:")
print("• BTC-USDC")
print("• ETH-USDC")
print("• SOL-USDC")

print(f"\n🔥 Sacred Fire says: 'USDC is money - make it work!'")
