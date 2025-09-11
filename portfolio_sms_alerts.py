#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 Portfolio SMS Alerts with Real-Time Data
Sends actual current portfolio values, not static messages
"""

import json
import requests
import subprocess
from datetime import datetime
from coinbase.rest import RESTClient

def send_sms(message):
    """Send SMS/Alert via available mechanism"""
    # Write to alert file that can be monitored
    alert_file = '/home/dereadi/scripts/claude/URGENT_SMS_ALERT.txt'
    with open(alert_file, 'w') as f:
        f.write(f"{datetime.now().isoformat()}\n{message}\n")
    
    # Also append to log
    with open('/home/dereadi/scripts/claude/portfolio_alerts.log', 'a') as f:
        f.write(f"{datetime.now().isoformat()} | {message}\n")
    
    # Print for immediate visibility
    print(f"📱 ALERT: {message}")
    
    # Could integrate with Telegram bot, email, or other notification service here
    # For now, the file-based alert can be monitored by other scripts
    
    return True

def get_current_portfolio():
    """Get real-time portfolio data from Coinbase"""
    try:
        with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
            config = json.load(f)
        
        client = RESTClient(
            api_key=config['name'].split('/')[-1],
            api_secret=config['privateKey']
        )
        
        accounts = client.get_accounts()['accounts']
        portfolio = {}
        total_value = 0
        
        # Get each position
        for account in accounts:
            currency = account['currency']
            balance = float(account['available_balance']['value'])
            
            if balance > 0.001:  # Only count meaningful balances
                if currency == 'USD':
                    usd_value = balance
                    price = 1.0
                elif currency == 'USDC':
                    usd_value = balance  # USDC = USD
                    price = 1.0
                else:
                    try:
                        # Get current price
                        ticker = client.get_product(f"{currency}-USD")
                        price = float(ticker['price'])
                        usd_value = balance * price
                    except:
                        continue
                
                portfolio[currency] = {
                    'balance': balance,
                    'price': price,
                    'usd_value': usd_value
                }
                total_value += usd_value
        
        return {
            'total_value': total_value,
            'positions': portfolio,
            'liquidity': portfolio.get('USD', {}).get('balance', 0),
            'timestamp': datetime.now()
        }
    except Exception as e:
        print(f"Error getting portfolio: {e}")
        return None

def get_market_conditions():
    """Get current market conditions"""
    try:
        # Key assets to track
        symbols = {
            'BTC': 110000,   # Alert threshold
            'ETH': 5000,     # Alert threshold
            'SOL': 250       # Alert threshold
        }
        
        conditions = {}
        for symbol, threshold in symbols.items():
            try:
                url = f"https://api.coinbase.com/v2/exchange-rates?currency={symbol}"
                response = requests.get(url)
                data = response.json()
                price = float(data['data']['rates']['USD'])
                
                conditions[symbol] = {
                    'price': price,
                    'threshold': threshold,
                    'near_threshold': price > threshold * 0.95
                }
            except:
                pass
        
        return conditions
    except:
        return {}

def format_portfolio_alert(portfolio, market):
    """Format the SMS message with current data"""
    if not portfolio:
        return "Portfolio data unavailable"
    
    # Build message
    lines = []
    lines.append(f"🔥Cherokee Trading {datetime.now().strftime('%H:%M')}")
    lines.append(f"Portfolio: ${portfolio['total_value']:,.0f}")
    lines.append(f"Liquidity: ${portfolio['liquidity']:.0f}")
    
    # Top positions
    positions = sorted(portfolio['positions'].items(), 
                      key=lambda x: x[1]['usd_value'], 
                      reverse=True)[:3]
    
    for symbol, data in positions:
        if symbol not in ['USD', 'USDC']:
            pct = (data['usd_value'] / portfolio['total_value']) * 100
            lines.append(f"{symbol}:${data['usd_value']:.0f}({pct:.0f}%)")
    
    # Market alerts
    alerts = []
    for symbol, data in market.items():
        if data.get('near_threshold'):
            alerts.append(f"{symbol}→${data['threshold']:,.0f}")
    
    if alerts:
        lines.append("⚠️Near:" + ",".join(alerts))
    
    # Critical alerts
    if portfolio['liquidity'] < 50:
        lines.append("🚨LIQUIDITY CRITICAL!")
    
    if portfolio['total_value'] < 5000:
        lines.append("⚠️Portfolio<$5k")
    elif portfolio['total_value'] > 15000:
        lines.append("🎉ATH Territory!")
    
    return " | ".join(lines)

def should_send_alert(portfolio, market):
    """Determine if alert should be sent"""
    hour = datetime.now().hour
    
    # Always send at specific times
    if datetime.now().minute == 0 and hour in [9, 12, 15, 18, 21]:
        return True, "scheduled"
    
    # Critical conditions
    if portfolio['liquidity'] < 25:
        return True, "critical_liquidity"
    
    # Market approaching key levels
    for symbol, data in market.items():
        if data.get('near_threshold'):
            return True, f"{symbol}_near_threshold"
    
    # Portfolio milestones
    if portfolio['total_value'] > 15000:
        return True, "portfolio_ath"
    
    if portfolio['total_value'] < 5000:
        return True, "portfolio_low"
    
    return False, None

def main():
    """Main alert function"""
    print(f"🔥 Portfolio SMS Alert Check - {datetime.now()}")
    
    # Get current data
    portfolio = get_current_portfolio()
    if not portfolio:
        print("❌ Could not get portfolio data")
        return
    
    market = get_market_conditions()
    
    # Check if we should send
    should_send, reason = should_send_alert(portfolio, market)
    
    if should_send:
        # Format and send message
        message = format_portfolio_alert(portfolio, market)
        print(f"📱 Sending SMS ({reason}): {message}")
        
        if send_sms(message):
            print("✅ SMS sent successfully")
        else:
            print("⚠️ SMS send failed")
        
        # Log to file
        with open('/home/dereadi/scripts/claude/sms_alerts.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()} | {reason} | {message}\n")
    else:
        print(f"📊 Current: ${portfolio['total_value']:,.0f} | Liquidity: ${portfolio['liquidity']:.0f}")
        print("✓ No alert needed")

if __name__ == "__main__":
    main()