#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🐋 EXECUTE WHALE FOLLOW STRATEGY
Bleed positions to build DOGE while whales accumulate
"""

import json
import time
from coinbase.rest import RESTClient

print("🐋 EXECUTING WHALE FOLLOW STRATEGY")
print("=" * 60)

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

# Small bleeds from MATIC and AVAX for DOGE building
bleed_targets = {
    'MATIC': 0.03,  # Bleed 3%
    'AVAX': 0.03    # Bleed 3%
}

total_generated = 0

for coin, bleed_pct in bleed_targets.items():
    print(f"\n{coin} BLEED:")
    
    # Get position
    accounts = client.get_accounts()
    position = 0
    for account in accounts['accounts']:
        if account['currency'] == coin:
            position = float(account['available_balance']['value'])
            break
    
    if position > 0:
        ticker = client.get_product(f'{coin}-USD')
        price = float(ticker['price'])
        
        bleed_amount = round(position * bleed_pct, 2)
        bleed_value = bleed_amount * price
        
        print(f"  Position: {position:.2f} {coin}")
        print(f"  Bleeding: {bleed_amount:.2f} {coin} (3%)")
        print(f"  Value: ${bleed_value:.2f}")
        
        if bleed_value > 10:
            try:
                order = client.market_order_sell(
                    client_order_id=f"whale_prep_{coin}_{int(time.time()*1000)}",
                    product_id=f"{coin}-USD",
                    base_size=str(bleed_amount)
                )
                print(f"  ✅ Generated ${bleed_value:.2f}")
                total_generated += bleed_value
            except Exception as e:
                print(f"  ❌ Failed: {str(e)[:50]}")

print(f"\n💵 Total Generated: ${total_generated:.2f}")

# Wait for settlement
print("\nWaiting 10 seconds for settlement...")
time.sleep(10)

# Now build DOGE position
print("\n🩸 BUILDING DOGE BLOOD BAG:")
print("-" * 40)

# Get updated USD balance
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"USD Available: ${usd_balance:.2f}")

if usd_balance > 20:
    # Use 80% for DOGE
    doge_buy_amount = usd_balance * 0.8
    
    ticker = client.get_product('DOGE-USD')
    doge_price = float(ticker['price'])
    doge_units = doge_buy_amount / doge_price
    
    print(f"DOGE Price: ${doge_price:.4f}")
    print(f"Buying: {doge_units:.0f} DOGE with ${doge_buy_amount:.2f}")
    
    try:
        order = client.market_order_buy(
            client_order_id=f"whale_follow_{int(time.time()*1000)}",
            product_id="DOGE-USD",
            quote_size=str(doge_buy_amount)
        )
        print(f"✅ BLOOD BAG BUILT: {doge_units:.0f} DOGE")
        print("\n🐋 Now following the whales!")
        print("📈 Ready to bleed at $0.22+")
    except Exception as e:
        print(f"❌ Failed to build: {str(e)[:50]}")

print("\n" + "=" * 60)
print("🔥 Whale follow strategy executed")
print("🩸 Blood bags ready for the pump")
print("🐋 Swimming with the giants")
print("=" * 60)