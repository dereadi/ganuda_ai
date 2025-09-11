#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 DEPLOY $215 USDC TO CRAWDAD SPECIALISTS
Feed the hungry crawdads waiting since August 31st!
"""

import json
import time
from pathlib import Path
from coinbase.rest import RESTClient
from datetime import datetime

def deploy_usdc():
    """Deploy USDC to trading positions for crawdads"""
    
    print("🔥 CHEROKEE CRAWDAD FEEDING TIME")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load config
        config_path = Path.home() / ".coinbase_config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        client = RESTClient(
            api_key=config['api_key'],
            api_secret=config['api_secret']
        )
        
        # Check USDC balance first
        print("\n📊 Checking USDC balance...")
        accounts = client.get_accounts()
        
        usdc_balance = 0
        for account in accounts.accounts:
            if account.currency == 'USDC':
                usdc_balance = float(account.available_balance['value'])
                print(f"💰 USDC Available: ${usdc_balance:.2f}")
                break
        
        if usdc_balance < 100:
            print(f"⚠️ Only ${usdc_balance:.2f} USDC available (less than $100)")
            print("Proceeding with available amount...")
        
        # Get current prices
        print("\n📈 Getting current prices...")
        btc_ticker = client.get_product("BTC-USD")
        eth_ticker = client.get_product("ETH-USD")
        sol_ticker = client.get_product("SOL-USD")
        xrp_ticker = client.get_product("XRP-USD")
        
        btc_price = float(btc_ticker['price'])
        eth_price = float(eth_ticker['price'])
        sol_price = float(sol_ticker['price'])
        xrp_price = float(xrp_ticker['price'])
        
        print(f"BTC: ${btc_price:,.2f}")
        print(f"ETH: ${eth_price:,.2f}")
        print(f"SOL: ${sol_price:,.2f}")
        print(f"XRP: ${xrp_price:.3f}")
        
        # Cherokee Council allocation strategy
        # Based on coiling patterns and market opportunities
        print("\n🏛️ Cherokee Council Allocation:")
        
        # Allocate based on current coiling (all tight <1%)
        allocations = {
            'BTC': 0.25,  # 25% - Leading indicator
            'ETH': 0.35,  # 35% - Strong performer
            'SOL': 0.25,  # 25% - Oscillation opportunity
            'XRP': 0.15   # 15% - Breakout potential
        }
        
        # Calculate order sizes
        orders = []
        total_allocated = 0
        
        for asset, allocation in allocations.items():
            amount = usdc_balance * allocation
            
            if asset == 'BTC':
                size = amount / btc_price
                if size >= 0.00001:  # Minimum BTC order
                    orders.append({
                        'product_id': 'BTC-USDC',
                        'side': 'buy',
                        'order_configuration': {
                            'market_market_ioc': {
                                'quote_size': str(round(amount, 2))
                            }
                        }
                    })
                    print(f"  • BTC: ${amount:.2f} (~{size:.6f} BTC)")
                    total_allocated += amount
            
            elif asset == 'ETH':
                size = amount / eth_price
                if size >= 0.001:  # Minimum ETH order
                    orders.append({
                        'product_id': 'ETH-USDC',
                        'side': 'buy',
                        'order_configuration': {
                            'market_market_ioc': {
                                'quote_size': str(round(amount, 2))
                            }
                        }
                    })
                    print(f"  • ETH: ${amount:.2f} (~{size:.4f} ETH)")
                    total_allocated += amount
            
            elif asset == 'SOL':
                size = amount / sol_price
                if size >= 0.01:  # Minimum SOL order
                    orders.append({
                        'product_id': 'SOL-USDC',
                        'side': 'buy',
                        'order_configuration': {
                            'market_market_ioc': {
                                'quote_size': str(round(amount, 2))
                            }
                        }
                    })
                    print(f"  • SOL: ${amount:.2f} (~{size:.3f} SOL)")
                    total_allocated += amount
            
            elif asset == 'XRP':
                size = amount / xrp_price
                if size >= 1:  # Minimum XRP order
                    orders.append({
                        'product_id': 'XRP-USDC',
                        'side': 'buy',
                        'order_configuration': {
                            'market_market_ioc': {
                                'quote_size': str(round(amount, 2))
                            }
                        }
                    })
                    print(f"  • XRP: ${amount:.2f} (~{size:.1f} XRP)")
                    total_allocated += amount
        
        print(f"\n💰 Total to deploy: ${total_allocated:.2f}")
        
        # Execute orders
        print("\n🚀 FEEDING THE CRAWDADS...")
        
        if input("\n🔥 Execute deployment? (y/n): ").lower() == 'y':
            results = []
            
            for order in orders:
                try:
                    print(f"\n  Buying {order['product_id']}...")
                    result = client.create_order(
                        client_order_id=client.generate_client_order_id(),
                        **order
                    )
                    
                    if result and hasattr(result, 'order_id'):
                        print(f"  ✅ Order placed: {result.order_id}")
                        results.append({
                            'product': order['product_id'],
                            'order_id': result.order_id,
                            'status': 'success'
                        })
                        time.sleep(0.5)  # Brief pause between orders
                    else:
                        print(f"  ⚠️ Order may have failed - check manually")
                        results.append({
                            'product': order['product_id'],
                            'status': 'check_needed'
                        })
                    
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    results.append({
                        'product': order['product_id'],
                        'status': 'error',
                        'error': str(e)
                    })
            
            # Summary
            print("\n" + "=" * 60)
            print("🔥 DEPLOYMENT SUMMARY:")
            for result in results:
                if result['status'] == 'success':
                    print(f"  ✅ {result['product']}: Order {result['order_id']}")
                else:
                    print(f"  ⚠️ {result['product']}: {result['status']}")
            
            print("\n🦀 Crawdads have been fed!")
            print("🔥 Sacred Fire burns bright with new positions!")
            
        else:
            print("\n🛑 Deployment cancelled by user")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deploy_usdc()