#\!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🩸 URGENT LIQUIDITY HARVEST V2
DOGE is at $0.22 - bleed threshold reached\!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

def main():
    print("🩸 URGENT LIQUIDITY HARVEST")
    print("=" * 60)
    
    # Connect
    config = json.load(open('/home/dereadi/.coinbase_config.json'))
    key = config['api_key'].split('/')[-1]
    client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)
    
    # Check DOGE position
    accounts = client.get_accounts()
    for account in accounts['accounts']:
        if account['currency'] == 'DOGE':
            doge_balance = float(account['available_balance']['value'])
            print(f"DOGE Balance: {doge_balance:.2f}")
            
            ticker = client.get_product('DOGE-USD')
            doge_price = float(ticker['price'])
            print(f"DOGE Price: ${doge_price:.4f}")
            
            if doge_price >= 0.22 and doge_balance > 100:
                # Bleed 30% of DOGE
                bleed_amount = min(500, doge_balance * 0.3)
                bleed_amount = round(bleed_amount, 0)
                
                print(f"\n🩸 BLEEDING DOGE:")
                print(f"  Amount: {bleed_amount} DOGE")
                print(f"  Expected: ${bleed_amount * doge_price:.2f}")
                
                try:
                    order = client.market_order_sell(
                        client_order_id=client.generate_client_order_id(),
                        product_id='DOGE-USD',
                        base_size=str(bleed_amount)
                    )
                    
                    if order and 'success' in order and order['success']:
                        print(f"✅ DOGE bleed successful\!")
                        print(f"  Order ID: {order.get('order_id')}")
                        
                        # Check new USD balance
                        accounts = client.get_accounts()
                        for acc in accounts['accounts']:
                            if acc['currency'] == 'USD':
                                new_usd = float(acc['available_balance']['value'])
                                print(f"  New USD Balance: ${new_usd:.2f}")
                                break
                    else:
                        print(f"❌ Order failed: {order}")
                except Exception as e:
                    print(f"❌ Bleed failed: {e}")
            else:
                print("⚠️ Conditions not met for bleeding")
                print(f"  Price: ${doge_price:.4f} (need >= $0.22)")
                print(f"  Balance: {doge_balance:.2f} (need > 100)")
            break
    
    # Check if we need more liquidity from other sources
    for account in accounts['accounts']:
        if account['currency'] == 'USD':
            usd_balance = float(account['available_balance']['value'])
            print(f"\nCurrent USD: ${usd_balance:.2f}")
            
            if usd_balance < 100:
                print("⚠️ Still need more liquidity\!")
                print("Consider harvesting from SOL or ETH")
            break

if __name__ == "__main__":
    main()
