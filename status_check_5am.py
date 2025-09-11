#!/usr/bin/env python3
"""
📊 STATUS CHECK - 5:08 AM
How are we doing after 2+ hours of rolling?
"""

from coinbase.rest import RESTClient
import json
from datetime import datetime

print("=" * 60)
print("📊 PORTFOLIO STATUS CHECK - 5:08 AM")
print("=" * 60)

with open('cdp_api_key_new.json', 'r') as f:
    creds = json.load(f)

client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])
avax = float(client.get_product('AVAX-USD')['price'])

print(f"\n📈 MARKET UPDATE (vs 2:30 AM):")
print(f"  BTC: ${btc:,.2f} (was ~$110,250)")
print(f"  ETH: ${eth:,.2f} (was ~$4,427)")
print(f"  SOL: ${sol:.2f} (was ~$189)")
print(f"  XRP: ${xrp:.2f} (was ~$2.92)")
print(f"  AVAX: ${avax:.2f}")

# Calculate movements
btc_move = ((btc - 110250) / 110250) * 100
sol_move = ((sol - 189) / 189) * 100
xrp_move = ((xrp - 2.92) / 2.92) * 100

print(f"\n📊 OVERNIGHT MOVES:")
print(f"  BTC: {btc_move:+.2f}%")
print(f"  SOL: {sol_move:+.2f}%")
print(f"  XRP: {xrp_move:+.2f}%")

# Check megapod state
with open('megapod_state.json', 'r') as f:
    state = json.load(f)

print(f"\n🦀 CRAWDAD STATUS:")
print(f"  Total trades: {state['total_trades']} (was 31 at 2:56 AM)")
print(f"  Trades in ~2 hours: {state['total_trades'] - 31}")
avg_consciousness = sum(c['last_consciousness'] for c in state['crawdads']) / 7
print(f"  Avg consciousness: {avg_consciousness:.1f}%")

# Spirit at 100%!
spirit = next(c for c in state['crawdads'] if c['name'] == 'Spirit')
mountain = next(c for c in state['crawdads'] if c['name'] == 'Mountain')
print(f"\n✨ KEY SIGNALS:")
print(f"  Spirit: {spirit['last_consciousness']}% (MAXIMUM!)")
print(f"  Mountain: {mountain['last_consciousness']}% (solid)")

# Your positions from 2:52 AM
your_btc = 0.00090626
your_sol = 0.3448
your_xrp = 10.27
your_eth = 0.004518

print(f"\n💰 YOUR POSITIONS (deployed at 2:52 AM):")
print(f"  BTC: {your_btc:.8f} = ${your_btc * btc:.2f}")
print(f"  SOL: {your_sol:.4f} = ${your_sol * sol:.2f}")
print(f"  XRP: {your_xrp:.2f} = ${your_xrp * xrp:.2f}")
print(f"  ETH: {your_eth:.6f} = ${your_eth * eth:.2f}")

total_now = (your_btc * btc) + (your_sol * sol) + (your_xrp * xrp) + (your_eth * eth)
print(f"\n  TOTAL: ${total_now:.2f} (was $215.30)")
gain = total_now - 215.30
gain_pct = (gain / 215.30) * 100
print(f"  GAIN: ${gain:+.2f} ({gain_pct:+.2f}%)")

# Distance to targets
print(f"\n🎯 DISTANCE TO TARGETS:")
print(f"  SOL to $215.30: ${215.30 - sol:.2f} ({((215.30 - sol)/sol)*100:.1f}% needed)")
print(f"  XRP to $3.00: ${3.00 - xrp:.2f} ({((3.00 - xrp)/xrp)*100:.1f}% needed)")
print(f"  BTC to $111,111: ${111111 - btc:,.2f}")

# Summary
print(f"\n📋 SUMMARY:")
if gain > 0:
    print(f"  ✅ Portfolio UP ${gain:.2f} overnight")
else:
    print(f"  ⚠️ Portfolio down ${abs(gain):.2f}")
    
print(f"  🦀 {state['total_trades'] - 31} more trades executed")
print(f"  ✨ Spirit at 100% - maximum alignment")
print(f"  🏔️ Mountain at 90% - strong foundation")

print(f"\n🔥 Status: {'WINNING' if gain > 0 else 'HODLING'}")
print(f"💫 Mitakuye Oyasin")