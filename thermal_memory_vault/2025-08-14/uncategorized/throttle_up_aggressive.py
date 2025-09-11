#!/usr/bin/env python3
"""
🚀 THROTTLE UP - AGGRESSIVE MODE
=================================
Time to stop being scared and START EATING!
Peak Asia in 1 hour - LET'S GO!
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import random

print("🚀 THROTTLE UP - PRESSING THE GAS!")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M')} - PEAK ASIA IN 1 HOUR!")
print("ENOUGH BEING SCARED - TIME TO EAT!")
print()

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

# Get current status
accounts = client.get_accounts()
account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts

usd_balance = 0
for account in account_list:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"💰 USD Available: ${usd_balance:.2f}")
print(f"🎯 Target: Deploy 20-30% before 2100!")
print()

# AGGRESSIVE PARAMETERS
THROTTLE = 60  # 60% throttle - GO TIME!
TRADE_PERCENT = 0.05  # 5% per trade
MAX_TRADES = 10  # Up to 10 trades

print("⚡ AGGRESSIVE SETTINGS:")
print(f"  Throttle: {THROTTLE}%")
print(f"  Trade Size: {TRADE_PERCENT*100}% of balance")
print(f"  Max Trades: {MAX_TRADES}")
print()

print("🟡 EXECUTING AGGRESSIVE PAC-MAN STRATEGY:")
print("-"*60)

trades_executed = 0
total_deployed = 0

# Focus on most volatile asset - SOL
symbols = ['SOL', 'ETH', 'SOL', 'BTC', 'SOL']  # Favor SOL

for i, symbol in enumerate(symbols):
    if trades_executed >= MAX_TRADES:
        break
        
    if usd_balance < 10:
        print("  USD too low, stopping")
        break
    
    # Calculate trade size
    trade_size = min(usd_balance * TRADE_PERCENT, 25.00)  # Max $25 per trade
    trade_size = round(trade_size, 2)
    
    if trade_size < 1.00:
        continue
    
    print(f"\n🎯 Trade #{trades_executed + 1}: {symbol}")
    
    # Get current price
    ticker = client.get_product(f'{symbol}-USD')
    price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
    print(f"  Price: ${price:.2f}")
    
    # Ghost check - but be LESS scared
    time.sleep(0.2)
    ticker2 = client.get_product(f'{symbol}-USD')
    price2 = float(ticker2.price if hasattr(ticker2, 'price') else ticker2.get('price', 0))
    
    movement = abs(price2 - price) / price
    
    if movement > 0.002:  # Only avoid if REALLY big ghost (was 0.001)
        print(f"  👻 BIG ghost detected ({movement*100:.3f}%) - skipping")
        continue
    
    # EXECUTE TRADE - NO MORE FEAR!
    try:
        print(f"  🟡 GOBBLING ${trade_size:.2f} of {symbol}!")
        
        order = client.market_order_buy(
            client_order_id=f"aggressive_{symbol}_{int(time.time())}",
            product_id=f"{symbol}-USD",
            quote_size=str(trade_size)
        )
        
        print(f"  ✅ WAKA WAKA! Gobbled ${trade_size:.2f}")
        trades_executed += 1
        total_deployed += trade_size
        usd_balance -= trade_size
        
        # Brief pause between trades
        time.sleep(random.uniform(2, 4))
        
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:50]}")
        continue

print("\n" + "="*60)
print("🚀 AGGRESSIVE SESSION COMPLETE!")
print("-"*60)
print(f"  Trades Executed: {trades_executed}")
print(f"  Total Deployed: ${total_deployed:.2f}")
print(f"  USD Remaining: ${usd_balance:.2f}")

if trades_executed > 5:
    print("\n🔥 THROTTLE SUCCESS - WE'RE ACCELERATING!")
elif trades_executed > 0:
    print("\n✅ Good start - keep pushing!")
else:
    print("\n⚠️ Too cautious - need MORE GAS!")

print("\n📊 NEXT STEPS:")
print("-"*60)
print("• Continue aggressive trading until 2100")
print("• Peak Asia window: 2100-2300 (MAX THROTTLE)")
print("• Monitor for quick profits")
print("• Be ready to take gains if we spike")

print("\n🟡 PAC-MAN CRAWDADS ACTIVATED!")
print("   NO MORE FEAR!")
print("   WAKA WAKA WAKA!")
print("   🚀 FULL SPEED AHEAD! 🚀")