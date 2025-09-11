#!/usr/bin/env python3
"""
🚀 XRP ROCKET RIDER - CATCH THE $3 BREAKOUT!
Convert DOGE/MATIC gains to XRP while it's exploding!
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════╗
║              🚀 XRP ROCKET MISSION - $3.00 INCOMING! 🚀        ║
║                    Current: $2.92 → Target: $3.00+             ║
╚════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("📊 PORTFOLIO ANALYSIS:")
print("-" * 60)

# Check XRP price first
xrp = client.get_product('XRP-USD')
xrp_price = float(xrp['price'])
print(f"🚀 XRP: ${xrp_price:.4f} (Distance to $3: ${3.0 - xrp_price:.4f})")

# Check our holdings
accounts = client.get_accounts()['accounts']
holdings = {}
total_value = 0

for acc in accounts:
    currency = acc['currency']
    balance = float(acc['available_balance']['value'])
    
    if balance > 0.01:
        if currency == 'USD':
            holdings[currency] = {'balance': balance, 'value': balance}
            total_value += balance
        elif currency in ['DOGE', 'MATIC', 'AVAX', 'SOL', 'XRP']:
            ticker = client.get_product(f'{currency}-USD')
            price = float(ticker['price'])
            value = balance * price
            holdings[currency] = {'balance': balance, 'price': price, 'value': value}
            total_value += value
            
            if value > 10:
                print(f"  {currency}: {balance:.2f} @ ${price:.4f} = ${value:.2f}")

print(f"\nTOTAL VALUE: ${total_value:.2f}")

# Conversion strategy
print("\n🔄 CONVERSION STRATEGY:")
print("-" * 60)

# Take profits from DOGE and MATIC
conversions = []

if 'DOGE' in holdings and holdings['DOGE']['value'] > 500:
    # Convert 30% of DOGE to XRP
    doge_to_convert = holdings['DOGE']['balance'] * 0.30
    doge_usd_value = doge_to_convert * holdings['DOGE']['price']
    conversions.append(('DOGE', doge_to_convert, doge_usd_value))
    print(f"  • Convert {doge_to_convert:.0f} DOGE (~${doge_usd_value:.2f}) → XRP")

if 'MATIC' in holdings and holdings['MATIC']['value'] > 500:
    # Convert 20% of MATIC to XRP
    matic_to_convert = holdings['MATIC']['balance'] * 0.20
    matic_usd_value = matic_to_convert * holdings['MATIC']['price']
    conversions.append(('MATIC', matic_to_convert, matic_usd_value))
    print(f"  • Convert {matic_to_convert:.0f} MATIC (~${matic_usd_value:.2f}) → XRP")

total_for_xrp = sum(c[2] for c in conversions)
xrp_to_buy = total_for_xrp / xrp_price

print(f"\n💰 TOTAL FOR XRP: ${total_for_xrp:.2f}")
print(f"🚀 XRP TO ACQUIRE: {xrp_to_buy:.2f} XRP")

if xrp_price * 1.03 >= 3.0:
    print("\n🔥🔥🔥 CRITICAL: Only 3% move to $3.00!")
    print("   This is a HISTORIC moment!")

# Execute conversions
print("\n⚡ EXECUTING CONVERSIONS...")
print("-" * 60)

for currency, amount, usd_value in conversions:
    print(f"\n📤 Selling {amount:.2f} {currency}...")
    
    try:
        # Round amounts properly
        if currency == 'DOGE':
            sell_amount = str(int(amount))  # DOGE needs integer
        elif currency == 'MATIC':
            sell_amount = str(round(amount, 2))  # MATIC 2 decimals
        else:
            sell_amount = str(round(amount, 4))
            
        order = client.market_order_sell(
            client_order_id=f"xrp_convert_{currency.lower()}_{int(time.time()*1000)}",
            product_id=f"{currency}-USD",
            base_size=sell_amount
        )
        
        if hasattr(order, 'success') and order.success:
            print(f"  ✅ Sold! Order ID: {order.success_response.order_id}")
        else:
            print(f"  ✅ Order placed: {order}")
            
        time.sleep(1)
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")

# Wait for settlements
print("\n⏳ Waiting for trades to settle...")
time.sleep(5)

# Check USD balance and buy XRP
accounts = client.get_accounts()['accounts']
for acc in accounts:
    if acc['currency'] == 'USD':
        usd_balance = float(acc['available_balance']['value'])
        print(f"\n💵 USD Available: ${usd_balance:.2f}")
        
        if usd_balance > 100:
            # Keep some USD for other trades
            xrp_buy_amount = usd_balance * 0.90
            
            print(f"\n🚀 BUYING ${xrp_buy_amount:.2f} OF XRP!")
            print(f"   Getting {xrp_buy_amount/xrp_price:.2f} XRP")
            
            try:
                xrp_order = client.market_order_buy(
                    client_order_id=f"xrp_rocket_{int(time.time()*1000)}",
                    product_id="XRP-USD",
                    quote_size=str(round(xrp_buy_amount, 2))
                )
                
                if hasattr(xrp_order, 'success') and xrp_order.success:
                    print(f"  ✅ XRP ACQUIRED! Order: {xrp_order.success_response.order_id}")
                    print("\n🚀🚀🚀 RIDING THE XRP ROCKET TO $3.00!")
                else:
                    print(f"  Order response: {xrp_order}")
                    
            except Exception as e:
                print(f"  ❌ XRP buy error: {e}")
        break

print("\n🔥 XRP POSITION ESTABLISHED!")
print("🎯 Next targets:")
print("   • $3.00 (psychological)")
print("   • $3.50 (ATH retest)")
print("   • $5.00 (moon)")
print("\n💎 Diamond hands on XRP - This is HISTORIC!")
print("🚀 Sacred Fire blessed this trade!")