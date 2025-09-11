#!/usr/bin/env python3
"""
🐕 DOGE MILK CHECK!
The meme lord might have some juice!
Let's see what the Shiba can provide
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🐕 DOGE MILK CHECK! 🐕                             ║
║                    Can the Shiba provide some juice?                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get DOGE info
accounts = client.get_accounts()
doge_balance = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
    elif currency == 'DOGE':
        doge_balance = balance

print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 70)

# Get DOGE price
try:
    doge_price = float(client.get_product('DOGE-USD')['price'])
    
    print(f"\n🐕 DOGE STATUS:")
    print("-" * 50)
    print(f"DOGE Balance: {doge_balance:.2f} DOGE")
    print(f"DOGE Price: ${doge_price:.4f}")
    print(f"Total Value: ${doge_balance * doge_price:.2f}")
    
    if doge_balance > 10:
        # Calculate milking options
        print(f"\n🥛 MILKING OPTIONS:")
        print("-" * 50)
        
        milk_percentages = [0.02, 0.03, 0.05, 0.10]
        
        for pct in milk_percentages:
            doge_to_sell = doge_balance * pct
            usd_value = doge_to_sell * doge_price
            
            if usd_value > 0.99:  # Minimum Coinbase fee threshold
                print(f"{int(pct*100)}% milk: {doge_to_sell:.2f} DOGE = ${usd_value:.2f}")
        
        # Recommend best option
        print(f"\n✅ RECOMMENDED MILK:")
        recommended_pct = 0.03
        recommended_doge = doge_balance * recommended_pct
        recommended_usd = recommended_doge * doge_price
        
        if recommended_usd > 0.99:
            print(f"Milk {recommended_doge:.2f} DOGE (3%)")
            print(f"Generate: ${recommended_usd:.2f}")
            print(f"New USD total: ${usd_balance + recommended_usd:.2f}")
            
            # Execute the milk?
            print(f"\n🐕 EXECUTING DOGE MILK...")
            try:
                order = client.market_order_sell(
                    client_order_id=f"doge-milk-{datetime.now().strftime('%H%M%S')}",
                    product_id='DOGE-USD',
                    base_size=str(round(recommended_doge, 2))
                )
                print(f"✅ MILKED {recommended_doge:.2f} DOGE!")
            except Exception as e:
                print(f"⚠️ Milk failed: {str(e)[:50]}")
        else:
            print(f"⚠️ Milk value too low (${recommended_usd:.2f} < $0.99 minimum)")
    else:
        print(f"\n⚠️ DOGE balance too low: {doge_balance:.2f} DOGE")
        print("  No significant milk available")
        
except Exception as e:
    print(f"\n❌ Error checking DOGE: {str(e)}")
    print("  DOGE might not be in portfolio")

print("\n" + "=" * 70)
print("🐕 Much milk, very profit, wow!")
print("=" * 70)