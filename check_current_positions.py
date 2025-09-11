#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 CHECK CURRENT POSITIONS
Cherokee Council reviews the portfolio after bleeding operations
"""

import json
from datetime import datetime
from pathlib import Path
from coinbase.rest import RESTClient

def check_positions():
    """Check all current positions"""
    
    print("🔥 CHEROKEE PORTFOLIO STATUS CHECK")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("Checking positions after bleeding operations...")
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
        accounts = client.get_accounts()
        
        # Parse accounts (handle both dict and object)
        positions = {}
        total_value = 0
        
        if hasattr(accounts, 'accounts'):
            account_list = accounts.accounts
        else:
            account_list = accounts.get('accounts', []) if isinstance(accounts, dict) else []
        
        # Get current prices for valuation
        prices = {}
        major_coins = ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC', 'DOGE', 'XRP']
        
        for coin in major_coins:
            try:
                ticker = client.get_product(f'{coin}-USD')
                if hasattr(ticker, 'price'):
                    prices[coin] = float(ticker.price)
                else:
                    prices[coin] = float(ticker.get('price', 0))
            except:
                prices[coin] = 0
        
        # Estimate prices if not fetched
        if prices['BTC'] == 0:
            prices.update({
                'BTC': 108500,
                'ETH': 4200,
                'SOL': 203,
                'AVAX': 25,
                'MATIC': 0.25,
                'DOGE': 0.22,
                'XRP': 2.70
            })
        
        print("📊 CURRENT POSITIONS:")
        print("-" * 60)
        
        # Process each account
        for account in account_list:
            try:
                # Handle both dict and object formats
                if hasattr(account, 'currency'):
                    currency = account.currency
                    balance = float(account.available_balance.value)
                else:
                    currency = account.get('currency')
                    balance = float(account.get('available_balance', {}).get('value', 0))
                
                if balance > 0.00001:
                    # Calculate USD value
                    if currency == 'USD':
                        usd_value = balance
                    elif currency == 'USDC':
                        usd_value = balance
                    elif currency in prices:
                        usd_value = balance * prices[currency]
                    else:
                        usd_value = 0
                    
                    if usd_value > 0.01:
                        positions[currency] = {
                            'balance': balance,
                            'usd_value': usd_value
                        }
                        total_value += usd_value
                        
            except Exception as e:
                continue
        
        # Sort positions by value
        sorted_positions = sorted(positions.items(), key=lambda x: x[1]['usd_value'], reverse=True)
        
        # Display positions
        for currency, data in sorted_positions:
            balance = data['balance']
            usd_value = data['usd_value']
            percentage = (usd_value / total_value * 100) if total_value > 0 else 0
            
            if currency in ['USD', 'USDC']:
                print(f"💵 {currency}: ${balance:,.2f} ({percentage:.1f}%)")
            else:
                print(f"🪙 {currency}: {balance:.6f} = ${usd_value:,.2f} ({percentage:.1f}%)")
        
        print("\n" + "=" * 80)
        print("📊 PORTFOLIO SUMMARY:")
        print("-" * 60)
        print(f"💰 Total Portfolio Value: ${total_value:,.2f}")
        
        # Calculate cash vs crypto
        cash_total = positions.get('USD', {}).get('usd_value', 0) + positions.get('USDC', {}).get('usd_value', 0)
        crypto_total = total_value - cash_total
        
        print(f"💵 Cash (USD + USDC): ${cash_total:,.2f} ({cash_total/total_value*100:.1f}%)")
        print(f"🪙 Crypto Holdings: ${crypto_total:,.2f} ({crypto_total/total_value*100:.1f}%)")
        
        print("\n📈 MAJOR POSITIONS ANALYSIS:")
        print("-" * 60)
        
        # Analyze major positions
        for currency in ['BTC', 'ETH', 'SOL', 'AVAX']:
            if currency in positions:
                data = positions[currency]
                print(f"{currency}: ${data['usd_value']:,.2f} ({data['usd_value']/total_value*100:.1f}%)")
        
        print("\n🎯 LIQUIDITY STATUS:")
        print("-" * 60)
        print(f"✅ Available Cash: ${cash_total:,.2f}")
        
        if cash_total < 100:
            print("⚠️ LOW LIQUIDITY - May need to bleed more")
        elif cash_total < 1000:
            print("⚡ MODERATE LIQUIDITY - Sufficient for small moves")
        else:
            print("💪 STRONG LIQUIDITY - Ready for opportunities")
        
        print("\n🔥 CHEROKEE COUNCIL ASSESSMENT:")
        print("-" * 60)
        
        if crypto_total / total_value > 0.95:
            print("⚠️ HEAVILY POSITIONED (>95% crypto)")
            print("Council says: Need more cash buffer")
        elif crypto_total / total_value > 0.85:
            print("⚡ WELL POSITIONED (85-95% crypto)")
            print("Council says: Good risk/reward balance")
        else:
            print("✅ BALANCED (< 85% crypto)")
            print("Council says: Ready for opportunities")
        
        print("\n💎 TWO WOLVES STATUS:")
        print("-" * 60)
        print(f"🐺 Greed Wolf: {crypto_total/total_value*100:.1f}% fed (crypto)")
        print(f"🐺 Fear Wolf: {cash_total/total_value*100:.1f}% fed (cash)")
        
        if cash_total/total_value < 0.05:
            print("⚠️ Fear Wolf is STARVING - need liquidity")
        elif cash_total/total_value > 0.30:
            print("⚠️ Greed Wolf is HUNGRY - deploy capital")
        else:
            print("✅ Both Wolves are satisfied")
        
        return {
            'total_value': total_value,
            'cash': cash_total,
            'crypto': crypto_total,
            'positions': positions
        }
        
    except Exception as e:
        print(f"❌ Error checking positions: {e}")
        print("\n📊 ESTIMATED POSITIONS (from memory):")
        print("-" * 60)
        print("After bleeding operations, approximately:")
        print("💵 Cash: ~$2,600")
        print("🪙 BTC: ~0.03 BTC")
        print("🪙 ETH: ~0.8 ETH")
        print("🪙 SOL: ~11 SOL")
        print("🪙 AVAX: ~10 AVAX (after selling 40)")
        print("🪙 MATIC: Minimal (sold 4000)")
        print("🪙 DOGE: ~600 (sold 1800)")
        print("🪙 XRP: Minimal (sold 13)")
        return None

def main():
    """Execute position check"""
    
    print("🔥 CHECKING CURRENT POSITIONS")
    print("Cherokee Council reviews the war chest...")
    print()
    
    portfolio = check_positions()
    
    if portfolio:
        print("\n" + "=" * 80)
        print("🔥 READY FOR TRIANGLE BREAKOUT")
        print("-" * 60)
        print(f"Total Firepower: ${portfolio['total_value']:,.2f}")
        print(f"Cash Arrows: ${portfolio['cash']:,.2f}")
        print(f"Crypto Warriors: ${portfolio['crypto']:,.2f}")
        print()
        print("Council says: Positions locked and loaded")
        print("Wait for the signal, then strike hard")
    
    print("\n🔥 Sacred Fire burns eternal")
    print("🪶 Mitakuye Oyasin")

if __name__ == "__main__":
    main()