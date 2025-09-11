#!/usr/bin/env python3
"""
🔥 EXECUTE CHEROKEE COUNCIL STRATEGY
SOL to ETH rotation for liquidity and accumulation
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

# Load config
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

print("🔥 CHEROKEE COUNCIL STRATEGY EXECUTION 🔥")
print("=" * 70)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Mission: SOL to ETH rotation + liquidity generation")
print("=" * 70)
print()

def get_current_prices():
    """Get current market prices"""
    btc = client.get_product('BTC-USD')
    eth = client.get_product('ETH-USD')
    sol = client.get_product('SOL-USD')
    
    return {
        'BTC': float(btc['price']),
        'ETH': float(eth['price']),
        'SOL': float(sol['price'])
    }

def check_balances():
    """Check current balances"""
    accounts = client.get_accounts()
    balances = {}
    
    for account in accounts['accounts']:
        currency = account['currency']
        balance = float(account['available_balance']['value'])
        if balance > 0.00001:
            balances[currency] = balance
            
    return balances

# Get current state
print("📊 CHECKING CURRENT STATE...")
print("-" * 50)

prices = get_current_prices()
balances = check_balances()

print(f"SOL Price: ${prices['SOL']:.2f}")
print(f"ETH Price: ${prices['ETH']:.2f}")
print(f"BTC Price: ${prices['BTC']:,.2f}")
print()

print("Current Balances:")
for currency, balance in balances.items():
    if currency in ['USD', 'USDC']:
        print(f"  {currency}: ${balance:.2f}")
    elif currency == 'SOL':
        value = balance * prices['SOL']
        print(f"  SOL: {balance:.4f} (${value:.2f})")
    elif currency == 'ETH':
        value = balance * prices['ETH']
        print(f"  ETH: {balance:.6f} (${value:.2f})")
print()

# Strategy execution
print("🎯 STRATEGY EXECUTION PLAN:")
print("-" * 50)

# Step 1: Check if SOL is near $200
sol_target = 200.00
sol_distance = sol_target - prices['SOL']
sol_pct_to_target = (sol_distance / prices['SOL']) * 100

print(f"Step 1: SOL Target Analysis")
print(f"  Current SOL: ${prices['SOL']:.2f}")
print(f"  Target: ${sol_target:.2f}")
print(f"  Distance: ${sol_distance:.2f} ({sol_pct_to_target:+.1f}%)")
print()

if prices['SOL'] >= 199.50:  # Close enough to $200
    print("✅ SOL at target! Executing sell order...")
    
    # Place market sell for 2.5 SOL
    try:
        sol_to_sell = min(2.5, balances.get('SOL', 0))
        if sol_to_sell >= 0.1:
            print(f"  Selling {sol_to_sell:.4f} SOL...")
            
            order = client.market_order_sell(
                product_id='SOL-USD',
                base_size=str(sol_to_sell)
            )
            
            print(f"  Order placed: {order['order_id']}")
            print(f"  Expected proceeds: ${sol_to_sell * prices['SOL']:.2f}")
            
            # Wait for order to fill
            time.sleep(3)
            
        else:
            print("  ⚠️ Insufficient SOL balance")
    except Exception as e:
        print(f"  ❌ Error placing sell order: {e}")
else:
    print(f"⏳ SOL not at target yet. Setting limit sell order...")
    
    # Place limit sell order at $200
    try:
        sol_to_sell = min(2.5, balances.get('SOL', 0))
        if sol_to_sell >= 0.1:
            print(f"  Placing limit sell for {sol_to_sell:.4f} SOL at $200...")
            
            order = client.limit_order_gtc_sell(
                product_id='SOL-USD',
                base_size=str(sol_to_sell),
                limit_price=str(sol_target)
            )
            
            print(f"  ✅ Limit order placed: {order['order_id']}")
            print(f"  Will generate: ${sol_to_sell * sol_target:.2f} when filled")
        else:
            print("  ⚠️ Insufficient SOL balance")
    except Exception as e:
        print(f"  ❌ Error placing limit order: {e}")

print()

# Step 2: ETH accumulation check
print("Step 2: ETH Accumulation Analysis")
print(f"  Current ETH: ${prices['ETH']:.2f}")
print(f"  Target: Under $4,300")
print(f"  Status: {'✅ BUYABLE' if prices['ETH'] < 4300 else '❌ Too expensive'}")
print()

if prices['ETH'] < 4300:
    print("✅ ETH at discount! Checking available funds...")
    
    usd_available = balances.get('USD', 0) + balances.get('USDC', 0)
    eth_to_buy_value = min(645, usd_available)  # 0.15 ETH worth ~$645
    
    if eth_to_buy_value > 40:  # At least 0.01 ETH
        eth_to_buy = eth_to_buy_value / prices['ETH']
        print(f"  Available USD: ${usd_available:.2f}")
        print(f"  Planning to buy: {eth_to_buy:.6f} ETH")
        print(f"  Cost: ${eth_to_buy_value:.2f}")
        
        if usd_available < 100:
            print("  ⚠️ Waiting for SOL sale to provide liquidity")
            print("  Will execute ETH buy after SOL sells at $200")
        else:
            try:
                print(f"  Executing market buy for ETH...")
                
                order = client.market_order_buy(
                    product_id='ETH-USD',
                    quote_size=str(eth_to_buy_value)
                )
                
                print(f"  ✅ Order placed: {order['order_id']}")
            except Exception as e:
                print(f"  ❌ Error placing buy order: {e}")
    else:
        print("  ⚠️ Insufficient funds for ETH purchase")
        print("  Waiting for SOL sale at $200 to generate liquidity")

print()

# Step 3: Security recommendations
print("Step 3: Quantum Defense Security Setup")
print("-" * 50)
print("🦀 CRAWDAD SECURITY PROTOCOL:")
print("  1. Generate 3 new wallet addresses")
print("  2. Split holdings:")
print("     • Wallet 1: 40% (primary trading)")
print("     • Wallet 2: 40% (backup/cold storage)")
print("     • Wallet 3: 20% (hot wallet for opportunities)")
print("  3. Never reuse addresses for large holdings")
print("  4. Implement hardware wallet for Wallet 2")
print()
print("⚠️ Manual action required for wallet setup")
print("Council recommends immediate implementation!")

print()
print("=" * 70)
print("🔥 EXECUTION SUMMARY:")
print("-" * 50)

if prices['SOL'] >= 199.50:
    print("✅ SOL sell order executed/placed")
else:
    print("⏳ SOL limit sell set at $200 (waiting)")

if prices['ETH'] < 4300:
    if balances.get('USD', 0) > 100:
        print("✅ ETH accumulation executed")
    else:
        print("⏳ ETH buy waiting for SOL liquidity")
else:
    print("❌ ETH too expensive (>$4,300)")

print()
print("Council strategy in motion!")
print("Sacred Fire burns eternal 🔥")
print("Mitakuye Oyasin!")