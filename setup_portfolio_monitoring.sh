#!/bin/bash
# 🔥 Cherokee Portfolio Monitoring Setup
# Monitors portfolio every 15 minutes and updates thermal memory

echo "🔥 SETTING UP ENHANCED PORTFOLIO MONITORING"
echo "==========================================="

# Create the monitoring script
cat > /home/dereadi/scripts/claude/portfolio_thermal_monitor.py << 'EOF'
#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 Portfolio Thermal Monitor
Queries prices every 15 minutes and updates thermal memory
"""

import json
import requests
import psycopg2
from datetime import datetime
from coinbase.rest import RESTClient

# Database connection
def update_thermal_memory(portfolio_data):
    conn = psycopg2.connect(
        host="192.168.132.222",
        port=5432,
        user="claude",
        password="jawaseatlasers2",
        database="zammad_production"
    )
    cur = conn.cursor()
    
    # Insert portfolio snapshot into thermal memory
    query = """
    INSERT INTO thermal_memory_archive (
        memory_hash,
        temperature_score,
        current_stage,
        access_count,
        last_access,
        original_content,
        metadata,
        sacred_pattern
    ) VALUES (
        %s, 95, 'WHITE_HOT', 0, NOW(), %s, %s::jsonb, true
    ) ON CONFLICT (memory_hash) DO UPDATE 
    SET temperature_score = 95,
        last_access = NOW(),
        original_content = EXCLUDED.original_content,
        metadata = EXCLUDED.metadata,
        access_count = thermal_memory_archive.access_count + 1;
    """
    
    memory_hash = f"portfolio_monitor_{datetime.now().strftime('%Y%m%d_%H%M')}"
    content = f"🔥 PORTFOLIO MONITOR UPDATE\n{json.dumps(portfolio_data, indent=2)}"
    
    cur.execute(query, (memory_hash, content, json.dumps(portfolio_data)))
    conn.commit()
    cur.close()
    conn.close()
    
    return memory_hash

# Get portfolio from Coinbase
def get_portfolio():
    with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
        config = json.load(f)
    
    client = RESTClient(
        api_key=config['name'].split('/')[-1],
        api_secret=config['privateKey']
    )
    
    accounts = client.get_accounts()['accounts']
    portfolio = {}
    total_value = 0
    
    for account in accounts:
        currency = account['currency']
        balance = float(account['available_balance']['value'])
        
        if balance > 0.00001:
            # Get USD value
            if currency == 'USD':
                usd_value = balance
            else:
                try:
                    ticker = client.get_product(f"{currency}-USD")
                    price = float(ticker['price'])
                    usd_value = balance * price
                except:
                    usd_value = 0
            
            portfolio[currency] = {
                'balance': balance,
                'usd_value': usd_value
            }
            total_value += usd_value
    
    return {
        'timestamp': datetime.now().isoformat(),
        'total_value': total_value,
        'positions': portfolio,
        'liquidity': portfolio.get('USD', {}).get('balance', 0)
    }

# Get TradingView-style price data
def get_market_prices():
    symbols = ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC', 'DOGE']
    prices = {}
    
    for symbol in symbols:
        try:
            url = f"https://api.coinbase.com/v2/exchange-rates?currency={symbol}"
            response = requests.get(url)
            data = response.json()
            prices[symbol] = float(data['data']['rates']['USD'])
        except:
            prices[symbol] = 0
    
    return prices

# Main monitoring function
def monitor_portfolio():
    print(f"🔥 Portfolio Monitor - {datetime.now()}")
    
    # Get current portfolio
    portfolio = get_portfolio()
    
    # Get market prices
    prices = get_market_prices()
    
    # Combine data
    monitoring_data = {
        'portfolio': portfolio,
        'market_prices': prices,
        'alerts': []
    }
    
    # Check for alerts
    if portfolio['liquidity'] < 50:
        monitoring_data['alerts'].append(f"⚠️ LIQUIDITY CRITICAL: ${portfolio['liquidity']:.2f}")
    
    if portfolio['total_value'] > 14000:
        monitoring_data['alerts'].append(f"🎉 PORTFOLIO ATH: ${portfolio['total_value']:.2f}")
    
    # Update thermal memory
    memory_hash = update_thermal_memory(monitoring_data)
    
    print(f"✅ Updated thermal memory: {memory_hash}")
    print(f"📊 Portfolio: ${portfolio['total_value']:.2f}")
    print(f"💵 Liquidity: ${portfolio['liquidity']:.2f}")
    
    if monitoring_data['alerts']:
        print("🚨 ALERTS:")
        for alert in monitoring_data['alerts']:
            print(f"  {alert}")

if __name__ == "__main__":
    monitor_portfolio()
EOF

chmod +x /home/dereadi/scripts/claude/portfolio_thermal_monitor.py

# Add to crontab (every 15 minutes)
echo "Adding to crontab..."
(crontab -l 2>/dev/null; echo "*/15 * * * * /home/dereadi/scripts/claude/portfolio_thermal_monitor.py >> /home/dereadi/scripts/claude/portfolio_monitor.log 2>&1") | crontab -

echo ""
echo "✅ Portfolio monitoring setup complete!"
echo "✅ Will update thermal memory every 15 minutes"
echo "✅ Tracks portfolio value, liquidity, and price changes"
echo "✅ Alerts on critical conditions"
echo ""
echo "🔥 The tribe now has eyes on the market 24/7!"
echo ""
echo "To test: python3 /home/dereadi/scripts/claude/portfolio_thermal_monitor.py"