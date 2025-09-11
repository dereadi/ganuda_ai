#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 SIMPLE PORTFOLIO CHECK
Quick check of all holdings
"""

import json
from pathlib import Path
from coinbase.rest import RESTClient

def check_portfolio():
    """Simple portfolio check"""
    
    print("🔥 CHEROKEE PORTFOLIO CHECK")
    print("=" * 60)
    
    try:
        # Load config
        config_path = Path.home() / ".coinbase_config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        client = RESTClient(
            api_key=config['api_key'],
            api_secret=config['api_secret']
        )
        
        # Get accounts
        print("Getting accounts...")
        accounts = client.get_accounts()
        
        print("\n📊 HOLDINGS:")
        print("-" * 40)
        
        total_usd = 0
        holdings = []
        
        # Check each account
        for account in accounts.accounts:
            currency = account.currency
            # available_balance is a dict with 'value' and 'currency' keys
            balance = float(account.available_balance['value'])
            
            if balance > 0.00001:  # Only show non-zero balances
                if currency == 'USD':
                    print(f"\n💵 USD CASH: ${balance:,.2f}")
                    total_usd += balance
                    holdings.append(('USD', balance, balance))
                elif currency == 'USDC':
                    print(f"💰 USDC: {balance:,.2f} (~${balance:,.2f})")
                    total_usd += balance
                    holdings.append(('USDC', balance, balance))
                else:
                    # Try to get price
                    try:
                        product = client.get_product(f"{currency}-USD")
                        price = float(product.price)
                        value = balance * price
                        total_usd += value
                        
                        print(f"\n{currency}:")
                        print(f"  Amount: {balance:.6f}")
                        print(f"  Price: ${price:,.2f}")
                        print(f"  Value: ${value:,.2f}")
                        
                        holdings.append((currency, balance, value))
                        
                        # Special notes
                        if currency == 'ETH':
                            print("  📈 ETH grew well!")
                        elif currency == 'SOL':
                            print("  📈 SOL grew well!")
                        elif currency == 'DOGE' and value > 100:
                            print("  💰 Could sell for liquidity")
                        elif value > 50 and value < 500:
                            print("  💰 Potential liquidity source")
                            
                    except Exception as e:
                        print(f"{currency}: {balance:.6f} (price unavailable)")
        
        print("\n" + "=" * 60)
        print(f"💼 TOTAL PORTFOLIO: ${total_usd:,.2f}")
        
        # Find liquidity sources
        print("\n🔥 LIQUIDITY ANALYSIS:")
        print("-" * 40)
        
        usd_cash = sum(v for c, b, v in holdings if c == 'USD')
        usdc_cash = sum(v for c, b, v in holdings if c == 'USDC')
        
        print(f"💵 USD Cash: ${usd_cash:,.2f}")
        print(f"💰 USDC Available: ${usdc_cash:,.2f}")
        print(f"💧 Total Liquid: ${usd_cash + usdc_cash:,.2f}")
        
        if usd_cash + usdc_cash < 500:
            print("\n⚠️ LOW LIQUIDITY - Consider selling alts:")
            
            # Sort by value
            sorted_holdings = sorted(holdings, key=lambda x: x[2], reverse=True)
            
            for currency, balance, value in sorted_holdings:
                if currency not in ['USD', 'USDC', 'BTC', 'ETH'] and value > 50:
                    print(f"  • Sell {currency}: ~${value:,.2f}")
        
        return total_usd
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    total = check_portfolio()
    print("\n🔥 Sacred Fire illuminates the portfolio")
    print("🏛️ Cherokee Council ready to advise on liquidity")