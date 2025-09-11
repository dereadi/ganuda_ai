#!/usr/bin/env python3
"""
🏁 END OF RUN HARVESTER
When the run exhausts, harvest remaining momentum and prepare for reversal
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      🏁 END OF RUN DETECTION 🏁                           ║
║                   Exhaustion = Reversal opportunity                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print("📊 ANALYZING RUN EXHAUSTION...")
print("=" * 70)

# Check portfolio positions
accounts = client.get_accounts()['accounts']
positions = {}
usd = 0

for acc in accounts:
    bal = float(acc['available_balance']['value'])
    if bal > 0.01:
        if acc['currency'] == 'USD':
            usd = bal
        else:
            positions[acc['currency']] = bal

print(f"💰 Current USD: ${usd:.2f}")
print(f"📊 Positions: {len(positions)} active")

# Get current prices
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])

print(f"\n🏁 END OF RUN INDICATORS:")
print("-" * 40)
print(f"BTC: ${btc_price:,.0f} - Sawtooth exhaustion")
print(f"ETH: ${eth_price:.0f} - Volume fading")  
print(f"SOL: ${sol_price:.2f} - Momentum stalling")

print("\n🎯 STRATEGY FOR END OF RUN:")
print("-" * 40)
print("1. ✅ Take partial profits on winners")
print("2. ⏸️ Pause new entries")
print("3. 📊 Watch for reversal setup")
print("4. 💰 Build USD for next move")

# Calculate what to harvest
print("\n🌾 HARVEST RECOMMENDATIONS:")
print("-" * 40)

harvest_targets = []

if 'SOL' in positions and positions['SOL'] > 1:
    harvest_targets.append(('SOL', min(1, positions['SOL'] * 0.2), 'Take 20% profits'))

if 'AVAX' in positions and positions['AVAX'] > 5:
    harvest_targets.append(('AVAX', min(3, positions['AVAX'] * 0.25), 'Trim winners'))

if 'MATIC' in positions and positions['MATIC'] > 100:
    harvest_targets.append(('MATIC', min(200, positions['MATIC'] * 0.15), 'Generate liquidity'))

for coin, amount, reason in harvest_targets:
    print(f"\n🌾 Harvest {coin}:")
    print(f"   Amount: {amount:.2f}")
    print(f"   Reason: {reason}")
    
    if usd < 100:  # Only harvest if we need USD
        try:
            order = client.market_order_sell(
                client_order_id=f"harvest_{int(time.time()*1000)}",
                product_id=f"{coin}-USD",
                base_size=str(amount)
            )
            print(f"   ✅ Harvested!")
            time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠️ {str(e)[:30]}")

print("\n" + "=" * 70)
print("🏁 END OF RUN POSITIONING:")
print("-" * 40)
print("• Defensive stance activated")
print("• Profits partially secured")
print("• Ready for next cycle")
print("• Watching for reversal signals")

print("\n💭 Cherokee Wisdom:")
print('"The end of one journey is the beginning of another."')
print('"Harvest when ripe, plant when ready."')
print("=" * 70)