#!/usr/bin/env python3
"""
📊 FULL ASSET INVENTORY CHECK
After seven coils and the breakout
Where do we stand?
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    📊 FULL ASSET INVENTORY CHECK 📊                       ║
║                     After Seven Coils & Breakout                          ║
║                        Where Everything Stands                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - COMPLETE INVENTORY")
print("=" * 70)

# Get current prices
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])

print(f"\n💹 CURRENT MARKET PRICES:")
print("-" * 50)
print(f"  BTC: ${btc_price:,.2f}")
print(f"  ETH: ${eth_price:,.2f}")
print(f"  SOL: ${sol_price:,.2f}")

# Get all account balances
accounts = client.get_accounts()
total_portfolio_value = 0
asset_breakdown = {}

print(f"\n💼 ASSET HOLDINGS:")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0:
        if currency == 'USD':
            value = balance
            print(f"\n💵 USD:")
            print(f"   Balance: ${balance:.2f}")
            print(f"   Status: {'⚠️ CRITICALLY LOW!' if balance < 100 else '✅ Ready for trading'}")
            asset_breakdown['USD'] = value
            
        elif currency == 'BTC':
            value = balance * btc_price
            print(f"\n₿ BTC:")
            print(f"   Balance: {balance:.8f} BTC")
            print(f"   Value: ${value:,.2f}")
            print(f"   Price: ${btc_price:,.2f}")
            asset_breakdown['BTC'] = value
            
        elif currency == 'ETH':
            value = balance * eth_price
            print(f"\n⟠ ETH:")
            print(f"   Balance: {balance:.6f} ETH")
            print(f"   Value: ${value:,.2f}")
            print(f"   Price: ${eth_price:,.2f}")
            asset_breakdown['ETH'] = value
            
        elif currency == 'SOL':
            value = balance * sol_price
            print(f"\n◎ SOL:")
            print(f"   Balance: {balance:.4f} SOL")
            print(f"   Value: ${value:,.2f}")
            print(f"   Price: ${sol_price:,.2f}")
            asset_breakdown['SOL'] = value
            
        else:
            # Other assets
            if currency in ['USDC', 'USDT', 'DAI']:
                value = balance
            else:
                try:
                    product = client.get_product(f'{currency}-USD')
                    price = float(product['price'])
                    value = balance * price
                except:
                    value = 0
            
            if value > 0.01:
                print(f"\n{currency}:")
                print(f"   Balance: {balance}")
                print(f"   Value: ${value:.2f}")
                asset_breakdown[currency] = value
        
        total_portfolio_value += value

print("\n" + "=" * 70)
print("📊 PORTFOLIO SUMMARY:")
print("-" * 50)
print(f"💰 Total Portfolio Value: ${total_portfolio_value:,.2f}")

# Calculate percentages
print("\n📈 ASSET ALLOCATION:")
for asset, value in sorted(asset_breakdown.items(), key=lambda x: x[1], reverse=True):
    percentage = (value / total_portfolio_value) * 100
    bar_length = int(percentage / 2)
    bar = '█' * bar_length
    print(f"  {asset:6} ${value:8.2f} ({percentage:5.2f}%) {bar}")

# Performance metrics
print("\n🎯 TRADING STATUS:")
print("-" * 50)

usd_balance = asset_breakdown.get('USD', 0)
crypto_value = total_portfolio_value - usd_balance

print(f"  Cash Available: ${usd_balance:.2f}")
print(f"  Crypto Holdings: ${crypto_value:.2f}")
print(f"  Cash Ratio: {(usd_balance/total_portfolio_value)*100:.1f}%")
print(f"  Crypto Ratio: {(crypto_value/total_portfolio_value)*100:.1f}%")

if usd_balance < 100:
    print("\n⚠️ WARNING: INSUFFICIENT TRADING CAPITAL!")
    print("   Need to harvest profits to feed crawdads")
    suggested_harvest = min(crypto_value * 0.15, 500)
    print(f"   Suggested harvest: ${suggested_harvest:.2f}")
else:
    print("\n✅ READY FOR ACTIVE TRADING")
    print(f"   ${usd_balance/7:.2f} available per crawdad")

# Tonight's journey
print("\n🌙 TONIGHT'S JOURNEY:")
print("-" * 50)
print("• Started with four coils before 01:00")
print("• Hit SEVEN unprecedented coils total")
print("• Broke through $113,000 resistance")
print("• Peak reached: $113,352")
print("• Current altitude: $113,300+")

# Calculate potential gains if fully deployed
print("\n💡 OPPORTUNITY ANALYSIS:")
print("-" * 50)
btc_24h_range = 113352 - 112900  # Approximate tonight's range
potential_gain_percent = (btc_24h_range / 113000) * 100

print(f"Tonight's BTC range: ${btc_24h_range}")
print(f"Percentage swing: {potential_gain_percent:.2f}%")
print(f"If crawdads had ${usd_balance:.2f} each:")
print(f"  Potential per crawdad: ${(usd_balance/7) * (potential_gain_percent/100):.2f}")
print(f"  Total opportunity: ${usd_balance * (potential_gain_percent/100):.2f}")

print("\n🦀 CRAWDAD STATUS:")
print("-" * 50)
if usd_balance < 50:
    print("😵 STARVING - Need immediate feeding!")
    print("   Cannot capitalize on volatility")
elif usd_balance < 200:
    print("🦀 HUNGRY - Limited hunting ability")
    print("   Missing profit opportunities")
elif usd_balance < 500:
    print("🦀🦀 FED - Ready to hunt")
    print("   Can catch some waves")
else:
    print("🦀🦀🦀 WELL FED - Full hunting mode!")
    print("   Ready to feast on volatility")

print("=" * 70)