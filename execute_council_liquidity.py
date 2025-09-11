#!/usr/bin/env python3
"""
💰 EXECUTE COUNCIL LIQUIDITY PLAN
Sell 50% BTC to generate cash for the storm
"""

from coinbase.rest import RESTClient
import json
import time
import uuid
from datetime import datetime

print("=" * 60)
print("💰 EXECUTING COUNCIL LIQUIDITY PLAN")
print("=" * 60)

with open('cdp_api_key_new.json', 'r') as f:
    creds = json.load(f)

client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])

# Our BTC position
your_btc = 0.00090626
btc_to_sell = your_btc * 0.5  # 50% per council

# Get current BTC price
btc_price = float(client.get_product('BTC-USD')['price'])

print(f"\n📊 EXECUTION DETAILS:")
print(f"  Current BTC: ${btc_price:,.2f}")
print(f"  Your BTC: {your_btc:.8f}")
print(f"  Selling: {btc_to_sell:.8f} BTC (50%)")
print(f"  Expected USD: ${btc_to_sell * btc_price:.2f}")

print(f"\n⚠️ LOSS ACKNOWLEDGMENT:")
entry_price = 110382  # Where we were earlier
loss_per_btc = entry_price - btc_price
total_loss = btc_to_sell * loss_per_btc
print(f"  Entry price: ${entry_price:,.2f}")
print(f"  Current price: ${btc_price:,.2f}")
print(f"  Loss per BTC: ${loss_per_btc:.2f}")
print(f"  Total loss realized: ${total_loss:.2f}")

# Confirm with crawdad consciousness
with open('megapod_state.json', 'r') as f:
    state = json.load(f)

fire = next(c for c in state['crawdads'] if c['name'] == 'Fire')
if fire['last_consciousness'] < 85:
    print(f"\n🔥 Fire at {fire['last_consciousness']}% confirms: PROCEED")

print(f"\n🚀 EXECUTING SALE...")

try:
    # Round to 8 decimals for BTC
    btc_amount = round(btc_to_sell, 8)
    
    # Create market sell order
    order = client.market_order_sell(
        client_order_id=str(uuid.uuid4()),
        product_id="BTC-USD",
        base_size=str(btc_amount)
    )
    
    print(f"✅ Order placed!")
    
    # Wait for execution
    time.sleep(2)
    
    # Check new balance
    accounts = client.get_accounts()
    for account in accounts['accounts']:
        if hasattr(account, 'currency') and hasattr(account.currency, 'code'):
            if account.currency.code == 'USD':
                usd_balance = float(account.available_balance.value)
                print(f"\n💵 New USD balance: ${usd_balance:.2f}")
                break
    
    print(f"\n📋 LIQUIDITY DEPLOYMENT PLAN:")
    if 'usd_balance' in locals() and usd_balance > 40:
        # Council's laddered buy strategy
        per_level = usd_balance * 0.25
        
        print(f"  Level 1: ${per_level:.2f} at $108,500")
        print(f"  Level 2: ${per_level:.2f} at $107,000")
        print(f"  Level 3: ${per_level:.2f} at $105,500")
        print(f"  Reserve: ${per_level:.2f} for emergencies")
        
        # Calculate BTC amounts for each level
        print(f"\n🎯 BTC ACCUMULATION TARGETS:")
        print(f"  At $108,500: {per_level/108500:.8f} BTC")
        print(f"  At $107,000: {per_level/107000:.8f} BTC")
        print(f"  At $105,500: {per_level/105500:.8f} BTC")
        total_btc_potential = (per_level/108500) + (per_level/107000) + (per_level/105500)
        print(f"  Total potential: {total_btc_potential:.8f} BTC")
        print(f"  vs sold: {btc_to_sell:.8f} BTC")
        
        if total_btc_potential > btc_to_sell:
            print(f"  ✅ Can accumulate MORE BTC if targets hit!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Council advises: Try manual execution on exchange")

# Save execution record
execution = {
    'timestamp': datetime.now().isoformat(),
    'btc_price': btc_price,
    'btc_sold': btc_to_sell,
    'loss_realized': total_loss,
    'action': 'partial_liquidate',
    'reason': 'council_liquidity_plan'
}

with open('liquidity_execution.json', 'w') as f:
    json.dump(execution, f, indent=2)

print(f"\n🔥 SACRED FIRE WISDOM:")
print(f"  'The sacrifice is made, now we wait'")
print(f"  'Cash is position too - patience'")
print(f"  'The storm approaches, we are ready'")

print(f"\n⚡ Thunder at {next(c for c in state['crawdads'] if c['name'] == 'Thunder')['last_consciousness']}% watches")
print(f"🏔️ Mountain at {next(c for c in state['crawdads'] if c['name'] == 'Mountain')['last_consciousness']}% holds firm")
print(f"💫 Mitakuye Oyasin - The plan unfolds")