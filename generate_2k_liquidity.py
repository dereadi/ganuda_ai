#!/usr/bin/env python3
"""
💰 GENERATE $2,000 LIQUIDITY
Council mandate: Need $2k for proper positioning
"""

import json
import time
from coinbase.rest import RESTClient

print("💰 GENERATING $2,000 LIQUIDITY (COUNCIL MANDATE)")
print("=" * 60)

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

# Check current state
accounts = client.get_accounts()
positions = {}
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
    elif balance > 0:
        positions[currency] = balance

print(f"Current USD: ${usd_balance:,.2f}")
print(f"Target: $2,000.00")
print(f"Need: ${max(2000 - usd_balance, 0):,.2f}")
print()

if usd_balance >= 2000:
    print("✅ Already have sufficient liquidity!")
else:
    # Calculate what to sell
    need_to_raise = 2000 - usd_balance
    print(f"📊 POSITIONS AVAILABLE FOR LIQUIDITY:")
    print("-" * 40)
    
    # Get current prices and values
    position_values = []
    for coin, balance in positions.items():
        if coin not in ['USD', 'USDC']:
            try:
                ticker = client.get_product(f'{coin}-USD')
                price = float(ticker['price'])
                value = balance * price
                position_values.append((coin, balance, price, value))
                print(f"{coin}: {balance:.4f} @ ${price:.2f} = ${value:,.2f}")
            except:
                pass
    
    # Sort by value (sell from largest positions)
    position_values.sort(key=lambda x: x[3], reverse=True)
    
    print(f"\n🔄 EXECUTING STRATEGIC LIQUIDITY GENERATION:")
    print("-" * 40)
    
    raised = 0
    sells = []
    
    # Strategy: Take 20% from largest positions
    for coin, balance, price, value in position_values:
        if raised >= need_to_raise:
            break
            
        # Skip if position too small
        if value < 100:
            continue
            
        # Calculate sell amount (20% of position or what we need)
        sell_value = min(value * 0.2, need_to_raise - raised)
        sell_amount = sell_value / price
        
        # Don't sell tiny amounts
        if sell_value < 50:
            continue
            
        sells.append((coin, sell_amount, sell_value))
        raised += sell_value
    
    # Execute sells
    if sells:
        print("Executing sells to raise liquidity:\n")
        
        for coin, amount, expected_value in sells:
            try:
                print(f"Selling {amount:.6f} {coin} (≈${expected_value:.2f})...")
                
                order = client.market_order_sell(
                    client_order_id=f"liquidity_{coin}_{int(time.time()*1000)}",
                    product_id=f"{coin}-USD",
                    base_size=str(amount)
                )
                
                print(f"  ✅ {coin} sold successfully")
                time.sleep(1)
                
            except Exception as e:
                print(f"  ❌ {coin} failed: {str(e)[:100]}")
        
        # Check final balance
        time.sleep(3)
        accounts = client.get_accounts()
        for account in accounts['accounts']:
            if account['currency'] == 'USD':
                new_balance = float(account['available_balance']['value'])
                print(f"\n💵 NEW USD BALANCE: ${new_balance:,.2f}")
                
                if new_balance >= 2000:
                    print("✅ COUNCIL MANDATE ACHIEVED: $2,000+ liquidity!")
                elif new_balance >= 1500:
                    print("🟡 PARTIAL SUCCESS: Have $1,500+ liquidity")
                else:
                    print("⚠️ Still below target, may need more aggressive sells")
                break
    else:
        print("❌ No suitable positions to sell for liquidity")