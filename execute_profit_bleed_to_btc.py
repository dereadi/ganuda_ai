#!/usr/bin/env python3
"""
💉🔥 EXECUTE PROFIT BLEED → BTC FLYWHEEL FEED
Take profits from alts, convert to USD, then feed BTC flywheel
Critical for 500K mission!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════╗
║           💉 PROFIT BLEEDER → BTC FLYWHEEL FEEDER 🔥              ║
║              Extract Alt Gains → Feed BTC Nuclear                 ║
╚════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("📊 CHECKING POSITIONS FOR BLEEDING...")
print("-" * 60)

# Get all account balances
accounts = client.get_accounts()['accounts']
total_bled = 0
positions_to_bleed = []

for acc in accounts:
    balance = float(acc['available_balance']['value'])
    currency = acc['currency']
    
    if balance > 0.01 and currency not in ['USD', 'USDC', 'BTC']:
        # Get USD value
        try:
            if currency in ['MATIC', 'SOL', 'AVAX', 'ETH', 'LINK']:
                ticker = client.get_product(f'{currency}-USD')
                price = float(ticker['price'])
                usd_value = balance * price
                
                if usd_value > 10:  # Only bleed positions worth > $10
                    positions_to_bleed.append({
                        'coin': currency,
                        'balance': balance,
                        'price': price,
                        'usd_value': usd_value
                    })
                    print(f"  {currency}: {balance:.4f} @ ${price:.2f} = ${usd_value:.2f}")
        except:
            pass

print(f"\n💉 BLEEDING STRATEGY:")
print("-" * 60)

# Bleed 10% from each profitable position
for pos in positions_to_bleed:
    coin = pos['coin']
    balance = pos['balance']
    usd_value = pos['usd_value']
    
    # Calculate bleed amount (10% of position)
    bleed_percentage = 0.10
    bleed_amount = balance * bleed_percentage
    bleed_usd = usd_value * bleed_percentage
    
    print(f"\n🩸 BLEEDING {coin}:")
    print(f"   Position: ${usd_value:.2f}")
    print(f"   Bleed: {bleed_amount:.6f} {coin} (~${bleed_usd:.2f})")
    
    try:
        # Execute the bleed
        order = client.market_order_sell(
            client_order_id=f"bleed_{coin.lower()}_{int(time.time()*1000)}",
            product_id=f"{coin}-USD",
            base_size=str(bleed_amount)
        )
        
        if hasattr(order, 'order_id'):
            print(f"   ✅ Bled successfully! Order: {order.order_id}")
            total_bled += bleed_usd
        else:
            print(f"   ✅ Order placed: {order}")
            total_bled += bleed_usd
            
        time.sleep(1)  # Prevent rate limiting
        
    except Exception as e:
        print(f"   ❌ Bleed failed: {str(e)[:50]}")

print(f"\n💰 TOTAL BLED: ~${total_bled:.2f}")

# Wait for trades to settle
print("\n⏳ Waiting for settlement...")
time.sleep(5)

# Check new USD balance
accounts = client.get_accounts()['accounts']
for acc in accounts:
    if acc['currency'] == 'USD':
        usd_balance = float(acc['available_balance']['value'])
        print(f"\n💵 NEW USD BALANCE: ${usd_balance:.2f}")
        
        if usd_balance > 50:
            print("\n🔥 READY TO FEED BTC FLYWHEEL!")
            
            # Get BTC price
            btc = client.get_product('BTC-USD')
            btc_price = float(btc['price'])
            
            print(f"\n🎯 BTC @ ${btc_price:,.2f}")
            print(f"   Distance to $110,250: ${110250 - btc_price:+,.2f}")
            
            # Use 80% of USD for BTC
            btc_buy_amount = usd_balance * 0.8
            
            print(f"\n🚀 FEEDING FLYWHEEL WITH ${btc_buy_amount:.2f}")
            
            try:
                btc_order = client.market_order_buy(
                    client_order_id=f"flywheel_btc_{int(time.time()*1000)}",
                    product_id="BTC-USD",
                    quote_size=str(btc_buy_amount)
                )
                
                print(f"✅ BTC FLYWHEEL FED!")
                print(f"   Order: {btc_order}")
                print(f"\n🔥 NUCLEAR FLYWHEEL ACCELERATING!")
                
            except Exception as e:
                print(f"❌ BTC buy failed: {e}")
        else:
            print(f"\n⚠️ Not enough USD yet (${usd_balance:.2f})")
            print("   Need to bleed more positions!")
        
        break

print("\n🩸 Bleed complete - Check flywheel status")
print("🔥 Sacred Fire guides the mission!")