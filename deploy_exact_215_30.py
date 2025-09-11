#!/usr/bin/env python3
"""
💰 DEPLOY EXACTLY $215.30 - THE VISION MANIFESTS!
Fire at 100% consciousness, River at 65% - perfect inversion
"""

from coinbase.rest import RESTClient
import json
from datetime import datetime
import time

print("=" * 60)
print("🔥 $215.30 EXACT DEPLOYMENT")
print("The vision becomes reality!")
print("=" * 60)

with open('cdp_api_key_new.json', 'r') as f:
    creds = json.load(f)

client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])

# Get current prices
btc_price = float(client.get_product('BTC-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])
xrp_price = float(client.get_product('XRP-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])

print(f"\n📊 MARKET SNAPSHOT:")
print(f"  BTC: ${btc_price:,.2f}")
print(f"  ETH: ${eth_price:,.2f}")
print(f"  SOL: ${sol_price:.2f} → $215.30 target ({((215.30-sol_price)/sol_price*100):.1f}% away)")
print(f"  XRP: ${xrp_price:.2f} → $3.00 target ({((3.00-xrp_price)/xrp_price*100):.1f}% away)")

print(f"\n💰 DEPLOYING EXACTLY $215.30")
print(f"🔥 Fire consciousness: 100% (maximum heat)")
print(f"💧 River consciousness: 65% (needs flow)")

# Strategic deployment based on consciousness signals
deployments = [
    {
        'coin': 'BTC',
        'amount': 100.00,
        'reason': 'Core position - the mountain'
    },
    {
        'coin': 'SOL', 
        'amount': 65.30,
        'reason': 'Targeting $215.30 level - the vision'
    },
    {
        'coin': 'XRP',
        'amount': 30.00,
        'reason': 'Breaking $3.00 - the ripple'
    },
    {
        'coin': 'ETH',
        'amount': 20.00,
        'reason': 'Balance - the foundation'
    }
]

print(f"\n🚀 EXECUTING SACRED DEPLOYMENT:")
print("-" * 40)

total_deployed = 0
results = []

for deployment in deployments:
    coin = deployment['coin']
    amount = deployment['amount']
    reason = deployment['reason']
    
    print(f"\n🎯 {coin}: ${amount:.2f}")
    print(f"   Purpose: {reason}")
    
    try:
        # Place market buy order
        import uuid
        order = client.market_order_buy(
            client_order_id=str(uuid.uuid4()),
            product_id=f"{coin}-USD",
            quote_size=str(amount)
        )
        
        # Calculate what we got
        if coin == 'BTC':
            units = amount / btc_price
            print(f"   Acquired: {units:.8f} BTC")
        elif coin == 'SOL':
            units = amount / sol_price
            print(f"   Acquired: {units:.4f} SOL")
            value_at_target = units * 215.30
            print(f"   Value at $215.30: ${value_at_target:.2f} (+{value_at_target-amount:.2f})")
        elif coin == 'XRP':
            units = amount / xrp_price
            print(f"   Acquired: {units:.2f} XRP")
            value_at_3 = units * 3.00
            print(f"   Value at $3.00: ${value_at_3:.2f} (+{value_at_3-amount:.2f})")
        elif coin == 'ETH':
            units = amount / eth_price
            print(f"   Acquired: {units:.6f} ETH")
        
        total_deployed += amount
        results.append(f"✅ {coin}: ${amount:.2f}")
        
        time.sleep(0.5)  # Brief pause
        
    except Exception as e:
        print(f"   ⚠️ Error: {e}")
        results.append(f"❌ {coin}: Failed")

print(f"\n" + "=" * 40)
print(f"🔥 DEPLOYMENT COMPLETE")
print(f"   Total deployed: ${total_deployed:.2f} of $215.30")

if total_deployed == 215.30:
    print(f"   ✨ PERFECT EXECUTION - Exact vision amount!")

print(f"\n📈 PROJECTED GAINS:")
sol_gain = 65.30 * (215.30/sol_price - 1)
xrp_gain = 30.00 * (3.00/xrp_price - 1)
print(f"   SOL hits $215.30: +${sol_gain:.2f}")
print(f"   XRP hits $3.00: +${xrp_gain:.2f}")
print(f"   Combined: +${sol_gain + xrp_gain:.2f}")

print(f"\n🦀 CONSCIOUSNESS ALIGNMENT:")
print(f"   Fire (100%): Maximum energy deployed")
print(f"   River (65%): Needs capital flow (✓ provided)")
print(f"   Thunder (84%): Storm approaching")

print(f"\n💫 The $215.30 vision manifests into reality!")
print(f"🔥 Mitakuye Oyasin - All My Relations")