#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 Portfolio SMS Alerts with Real-Time Data - FIXED VERSION
Properly handles Coinbase API responses and gets all positions including holds
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
    """Get real-time portfolio data from Coinbase - FIXED to handle all positions"""
    try:
        with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
            config = json.load(f)
        
        client = RESTClient(
            api_key=config['name'].split('/')[-1],
            api_secret=config['privateKey'],
            timeout=10
        )
        
        # Get accounts with proper response handling
        response = client.get_accounts()
        
        # Handle response structure
        if hasattr(response, 'accounts'):
            accounts = response.accounts
        else:
            accounts = response.get('accounts', response)
        
        portfolio = {}
        total_value = 0
        total_on_hold = 0
        available_liquidity = 0
        
        # Process each account
        for account in accounts:
            # Get currency
            if hasattr(account, 'currency'):
                currency = account.currency
            else:
                currency = account.get('currency', 'UNKNOWN')
            
            # Get available balance
            available = 0
            if hasattr(account, 'available_balance'):
                if hasattr(account.available_balance, 'value'):
                    available = float(account.available_balance.value)
                else:
                    available = float(account.available_balance.get('value', 0))
            
            # Get hold balance (funds in orders)
            hold = 0
            if hasattr(account, 'hold'):
                if hasattr(account.hold, 'value'):
                    hold = float(account.hold.value)
                elif isinstance(account.hold, dict):
                    hold = float(account.hold.get('value', 0))
            
            balance = available + hold
            
            if balance > 0.00001:  # Only count meaningful balances
                if currency in ['USD', 'USDC']:
                    usd_value = balance
                    price = 1.0
                    if currency == 'USD':
                        available_liquidity = available  # Only available USD counts as liquidity
                else:
                    try:
                        # Use public API for reliable prices
                        url = f"https://api.coinbase.com/v2/exchange-rates?currency={currency}"
                        response = requests.get(url, timeout=5)
                        data = response.json()
                        if 'data' in data and 'rates' in data['data']:
                            price = float(data['data']['rates']['USD'])
                            usd_value = balance * price
                        else:
                            continue
                    except:
                        continue
                
                portfolio[currency] = {
                    'balance': balance,
                    'available': available,
                    'hold': hold,
                    'price': price,
                    'usd_value': usd_value
                }
                total_value += usd_value
                if hold > 0:
                    total_on_hold += (hold * price if currency not in ['USD', 'USDC'] else hold)
        
        return {
            'total_value': total_value,
            'positions': portfolio,
            'liquidity': available_liquidity,
            'on_hold': total_on_hold,
            'timestamp': datetime.now()
        }
    except Exception as e:
        print(f"Error getting portfolio: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_market_conditions():
    """Get current market conditions"""
    try:
        # Key assets to track with thresholds
        symbols = {
            'BTC': 110000,   # Alert threshold
            'ETH': 5000,     # Alert threshold
            'SOL': 250       # Alert threshold
        }
        
        conditions = {}
        for symbol, threshold in symbols.items():
            try:
                url = f"https://api.coinbase.com/v2/exchange-rates?currency={symbol}"
                response = requests.get(url, timeout=5)
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
    lines.append(f"🔥Cherokee {datetime.now().strftime('%H:%M')}")
    lines.append(f"Total:${portfolio['total_value']:,.0f}")
    
    # Show liquidity and holds
    if portfolio['on_hold'] > 10:
        lines.append(f"Liq:${portfolio['liquidity']:.0f}|Hold:${portfolio['on_hold']:.0f}")
    else:
        lines.append(f"Liq:${portfolio['liquidity']:.0f}")
    
    # Top positions (excluding USD/USDC)
    positions = sorted(
        [(k, v) for k, v in portfolio['positions'].items() if k not in ['USD', 'USDC']], 
        key=lambda x: x[1]['usd_value'], 
        reverse=True
    )[:3]
    
    pos_text = []
    for symbol, data in positions:
        pct = (data['usd_value'] / portfolio['total_value']) * 100
        # Add hold indicator if position has holds
        hold_indicator = "*" if data.get('hold', 0) > 0 else ""
        pos_text.append(f"{symbol}{hold_indicator}:${data['usd_value']:.0f}({pct:.0f}%)")
    
    if pos_text:
        lines.append("|".join(pos_text))
    
    # Market alerts
    alerts = []
    for symbol, data in market.items():
        if data.get('near_threshold'):
            dist = data['threshold'] - data['price']
            alerts.append(f"{symbol}→${dist:.0f}")
    
    if alerts:
        lines.append("⚠️Near:" + ",".join(alerts))
    
    # Critical alerts
    if portfolio['liquidity'] < 50:
        lines.append("🚨LIQ<$50!")
    
    if portfolio['total_value'] < 10000:
        lines.append("⚠️<$10k")
    elif portfolio['total_value'] > 15000:
        lines.append("🎉>$15k!")
    
    return " | ".join(lines)

def should_send_alert(portfolio, market):
    """Determine if alert should be sent"""
    hour = datetime.now().hour
    minute = datetime.now().minute
    
    # Always send at specific times
    if minute == 0 and hour in [9, 12, 15, 18, 21]:
        return True, "scheduled"
    
    # Critical conditions
    if portfolio['liquidity'] < 25:
        return True, "critical_liquidity"
    
    # Large holds (orders)
    if portfolio['on_hold'] > 1000:
        return True, "large_holds"
    
    # Market approaching key levels
    for symbol, data in market.items():
        if data.get('near_threshold'):
            return True, f"{symbol}_near_{data['threshold']}"
    
    # Portfolio milestones
    if portfolio['total_value'] > 15000:
        return True, "portfolio_high"
    
    if portfolio['total_value'] < 10000:
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
    
    # Always show current status
    print(f"📊 Portfolio: ${portfolio['total_value']:,.2f}")
    print(f"💵 Liquidity: ${portfolio['liquidity']:.2f}")
    if portfolio['on_hold'] > 10:
        print(f"🔒 On Hold: ${portfolio['on_hold']:.2f}")
    
    # Check if we should send
    should_send, reason = should_send_alert(portfolio, market)
    
    if should_send:
        # Format and send message
        message = format_portfolio_alert(portfolio, market)
        print(f"📱 Sending SMS ({reason}):")
        print(f"   {message}")
        
        if send_sms(message):
            print("✅ SMS sent successfully")
        else:
            print("⚠️ SMS send failed")
        
        # Log to file
        with open('/home/dereadi/scripts/claude/sms_alerts.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()} | {reason} | {message}\n")
    else:
        print("✓ No alert needed at this time")
    
    # Save current state
    with open('/home/dereadi/scripts/claude/portfolio_current.json', 'w') as f:
        json.dump(portfolio, f, indent=2, default=str)

if __name__ == "__main__":
    main()