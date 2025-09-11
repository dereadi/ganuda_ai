#!/usr/bin/env python3
"""
🥛💀 MILK ALL ALTS AGGRESSIVELY
Continue the milking with ALL altcoins
Focus on non-core positions
Keep milking while the profits flow
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                 🥛💀 AGGRESSIVE ALT MILKING MODE 💀🥛                    ║
║                      Milk Every Alt For Maximum USD                       ║
║                         The Profits Must Flow                             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ALT MILK EXTRACTION")
print("=" * 70)

# Get all holdings
accounts = client.get_accounts()
alt_holdings = {}
usd_before = 0

print("\n🥛 IDENTIFYING ALT MILK SOURCES:")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_before = balance
        print(f"Current USD: ${balance:.2f}")
    elif balance > 0 and currency not in ['BTC', 'ETH']:  # Focus on alts
        try:
            # Get current price
            if currency == 'SOL':
                price = float(client.get_product('SOL-USD')['price'])
            elif currency == 'MATIC':
                price = float(client.get_product('MATIC-USD')['price'])
            elif currency == 'AVAX':
                price = float(client.get_product('AVAX-USD')['price'])
            elif currency == 'DOGE':
                price = float(client.get_product('DOGE-USD')['price'])
            elif currency == 'XRP':
                price = float(client.get_product('XRP-USD')['price'])
            elif currency == 'LINK':
                price = float(client.get_product('LINK-USD')['price'])
            else:
                continue
                
            value = balance * price
            if value > 5:  # Only milk if worth more than $5
                alt_holdings[currency] = {
                    "balance": balance,
                    "price": price,
                    "value": value
                }
                print(f"{currency}: {balance:.2f} = ${value:.2f}")
        except:
            pass

# Aggressive milking percentages for alts
milk_percentages = {
    "XRP": 0.15,    # 15% - we don't need much XRP
    "LINK": 0.15,   # 15% - small position
    "DOGE": 0.10,   # 10% - meme milk
    "MATIC": 0.05,  # 5% - already milked some
    "AVAX": 0.05,   # 5% - already milked some
    "SOL": 0.04,    # 4% - keep most SOL
}

print("\n💀 EXECUTING AGGRESSIVE ALT MILKING:")
print("-" * 50)

total_milked = 0
successful_milks = 0

# Execute milking for each alt
for currency, data in alt_holdings.items():
    balance = data['balance']
    price = data['price']
    value = data['value']
    
    # Get milking percentage
    milk_pct = milk_percentages.get(currency, 0.05)  # Default 5%
    milk_amount = balance * milk_pct
    milk_value = milk_amount * price
    
    # Only milk if value > $10 to beat fees
    if milk_value > 10:
        print(f"\n{currency}:")
        print(f"  Milking {milk_pct*100:.0f}% = {milk_amount:.4f} {currency}")
        print(f"  Expected: ${milk_value:.2f}")
        
        try:
            # Execute based on currency
            if currency == 'SOL' and milk_amount > 0.1:
                order = client.market_order_sell(
                    client_order_id=f"milk-alt-sol-{datetime.now().strftime('%H%M%S')}",
                    product_id='SOL-USD',
                    base_size=str(round(milk_amount, 3))
                )
                total_milked += milk_value
                successful_milks += 1
                print(f"  ✅ MILKED ${milk_value:.2f}")
                
            elif currency == 'MATIC' and milk_amount > 10:
                order = client.market_order_sell(
                    client_order_id=f"milk-alt-matic-{datetime.now().strftime('%H%M%S')}",
                    product_id='MATIC-USD',
                    base_size=str(int(milk_amount))
                )
                total_milked += milk_value
                successful_milks += 1
                print(f"  ✅ MILKED ${milk_value:.2f}")
                
            elif currency == 'AVAX' and milk_amount > 0.5:
                order = client.market_order_sell(
                    client_order_id=f"milk-alt-avax-{datetime.now().strftime('%H%M%S')}",
                    product_id='AVAX-USD',
                    base_size=str(round(milk_amount, 2))
                )
                total_milked += milk_value
                successful_milks += 1
                print(f"  ✅ MILKED ${milk_value:.2f}")
                
            elif currency == 'DOGE' and milk_amount > 50:
                order = client.market_order_sell(
                    client_order_id=f"milk-alt-doge-{datetime.now().strftime('%H%M%S')}",
                    product_id='DOGE-USD',
                    base_size=str(int(milk_amount))
                )
                total_milked += milk_value
                successful_milks += 1
                print(f"  ✅ MILKED ${milk_value:.2f}")
                
            elif currency == 'XRP' and milk_amount > 5:
                order = client.market_order_sell(
                    client_order_id=f"milk-alt-xrp-{datetime.now().strftime('%H%M%S')}",
                    product_id='XRP-USD',
                    base_size=str(round(milk_amount, 1))
                )
                total_milked += milk_value
                successful_milks += 1
                print(f"  ✅ MILKED ${milk_value:.2f}")
                
            elif currency == 'LINK' and milk_amount > 0.1:
                # Check if we have enough LINK
                if milk_amount > 0.1 and milk_value > 5:
                    # Small LINK position - milk what we can
                    actual_milk = min(milk_amount, balance * 0.5)  # Max 50% of small position
                    if actual_milk > 0.1:
                        print(f"  Adjusted: Milking {actual_milk:.2f} LINK")
                        order = client.market_order_sell(
                            client_order_id=f"milk-alt-link-{datetime.now().strftime('%H%M%S')}",
                            product_id='LINK-USD',
                            base_size=str(round(actual_milk, 2))
                        )
                        link_value = actual_milk * price
                        total_milked += link_value
                        successful_milks += 1
                        print(f"  ✅ MILKED ${link_value:.2f}")
            else:
                print(f"  ⚠️ Below minimum threshold")
                
            time.sleep(0.5)  # Small delay between orders
            
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:40]}")

# Check results
print("\n⏳ Collecting the milk...")
time.sleep(3)

accounts = client.get_accounts()
usd_after = 0

for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_after = float(account['available_balance']['value'])
        break

# Final report
print("\n" + "=" * 70)
print("🥛 ALT MILKING COMPLETE:")
print("-" * 50)
print(f"Alts milked: {successful_milks}")
print(f"Expected milk: ${total_milked:.2f}")
print(f"USD Before: ${usd_before:.2f}")
print(f"USD After: ${usd_after:.2f}")
print(f"Total milked: ${usd_after - usd_before:.2f}")

# Calculate total milk so far
print(f"\n💰 CUMULATIVE MILK SESSION:")
print(f"  Started at: $5.34")
print(f"  Now have: ${usd_after:.2f}")
print(f"  Total milk: ${usd_after - 5.34:.2f}")

# Crawdad status
print(f"\n🦀 CRAWDAD FUEL STATUS:")
print(f"  Per crawdad: ${usd_after/7:.2f}")

if usd_after > 500:
    print("  🥛🥛🥛 MAXIMUM MILK ACHIEVED!")
    print("  Crawdads swimming in profits!")
elif usd_after > 300:
    print("  🥛🥛 EXCELLENT MILK FLOW!")
    print("  Crawdads well fed!")
elif usd_after > 200:
    print("  🥛 Good milk supply!")
    print("  Keep milking!")
else:
    print("  📊 Adequate milk")
    print("  Continue monitoring")

# Check if we should continue
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"\n📊 MARKET CHECK:")
print(f"  BTC: ${btc:,.0f}")
print(f"  ETH: ${eth:.2f}")
print(f"  SOL: ${sol:.2f}")

print("\n🥛 CONTINUE THE MILKING")
print("   Alts are flowing")
print("   Profits secured")
print("   Ready for more")
print("=" * 70)