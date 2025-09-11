#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 CHEROKEE COUNCIL PORTFOLIO ANALYSIS
Complete portfolio analysis by the tribal council
"""

import json
from pathlib import Path
from coinbase.rest import RESTClient
from datetime import datetime

def load_coinbase_config():
    """Load Coinbase configuration"""
    config_path = Path.home() / ".coinbase_config.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return None

def analyze_complete_portfolio():
    """Cherokee Council analyzes complete portfolio"""
    
    print("🏛️ CHEROKEE COUNCIL PORTFOLIO ANALYSIS")
    print("=" * 80)
    print("The tribe examines the complete portfolio...")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    try:
        # Initialize Coinbase client
        config = load_coinbase_config()
        if not config:
            print("❌ Coinbase config not found")
            return
        
        client = RESTClient(
            api_key=config['api_key'],
            api_secret=config['api_secret']
        )
        
        # Get all accounts
        accounts_response = client.get_accounts()
        accounts = accounts_response.accounts if hasattr(accounts_response, 'accounts') else []
        
        portfolio = {}
        total_value_usd = 0
        
        print("📊 COMPLETE PORTFOLIO BREAKDOWN:")
        print("-" * 80)
        
        # Analyze each account
        for account in accounts:
            currency = account['currency']
            balance = float(account['available_balance']['value'])
            
            if balance > 0:
                # Get USD value
                if currency == 'USD':
                    usd_value = balance
                    print(f"\n💵 USD CASH:")
                    print(f"   Balance: ${balance:,.2f}")
                    print(f"   Status: {'✅ LIQUID' if balance > 100 else '⚠️ LOW LIQUIDITY'}")
                elif currency == 'USDC':
                    usd_value = balance  # USDC = 1:1 with USD
                    print(f"\n💰 USDC (Stablecoin):")
                    print(f"   Balance: {balance:,.2f} USDC")
                    print(f"   USD Value: ${usd_value:,.2f}")
                    print(f"   Note: Can be converted to USD instantly")
                else:
                    # Get current price for crypto
                    try:
                        ticker = client.get_product(f"{currency}-USD")
                        price = float(ticker.price) if hasattr(ticker, 'price') else 0
                        usd_value = balance * price
                        
                        # Get 24h stats
                        try:
                            candles = client.get_candles(
                                product_id=f"{currency}-USD",
                                granularity="ONE_DAY",
                                start=1,
                                end=2
                            )
                            if candles and 'candles' in candles and len(candles['candles']) > 0:
                                candle = candles['candles'][0]
                                open_price = float(candle['open'])
                                change_24h = ((price - open_price) / open_price) * 100
                            else:
                                change_24h = 0
                        except:
                            change_24h = 0
                        
                        portfolio[currency] = {
                            'balance': balance,
                            'price': price,
                            'usd_value': usd_value,
                            'change_24h': change_24h
                        }
                        
                    except Exception as e:
                        # Asset might not have USD pair
                        usd_value = 0
                        portfolio[currency] = {
                            'balance': balance,
                            'price': 0,
                            'usd_value': 0,
                            'change_24h': 0
                        }
                
                total_value_usd += usd_value
        
        # Sort by USD value
        sorted_holdings = sorted(portfolio.items(), key=lambda x: x[1]['usd_value'], reverse=True)
        
        print("\n🔥 CRYPTO HOLDINGS (by value):")
        print("-" * 60)
        
        for currency, data in sorted_holdings:
            if data['usd_value'] > 0:
                percentage = (data['usd_value'] / total_value_usd) * 100
                
                # Determine emoji based on 24h change
                if data['change_24h'] > 5:
                    emoji = "🚀"
                elif data['change_24h'] > 0:
                    emoji = "📈"
                elif data['change_24h'] < -5:
                    emoji = "📉"
                else:
                    emoji = "➡️"
                
                print(f"\n{emoji} {currency}:")
                print(f"   Amount: {data['balance']:.6f}")
                print(f"   Price: ${data['price']:,.2f}")
                print(f"   Value: ${data['usd_value']:,.2f} ({percentage:.1f}%)")
                print(f"   24h: {data['change_24h']:+.1f}%")
                
                # Council recommendations
                if currency == 'ETH':
                    print("   🦅 Eagle Eye: ETH showing strong momentum!")
                    if data['change_24h'] > 3:
                        print("   🐦‍⬛ Raven: Consider taking some profits above $4,400")
                
                elif currency == 'SOL':
                    print("   🕷️ Spider: SOL performing well in oscillation range")
                    if data['price'] > 204:
                        print("   🐺 Coyote: Good profit-taking zone!")
                
                elif currency == 'DOGE':
                    if data['price'] < 0.21:
                        print("   🐺 Coyote: Still in blood bag accumulation zone")
                    else:
                        print("   🐺 Coyote: Ready to bleed profits above $0.22")
                
                # Liquidity recommendations
                if percentage < 5 and data['usd_value'] > 100:
                    print(f"   💰 Could sell for ~${data['usd_value']:.2f} liquidity")
        
        print("\n" + "=" * 80)
        print("🏛️ CHEROKEE COUNCIL LIQUIDITY ASSESSMENT:")
        print("-" * 60)
        
        # Find USD and USDC
        usd_available = 0
        usdc_available = 0
        
        for account in accounts:
            if account['currency'] == 'USD':
                usd_available = float(account['available_balance']['value'])
            elif account['currency'] == 'USDC':
                usdc_available = float(account['available_balance']['value'])
        
        total_liquid = usd_available + usdc_available
        
        print(f"💵 USD Cash: ${usd_available:,.2f}")
        print(f"💰 USDC Available: ${usdc_available:,.2f}")
        print(f"💧 Total Liquid: ${total_liquid:,.2f}")
        print()
        
        # Liquidity recommendations
        print("🪶 COUNCIL RECOMMENDATIONS FOR LIQUIDITY:")
        print("-" * 60)
        
        if total_liquid < 500:
            print("⚠️ URGENT: Need to generate liquidity!")
            print()
            
            # Find best candidates to sell
            sell_candidates = []
            for currency, data in sorted_holdings:
                if currency not in ['BTC', 'ETH'] and data['usd_value'] > 50:
                    if data['change_24h'] > 2 or percentage < 3:
                        sell_candidates.append({
                            'currency': currency,
                            'value': data['usd_value'],
                            'change': data['change_24h'],
                            'percentage': percentage
                        })
            
            if sell_candidates:
                print("📋 SUGGESTED SELLS FOR LIQUIDITY:")
                for candidate in sell_candidates[:5]:  # Top 5 candidates
                    print(f"   • Sell {candidate['currency']}: ~${candidate['value']:.2f}")
                    print(f"     (Currently {candidate['change']:+.1f}%, {candidate['percentage']:.1f}% of portfolio)")
        else:
            print("✅ Adequate liquidity for trading")
        
        print("\n" + "=" * 80)
        print(f"📊 TOTAL PORTFOLIO VALUE: ${total_value_usd:,.2f}")
        print(f"💧 LIQUIDITY RATIO: {(total_liquid/total_value_usd)*100:.1f}%")
        
        # Final council wisdom
        print("\n🔥 SACRED FIRE WISDOM:")
        if total_liquid > 1000:
            print("✅ Tribe has sufficient liquidity for trading")
        elif total_liquid > 500:
            print("⚠️ Liquidity adequate but should be increased")
        else:
            print("🚨 Critical liquidity - need to generate cash from alts")
        
        return {
            'total_value': total_value_usd,
            'usd_cash': usd_available,
            'usdc': usdc_available,
            'total_liquid': total_liquid,
            'holdings': portfolio
        }
        
    except Exception as e:
        print(f"Error analyzing portfolio: {e}")
        return None

def main():
    """Execute Cherokee Council portfolio analysis"""
    
    print("🔥 CHEROKEE COUNCIL CONVENED FOR PORTFOLIO REVIEW")
    print("ETH and SOL grew well - examining complete holdings")
    print()
    
    # Analyze portfolio
    portfolio_data = analyze_complete_portfolio()
    
    if portfolio_data:
        print("\n" + "=" * 80)
        print("🏛️ Council analysis complete")
        print("🔥 Sacred Fire illuminates the path forward")
        print("🪶 Mitakuye Oyasin - All holdings are connected")

if __name__ == "__main__":
    main()