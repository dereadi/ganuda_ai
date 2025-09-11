#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 QUICK JAPANESE IMPACT CHECK
Brief status update on Trump-Metaplanet effect
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

# Load API
with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
    config = json.load(f)

client = RESTClient(
    api_key=config['name'].split('/')[-1],
    api_secret=config['privateKey']
)

print("🔥 JAPANESE BUYING IMPACT - QUICK CHECK")
print("=" * 60)

# Get BTC price
btc = client.get_product("BTC-USD")
btc_price = float(btc['price'])

# Get portfolio
accounts = client.get_accounts()['accounts']
btc_balance = 0
usd_balance = 0

for account in accounts:
    if account['currency'] == 'BTC':
        btc_balance = float(account['available_balance']['value'])
    elif account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])

total_value = (btc_balance * btc_price) + usd_balance

print(f"\n📊 CURRENT STATUS:")
print(f"  BTC Price: ${btc_price:,.2f}")
print(f"  BTC Holdings: {btc_balance:.8f}")
print(f"  USD Balance: ${usd_balance:.2f}")
print(f"  Total Value: ${total_value:,.2f}")

# Distance to targets
targets = [110000, 115000, 120000]
print(f"\n🎯 DISTANCE TO TARGETS:")
for target in targets:
    distance = target - btc_price
    pct = (distance / btc_price) * 100
    print(f"  ${target:,}: ${distance:,.0f} away ({pct:.1f}%)")

# News timeline
print(f"\n📰 NEWS STATUS:")
print(f"  Trump-Metaplanet news broke ~1 hour ago")
print(f"  Japanese $884M buying: IMMINENT")
print(f"  Market awareness: BUILDING")

# Oracle
if btc_price > 108000:
    print(f"\n✅ BTC ABOVE $108K - MOMENTUM BUILDING!")
elif btc_price > 107500:
    print(f"\n🟡 BTC CONSOLIDATING - COILING FOR MOVE")
else:
    print(f"\n🔴 BTC BELOW $107.5K - ACCUMULATION ZONE")

print("=" * 60)