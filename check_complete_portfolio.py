#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 Complete Portfolio Check - ALL Positions
Gets every balance type from Coinbase
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient
import sys

def get_complete_portfolio():
    """Get ALL positions from Coinbase including holds"""
    try:
        with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
            config = json.load(f)
        
        client = RESTClient(
            api_key=config['name'].split('/')[-1],
            api_secret=config['privateKey']
        )
        
        # Get ALL accounts
        accounts_response = client.get_accounts()
        # Handle the response properly
        if hasattr(accounts_response, 'accounts'):
            accounts = accounts_response.accounts
        else:
            accounts = accounts_response.get('accounts', [])
        
        print(f"🔥 COMPLETE PORTFOLIO CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        portfolio = {}
        total_value = 0
        total_on_hold = 0
        
        # Check each account thoroughly
        for account in accounts:
            # Handle account as object
            currency = account.currency if hasattr(account, 'currency') else 'UNKNOWN'
            
            # Get ALL balance types
            if hasattr(account, 'available_balance'):
                available = float(account.available_balance.value)
            else:
                available = 0
            
            # Check for hold balance
            if hasattr(account, 'hold') and account.hold:
                hold = float(account.hold.value)
            else:
                hold = 0
            
            # Calculate total balance
            total_balance = available + hold
            
            # Skip if truly zero
            if total_balance < 0.00001:
                continue
            
            # Get USD value
            if currency in ['USD', 'USDC']:
                price = 1.0
                usd_value = total_balance
            else:
                try:
                    # Try to get the current price
                    ticker = client.get_product(f"{currency}-USD")
                    price = float(ticker.get('price', 0))
                    usd_value = total_balance * price
                except Exception as e:
                    # Try alternate method
                    try:
                        import requests
                        url = f"https://api.coinbase.com/v2/exchange-rates?currency={currency}"
                        response = requests.get(url)
                        data = response.json()
                        price = float(data['data']['rates']['USD'])
                        usd_value = total_balance * price
                    except:
                        print(f"  ⚠️ Could not get price for {currency}")
                        continue
            
            # Store position data
            portfolio[currency] = {
                'available': available,
                'hold': hold,
                'total': total_balance,
                'price': price,
                'usd_value': usd_value
            }
            
            total_value += usd_value
            if hold > 0:
                total_on_hold += (hold * price)
            
            # Print position details
            print(f"\n{currency}:")
            print(f"  Available: {available:.8f}")
            if hold > 0:
                print(f"  On Hold: {hold:.8f}")
            print(f"  Total: {total_balance:.8f}")
            print(f"  Price: ${price:,.2f}")
            print(f"  USD Value: ${usd_value:,.2f}")
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 PORTFOLIO SUMMARY:")
        print(f"  Total Value: ${total_value:,.2f}")
        print(f"  Available Liquidity: ${portfolio.get('USD', {}).get('available', 0):,.2f}")
        if total_on_hold > 0:
            print(f"  ⚠️ On Hold: ${total_on_hold:,.2f}")
        
        # Show top positions by value
        print(f"\n🏆 TOP POSITIONS:")
        sorted_positions = sorted(
            [(k, v) for k, v in portfolio.items() if k not in ['USD', 'USDC']], 
            key=lambda x: x[1]['usd_value'], 
            reverse=True
        )
        
        for i, (symbol, data) in enumerate(sorted_positions[:10], 1):
            pct = (data['usd_value'] / total_value) * 100
            hold_indicator = " 🔒" if data['hold'] > 0 else ""
            print(f"  {i}. {symbol}: ${data['usd_value']:,.2f} ({pct:.1f}%){hold_indicator}")
        
        # Check for issues
        print(f"\n⚠️ ALERTS:")
        if portfolio.get('USD', {}).get('available', 0) < 50:
            print(f"  🚨 LIQUIDITY CRITICAL: Only ${portfolio.get('USD', {}).get('available', 0):,.2f} available")
        
        if total_on_hold > 100:
            print(f"  🔒 SIGNIFICANT HOLDS: ${total_on_hold:,.2f} locked up")
        
        # Save to file
        with open('/home/dereadi/scripts/claude/portfolio_complete.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_value': total_value,
                'total_on_hold': total_on_hold,
                'positions': portfolio
            }, f, indent=2)
        
        return portfolio, total_value
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

if __name__ == "__main__":
    portfolio, total = get_complete_portfolio()
    
    if total > 0:
        print(f"\n✅ Portfolio data saved to portfolio_complete.json")
        print(f"\n🔥 ACTUAL TOTAL: ${total:,.2f}")
    else:
        print("\n❌ Failed to get portfolio data")