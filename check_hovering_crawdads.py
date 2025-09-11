
#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

# Get market status
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print(f"BTC: ${btc_price:,.2f} - HOVERING")
print(f"ETH: ${eth_price:,.2f}")
print(f"SOL: ${sol_price:,.2f}")

# Calculate hovering metrics
volatility = abs(btc_price - 112200) / 112200 * 100
print(f"\nHovering Volatility: {volatility:.2f}%")

if volatility < 0.5:
    print("✅ PERFECT HOVERING - Crawdads can feed!")
elif volatility < 1.0:
    print("⚠️ MILD HOVERING - Crawdads cautious")
else:
    print("🚨 TOO VOLATILE - Crawdads waiting")

# Check USD balance
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"\nUSD Available: ${usd_balance:.2f}")
if usd_balance < 20:
    print("  → Need more USD for crawdads to trade effectively")
else:
    print("  → Crawdads have ammunition!")

# Crawdad personalities
print("\n🦀 CRAWDAD PERSONALITIES:")
print("  Thunder: Aggressive on dips (needs $50+ USD)")
print("  Mountain: Steady accumulator (needs $30+ USD)")  
print("  Fire: Quick scalper (needs $20+ USD)")
print("  Wind: Momentum rider (needs $25+ USD)")
print("  Earth: Support buyer (needs $40+ USD)")
print("  River: Flow trader (needs $35+ USD)")
print("  Spirit: Intuitive trader (needs $45+ USD)")

print(f"\n  Current funding allows: {'None - need more USD!' if usd_balance < 20 else 'Fire only' if usd_balance < 25 else 'Fire & Wind' if usd_balance < 30 else 'Multiple crawdads'}")
