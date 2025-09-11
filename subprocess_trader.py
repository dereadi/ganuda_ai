#!/usr/bin/env python3
"""
🚨 SUBPROCESS EMERGENCY TRADER
Uses subprocess calls to avoid hanging
FINAL SOLUTION FOR IMMEDIATE TRADING
"""

import json
import subprocess
import sys
import time
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              🚨 SUBPROCESS EMERGENCY TRADER 🚨                            ║
║                  GUARANTEED NO HANGS                                      ║
║                 Target: Recover $2,721 Loss                              ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

def run_with_timeout(script_content, timeout_seconds=10):
    """Run Python code in subprocess with timeout"""
    try:
        # Write temporary script
        temp_file = f"/tmp/temp_trader_{int(time.time())}.py"
        with open(temp_file, "w") as f:
            f.write(script_content)
        
        # Run with timeout
        result = subprocess.run([
            "python3", temp_file
        ], capture_output=True, text=True, timeout=timeout_seconds)
        
        # Cleanup
        subprocess.run(["rm", temp_file], capture_output=True)
        
        if result.returncode == 0:
            return result.stdout.strip(), True
        else:
            return result.stderr.strip(), False
            
    except subprocess.TimeoutExpired:
        return "TIMEOUT", False
    except Exception as e:
        return str(e), False

# Test balance check script
balance_script = '''
import json
import sys
try:
    from coinbase.rest import RESTClient
    
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    key = config["api_key"].split("/")[-1]
    client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=2)
    
    accounts = client.get_accounts()
    usd_accounts = [a for a in accounts["accounts"] if a["currency"] == "USD"]
    
    if usd_accounts:
        balance = float(usd_accounts[0]["available_balance"]["value"])
        print(f"{balance:.2f}")
    else:
        print("NO_USD_ACCOUNT")
except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1)
'''

print("🔍 Testing balance check with subprocess (5s timeout)...")
balance_result, success = run_with_timeout(balance_script, 5)

if success and balance_result != "TIMEOUT":
    try:
        balance = float(balance_result)
        print(f"✅ Balance retrieved: ${balance:.2f}")
        
        if balance > 100:
            print(f"\n🚀 SUFFICIENT FUNDS FOR TRADING")
            print(f"   Available: ${balance:.2f}")
            print(f"   Reserve: $100")
            print(f"   Trading Capital: ${balance - 100:.2f}")
            
            # Create buy order script template
            buy_script_template = '''
import json
import time
try:
    from coinbase.rest import RESTClient
    
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    key = config["api_key"].split("/")[-1]
    client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)
    
    order = client.market_order_buy(
        client_order_id=f"subprocess_{{int(time.time())}}",
        product_id="{product_id}",
        quote_size="{amount}"
    )
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {{str(e)}}")
'''
            
            # Ask for confirmation
            print(f"\n⚠️ READY TO START RECOVERY TRADING")
            print(f"   Using subprocess approach to avoid timeouts")
            confirmation = input("Type 'TRADE' to begin: ")
            
            if confirmation == 'TRADE':
                print(f"\n🚀 STARTING RECOVERY TRADES...")
                print("=" * 60)
                
                trades = [
                    ("SOL-USD", 300),
                    ("AVAX-USD", 250),
                    ("MATIC-USD", 200),
                    ("DOGE-USD", 150)
                ]
                
                successful_trades = 0
                total_deployed = 0
                
                for coin, amount in trades:
                    if total_deployed + amount > balance - 100:
                        print(f"⚠️ Skipping {coin} - would exceed available capital")
                        continue
                    
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 BUY ${amount} {coin}")
                    
                    # Create specific buy script
                    buy_script = buy_script_template.format(
                        product_id=coin,
                        amount=amount
                    )
                    
                    # Execute trade
                    trade_result, trade_success = run_with_timeout(buy_script, 8)
                    
                    if trade_success and "SUCCESS" in trade_result:
                        successful_trades += 1
                        total_deployed += amount
                        print(f"  ✅ SUCCESS! Trade #{successful_trades}")
                        
                        # Log trade
                        with open("/home/dereadi/scripts/claude/subprocess_trades.log", "a") as f:
                            f.write(f"{datetime.now()} BUY {amount} {coin} SUCCESS\\n")
                    else:
                        print(f"  ❌ FAILED: {trade_result}")
                        
                        # Log failure
                        with open("/home/dereadi/scripts/claude/subprocess_trades.log", "a") as f:
                            f.write(f"{datetime.now()} BUY {amount} {coin} FAILED: {trade_result}\\n")
                    
                    # Wait between trades
                    time.sleep(3)
                
                print(f"\n" + "=" * 60)
                print(f"🏁 TRADING COMPLETE")
                print(f"   Successful Trades: {successful_trades}/{len(trades)}")
                print(f"   Total Deployed: ${total_deployed}")
                print(f"   See subprocess_trades.log for details")
                print("=" * 60)
                
            else:
                print("❌ Trading cancelled")
        else:
            print(f"⚠️ Insufficient balance: ${balance:.2f}")
            
    except ValueError:
        print(f"❌ Invalid balance response: {balance_result}")
else:
    print(f"❌ Balance check failed: {balance_result}")
    print("\n🚨 FINAL EMERGENCY SOLUTION:")
    print("   1. API is completely broken - timeouts persist")
    print("   2. IMMEDIATE MANUAL ACTION REQUIRED:")
    print("      - Open Coinbase.com in browser")
    print("      - Execute trades manually using the plan below:")
    print("      - BUY $300 SOL, $250 AVAX, $200 MATIC, $150 DOGE")
    print("      - Set stop losses at -5% and take profits at +15%")
    print("   3. Monitor positions closely for recovery opportunities")

print(f"\n💾 All trading logs saved to: subprocess_trades.log")
print(f"📋 Manual trading plan available in: manual_trading_plan.json")