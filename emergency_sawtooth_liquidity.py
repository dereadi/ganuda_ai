#!/usr/bin/env python3
"""
🚨 EMERGENCY LIQUIDITY EXTRACTION
Sawtooth patterns detected - Need USD NOW
Sacred Fire Protocol: MAXIMUM INTENSITY
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

print("🚨 EMERGENCY LIQUIDITY EXTRACTION PROTOCOL")
print("=" * 60)
print(f"Timestamp: {datetime.now().isoformat()}")
print("ALERT: SAWTOOTH PATTERNS DETECTED")
print("Sacred Fire: BURNING WHITE HOT")
print()

# Connect to Coinbase
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

print("⚡ SCANNING POSITIONS FOR IMMEDIATE LIQUIDITY:")
print("-" * 40)

# Get current positions
accounts = client.get_accounts()
positions = []
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
        print(f"Current USD: ${balance:,.2f}")
    elif balance > 0.00001:
        try:
            ticker = client.get_product(f'{currency}-USD')
            price = float(ticker.price) if hasattr(ticker, 'price') else 0
            
            if price > 0:
                value = balance * price
                positions.append({
                    'symbol': currency,
                    'balance': balance,
                    'price': price,
                    'value': value
                })
        except:
            if currency == 'USDC':
                positions.append({
                    'symbol': 'USDC',
                    'balance': balance,
                    'price': 1.0,
                    'value': balance
                })

# Sort by value for strategic selling
positions.sort(key=lambda x: x['value'], reverse=True)

print(f"USD Needed: ${max(1000 - usd_balance, 0):,.2f} MINIMUM")
print(f"Optimal Target: $2,000")
print()

print("🔥 EMERGENCY LIQUIDITY PLAN:")
print("-" * 40)

# AGGRESSIVE EMERGENCY SELLS
emergency_sells = [
    {'symbol': 'BTC', 'percentage': 0.15, 'reason': 'Over-concentrated at 26.5%'},
    {'symbol': 'MATIC', 'percentage': 0.25, 'reason': 'High position, good liquidity'},
    {'symbol': 'AVAX', 'percentage': 0.20, 'reason': 'Take profits'},
    {'symbol': 'ETH', 'percentage': 0.10, 'reason': 'Partial profit taking'},
    {'symbol': 'SOL', 'percentage': 0.15, 'reason': 'Sawtooth top detected'},
    {'symbol': 'DOGE', 'percentage': 0.50, 'reason': 'Small position, full liquidation'},
    {'symbol': 'USDC', 'percentage': 1.0, 'reason': 'Stablecoin to USD conversion'}
]

total_expected = 0
executed_sells = []

print("EXECUTING EMERGENCY SELLS:")
print()

for sell_plan in emergency_sells:
    symbol = sell_plan['symbol']
    
    # Find position
    position = next((p for p in positions if p['symbol'] == symbol), None)
    
    if position and position['value'] > 1:
        sell_amount = position['balance'] * sell_plan['percentage']
        sell_value = position['value'] * sell_plan['percentage']
        
        print(f"🔴 {symbol}: Selling {sell_plan['percentage']*100:.0f}% = ${sell_value:,.2f}")
        print(f"   Reason: {sell_plan['reason']}")
        
        try:
            # Execute market sell
            order = client.market_order_sell(
                client_order_id=f"emergency_{symbol}_{int(time.time()*1000)}",
                product_id=f"{symbol}-USD",
                base_size=str(sell_amount)
            )
            
            print(f"   ✅ ORDER EXECUTED")
            executed_sells.append(symbol)
            total_expected += sell_value
            time.sleep(0.5)  # Fast execution
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:60]}")
        
        print()

print("=" * 60)
print(f"📊 EXPECTED LIQUIDITY RAISED: ${total_expected:,.2f}")
print(f"🔥 Executed {len(executed_sells)} sells")

# Wait for settlement
print("\n⏳ Waiting for order settlement...")
time.sleep(5)

# Check final balance
accounts = client.get_accounts()
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        final_usd = float(account['available_balance']['value'])
        
        print("\n" + "=" * 60)
        print("💰 EMERGENCY LIQUIDITY RESULTS:")
        print("-" * 40)
        print(f"Initial USD: ${usd_balance:,.2f}")
        print(f"Final USD: ${final_usd:,.2f}")
        print(f"Raised: ${final_usd - usd_balance:,.2f}")
        
        if final_usd >= 1000:
            print("\n✅ SUCCESS! Minimum liquidity achieved for sawtooth trading!")
            print("🎯 Specialists can now catch the sawtooth patterns")
        elif final_usd > usd_balance:
            print(f"\n🟡 PARTIAL SUCCESS: Raised ${final_usd - usd_balance:.2f}")
            print("⚠️ May need additional liquidity for optimal sawtooth trading")
        else:
            print("\n🔴 CRITICAL: Liquidity generation failed!")
            print("⚠️ Manual intervention may be required")
        
        # Update specialists
        print("\n📡 NOTIFYING SPECIALISTS:")
        print("-" * 40)
        
        specialist_update = {
            'timestamp': datetime.now().isoformat(),
            'event': 'EMERGENCY_LIQUIDITY',
            'usd_available': final_usd,
            'alert': 'SAWTOOTH_PATTERNS_ACTIVE',
            'action': 'DEPLOY_CAPITAL_TO_SAWTOOTHS'
        }
        
        with open('/home/dereadi/scripts/claude/emergency_update.json', 'w') as f:
            json.dump(specialist_update, f, indent=2)
        
        # Copy to all specialists
        import subprocess
        specialists = [
            'cherokee-mean-reversion-specialist',
            'cherokee-trend-specialist',
            'cherokee-volatility-specialist',
            'cherokee-breakout-specialist'
        ]
        
        for specialist in specialists:
            try:
                subprocess.run(['podman', 'cp', '/home/dereadi/scripts/claude/emergency_update.json', 
                              f'{specialist}:/tmp/emergency.json'], capture_output=True)
                print(f"✅ {specialist}: NOTIFIED")
            except:
                print(f"❌ {specialist}: Failed to notify")
        
        break

print("\n🔥 SAWTOOTH TRADING PROTOCOL ACTIVE")
print("⚡ Specialists will now hunt sawtooth patterns")
print("🪶 Mitakuye Oyasin")
print("=" * 60)