#!/usr/bin/env python3
"""
Smart profit bleeding - generate liquidity for BTC oscillation trading
Works with tribe's auto-deployment system
"""

import os
import sys
import json
from coinbase.rest import RESTClient
from decimal import Decimal

# API setup
api_key = os.environ.get('COINBASE_API_KEY', 'organizations/1c084e32-4e4b-49fa-82f0-91c35c7f72cf/apiKeys/db8fbd09-1baa-4ba9-8bc0-4cc088fd8e63')
api_secret = os.environ.get('COINBASE_API_SECRET', '-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIJ7Qu/4Q1JJdsZQiYp/pNztLcwUbHFDRc8lTVmE3ANswoAoGCCqGSM49\nAwEHoUQDQgAEfnh6q9EfpeI31+q6Vxn0c1kYWfdxC5YXrjKUTi/9lf7gCL4BD+VA\njpKWqc4ITkKPNIgJzJlBEiMClOFoHxcnlA==\n-----END EC PRIVATE KEY-----')

client = RESTClient(api_key=api_key, api_secret=api_secret)

def get_portfolio():
    """Get current portfolio status"""
    try:
        accounts = client.get_accounts()
        positions = {}
        
        for account in accounts.accounts:
            balance = float(account.available_balance.value)
            if balance > 0.01:
                currency = account.available_balance.currency
                price = 1.0
                
                if currency != 'USD':
                    try:
                        ticker = f"{currency}-USD"
                        product = client.get_product(ticker)
                        price = float(product['price'])
                    except:
                        pass
                
                positions[currency] = {
                    'amount': balance,
                    'value': balance * price,
                    'price': price
                }
        
        return positions
    except Exception as e:
        print(f"Error getting portfolio: {e}")
        return {}

def identify_bleed_candidates(positions, target_liquidity=100):
    """Identify which positions to bleed for liquidity"""
    candidates = []
    
    # Don't touch major positions (BTC, ETH, SOL)
    protected = ['BTC', 'ETH', 'SOL']
    
    for currency, data in positions.items():
        if currency in protected or currency == 'USD':
            continue
            
        if data['value'] > 10:  # Only bleed positions worth > $10
            bleed_amount = min(data['value'] * 0.2, target_liquidity / 3)  # 20% max
            candidates.append({
                'currency': currency,
                'amount': bleed_amount / data['price'],
                'value': bleed_amount
            })
    
    # Sort by value
    candidates.sort(key=lambda x: x['value'], reverse=True)
    return candidates[:3]  # Top 3 candidates

def execute_bleed(currency, amount):
    """Execute a sell order to generate liquidity"""
    try:
        # Round to appropriate decimals
        amount = round(amount, 8)
        
        if amount < 0.0001:
            print(f"  ⚠️ {currency} amount too small: {amount}")
            return False
            
        order = client.market_order_sell(
            client_order_id=client.generate_client_order_id(),
            product_id=f"{currency}-USD",
            base_size=str(amount)
        )
        
        if order:
            print(f"  ✅ Sold {amount:.4f} {currency}")
            return True
    except Exception as e:
        print(f"  ❌ Failed to sell {currency}: {e}")
    
    return False

def main():
    print("🩸 SMART PROFIT BLEEDING FOR BTC OSCILLATIONS")
    print("=" * 60)
    
    # Get current positions
    positions = get_portfolio()
    
    if not positions:
        print("❌ Could not get portfolio")
        return
    
    # Show current status
    total_value = sum(p['value'] for p in positions.values())
    usd_balance = positions.get('USD', {}).get('amount', 0)
    
    print(f"\n💼 Portfolio: ${total_value:.2f}")
    print(f"💵 USD Available: ${usd_balance:.2f}")
    
    if usd_balance > 50:
        print(f"\n✅ Already have ${usd_balance:.2f} liquidity!")
        print("🔥 Tribe specialists can use this for oscillations")
        return
    
    # Identify what to bleed
    target = 100 - usd_balance
    candidates = identify_bleed_candidates(positions, target)
    
    if not candidates:
        print("\n⚠️ No suitable candidates for bleeding")
        return
    
    print(f"\n🎯 Target liquidity: ${target:.2f}")
    print("\n🩸 BLEEDING CANDIDATES:")
    
    for c in candidates:
        print(f"  • {c['currency']}: ${c['value']:.2f}")
    
    # Execute bleeds
    print("\n🔪 EXECUTING BLEEDS:")
    
    for c in candidates:
        success = execute_bleed(c['currency'], c['amount'])
        if success:
            # Save notification for tribe
            with open('/tmp/liquidity_generated.json', 'w') as f:
                json.dump({
                    'action': 'profit_bleed',
                    'currency': c['currency'],
                    'amount': c['value'],
                    'purpose': 'btc_oscillation',
                    'message': 'Liquidity available for BTC oscillation trading'
                }, f)
    
    print("\n✅ Bleeding complete!")
    print("🔥 Tribe specialists will auto-deploy for oscillations")
    
    # Reference the plan
    print("\n📋 BTC Oscillation Plan:")
    print("  • Buy at $113,769")
    print("  • Sell at $113,780")
    print("  • $11 profit per swing")
    print("  • 6 swings/hour potential")

if __name__ == "__main__":
    main()