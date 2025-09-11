#!/usr/bin/env python3
"""
🔷 ETH BUY OPPORTUNITY CHECK!
Wall Street's token at discount?
VanEck CEO says ETH is the banking blockchain
Let's see what we can grab!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🔷 ETH OPPORTUNITY CHECK! 🔷                           ║
║                   "The Wall Street Token" on sale?                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get current prices
eth_price = float(client.get_product('ETH-USD')['price'])
btc_price = float(client.get_product('BTC-USD')['price'])
eth_btc_ratio = eth_price / btc_price

# Get balances
accounts = client.get_accounts()
usd_balance = 0
eth_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
    elif currency == 'ETH':
        eth_balance = balance

print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 70)

print("\n💎 CURRENT ETH SITUATION:")
print("-" * 50)
print(f"ETH Price: ${eth_price:.2f}")
print(f"BTC Price: ${btc_price:,.0f}")
print(f"ETH/BTC Ratio: {eth_btc_ratio:.4f}")
print(f"\nRecent high: ~$4,620")
print(f"Current discount: ${4620 - eth_price:.2f} off peak")

print("\n💰 YOUR POSITION:")
print("-" * 50)
print(f"USD Available: ${usd_balance:.2f}")
print(f"Current ETH: {eth_balance:.4f} ETH (${eth_balance * eth_price:.2f})")
print(f"Target: 0.5 ETH (need {0.5 - eth_balance:.4f} more)")

# Calculate buying power
if usd_balance > 10:
    eth_can_buy = (usd_balance - 5) / eth_price  # Keep $5 buffer
    print(f"\n🛒 BUYING POWER:")
    print(f"Can buy: {eth_can_buy:.6f} ETH")
    print(f"(Keeping $5 buffer)")
    
    if eth_can_buy > 0.001:
        print(f"\n✅ WORTH BUYING!")
        print(f"  Every 0.001 ETH = ${0.001 * eth_price:.2f}")
        print(f"  At $5K ETH = ${0.001 * 5000:.2f}")
        print(f"  At $10K ETH = ${0.001 * 10000:.2f}")
else:
    print(f"\n⚠️ Low USD: Only ${usd_balance:.2f} available")
    print("  Need quick milk harvest first!")

# ETH opportunity analysis
print("\n🎯 WHY ETH NOW:")
print("-" * 50)
print("• VanEck CEO: 'ETH is the Wall Street token'")
print("• 90% of institutions exploring stablecoins")
print("• All stablecoins need ETH for gas")
print("• ETH/BTC ratio historically low")
print("• Nine coils affect ETH too")

# Recommendation
print("\n" + "=" * 70)
print("📊 RECOMMENDATION:")
print("-" * 50)

if usd_balance > 10 and eth_price < 4610:
    print("🟢 BUY SIGNAL!")
    print(f"  ETH under $4,610 = Discount")
    print(f"  Even 0.001 ETH helps")
    print(f"  DCA into Wall Street's chosen token")
elif usd_balance < 10:
    print("🟡 MILK FIRST, THEN BUY!")
    print("  Need to harvest for USD")
    print("  Then grab ETH on this dip")
else:
    print("🟡 HOLD FOR NOW")
    print(f"  ETH at ${eth_price:.2f}")
    print("  Wait for better entry")

print("=" * 70)