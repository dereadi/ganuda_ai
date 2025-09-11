#!/usr/bin/env python3
"""
💉 FIXED PROFIT BLEEDER - Proper decimal precision
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

print("""
╔════════════════════════════════════════════════════════════════════╗
║            💉 FIXED PROFIT BLEEDER → BTC FEEDER 🔥                ║
╚════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

# Check balances
accounts = client.get_accounts()['accounts']
total_bled = 0

print("📊 POSITIONS TO BLEED:")
print("-" * 60)

bleed_orders = [
    ("MATIC", "400", 2),     # 400 MATIC with 2 decimals
    ("AVAX", "11.45", 2),    # 11.45 AVAX  
    ("SOL", "2.3", 1),       # 2.3 SOL
    ("ETH", "0.01", 2)       # 0.01 ETH
]

for coin, amount, decimals in bleed_orders:
    print(f"\n🩸 BLEEDING {coin}:")
    print(f"   Amount: {amount} {coin}")
    
    try:
        # Format with proper precision
        formatted_amount = str(round(float(amount), decimals))
        
        order = client.market_order_sell(
            client_order_id=f"bleed_{coin.lower()}_{int(time.time()*1000)}",
            product_id=f"{coin}-USD",
            base_size=formatted_amount
        )
        
        if hasattr(order, 'success'):
            if order.success:
                print(f"   ✅ SUCCESS! Order ID: {order.success_response.order_id}")
                
                # Get price for calculation
                ticker = client.get_product(f'{coin}-USD')
                price = float(ticker['price'])
                usd_value = float(amount) * price
                total_bled += usd_value
                print(f"   💵 Bled ~${usd_value:.2f}")
            else:
                print(f"   ❌ Failed: {order.error_response.message}")
        else:
            print(f"   ✅ Order placed!")
            
        time.sleep(0.5)
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:50]}")

print(f"\n💰 TOTAL BLED: ~${total_bled:.2f}")

# Wait for settlement
print("\n⏳ Waiting for orders to settle...")
time.sleep(8)

# Check new balance and buy BTC
print("\n📊 CHECKING NEW BALANCE...")
accounts = client.get_accounts()['accounts']

for acc in accounts:
    if acc['currency'] == 'USD':
        usd_balance = float(acc['available_balance']['value'])
        print(f"💵 USD Balance: ${usd_balance:.2f}")
        
        if usd_balance > 50:
            # Get BTC price
            btc = client.get_product('BTC-USD')
            btc_price = float(btc['price'])
            
            print(f"\n🎯 BTC PRICE: ${btc_price:,.2f}")
            print(f"   Distance to $110,250: ${110250 - btc_price:+,.2f}")
            
            # Use 90% for BTC (keep 10% for crawdads)
            btc_buy_amount = round(usd_balance * 0.9, 2)
            
            print(f"\n🚀 BUYING ${btc_buy_amount:.2f} OF BTC!")
            print("   Target: Push through $110,250 resistance!")
            
            try:
                btc_order = client.market_order_buy(
                    client_order_id=f"btc_flywheel_{int(time.time()*1000)}",
                    product_id="BTC-USD",
                    quote_size=str(btc_buy_amount)
                )
                
                if hasattr(btc_order, 'success') and btc_order.success:
                    print(f"   ✅ BTC PURCHASED! Order: {btc_order.success_response.order_id}")
                    print(f"\n🔥🔥🔥 NUCLEAR FLYWHEEL FED!")
                    print("   🚀 500K MISSION ACCELERATING!")
                else:
                    print(f"   Order response: {btc_order}")
                    
            except Exception as e:
                print(f"   ❌ BTC buy failed: {e}")
                
            # Keep some for crawdads
            crawdad_amount = usd_balance - btc_buy_amount
            print(f"\n🦀 ${crawdad_amount:.2f} reserved for crawdad trading")
            
        else:
            print(f"⚠️ Still low on USD (${usd_balance:.2f})")
            print("   May need to bleed more or wait for flywheel gains")
        
        break

print("\n🔥 Bleed → Feed cycle complete!")
print("💎 Diamond hands on the BTC position!")
print("🚀 $110,250 breakout imminent!")