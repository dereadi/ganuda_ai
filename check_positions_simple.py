#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 SIMPLE POSITION CHECK
Direct API call to check positions
"""

import json
from pathlib import Path
from coinbase.rest import RESTClient

def check_positions_simple():
    """Simple position check"""
    
    print("🔥 CHECKING POSITIONS (SIMPLE)")
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
        
        # Get all accounts
        print("Fetching accounts...")
        accounts = client.get_accounts()
        
        print("\n📊 YOUR POSITIONS:")
        print("-" * 60)
        
        # Try to parse the response
        total_value = 0
        positions = []
        
        # Handle the response format
        if hasattr(accounts, 'accounts'):
            account_list = accounts.accounts
            for acc in account_list:
                currency = acc.currency
                balance = float(acc.available_balance.value)
                if balance > 0.00001:
                    positions.append((currency, balance))
        else:
            # Try as dict
            if 'accounts' in accounts:
                for acc in accounts['accounts']:
                    currency = acc.get('currency')
                    balance = float(acc.get('available_balance', {}).get('value', 0))
                    if balance > 0.00001:
                        positions.append((currency, balance))
        
        # Price estimates for calculation
        prices = {
            'BTC': 108500,
            'ETH': 4200,
            'SOL': 203,
            'AVAX': 25,
            'MATIC': 0.25,
            'DOGE': 0.22,
            'XRP': 2.70,
            'USD': 1,
            'USDC': 1
        }
        
        # Display positions
        cash_total = 0
        crypto_value = 0
        
        for currency, balance in positions:
            price = prices.get(currency, 0)
            value = balance * price
            
            if currency in ['USD', 'USDC']:
                cash_total += value
                print(f"💵 {currency}: ${balance:,.2f}")
            elif value > 0.01:
                crypto_value += value
                print(f"🪙 {currency}: {balance:.6f} ≈ ${value:,.2f}")
        
        total_value = cash_total + crypto_value
        
        print("\n" + "=" * 60)
        print("📊 SUMMARY:")
        print(f"💵 Total Cash: ${cash_total:,.2f}")
        print(f"🪙 Total Crypto: ${crypto_value:,.2f}")
        print(f"💰 TOTAL VALUE: ${total_value:,.2f}")
        
        print("\n🎯 LIQUIDITY STATUS:")
        if cash_total > 2000:
            print(f"✅ GOOD - ${cash_total:,.2f} ready to deploy")
        elif cash_total > 500:
            print(f"⚡ MODERATE - ${cash_total:,.2f} available")
        else:
            print(f"⚠️ LOW - Only ${cash_total:,.2f} cash")
        
    except Exception as e:
        print(f"\n❌ API Error: {e}")
        print("\n📊 ESTIMATED POSITIONS (After Bleeding):")
        print("-" * 60)
        
        # Calculate from memory
        estimated = {
            'USD/USDC': 2600,
            'BTC': 0.03 * 108500,
            'ETH': 0.8 * 4200,
            'SOL': 11 * 203,
            'AVAX': 10 * 25,
            'DOGE': 600 * 0.22,
            'Others': 500
        }
        
        total = sum(estimated.values())
        
        for asset, value in estimated.items():
            print(f"{asset}: ${value:,.2f}")
        
        print(f"\n💰 ESTIMATED TOTAL: ${total:,.2f}")
        print(f"💵 Cash Available: $2,600")
        print(f"🪙 Crypto Holdings: ${total - 2600:,.2f}")

if __name__ == "__main__":
    check_positions_simple()