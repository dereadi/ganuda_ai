#!/usr/bin/env python3
"""
DIRECT EXECUTION - Greeks Solar Rebalancing
"""
import json
import time
from coinbase.rest import RESTClient

print("🏛️ EXECUTING GREEKS REBALANCING...")

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

client = RESTClient(
    api_key=api_data['name'].split('/')[-1],
    api_secret=api_data['privateKey']
)

# Execute trades in order of priority
trades = [
    ('MATIC-USD', '2455', 'MATIC liquidation'),
    ('AVAX-USD', '14.67', 'AVAX trim'),
    ('SOL-USD', '2.99', 'SOL partial'),
    ('DOGE-USD', '6018', 'DOGE full exit')
]

results = []
for product_id, amount, desc in trades:
    try:
        print(f"\n🔄 {desc}: Selling {amount} {product_id.split('-')[0]}...")
        
        order = client.market_order_sell(
            client_order_id=f"greek_{int(time.time())}",
            product_id=product_id,
            base_size=amount
        )
        
        if order and 'order_id' in order:
            print(f"✅ SUCCESS: Order {order['order_id']}")
            results.append({'coin': product_id, 'status': 'success', 'order_id': order['order_id']})
        else:
            print(f"⚠️ Order response: {order}")
            results.append({'coin': product_id, 'status': 'failed'})
            
        time.sleep(2)  # Rate limiting
        
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
        results.append({'coin': product_id, 'status': 'error', 'error': str(e)[:100]})

# Check new balance
time.sleep(5)
accounts = client.get_accounts()['accounts']
for account in accounts:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        print(f"\n💰 NEW USD BALANCE: ${usd_balance:,.2f}")
        break

print("\n📊 TRADE RESULTS:")
for r in results:
    print(f"  {r['coin']}: {r['status']}")

print("\n🔥 Rebalancing complete! Ready for solar volatility!")