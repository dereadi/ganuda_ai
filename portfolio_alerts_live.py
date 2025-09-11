#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 Cherokee Trading Council - LIVE Portfolio Alerts
Actually fetches CURRENT prices and updates properly!
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

def send_alert(message):
    """Send alert via file system for monitoring"""
    alert_file = '/home/dereadi/scripts/claude/URGENT_SMS_ALERT.txt'
    with open(alert_file, 'w') as f:
        f.write(f"{datetime.now().isoformat()}\n{message}\n")
    
    with open('/home/dereadi/scripts/claude/portfolio_alerts.log', 'a') as f:
        f.write(f"{datetime.now().isoformat()} | {message}\n")
    
    print(f"📱 ALERT: {message}")
    return True

def get_live_portfolio():
    """Get ACTUAL LIVE portfolio data"""
    try:
        # Load API credentials
        with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
            config = json.load(f)
        
        client = RESTClient(
            api_key=config['name'].split('/')[-1],
            api_secret=config['privateKey'],
            timeout=10
        )
        
        # Get ALL accounts including holds
        accounts = client.get_accounts()
        
        portfolio = {
            'timestamp': datetime.now().isoformat(),
            'positions': {},
            'total_value': 0,
            'liquidity': 0,
            'on_hold': 0
        }
        
        # Process each account
        for account in accounts.accounts if hasattr(accounts, 'accounts') else accounts:
            if not hasattr(account, 'balance') or not hasattr(account.balance, 'value'):
                continue
                
            balance = float(account.balance.value)
            if balance <= 0:
                continue
            
            currency = account.balance.currency
            
            # Handle USD separately
            if currency == 'USD':
                available = float(account.available_balance.value) if hasattr(account, 'available_balance') else balance
                hold = float(account.hold.value) if hasattr(account, 'hold') and hasattr(account.hold, 'value') else 0
                
                portfolio['liquidity'] = available
                portfolio['on_hold'] = hold
                portfolio['positions']['USD'] = {
                    'balance': balance,
                    'value': balance,
                    'hold': hold
                }
                portfolio['total_value'] += balance
            else:
                # Get LIVE price for crypto
                try:
                    ticker = client.get_product(f"{currency}-USD")
                    if hasattr(ticker, 'price'):
                        price = float(ticker.price)
                    else:
                        # Try market trades as backup
                        trades = client.get_market_trades(f"{currency}-USD", limit=1)
                        if trades and hasattr(trades, 'trades') and len(trades.trades) > 0:
                            price = float(trades.trades[0].price)
                        else:
                            price = 0
                    
                    usd_value = balance * price
                    
                    portfolio['positions'][currency] = {
                        'balance': balance,
                        'price': price,
                        'value': usd_value
                    }
                    portfolio['total_value'] += usd_value
                    
                except Exception as e:
                    print(f"⚠️ Could not get price for {currency}: {e}")
        
        # Save current state
        with open('/home/dereadi/scripts/claude/portfolio_current.json', 'w') as f:
            json.dump(portfolio, f, indent=2, default=str)
        
        return portfolio
        
    except Exception as e:
        print(f"❌ Error fetching portfolio: {e}")
        return None

def format_alert(portfolio):
    """Format portfolio for SMS/alert"""
    if not portfolio:
        return "❌ Unable to fetch portfolio data"
    
    total = portfolio['total_value']
    liquidity = portfolio['liquidity']
    on_hold = portfolio['on_hold']
    
    # Get top positions
    positions = []
    for currency, data in portfolio['positions'].items():
        if currency != 'USD' and data.get('value', 0) > 100:
            pct = (data['value'] / total * 100)
            positions.append(f"{currency}:${data['value']:.0f}({pct:.0f}%)")
    
    # Build alert
    alert = f"🔥Cherokee {datetime.now().strftime('%H:%M')} | "
    alert += f"Total:${total:.0f} | "
    alert += f"Liq:${liquidity:.0f}"
    
    if on_hold > 0:
        alert += f"|Hold:${on_hold:.0f}"
    
    if positions:
        alert += " | " + "|".join(positions[:3])  # Top 3 positions
    
    # Add status flags
    if liquidity < 50:
        alert += " | 🚨LIQ<$50!"
    if total > 15000:
        alert += " | 🎉>$15k!"
    elif total > 14000:
        alert += " | 📈>$14k"
    
    return alert

def main():
    """Main execution"""
    print(f"🔥 Cherokee Live Portfolio Alert - {datetime.now()}")
    
    # Get LIVE data
    portfolio = get_live_portfolio()
    
    if portfolio:
        print(f"📊 Portfolio: ${portfolio['total_value']:.2f}")
        print(f"💵 Liquidity: ${portfolio['liquidity']:.2f}")
        print(f"🔒 On Hold: ${portfolio['on_hold']:.2f}")
        
        # Format and send alert
        alert = format_alert(portfolio)
        send_alert(alert)
        print("✅ Alert sent with LIVE data!")
    else:
        print("❌ Failed to fetch portfolio")
        send_alert("❌ Portfolio fetch failed - check API")

if __name__ == "__main__":
    main()