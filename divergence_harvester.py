#!/usr/bin/env python3
"""
🔄 DIVERGENCE HARVESTER
When assets move in opposite directions, we profit from both!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      🔄 DIVERGENCE HARVESTER ACTIVE 🔄                    ║
║                   SOL climbing while others bounce = PROFIT               ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

def execute_divergence_trade():
    """Execute divergence strategy"""
    
    # Get current prices
    sol = client.get_product('SOL-USD')
    btc = client.get_product('BTC-USD')
    eth = client.get_product('ETH-USD')
    
    sol_price = float(sol['price'])
    btc_price = float(btc['price'])
    eth_price = float(eth['price'])
    
    print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} DIVERGENCE CHECK:")
    print("-" * 40)
    
    # SOL climbing strategy
    if sol_price > 206.00:
        print(f"🚀 SOL at ${sol_price:.2f} - TAKING PROFITS")
        try:
            # Sell small amount of SOL
            order = client.market_order_sell(
                client_order_id=f"div_sol_{int(time.time()*1000)}",
                product_id="SOL-USD",
                base_size="0.25"  # Small amount
            )
            profit = 0.25 * sol_price
            print(f"   ✅ Sold 0.25 SOL for ${profit:.2f}")
        except Exception as e:
            print(f"   ⚠️ SOL sell failed: {str(e)[:30]}")
    
    # BTC/ETH bounce strategy
    if btc_price < 111600:
        print(f"🏀 BTC at ${btc_price:,.2f} - BUYING BOUNCE")
        try:
            # Buy small amount on bounce
            order = client.market_order_buy(
                client_order_id=f"div_btc_{int(time.time()*1000)}",
                product_id="BTC-USD",
                quote_size="20"  # $20 position
            )
            print(f"   ✅ Bought $20 of BTC on bounce")
        except Exception as e:
            print(f"   ⚠️ BTC buy failed: {str(e)[:30]}")
    
    if eth_price < 4510:
        print(f"🏀 ETH at ${eth_price:.2f} - BUYING BOUNCE")
        try:
            order = client.market_order_buy(
                client_order_id=f"div_eth_{int(time.time()*1000)}",
                product_id="ETH-USD",
                quote_size="20"  # $20 position
            )
            print(f"   ✅ Bought $20 of ETH on bounce")
        except Exception as e:
            print(f"   ⚠️ ETH buy failed: {str(e)[:30]}")
    
    return sol_price, btc_price, eth_price

# Main monitoring loop
print("\n📊 MONITORING DIVERGENCE PATTERNS...")
print("=" * 60)

cycles = 0
sol_high = 205.00
btc_low = 112000
eth_low = 4530

while cycles < 50:
    cycles += 1
    
    sol_p, btc_p, eth_p = execute_divergence_trade()
    
    # Track extremes
    if sol_p > sol_high:
        sol_high = sol_p
        print(f"   📈 SOL NEW HIGH: ${sol_high:.2f}")
    
    if btc_p < btc_low:
        btc_low = btc_p
        print(f"   📉 BTC NEW LOW: ${btc_low:,.2f}")
    
    if eth_p < eth_low:
        eth_low = eth_p
        print(f"   📉 ETH NEW LOW: ${eth_low:.2f}")
    
    # Status update
    if cycles % 5 == 0:
        print(f"\n🔄 CYCLE {cycles}: SOL ${sol_p:.2f} | BTC ${btc_p:,.0f} | ETH ${eth_p:.0f}")
        
        # Check USD balance
        accounts = client.get_accounts()['accounts']
        for acc in accounts:
            if acc['currency'] == 'USD':
                usd = float(acc['available_balance']['value'])
                print(f"   💰 USD Balance: ${usd:.2f}")
                break
    
    time.sleep(30)  # Check every 30 seconds

print("\n" + "=" * 60)
print("📊 DIVERGENCE HARVEST COMPLETE")
print(f"SOL High: ${sol_high:.2f}")
print(f"BTC Low: ${btc_low:,.2f}")
print(f"ETH Low: ${eth_low:.2f}")
print("=" * 60)