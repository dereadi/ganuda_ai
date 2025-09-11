#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 ETH-BTC SYNC CHECK - SIMPLE AND DIRECT
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

print("🔥 ETH-BTC SYNCHRONIZATION CHECK")
print("=" * 60)

# Get current prices
btc = client.get_product("BTC-USD")
eth = client.get_product("ETH-USD")
sol = client.get_product("SOL-USD")

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

# Get 1hr candles to see recent movement
from datetime import timedelta
end = datetime.now()
start = end - timedelta(hours=6)

# Use valid granularity
btc_candles = client.get_candles("BTC-USD", start.isoformat(), end.isoformat(), "ONE_HOUR")
eth_candles = client.get_candles("ETH-USD", start.isoformat(), end.isoformat(), "ONE_HOUR")
sol_candles = client.get_candles("SOL-USD", start.isoformat(), end.isoformat(), "ONE_HOUR")

# Get 6hr ago prices
btc_6hr = float(btc_candles['candles'][-1]['open']) if btc_candles['candles'] else btc_price
eth_6hr = float(eth_candles['candles'][-1]['open']) if eth_candles['candles'] else eth_price
sol_6hr = float(sol_candles['candles'][-1]['open']) if sol_candles['candles'] else sol_price

# Calculate changes
btc_change = ((btc_price - btc_6hr) / btc_6hr) * 100
eth_change = ((eth_price - eth_6hr) / eth_6hr) * 100
sol_change = ((sol_price - sol_6hr) / sol_6hr) * 100

print(f"\n📊 CURRENT PRICES (6hr change):")
print(f"  BTC: ${btc_price:,.2f} ({btc_change:+.2f}%)")
print(f"  ETH: ${eth_price:,.2f} ({eth_change:+.2f}%)")
print(f"  SOL: ${sol_price:,.2f} ({sol_change:+.2f}%)")

# Check sync
btc_eth_diff = abs(btc_change - eth_change)
print(f"\n🔗 BTC-ETH Divergence: {btc_eth_diff:.2f}%")

if btc_eth_diff < 0.5:
    print("  Status: PERFECT SYNC! 🔥")
elif btc_eth_diff < 1.0:
    print("  Status: STRONG SYNC!")
elif btc_eth_diff < 2.0:
    print("  Status: MODERATE SYNC")
else:
    print("  Status: DIVERGING")

# Direction
if btc_change > 0.5 and eth_change > 0.5:
    print("  Direction: 🚀 BOTH PUMPING TOGETHER!")
elif btc_change < -0.5 and eth_change < -0.5:
    print("  Direction: 🔴 BOTH DUMPING TOGETHER!")
else:
    print("  Direction: 😴 SIDEWAYS/MIXED")

# Trading implications
print(f"\n🎯 TRADING SIGNALS:")

# Check key levels
if btc_price > 109000:
    print("  ⚠️ BTC approaching $110k resistance!")
if eth_price > 4450:
    print("  ⚠️ ETH approaching $4,500 resistance!")
if sol_price > 203:
    print("  ⚠️ SOL approaching $205 harvest zone!")

if btc_price < 108000:
    print("  🟢 BTC in accumulation zone (<$108k)")
if eth_price < 4400:
    print("  🟢 ETH in accumulation zone (<$4,400)")
if sol_price < 200:
    print("  🟢 SOL in feed zone (<$200)")

# Fee-aware targets
print(f"\n💸 FEE-AWARE PROFIT TARGETS (need 2% to beat fees):")
print(f"  BTC: ${btc_price * 1.02:,.2f} (+2%)")
print(f"  ETH: ${eth_price * 1.02:,.2f} (+2%)")
print(f"  SOL: ${sol_price * 1.02:,.2f} (+2%)")

print("\n" + "=" * 60)
print("🐿️ Flying Squirrel Tewa: 'Watch them fly together!'")
print("=" * 60)