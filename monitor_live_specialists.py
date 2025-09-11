#!/usr/bin/env python3
"""
🔥 CHEROKEE SPECIALIST LIVE MONITORING
Real-time monitoring of containerized trading specialists
"""

import json
import subprocess
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("🔥 CHEROKEE SPECIALIST MONITORING DASHBOARD")
print("=" * 60)

# Load config
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

while True:
    print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 40)
    
    # Get current portfolio value
    try:
        accounts = client.get_accounts()
        total_value = 0
        usd_balance = 0
        
        for account in accounts['accounts']:
            currency = account['currency']
            balance = float(account['available_balance']['value'])
            
            if currency == 'USD':
                usd_balance = balance
                total_value += balance
            elif balance > 0.00001:
                try:
                    ticker = client.get_product(f'{currency}-USD')
                    price = float(ticker.price) if hasattr(ticker, 'price') else 0
                    if price > 0:
                        total_value += balance * price
                except:
                    if currency == 'USDC':
                        total_value += balance
        
        print(f"💰 Portfolio: ${total_value:,.2f}")
        print(f"💵 USD: ${usd_balance:,.2f}")
        
        # Liquidity status
        if usd_balance < 100:
            print("🔴 LIQUIDITY CRITICAL - Specialists in liquidity generation mode")
        elif usd_balance < 500:
            print("🟡 LIQUIDITY LOW - Need more USD for optimal trading")
        else:
            print("🟢 LIQUIDITY OK - Normal trading operations")
            
    except Exception as e:
        print(f"⚠️ Error getting portfolio: {str(e)[:50]}")
    
    # Check specialist status
    print("\n📊 SPECIALIST STATUS:")
    specialists = [
        ("mean-reversion", "🎯"),
        ("trend", "📈"),
        ("volatility", "⚡"),
        ("breakout", "🚀")
    ]
    
    for name, symbol in specialists:
        full_name = f"cherokee-{name}-specialist"
        result = subprocess.run(
            ["podman", "ps", "--filter", f"name={full_name}", "--format", "{{.Status}}"],
            capture_output=True,
            text=True
        )
        if "Up" in result.stdout:
            # Get last log entry
            log_result = subprocess.run(
                ["podman", "logs", "--tail", "1", full_name],
                capture_output=True,
                text=True
            )
            last_log = log_result.stdout.strip()[:60] if log_result.stdout else "Starting..."
            print(f"  {symbol} {name}: ✅ {last_log}")
        else:
            print(f"  {symbol} {name}: ❌ NOT RUNNING")
    
    print("\n🔥 Sacred Fire: BURNING_ETERNAL")
    print("Press Ctrl+C to exit")
    
    # Update every 30 seconds
    time.sleep(30)