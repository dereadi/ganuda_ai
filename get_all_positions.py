#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 GET ALL CRYPTO POSITIONS
Cherokee Council examines complete portfolio
"""

import json
from pathlib import Path
from coinbase.rest import RESTClient

def get_all_positions():
    """Get all crypto positions from Coinbase"""
    
    print("🔥 CHEROKEE PORTFOLIO POSITIONS")
    print("=" * 80)
    print("Complete crypto holdings analysis...")
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
        print("Fetching all accounts...")
        accounts_response = client.get_accounts()
        
        # Try to access accounts properly
        if hasattr(accounts_response, 'accounts'):
            accounts = accounts_response.accounts
        else:
            accounts = accounts_response
        
        positions = []
        total_value = 0
        
        print("\n📊 CURRENT POSITIONS:")
        print("-" * 80)
        
        # Process each account
        for account in accounts:
            try:
                # Handle different response formats
                if hasattr(account, '__dict__'):
                    currency = account.currency
                    balance_data = account.available_balance
                    if hasattr(balance_data, 'value'):
                        balance = float(balance_data.value)
                    else:
                        balance = float(balance_data['value'])
                else:
                    # Dictionary format
                    currency = account['currency']
                    balance = float(account['available_balance']['value'])
                
                # Only show non-zero balances
                if balance > 0.00001:
                    # Get price for crypto
                    if currency == 'USD':
                        price = 1.0
                        usd_value = balance
                        print(f"\n💵 USD (Cash):")
                        print(f"   Balance: ${balance:,.2f}")
                        positions.append({
                            'currency': 'USD',
                            'balance': balance,
                            'price': 1,
                            'value': balance
                        })
                    elif currency == 'USDC':
                        price = 1.0
                        usd_value = balance
                        print(f"\n💰 USDC (Stablecoin):")
                        print(f"   Balance: {balance:,.2f} USDC")
                        print(f"   Value: ${balance:,.2f}")
                        positions.append({
                            'currency': 'USDC',
                            'balance': balance,
                            'price': 1,
                            'value': balance
                        })
                    else:
                        # Get current price
                        try:
                            product = client.get_product(f"{currency}-USD")
                            if hasattr(product, 'price'):
                                price = float(product.price)
                            else:
                                price = float(product['price'])
                            
                            usd_value = balance * price
                            
                            if usd_value > 0.01:  # Only show if worth more than 1 cent
                                print(f"\n{currency}:")
                                print(f"   Amount: {balance:.8f}")
                                print(f"   Price: ${price:,.2f}")
                                print(f"   Value: ${usd_value:,.2f}")
                                
                                positions.append({
                                    'currency': currency,
                                    'balance': balance,
                                    'price': price,
                                    'value': usd_value
                                })
                                
                        except Exception as e:
                            # No USD pair available
                            print(f"\n{currency}:")
                            print(f"   Amount: {balance:.8f}")
                            print(f"   Price: Unable to fetch")
                            usd_value = 0
                    
                    total_value += usd_value
                    
            except Exception as e:
                print(f"Error processing account: {e}")
                continue
        
        # Sort positions by value
        positions.sort(key=lambda x: x['value'], reverse=True)
        
        print("\n" + "=" * 80)
        print("📊 PORTFOLIO SUMMARY:")
        print("-" * 60)
        print(f"💼 Total Portfolio Value: ${total_value:,.2f}")
        print(f"📈 Number of Positions: {len(positions)}")
        
        # Calculate percentages
        print("\n📊 POSITION BREAKDOWN:")
        print("-" * 60)
        for pos in positions:
            if pos['value'] > 0:
                percentage = (pos['value'] / total_value) * 100
                print(f"{pos['currency']:8} ${pos['value']:10,.2f} ({percentage:5.1f}%)")
        
        # Cherokee Council Analysis
        print("\n🏛️ CHEROKEE COUNCIL ANALYSIS:")
        print("-" * 60)
        
        # Find key positions
        for pos in positions:
            if pos['currency'] == 'ETH':
                print(f"🦅 Eagle Eye: ETH at ${pos['price']:,.2f} - momentum building!")
            elif pos['currency'] == 'SOL':
                print(f"🕷️ Spider: SOL at ${pos['price']:,.2f} - oscillation zone")
            elif pos['currency'] == 'BTC':
                print(f"🐢 Turtle: BTC at ${pos['price']:,.2f} - long-term hold")
            elif pos['currency'] == 'DOGE':
                if pos['price'] < 0.21:
                    print(f"🐺 Coyote: DOGE at ${pos['price']:.4f} - blood bag accumulation zone!")
                else:
                    print(f"🐺 Coyote: DOGE at ${pos['price']:.4f} - ready to bleed!")
        
        return positions
        
    except Exception as e:
        print(f"\n❌ Error getting positions: {e}")
        print("\nTrying alternative method...")
        
        # Alternative: Direct API call
        try:
            import requests
            import hmac
            import hashlib
            import time
            
            with open(Path.home() / ".coinbase_config.json", 'r') as f:
                config = json.load(f)
            
            timestamp = str(int(time.time()))
            message = timestamp + 'GET' + '/api/v3/brokerage/accounts'
            signature = hmac.new(
                config['api_secret'].encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            headers = {
                'CB-ACCESS-KEY': config['api_key'],
                'CB-ACCESS-SIGN': signature,
                'CB-ACCESS-TIMESTAMP': timestamp,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://api.coinbase.com/api/v3/brokerage/accounts',
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print("\n✅ Alternative method successful!")
                print(json.dumps(data, indent=2)[:500])
            else:
                print(f"\n❌ Alternative method failed: {response.status_code}")
                print(response.text[:200])
                
        except Exception as e2:
            print(f"Alternative method error: {e2}")
            
        return []

def main():
    """Execute position check"""
    
    print("🔥 CHEROKEE COUNCIL POSITION CHECK")
    print("Examining all crypto holdings...")
    print()
    
    positions = get_all_positions()
    
    if positions:
        print("\n" + "=" * 80)
        print("🔥 Sacred Fire illuminates our positions")
        print("🏛️ Cherokee Council ready to advise")
        print("🪶 Mitakuye Oyasin - All positions connected")
    else:
        print("\n⚠️ Unable to fetch positions - API issues")
        print("Known positions from observation:")
        print("  • $200 USD cash")
        print("  • ETH (grew well)")
        print("  • SOL (grew well)")
        print("  • BTC (core position)")
        print("  • DOGE (blood bag strategy)")
        print("  • Various small alts")

if __name__ == "__main__":
    main()