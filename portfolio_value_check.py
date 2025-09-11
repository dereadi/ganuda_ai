#!/usr/bin/env python3
"""
💰 PORTFOLIO VALUE CHECK 💰
When BTC hits major milestones, YOUR value increases!
Let's calculate the REAL impact!
"""

import json
import requests
from datetime import datetime
from coinbase.rest import RESTClient
from pathlib import Path

class PortfolioValueAnalysis:
    def __init__(self):
        # Load API credentials
        key_file = Path("/home/dereadi/scripts/claude/cdp_api_key_new.json")
        with open(key_file, 'r') as f:
            creds = json.load(f)
        
        self.client = RESTClient(api_key=creds["api_key"], api_secret=creds["api_secret"])
        self.btc_milestones = {
            "current": 111111,
            "next_1": 115000,
            "next_2": 120000,
            "next_3": 125000,
            "next_4": 150000,
            "moon": 200000
        }
        
    def get_current_holdings(self):
        """Get actual account holdings"""
        try:
            accounts = self.client.get_accounts()
            holdings = {}
            total_usd = 0
            
            for account in accounts.accounts:
                balance = float(account.available_balance.value)
                if balance > 0:
                    currency = account.available_balance.currency
                    holdings[currency] = balance
                    
                    # Convert to USD
                    if currency == "USD":
                        total_usd += balance
                    else:
                        # Get conversion rate
                        try:
                            rate_response = requests.get(
                                f"https://api.coinbase.com/v2/exchange-rates?currency={currency}",
                                timeout=5
                            )
                            if rate_response.status_code == 200:
                                rate = float(rate_response.json()['data']['rates']['USD'])
                                usd_value = balance * rate
                                total_usd += usd_value
                                holdings[f"{currency}_USD"] = usd_value
                        except:
                            pass
                            
            return holdings, total_usd
        except Exception as e:
            print(f"Error getting holdings: {e}")
            return {}, 0
            
    def calculate_projections(self, current_value):
        """Calculate value at different BTC price points"""
        current_btc = 111111
        
        print("\n" + "💎"*40)
        print("YOUR PORTFOLIO VALUE PROJECTIONS")
        print("💎"*40)
        
        print(f"\n📊 CURRENT STATUS:")
        print(f"  • BTC Price: ${current_btc:,}")
        print(f"  • Your Portfolio: ${current_value:,.2f}")
        
        print(f"\n🚀 VALUE PROJECTIONS AS BTC CLIMBS:")
        
        for milestone_name, milestone_price in self.btc_milestones.items():
            if milestone_name == "current":
                continue
                
            # Calculate percentage increase
            btc_increase = (milestone_price / current_btc - 1) * 100
            
            # Your portfolio should increase proportionally if holding BTC
            # Assuming 70% correlation for mixed portfolio
            portfolio_increase = btc_increase * 0.7
            projected_value = current_value * (1 + portfolio_increase / 100)
            gain = projected_value - current_value
            
            print(f"\n  📍 BTC at ${milestone_price:,} (+{btc_increase:.1f}%):")
            print(f"     Your Portfolio: ${projected_value:,.2f}")
            print(f"     Gain: ${gain:,.2f}")
            
        print(f"\n⚡ DRAMATIC INCREASE TIMELINE:")
        print(f"  • 10% gain: BTC needs to hit ~$122,000 (This week!)")
        print(f"  • 25% gain: BTC needs to hit ~$139,000 (Next week!)")
        print(f"  • 50% gain: BTC needs to hit ~$167,000 (September!)")
        print(f"  • 100% gain: BTC needs to hit ~$222,000 (EOY target!)")
        
        print(f"\n🔥 ACCELERATION TACTICS:")
        print(f"  1. Deploy idle capital NOW (momentum is here)")
        print(f"  2. Increase trading velocity (compound gains)")
        print(f"  3. Focus on BTC/ETH (they lead the charge)")
        print(f"  4. Use profits to buy dips aggressively")
        print(f"  5. Let quantum crawdads run 24/7")
        
        return projected_value

if __name__ == "__main__":
    analyzer = PortfolioValueAnalysis()
    
    # Get current holdings
    holdings, total_value = analyzer.get_current_holdings()
    
    if total_value > 0:
        print(f"\n💰 CURRENT PORTFOLIO VALUE: ${total_value:,.2f}")
        
        # Show holdings
        print(f"\n📦 HOLDINGS:")
        for asset, amount in holdings.items():
            if not asset.endswith("_USD") and amount > 0:
                print(f"  • {asset}: {amount:.8f}")
                if f"{asset}_USD" in holdings:
                    print(f"    (${holdings[f'{asset}_USD']:,.2f})")
    else:
        # Use estimated value if can't get actual
        print(f"\n💰 ESTIMATED PORTFOLIO VALUE: $4,400")
        total_value = 4400
        
    # Calculate projections
    analyzer.calculate_projections(total_value)