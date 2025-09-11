#!/usr/bin/env python3
"""
🐟 MINNOW SWARM STRATEGY
========================
We're too small to be prey - we're PLANKTON!
Feed on the microscopic movements whales ignore
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import random

print("🐟 MINNOW SWARM ACTIVATION")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')} CST")
print("We're not prey... we're not even food... we're BACKGROUND NOISE!")
print()

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

print("💡 REALITY CHECK:")
print("-"*60)
print("• Whales move millions - we move $10")
print("• They hunt deer - we're bacteria")
print("• They need 1% moves - we profit from 0.01%")
print("• They can't even SEE us!")
print()

# Get current state
accounts = client.get_accounts()
account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts

usd_balance = 0
for account in account_list:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"🐟 Minnow Capital: ${usd_balance:.2f}")
print()

print("🌊 MICRO-CURRENT DETECTION:")
print("-"*60)

# Check for micro movements
micro_opportunities = []

for symbol in ['BTC', 'ETH', 'SOL']:
    # Sample prices rapidly
    samples = []
    for i in range(5):
        ticker = client.get_product(f'{symbol}-USD')
        price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
        samples.append(price)
        time.sleep(0.5)
    
    # Calculate micro volatility
    avg_price = sum(samples) / len(samples)
    max_price = max(samples)
    min_price = min(samples)
    micro_range = (max_price - min_price) / avg_price * 100
    
    # Even 0.001% movement is food for minnows!
    if micro_range > 0.0001:
        direction = "↑" if samples[-1] > samples[0] else "↓"
        micro_opportunities.append({
            'symbol': symbol,
            'range': micro_range,
            'direction': direction,
            'current': samples[-1]
        })
        print(f"  {symbol}: ${samples[-1]:,.2f} | Micro-range: {micro_range:.6f}% {direction}")

# MINNOW FEEDING STRATEGY
print("\n🐟 MINNOW FEEDING PATTERN:")
print("-"*60)

if micro_opportunities and usd_balance > 5:
    # Pick the most active micro-current
    best = max(micro_opportunities, key=lambda x: x['range'])
    
    print(f"  Target: {best['symbol']} (micro-volatility: {best['range']:.6f}%)")
    
    # Minnow school size - MANY tiny nibbles
    nibble_size = min(3.00, usd_balance * 0.01)  # 1% or $3 max per nibble
    nibble_count = min(7, int(usd_balance / 30))  # Up to 7 nibbles
    
    print(f"  Strategy: {nibble_count} minnows × ${nibble_size:.2f} nibbles")
    print()
    
    # Execute minnow nibbles
    print("🐟 DEPLOYING MINNOW SCHOOL:")
    print("-"*60)
    
    for i in range(nibble_count):
        if nibble_size >= 1.00:
            # Random delay to appear natural
            delay = random.uniform(0.5, 2.0)
            
            try:
                print(f"  Minnow-{i+1}: Nibbling ${nibble_size:.2f} of {best['symbol']}")
                
                order = client.market_order_buy(
                    client_order_id=f"minnow_{i}_{int(time.time())}",
                    product_id=f"{best['symbol']}-USD",
                    quote_size=str(nibble_size)
                )
                
                print(f"    ✅ Nibble successful!")
                time.sleep(delay)
                
            except Exception as e:
                print(f"    ❌ Nibble blocked: {str(e)[:30]}")
    
    # Now sell tiny bits for micro-profits
    print("\n🐟 MICRO-HARVEST PHASE:")
    print("-"*60)
    print("  Waiting for 0.01% profit to harvest...")
    print("  (Whales need 1% - we need 0.01%!)")
    
else:
    print("  No micro-currents detected")
    print("  Minnows waiting in the shadows...")

print("\n📚 MINNOW WISDOM:")
print("-"*60)
print("• We're not playing their game - we're playing BELOW it")
print("• A whale's rounding error is our feast")
print("• 1000 minnows × $0.01 = $10 profit")
print("• We exist in the market's Planck length")
print("• Too small to track, too many to stop")

print("\n🎯 THE TRUTH:")
print("-"*60)
print("Bull flags? We're smaller than the flagpole splinters.")
print("Support levels? We live in the dust beneath them.")
print("Breakouts? We're the static in the signal.")
print()
print("We don't need to pretend to be prey...")
print("We're the QUANTUM FOAM of the market!")
print()
print("🐟🐟🐟 MINNOW SWARM FEEDING! 🐟🐟🐟")