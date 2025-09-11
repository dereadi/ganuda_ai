#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 Execute XRP Accumulation Strategy
Cherokee Trading Council - September 1, 2025
Generate liquidity and build XRP position
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient
import time

def execute_xrp_strategy():
    """Generate liquidity and buy XRP"""
    
    print("🔥 CHEROKEE TRADING COUNCIL - XRP ACCUMULATION")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Load API config
        with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
            config = json.load(f)
        
        client = RESTClient(
            api_key=config['name'].split('/')[-1],
            api_secret=config['privateKey'],
            timeout=10
        )
        
        print("📊 CURRENT POSITIONS:")
        print("-" * 40)
        
        # Get current balances
        response = client.get_accounts()
        if hasattr(response, 'accounts'):
            accounts = response.accounts
        else:
            accounts = response.get('accounts', response)
        
        positions = {}
        for account in accounts:
            if hasattr(account, 'currency'):
                currency = account.currency
                if hasattr(account.available_balance, 'value'):
                    available = float(account.available_balance.value)
                else:
                    available = float(account.available_balance.get('value', 0))
                
                if available > 0.00001:
                    positions[currency] = available
        
        print(f"  USD Available: ${positions.get('USD', 0):.2f}")
        print(f"  SOL: {positions.get('SOL', 0):.4f}")
        print(f"  AVAX: {positions.get('AVAX', 0):.4f}")
        print(f"  XRP Current: {positions.get('XRP', 0):.4f}")
        print()
        
        # Strategy: Generate $300 for XRP purchase
        print("🎯 LIQUIDITY GENERATION PLAN:")
        print("-" * 40)
        
        orders = []
        
        # Option 1: Trim SOL position (1.5 SOL = ~$300)
        if positions.get('SOL', 0) > 2:
            sol_to_sell = min(1.5, positions.get('SOL', 0) * 0.2)  # Max 20% of SOL
            print(f"  1. Sell {sol_to_sell:.4f} SOL for liquidity")
            
            order = {
                'type': 'market',
                'side': 'sell',
                'product_id': 'SOL-USD',
                'quantity': sol_to_sell
            }
            orders.append(order)
            
            # Execute SOL sale
            try:
                print(f"\n⚡ Executing SOL sale...")
                result = client.market_order_sell(
                    product_id='SOL-USD',
                    base_size=str(sol_to_sell)
                )
                print(f"  ✅ SOL sell order placed: {result}")
                time.sleep(2)  # Wait for settlement
            except Exception as e:
                print(f"  ⚠️ SOL sell failed: {e}")
        
        # Option 2: Trim AVAX position (10 AVAX = ~$235)
        elif positions.get('AVAX', 0) > 20:
            avax_to_sell = min(10, positions.get('AVAX', 0) * 0.15)  # Max 15% of AVAX
            print(f"  2. Sell {avax_to_sell:.4f} AVAX for liquidity")
            
            try:
                print(f"\n⚡ Executing AVAX sale...")
                result = client.market_order_sell(
                    product_id='AVAX-USD',
                    base_size=str(avax_to_sell)
                )
                print(f"  ✅ AVAX sell order placed: {result}")
                time.sleep(2)
            except Exception as e:
                print(f"  ⚠️ AVAX sell failed: {e}")
        
        # Check updated USD balance
        print("\n📊 CHECKING LIQUIDITY...")
        response = client.get_accounts()
        if hasattr(response, 'accounts'):
            accounts = response.accounts
        else:
            accounts = response.get('accounts', response)
        
        usd_available = 0
        for account in accounts:
            if hasattr(account, 'currency') and account.currency == 'USD':
                if hasattr(account.available_balance, 'value'):
                    usd_available = float(account.available_balance.value)
                    break
        
        print(f"  USD Available: ${usd_available:.2f}")
        
        # Calculate XRP purchase amount
        if usd_available > 50:
            # Keep $10 for fees and emergency
            xrp_budget = usd_available - 10
            print(f"\n🚀 XRP PURCHASE EXECUTION:")
            print("-" * 40)
            print(f"  Budget for XRP: ${xrp_budget:.2f}")
            
            # Get current XRP price
            ticker = client.get_product('XRP-USD')
            if hasattr(ticker, 'price'):
                xrp_price = float(ticker.price)
            else:
                xrp_price = 2.77
            
            xrp_to_buy = xrp_budget / xrp_price
            print(f"  XRP Price: ${xrp_price:.3f}")
            print(f"  XRP to Buy: {xrp_to_buy:.2f}")
            
            # Execute XRP purchase
            try:
                print(f"\n⚡ EXECUTING XRP PURCHASE...")
                
                # Use quote_size for USD amount
                result = client.market_order_buy(
                    product_id='XRP-USD',
                    quote_size=str(int(xrp_budget))  # USD amount to spend
                )
                
                print(f"  ✅ XRP BUY ORDER PLACED!")
                print(f"  Order details: {result}")
                
                # Wait and check final position
                time.sleep(3)
                
                # Get final XRP balance
                response = client.get_accounts()
                if hasattr(response, 'accounts'):
                    accounts = response.accounts
                else:
                    accounts = response.get('accounts', response)
                
                for account in accounts:
                    if hasattr(account, 'currency') and account.currency == 'XRP':
                        if hasattr(account.available_balance, 'value'):
                            final_xrp = float(account.available_balance.value)
                            print(f"\n💎 FINAL XRP POSITION: {final_xrp:.2f} XRP")
                            print(f"  Value: ${final_xrp * xrp_price:.2f}")
                            break
                
            except Exception as e:
                print(f"  ❌ XRP purchase failed: {e}")
                print("  Try manual purchase or adjust parameters")
        
        else:
            print("\n⚠️ INSUFFICIENT LIQUIDITY")
            print("  Manual intervention required:")
            print("  1. Cancel some open orders to free up funds")
            print("  2. Manually sell SOL or AVAX")
            print("  3. Wait for BTC $110k trigger")
        
        print("\n" + "=" * 70)
        print("🔥 XRP ACCUMULATION COMPLETE")
        print("Sacred Fire burns for XRP Army!")
        
        # Log the operation
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'XRP_ACCUMULATION',
            'usd_used': xrp_budget if 'xrp_budget' in locals() else 0,
            'xrp_purchased': xrp_to_buy if 'xrp_to_buy' in locals() else 0,
            'final_position': final_xrp if 'final_xrp' in locals() else positions.get('XRP', 0)
        }
        
        with open('/home/dereadi/scripts/claude/xrp_accumulation_log.json', 'w') as f:
            json.dump(log_entry, f, indent=2)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("⚠️ WARNING: This will execute REAL trades!")
    print("It will:")
    print("  1. Sell SOL or AVAX to generate liquidity")
    print("  2. Use proceeds to buy XRP")
    print()
    
    response = input("Type 'EXECUTE' to proceed: ")
    if response == 'EXECUTE':
        execute_xrp_strategy()
    else:
        print("Cancelled - no trades executed")