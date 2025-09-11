#!/usr/bin/env python3
"""
🚗 ETH VOLUME DRIVER
ETH is leading the market with volume - ride the wave!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                       🚗 ETH VOLUME DRIVER ACTIVE 🚗                      ║
║                    ETH leading with volume = OPPORTUNITY                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

# Get ETH price and deploy
eth_ticker = client.get_product('ETH-USD')
eth_price = float(eth_ticker['price'])

print(f"🚗 ETH DRIVING at ${eth_price:.2f}")
print("=" * 70)

# AGGRESSIVE ETH STRATEGY
strategies = [
    {
        "action": "buy",
        "amount": 150,
        "trigger": eth_price < 4520,
        "reason": "ETH volume surge - ride momentum"
    },
    {
        "action": "buy", 
        "amount": 100,
        "trigger": eth_price < 4515,
        "reason": "ETH dip with volume = spring loading"
    },
    {
        "action": "buy",
        "amount": 50,
        "trigger": eth_price < 4510,
        "reason": "Deep dip = aggressive accumulation"
    }
]

deployed = 0

for strat in strategies:
    if strat['trigger']:
        print(f"\n🎯 TRIGGER HIT: {strat['reason']}")
        print(f"   Deploying ${strat['amount']} into ETH...")
        
        try:
            order = client.market_order_buy(
                client_order_id=f"eth_vol_{int(time.time()*1000)}",
                product_id="ETH-USD",
                quote_size=str(strat['amount'])
            )
            deployed += strat['amount']
            print(f"   ✅ DEPLOYED! ETH position increased")
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:50]}")

# Also catch correlated moves
print("\n🔄 CORRELATION TRADES:")
print("-" * 40)

# If ETH driving, others follow
if deployed > 0:
    # BTC usually follows ETH volume
    print("📊 BTC correlation play...")
    try:
        btc_order = client.market_order_buy(
            client_order_id=f"btc_cor_{int(time.time()*1000)}",
            product_id="BTC-USD",
            quote_size="100"
        )
        print("   ✅ $100 into BTC (follows ETH)")
        deployed += 100
    except:
        pass
    
    # Small caps amplify ETH moves
    print("🚀 Small cap amplification...")
    try:
        avax_order = client.market_order_buy(
            client_order_id=f"avax_amp_{int(time.time()*1000)}",
            product_id="AVAX-USD",
            quote_size="50"
        )
        print("   ✅ $50 into AVAX (amplifies ETH)")
        deployed += 50
    except:
        pass

print("\n" + "=" * 70)
print(f"💰 TOTAL DEPLOYED: ${deployed:.2f}")
print(f"🎯 Strategy: Ride ETH volume leadership")
print(f"📈 Target: +2-3% on volume surge")
print("=" * 70)

# Monitor for 1 minute
print("\n📊 MONITORING ETH DRIVE...")
for i in range(6):
    time.sleep(10)
    eth = client.get_product('ETH-USD')
    new_price = float(eth['price'])
    change = new_price - eth_price
    pct = (change / eth_price) * 100
    
    print(f"\r⏰ {datetime.now().strftime('%H:%M:%S')} ETH: ${new_price:.2f} ({pct:+.2f}%)", end="")

print("\n\n✅ ETH VOLUME DRIVER POSITIONED")
print("Let the volume drive profits!")