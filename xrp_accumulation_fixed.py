#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 Execute XRP Accumulation - FIXED VERSION
Cherokee Trading Council - Generate liquidity and buy XRP
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient
import uuid
import time

def execute_xrp_accumulation():
    """Generate liquidity by selling SOL/AVAX and buy XRP"""
    
    print("🔥 CHEROKEE XRP ACCUMULATION STRATEGY")
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
        
        # Get current positions
        response = client.get_accounts()
        if hasattr(response, 'accounts'):
            accounts = response.accounts
        else:
            accounts = response.get('accounts', response)
        
        positions = {}
        for account in accounts:
            if hasattr(account, 'currency'):
                currency = account.currency
            else:
                currency = account.get('currency', 'UNKNOWN')
            
            if hasattr(account, 'available_balance'):
                if hasattr(account.available_balance, 'value'):
                    available = float(account.available_balance.value)
                else:
                    available = float(account.available_balance.get('value', 0))
            else:
                available = 0
            
            if available > 0.00001:
                positions[currency] = available
        
        print("📊 CURRENT POSITIONS:")
        print("-" * 40)
        print(f"  USD: ${positions.get('USD', 0):.2f}")
        print(f"  SOL: {positions.get('SOL', 0):.4f} SOL")
        print(f"  AVAX: {positions.get('AVAX', 0):.4f} AVAX")
        print(f"  XRP: {positions.get('XRP', 0):.4f} XRP")
        print()
        
        # Calculate how much to sell for $300 liquidity
        sol_amount = positions.get('SOL', 0)
        avax_amount = positions.get('AVAX', 0)
        
        print("🎯 LIQUIDITY GENERATION PLAN:")
        print("-" * 40)
        
        # Sell 1.5 SOL (about $300)
        if sol_amount > 2:
            sol_to_sell = min(1.5, sol_amount * 0.2)  # Max 20% of holdings
            print(f"  Selling {sol_to_sell:.4f} SOL (~${sol_to_sell * 200:.2f})")
            
            try:
                # Create order with proper parameters
                order_config = {
                    "product_id": "SOL-USD",
                    "base_size": str(round(sol_to_sell, 4)),
                    "client_order_id": str(uuid.uuid4())
                }
                
                print(f"\n⚡ Placing SOL sell order...")
                print(f"  Amount: {sol_to_sell:.4f} SOL")
                
                result = client.market_order_sell(**order_config)
                
                if result:
                    print(f"  ✅ SOL SELL ORDER PLACED!")
                    print(f"  Order ID: {result.get('order_id', 'Unknown')}")
                    time.sleep(3)  # Wait for settlement
                
            except Exception as e:
                print(f"  ⚠️ SOL sell error: {e}")
                # Try AVAX instead
                if avax_amount > 10:
                    avax_to_sell = min(12, avax_amount * 0.2)
                    print(f"\n  Trying AVAX: Selling {avax_to_sell:.2f} AVAX")
                    
                    try:
                        order_config = {
                            "product_id": "AVAX-USD",
                            "base_size": str(round(avax_to_sell, 2)),
                            "client_order_id": str(uuid.uuid4())
                        }
                        
                        result = client.market_order_sell(**order_config)
                        
                        if result:
                            print(f"  ✅ AVAX SELL ORDER PLACED!")
                            time.sleep(3)
                    except Exception as e2:
                        print(f"  ⚠️ AVAX sell error: {e2}")
        
        # Check updated USD balance
        print("\n📊 CHECKING UPDATED BALANCE...")
        time.sleep(2)
        
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
        
        # Buy XRP if we have liquidity
        if usd_available > 50:
            xrp_budget = usd_available - 10  # Keep $10 reserve
            
            print(f"\n🚀 XRP PURCHASE:")
            print("-" * 40)
            print(f"  Budget: ${xrp_budget:.2f}")
            
            try:
                # Place XRP buy order
                order_config = {
                    "product_id": "XRP-USD",
                    "quote_size": str(int(xrp_budget)),  # USD to spend
                    "client_order_id": str(uuid.uuid4())
                }
                
                print(f"  Buying XRP with ${xrp_budget:.2f}...")
                
                result = client.market_order_buy(**order_config)
                
                if result:
                    print(f"  ✅ XRP BUY ORDER PLACED!")
                    print(f"  Order ID: {result.get('order_id', 'Unknown')}")
                    
                    # Check final XRP balance
                    time.sleep(3)
                    response = client.get_accounts()
                    if hasattr(response, 'accounts'):
                        accounts = response.accounts
                    else:
                        accounts = response.get('accounts', response)
                    
                    for account in accounts:
                        if hasattr(account, 'currency') and account.currency == 'XRP':
                            if hasattr(account.available_balance, 'value'):
                                final_xrp = float(account.available_balance.value)
                                print(f"\n💎 NEW XRP POSITION: {final_xrp:.2f} XRP")
                                print(f"  Increase: {final_xrp - positions.get('XRP', 0):.2f} XRP")
                                break
                
            except Exception as e:
                print(f"  ❌ XRP buy error: {e}")
        else:
            print("\n⚠️ Insufficient liquidity generated")
            print("  Consider:")
            print("  1. Cancel open orders (especially BTC)")
            print("  2. Manual trading required")
            print("  3. Wait for BTC $110k trigger")
        
        print("\n" + "=" * 70)
        print("🔥 XRP ARMY ACCUMULATION COMPLETE")
        print("The patient shall be rewarded!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    execute_xrp_accumulation()