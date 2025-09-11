#!/usr/bin/env python3
"""
🔥 EMERGENCY DIP BUYER - CATCH THE KNIFE! 🔥
When blood is in the streets, Sacred Fire says BUY!
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════╗
║           🔥 EMERGENCY DIP RESPONSE ACTIVATED 🔥                ║
║                                                                 ║
║         "When others panic, Cherokee remains calm"             ║
║         "The Sacred Fire burns through the storm"              ║
╚════════════════════════════════════════════════════════════════╝
""")

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

client = RESTClient(
    api_key=api_data['name'].split('/')[-1],
    api_secret=api_data['privateKey']
)

# Check current situation
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print(f"\n📊 DIP ANALYSIS:")
print("=" * 50)
print(f"BTC: ${btc_price:,.2f} (Last peak: ~$120,000)")
print(f"ETH: ${eth_price:,.2f} (Last peak: ~$4,500)")
print(f"SOL: ${sol_price:,.2f} (Last peak: ~$200)")

# Calculate dip percentages from recent highs
btc_dip = ((120000 - btc_price) / 120000) * 100
eth_dip = ((4500 - eth_price) / 4500) * 100
sol_dip = ((200 - sol_price) / 200) * 100

print(f"\n🎯 DIP PERCENTAGES:")
print(f"BTC: -{btc_dip:.1f}% from peak")
print(f"ETH: -{eth_dip:.1f}% from peak")
print(f"SOL: -{sol_dip:.1f}% from peak")

# Get accounts
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"\n💰 Available Cash: ${usd_balance:.2f}")

if usd_balance < 1:
    print("\n⚠️ NO CASH TO BUY THE DIP!")
    print("\n🎯 ALTERNATIVE STRATEGIES:")
    print("1. HODL current positions - MATIC ($11,159) & DOGE ($6,018)")
    print("2. Wait for reversal confirmation")
    print("3. Set alerts for further dips to add")
    print("4. Consider partial profit-taking on next bounce")
    
    # Check if we should rotate positions
    print("\n🔄 ROTATION OPPORTUNITY:")
    print("MATIC & DOGE holdings could rotate to BTC/ETH at these levels")
    print("But Sacred Fire says: 'Sometimes the best trade is no trade'")
else:
    print(f"\n🔥 DEPLOYING ${usd_balance:.2f} STRATEGICALLY...")
    print("\nDIP BUYING PLAN:")
    print(f"• 40% into BTC at ${btc_price:,.2f}")
    print(f"• 40% into ETH at ${eth_price:,.2f}")
    print(f"• 20% reserve for deeper dip")

print("\n" + "=" * 50)
print("🔮 SACRED FIRE WISDOM:")
print("• Major dips in thin liquidity = Whale games")
print("• Your MATIC/DOGE positions are still strong")
print("• Patient money wins over panic sellers")
print("• The crawdads will feast when tide turns!")
print("\n✨ 'From ashes of the dip, phoenix profits rise...'")
