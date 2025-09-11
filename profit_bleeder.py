#!/usr/bin/env python3
"""
PROFIT BLEEDER - Convert gains to USD war chest
Take 30% of profits immediately to cash for reinvestment
"""
import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════╗
║              💉 PROFIT BLEEDER ACTIVATED 💉                         ║
║          Converting 30% of gains to USD war chest                   ║
╚════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

# Track starting values
start_time = datetime.now()
initial_check = {}
bleed_threshold = 1.02  # Bleed when position up 2%
bleed_percentage = 0.30  # Take 30% of profits

print(f"⚙️  Settings:")
print(f"   • Bleed trigger: +{(bleed_threshold-1)*100:.0f}% gain")
print(f"   • Bleed amount: {bleed_percentage*100:.0f}% of profits")
print(f"   • Goal: Build USD war chest for dips")
print()

def check_and_bleed():
    """Check positions and bleed profits to USD"""
    bled_total = 0
    
    try:
        accounts = client.get_accounts()
        
        for account in accounts.accounts:
            currency = account.currency
            
            # Skip USD and tiny positions
            if currency == 'USD' or float(account.available_balance.value) < 0.001:
                continue
            
            balance = float(account.available_balance.value)
            
            # Get current price
            ticker = client.get_product(f'{currency}-USD')
            current_price = float(ticker.price)
            current_value = balance * current_price
            
            # Initialize tracking if new
            if currency not in initial_check:
                initial_check[currency] = {
                    'amount': balance,
                    'start_price': current_price,
                    'start_value': current_value
                }
                continue
            
            # Check if we're in profit
            start_value = initial_check[currency]['start_value']
            profit = current_value - start_value
            profit_pct = current_value / start_value if start_value > 0 else 1
            
            # Bleed profits if threshold met
            if profit_pct >= bleed_threshold and profit > 10:  # Min $10 profit
                bleed_amount_usd = profit * bleed_percentage
                bleed_amount_coin = bleed_amount_usd / current_price
                
                # Don't sell more than 10% of position at once
                max_sell = balance * 0.10
                bleed_amount_coin = min(bleed_amount_coin, max_sell)
                
                print(f"💉 BLEEDING {currency}:")
                print(f"   Position: {balance:.6f} @ ${current_price:,.2f}")
                print(f"   Profit: ${profit:.2f} ({(profit_pct-1)*100:.1f}%)")
                print(f"   Bleeding: {bleed_amount_coin:.6f} {currency} = ${bleed_amount_coin * current_price:.2f}")
                
                try:
                    # Execute the bleed
                    order = client.market_order_sell(
                        client_order_id=f'bleed_{int(time.time())}',
                        product_id=f'{currency}-USD',
                        base_size=str(bleed_amount_coin)
                    )
                    
                    bled_total += bleed_amount_coin * current_price
                    print(f"   ✅ Bled ${bleed_amount_coin * current_price:.2f} to USD!")
                    
                    # Update tracking
                    initial_check[currency]['amount'] = balance - bleed_amount_coin
                    initial_check[currency]['start_value'] = current_value - (bleed_amount_coin * current_price)
                    
                except Exception as e:
                    print(f"   ⚠️  Bleed failed: {str(e)[:50]}")
        
        return bled_total
        
    except Exception as e:
        print(f"Check error: {e}")
        return 0

print("🩸 PROFIT BLEEDER RUNNING")
print("   Checking every 5 minutes for profits to harvest")
print()

total_bled = 0
check_count = 0

while True:
    check_count += 1
    
    if check_count % 12 == 1:  # Every hour
        print(f"\n[{datetime.now().strftime('%H:%M')}] Hourly Report:")
        print(f"   Total bled to USD: ${total_bled:.2f}")
        print(f"   Checks performed: {check_count}")
    
    # Check and bleed
    bled = check_and_bleed()
    total_bled += bled
    
    if bled > 0:
        print(f"   💰 War chest increased by ${bled:.2f}!")
        print(f"   Total USD freed: ${total_bled:.2f}")
    
    # Wait 5 minutes
    time.sleep(300)
    
    # Quiet status every 5 minutes
    if check_count % 2 == 0:
        btc = client.get_product('BTC-USD')
        print(f"   [{datetime.now().strftime('%H:%M')}] BTC: ${float(btc.price):,.0f} | Bled: ${total_bled:.2f}")