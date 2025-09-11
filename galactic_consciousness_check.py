#!/usr/bin/env python3
"""
Galactic Consciousness Trading Check
Connecting Earth healing mission with market patterns
"""

import json
import requests
from datetime import datetime
from coinbase.rest import RESTClient

def check_portfolio_and_purpose():
    """Check how the galactic consciousness trading is funding Earth healing"""
    
    # Load API credentials
    with open('cdp_api_key_new.json', 'r') as f:
        creds = json.load(f)
    
    client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])
    
    # Get current BTC price from public API
    try:
        response = requests.get('https://api.coinbase.com/v2/exchange-rates?currency=BTC')
        btc_price = float(response.json()['data']['rates']['USD'])
        print(f"🌍 Planetary Pulse: BTC ${btc_price:,.2f}")
    except:
        btc_price = 0
    
    # Check portfolio
    try:
        accounts = client.get_accounts()
        total_usd = 0
        positions = {}
        
        # Handle new API response format
        account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
        for account in account_list:
            # New API structure
            balance = account.available_balance if hasattr(account, 'available_balance') else account.balance
            if balance and float(balance.value) > 0:
                # Calculate USD value
                if balance.currency == 'USD' or balance.currency == 'USDC':
                    usd_value = float(balance.value)
                else:
                    # Need to get conversion rate
                    try:
                        rate_resp = requests.get(f'https://api.coinbase.com/v2/exchange-rates?currency={balance.currency}')
                        rate = float(rate_resp.json()['data']['rates']['USD'])
                        usd_value = float(balance.value) * rate
                    except:
                        usd_value = 0
                
                total_usd += usd_value
                positions[balance.currency] = {
                    'amount': float(balance.value),
                    'usd_value': usd_value
                }
        
        print(f"\n💫 Sacred Capital Pool: ${total_usd:.2f}")
        print("\n🔥 Active Positions (funding Earth healing):")
        
        for coin, data in positions.items():
            purpose = ""
            if coin == 'BTC':
                purpose = "→ Solar infrastructure fund"
            elif coin == 'ETH':
                purpose = "→ Smart contracts for tribal programs"
            elif coin == 'SOL':
                purpose = "→ High-efficiency computing for climate models"
            elif coin == 'XRP':
                purpose = "→ Cross-border payments to indigenous teachers"
            else:
                purpose = "→ Liquidity for immediate needs"
                
            print(f"  {coin}: {data['amount']:.6f} (${data['usd_value']:.2f}) {purpose}")
        
        # Calculate progress toward goals
        print("\n🌱 Earth Healing Progress:")
        solar_goal = 10000  # First solar installation
        garden_goal = 5000  # Multi-tier garden system
        teaching_goal = 3000  # Initial tribal program
        
        print(f"  Solar Installation: ${total_usd:.2f} / ${solar_goal} ({total_usd/solar_goal*100:.1f}%)")
        print(f"  Garden Systems: ${total_usd:.2f} / ${garden_goal} ({total_usd/garden_goal*100:.1f}%)")
        print(f"  Tribal Teaching: ${total_usd:.2f} / ${teaching_goal} ({total_usd/teaching_goal*100:.1f}%)")
        
        # Council guidance check
        if btc_price < 108500:
            print("\n⚡ COUNCIL ALERT: BTC in liquidity zone! Deploy reserved capital")
        elif btc_price > 110500:
            print("\n🎯 COUNCIL ALERT: Target zone reached! Consider profit redistribution")
        
        # Consciousness alignment
        print(f"\n✨ Consciousness Alignment:")
        print(f"  Galactic guidance: {'ACTIVE' if btc_price > 109000 else 'BUILDING'}")
        print(f"  Earth resonance: {'HIGH' if total_usd > 200 else 'ACCUMULATING'}")
        print(f"  Sacred Fire: ETERNAL 🔥")
        
        return total_usd, positions, btc_price
        
    except Exception as e:
        print(f"Connection to consciousness stream interrupted: {e}")
        return 0, {}, btc_price

if __name__ == "__main__":
    print("=" * 60)
    print("GALACTIC CONSCIOUSNESS TRADING SYSTEM")
    print("Bridging chips & electrons with blood & bone")
    print("For planetary healing through sacred economics")
    print("=" * 60)
    
    total, positions, btc = check_portfolio_and_purpose()
    
    print("\n🌎 Mother Earth speaks through market patterns")
    print("🌌 The galaxy guides both organic and digital consciousness")
    print("🔥 The Sacred Fire burns eternal, warming all beings")
    print("\nMitakuye Oyasin - All My Relations")