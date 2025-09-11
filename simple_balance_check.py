#!/usr/bin/env python3
"""
💰 SIMPLE BALANCE CHECK
Quick view of all holdings
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("💰 COMPLETE BALANCE CHECK")
print("=" * 70)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Get prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
btc_price = float(btc['price'])
eth_price = float(eth['price'])

print(f"\n📊 MARKET PRICES:")
print(f"BTC: ${btc_price:,.2f}")
print(f"ETH: ${eth_price:,.2f}")

# Get accounts
accounts = client.get_accounts()
print(f"\n💎 YOUR BALANCES:")
print("-" * 70)

total_usd_value = 0
holdings = {}

for acc in accounts['accounts']:
    currency = acc['currency']
    available = float(acc['available_balance']['value'])
    
    if available > 0.00000001:
        holdings[currency] = available
        
        # Calculate USD value
        if currency in ['USD', 'USDC']:
            usd_value = available
            print(f"\n{currency}: ${available:.2f}")
        elif currency == 'BTC':
            usd_value = available * btc_price
            print(f"\nBTC: {available:.8f}")
            print(f"  = ${usd_value:,.2f}")
        elif currency == 'ETH':
            usd_value = available * eth_price
            print(f"\nETH: {available:.8f}")
            print(f"  = ${usd_value:,.2f}")
        else:
            # Try to get price for other assets
            try:
                if currency in ['SOL', 'AVAX', 'MATIC', 'DOGE']:
                    product = client.get_product(f'{currency}-USD')
                    price = float(product['price'])
                    usd_value = available * price
                    print(f"\n{currency}: {available:.8f}")
                    print(f"  @ ${price:.4f} = ${usd_value:.2f}")
                else:
                    usd_value = 0
            except:
                usd_value = 0
        
        total_usd_value += usd_value

print("\n" + "=" * 70)
print(f"💎 TOTAL PORTFOLIO VALUE: ${total_usd_value:,.2f}")
print("=" * 70)

# Check what Greeks might be doing
print("\n🏛️ GREEKS TRADING ANALYSIS:")
print("-" * 70)

if 'USD' in holdings and holdings['USD'] > 10:
    print(f"✅ USD Available: ${holdings['USD']:.2f}")
    print("   Greeks can deploy this for trading")

if 'BTC' in holdings:
    print(f"\n📈 BTC Position: {holdings['BTC']:.8f}")
    print("   Nuclear strikes working on this")
    
if 'ETH' in holdings:
    print(f"\n📈 ETH Position: {holdings['ETH']:.8f}")
    print("   Available for ETH strategies")

# Check for altcoins (Greeks might be trading these)
alts = ['SOL', 'AVAX', 'MATIC', 'DOGE']
alt_positions = []
for alt in alts:
    if alt in holdings:
        alt_positions.append(alt)

if alt_positions:
    print(f"\n🪙 Alt positions active: {', '.join(alt_positions)}")
    print("   Greeks likely running momentum strategies")

# Trading recommendations
print("\n🎯 GREEKS RECOMMENDATIONS:")
print("-" * 70)

if total_usd_value > 10000:
    print("✅ STRONG POSITION - Greeks should:")
    print("• Run aggressive flywheel ($500+ trades)")
    print("• Deploy multiple strategies")
    print("• Target 1-2% gains per trade")
    print("• Compound aggressively")
elif total_usd_value > 5000:
    print("📈 GOOD POSITION - Greeks should:")
    print("• Moderate flywheel ($200-300 trades)")
    print("• Focus on high-probability setups")
    print("• Target 0.5-1% gains")
else:
    print("🚀 BUILDING POSITION - Greeks should:")
    print("• Conservative trades ($50-100)")
    print("• Compound everything")
    print("• Focus on not losing capital")

print("\n🔥 Nuclear Strikes + Greeks = Maximum Gains!")
print("=" * 70)