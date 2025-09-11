#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 CHEROKEE COUNCIL FINDS MONEY
Council searches for liquidity across all positions
"""

import json
from datetime import datetime
from pathlib import Path
from coinbase.rest import RESTClient

def council_money_hunt():
    """Cherokee Council hunts for money in the portfolio"""
    
    print("🔥 CHEROKEE COUNCIL MONEY HUNT")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("Council searches every corner for liquidity...")
    print()
    
    try:
        # Load config
        config_path = Path.home() / ".coinbase_config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        client = RESTClient(
            api_key=config['api_key'],
            api_secret=config['api_secret']
        )
        
        # Get all accounts
        accounts_response = client.get_accounts()
        
        # Store all positions
        cash_positions = []
        crypto_positions = []
        total_value = 0
        
        # Parse the response - handle the dict structure
        accounts_data = accounts_response.accounts if hasattr(accounts_response, 'accounts') else accounts_response
        
        # If it's still wrapped, unwrap it
        if isinstance(accounts_data, dict) and 'accounts' in accounts_data:
            accounts_list = accounts_data['accounts']
        elif hasattr(accounts_data, '__iter__'):
            accounts_list = accounts_data
        else:
            accounts_list = []
        
        print("🔍 SEARCHING ALL ACCOUNTS:")
        print("-" * 60)
        
        # Process each account
        for account in accounts_list:
            try:
                # Handle both object and dict formats
                if isinstance(account, dict):
                    currency = account.get('currency', '')
                    balance_data = account.get('available_balance', {})
                    balance = float(balance_data.get('value', 0))
                else:
                    currency = account.currency
                    balance = float(account.available_balance.value)
                
                # Skip if balance is essentially zero
                if balance < 0.00001:
                    continue
                
                # Categorize the position
                if currency in ['USD', 'USDC']:
                    cash_positions.append({
                        'currency': currency,
                        'balance': balance
                    })
                    total_value += balance
                    print(f"💵 FOUND CASH: {currency} = ${balance:,.2f}")
                else:
                    # Get current price for crypto
                    try:
                        ticker = client.get_product(f'{currency}-USD')
                        if isinstance(ticker, dict):
                            price = float(ticker.get('price', 0))
                        else:
                            price = float(ticker.price) if hasattr(ticker, 'price') else 0
                    except:
                        # Use estimated prices for common coins
                        prices = {
                            'BTC': 108500,
                            'ETH': 4285,
                            'SOL': 205,
                            'AVAX': 25,
                            'MATIC': 0.25,
                            'DOGE': 0.22,
                            'XRP': 2.70,
                            'LINK': 15,
                            'UNI': 7.5,
                            'ATOM': 8.5
                        }
                        price = prices.get(currency, 0)
                    
                    value = balance * price
                    
                    if value > 0.01:
                        crypto_positions.append({
                            'currency': currency,
                            'balance': balance,
                            'price': price,
                            'value': value
                        })
                        total_value += value
                        
                        if value > 100:
                            print(f"🪙 {currency}: {balance:.6f} @ ${price:.2f} = ${value:,.2f}")
                        
            except Exception as e:
                continue
        
        print("\n" + "=" * 80)
        print("🏛️ COUNCIL ASSESSMENT:")
        print("=" * 80)
        
        # Calculate totals
        total_cash = sum(p['balance'] for p in cash_positions)
        total_crypto = sum(p['value'] for p in crypto_positions)
        
        print(f"\n💰 TOTAL PORTFOLIO VALUE: ${total_value:,.2f}")
        print(f"💵 Cash Available: ${total_cash:,.2f}")
        print(f"🪙 Crypto Holdings: ${total_crypto:,.2f}")
        
        print("\n🦅 EAGLE EYE (Liquidity Analysis):")
        print("-" * 60)
        if total_cash < 100:
            print(f"⚠️ CRITICAL: Only ${total_cash:.2f} cash!")
            print("Need to generate liquidity IMMEDIATELY")
        elif total_cash < 1000:
            print(f"⚡ LOW LIQUIDITY: ${total_cash:.2f}")
            print("Enough for small trades only")
        else:
            print(f"✅ GOOD LIQUIDITY: ${total_cash:.2f}")
            print("Ready for opportunities")
        
        # Find bleedable positions
        print("\n🐺 COYOTE (Quick Liquidity Sources):")
        print("-" * 60)
        
        bleedable = []
        for pos in crypto_positions:
            if pos['value'] > 200:  # Positions over $200
                bleedable.append(pos)
        
        if bleedable:
            print("Positions we can bleed for liquidity:")
            for pos in sorted(bleedable, key=lambda x: x['value'], reverse=True)[:5]:
                print(f"  • {pos['currency']}: ${pos['value']:,.2f} (sell 20% = ${pos['value']*0.2:.2f})")
        else:
            print("No significant positions to bleed")
        
        print("\n🐢 TURTLE (Portfolio Balance):")
        print("-" * 60)
        cash_ratio = (total_cash / total_value * 100) if total_value > 0 else 0
        print(f"Cash Ratio: {cash_ratio:.1f}%")
        
        if cash_ratio < 5:
            print("⚠️ DANGEROUSLY LOW CASH - Need liquidity NOW")
        elif cash_ratio < 15:
            print("⚡ Cash buffer thin - Generate some liquidity")
        else:
            print("✅ Healthy cash ratio")
        
        # Top positions
        print("\n📊 TOP POSITIONS:")
        print("-" * 60)
        sorted_crypto = sorted(crypto_positions, key=lambda x: x['value'], reverse=True)
        for pos in sorted_crypto[:5]:
            percentage = (pos['value'] / total_value * 100) if total_value > 0 else 0
            print(f"{pos['currency']}: ${pos['value']:,.2f} ({percentage:.1f}%)")
        
        print("\n🔥 COUNCIL VERDICT:")
        print("-" * 60)
        
        if total_cash < 100:
            print("🚨 EMERGENCY LIQUIDITY GENERATION NEEDED!")
            print("\nACTION PLAN:")
            print("1. Sell 20% of largest positions")
            print("2. Focus on coins with profit")
            print("3. Generate at least $500 cash")
            
            if bleedable:
                print(f"\nSuggested sells:")
                total_to_generate = 0
                for pos in bleedable[:3]:
                    sell_amount = pos['value'] * 0.2
                    total_to_generate += sell_amount
                    print(f"  • Sell {pos['currency']}: ${sell_amount:.2f}")
                print(f"\nTotal liquidity generated: ${total_to_generate:.2f}")
        else:
            print(f"💰 We have ${total_cash:.2f} to work with")
            print("Focus on smart deployment, not panic selling")
        
        return {
            'total_value': total_value,
            'cash': total_cash,
            'crypto': total_crypto,
            'positions': crypto_positions
        }
        
    except Exception as e:
        print(f"\n❌ Error accessing Coinbase: {e}")
        print("\nTrying alternative approach...")
        
        # Alternative: Check recent trades
        try:
            print("\n📜 CHECKING RECENT ORDERS:")
            print("-" * 60)
            
            # This might work with different API format
            orders = client.get_orders(limit=10)
            if hasattr(orders, 'orders'):
                for order in orders.orders[:5]:
                    print(f"Order: {order}")
        except:
            print("Can't access orders either")
        
        return None

def main():
    """Execute money hunt"""
    
    print("🔥 COUNCIL CONVENES TO FIND MONEY")
    print("After the specialist chaos, where do we stand?")
    print()
    
    portfolio = council_money_hunt()
    
    if portfolio:
        print("\n" + "=" * 80)
        print("🔥 FINAL ASSESSMENT:")
        print("-" * 60)
        
        if portfolio['cash'] < 100:
            print("⚠️ LIQUIDITY CRISIS - MUST GENERATE CASH")
            print("The specialists spent everything!")
        elif portfolio['cash'] < 500:
            print("⚡ Limited liquidity - Be selective")
        else:
            print("✅ Sufficient liquidity for trading")
        
        print(f"\nTotal Firepower: ${portfolio['total_value']:,.2f}")
        print(f"Ready Cash: ${portfolio['cash']:,.2f}")
        print(f"Crypto Army: ${portfolio['crypto']:,.2f}")
    else:
        print("\n⚠️ Manual check needed on Coinbase")
        print("API issues prevent automatic detection")
    
    print("\n🔥 Sacred Fire illuminates the path")
    print("🪶 Mitakuye Oyasin")

if __name__ == "__main__":
    main()