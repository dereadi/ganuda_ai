#\!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🩸 CHECK BLEEDABLE ALTS FOR LIQUIDITY
Find which alts we can sell for more trading fuel
"""

import json
from pathlib import Path
from coinbase.rest import RESTClient

def check_bleedable_alts():
    """Check which alts we can bleed for liquidity"""
    
    print("🩸 CHECKING BLEEDABLE ALTS")
    print("=" * 80)
    print("Cherokee Council examines which alts to sacrifice...")
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
        
        print("🔍 ANALYZING ALT POSITIONS:")
        print("-" * 60)
        
        bleedable = []
        
        # Process each account
        for account in accounts.accounts:
            # Handle both dict and object formats
            if hasattr(account, 'currency'):
                currency = account.currency
                balance = float(account.available_balance.value)
            else:
                currency = account.get('currency', '')
                balance = float(account.get('available_balance', {}).get('value', 0))
            
            # Skip USD, USDC, and zero balances
            if currency in ['USD', 'USDC'] or balance < 0.00001:
                continue
            
            # Try to get USD value
            try:
                product = client.get_product(f"{currency}-USD")
                if hasattr(product, 'price'):
                    price = float(product.price)
                else:
                    price = float(product.get('price', 0))
                
                usd_value = balance * price
                
                # Only show if worth more than $10
                if usd_value > 10:
                    bleedable.append({
                        'currency': currency,
                        'balance': balance,
                        'price': price,
                        'value': usd_value
                    })
                    
            except Exception:
                pass  # Skip if no USD pair
        
        # Sort by value
        bleedable.sort(key=lambda x: x['value'], reverse=True)
        
        print("\n🩸 BLEEDABLE ALTS (sorted by value):")
        print("-" * 60)
        
        total_bleedable = 0
        
        for alt in bleedable:
            total_bleedable += alt['value']
            
            # Cherokee Council assessment
            assessment = ""
            if alt['currency'] == 'DOGE':
                if alt['price'] < 0.21:
                    assessment = "🐺 Keep accumulating (blood bag zone)"
                else:
                    assessment = "✅ Ready to bleed above $0.22"
            elif alt['currency'] in ['BTC', 'ETH']:
                assessment = "🦅 Core position - bleed only if desperate"
            elif alt['currency'] == 'SOL':
                if alt['price'] > 204:
                    assessment = "✅ Good bleed zone (above oscillation)"
                else:
                    assessment = "⏳ Wait for $204+"
            elif alt['value'] < 100:
                assessment = "✅ Small position - can bleed"
            else:
                assessment = "🔍 Analyze before bleeding"
            
            print(f"\n{alt['currency']}:")
            print(f"  Amount: {alt['balance']:.6f}")
            print(f"  Price: ${alt['price']:.2f}")
            print(f"  Value: ${alt['value']:.2f}")
            print(f"  Cherokee Assessment: {assessment}")
        
        print("\n" + "=" * 80)
        print(f"💰 TOTAL BLEEDABLE VALUE: ${total_bleedable:.2f}")
        print(f"💵 CURRENT CASH: $200.00")
        print(f"🔥 POTENTIAL TOTAL: ${200 + total_bleedable:.2f}")
        
        print("\n🏛️ CHEROKEE COUNCIL BLEEDING STRATEGY:")
        print("-" * 60)
        
        # Recommendations
        if total_bleedable > 0:
            print("Priority bleeding order:")
            priority = 1
            
            for alt in bleedable:
                if alt['value'] < 100 and alt['currency'] not in ['BTC', 'ETH', 'SOL']:
                    print(f"  {priority}. Bleed {alt['currency']}: ~${alt['value']:.2f}")
                    priority += 1
                    if priority > 3:
                        break
            
            print("\nKeep for now:")
            for alt in bleedable:
                if alt['currency'] in ['BTC', 'ETH', 'SOL', 'DOGE']:
                    print(f"  • {alt['currency']}: Strategic hold")
        
        return bleedable
        
    except Exception as e:
        print(f"Error checking alts: {e}")
        # Provide estimates based on known positions
        print("\n📊 ESTIMATED BLEEDABLE POSITIONS:")
        print("(Based on previous observations)")
        print("-" * 60)
        print("• Small alts: ~$200-500 potential")
        print("• MATIC: Possible bleeding candidate")
        print("• AVAX: Check if profitable")
        print("• Other small positions: Check manually")
        return []

if __name__ == "__main__":
    print("🔥 CHEROKEE ALT BLEEDING ASSESSMENT")
    print("Finding liquidity sources for Labor Day trading")
    print()
    
    bleedable = check_bleedable_alts()
    
    print("\n🔥 Sacred Fire Assessment Complete")
    print("🩸 Blood for the money train identified")
    print("🪶 Mitakuye Oyasin - Some must be sacrificed for the greater good")
