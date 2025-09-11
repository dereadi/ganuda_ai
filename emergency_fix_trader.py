#!/usr/bin/env python3
"""
🚨 EMERGENCY FIX TRADER - NO TIMEOUTS
Minimal robust trader that WORKS
Fixes the hanging API issue
"""

import json
import time
import signal
import subprocess
import sys
from datetime import datetime

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("API call timed out")

def safe_api_call(func, timeout_seconds=3):
    """Execute API call with hard timeout"""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    try:
        result = func()
        signal.alarm(0)  # Cancel alarm
        return result
    except TimeoutException:
        print(f"  ⚠️ API call timed out after {timeout_seconds}s")
        return None
    except Exception as e:
        signal.alarm(0)
        print(f"  ⚠️ API error: {str(e)[:50]}")
        return None

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  🚨 EMERGENCY FIX TRADER 🚨                                ║
║              Timeout-Proof Trading System                                  ║
║                 Target: Recover $2,721 Loss                               ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Load config
try:
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    print("✅ Config loaded")
except Exception as e:
    print(f"❌ Config error: {e}")
    sys.exit(1)

# Import with error handling
try:
    from coinbase.rest import RESTClient
    print("✅ Coinbase library loaded")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Create client with minimal timeout
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=2)
print("✅ Client created with 2s timeout")

def get_balance():
    """Get USD balance with timeout protection"""
    def _get_accounts():
        return client.get_accounts()
    
    accounts_data = safe_api_call(_get_accounts, 3)
    if not accounts_data or "accounts" not in accounts_data:
        return None
    
    usd_accounts = [a for a in accounts_data["accounts"] if a["currency"] == "USD"]
    if not usd_accounts:
        return None
    
    return float(usd_accounts[0]["available_balance"]["value"])

def execute_buy(coin, amount):
    """Execute buy order with timeout protection"""
    def _buy():
        return client.market_order_buy(
            client_order_id=f"fix_{int(time.time())}",
            product_id=coin,
            quote_size=str(amount)
        )
    
    return safe_api_call(_buy, 5)

def execute_sell(coin, size):
    """Execute sell order with timeout protection"""
    def _sell():
        return client.market_order_sell(
            client_order_id=f"sell_{int(time.time())}",
            product_id=coin,
            base_size=str(size)
        )
    
    return safe_api_call(_sell, 5)

# Test connection
print("\n🔍 Testing connection...")
balance = get_balance()
if balance is None:
    print("❌ Cannot connect to Coinbase API")
    print("💡 Try again in a few minutes - API may be overloaded")
    sys.exit(1)

print(f"✅ Connected! USD Balance: ${balance:.2f}")

# Recovery parameters
TARGET_COINS = ["SOL-USD", "AVAX-USD", "MATIC-USD", "DOGE-USD"]
MIN_TRADE = 50  # Minimum $50 trades
MAX_SINGLE_TRADE = 500  # Maximum $500 per trade
RECOVERY_TARGET = 2721  # Need to recover $2,721

print(f"\n🎯 RECOVERY PLAN:")
print(f"   Current Balance: ${balance:.2f}")
print(f"   Loss to Recover: ${RECOVERY_TARGET}")
print(f"   Available for Trading: ${balance - 100:.2f} (keeping $100 reserve)")
print(f"   Target Coins: {', '.join([c.split('-')[0] for c in TARGET_COINS])}")

# Ask for confirmation before trading
print(f"\n⚠️ READY TO START RECOVERY TRADING")
print(f"   This will make aggressive trades to recover losses")
confirmation = input("Type 'START' to begin trading: ")

if confirmation != 'START':
    print("❌ Trading cancelled")
    sys.exit(0)

print(f"\n🚀 STARTING RECOVERY TRADING...")
print("=" * 60)

trades_made = 0
deployed_capital = 0
max_deploy = balance - 100  # Keep $100 reserve

start_time = time.time()
last_balance_check = time.time()

while deployed_capital < max_deploy and trades_made < 20:  # Limit to 20 trades
    try:
        # Pick a coin
        coin = TARGET_COINS[trades_made % len(TARGET_COINS)]
        
        # Calculate trade size
        remaining_capital = max_deploy - deployed_capital
        trade_size = min(MAX_SINGLE_TRADE, remaining_capital, 
                        MIN_TRADE + (trades_made * 20))  # Increasing size
        
        if trade_size < MIN_TRADE:
            break
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🚀 BUY ${trade_size:.0f} {coin}")
        
        # Execute trade
        result = execute_buy(coin, trade_size)
        
        if result:
            deployed_capital += trade_size
            trades_made += 1
            print(f"  ✅ SUCCESS! Trade #{trades_made} | Deployed: ${deployed_capital:.0f}")
            
            # Log successful trade
            with open("/home/dereadi/scripts/claude/recovery_trades.log", "a") as f:
                f.write(f"{timestamp} BUY {trade_size} {coin} SUCCESS\n")
        else:
            print(f"  ❌ FAILED - skipping to next")
            
        # Check balance every 5 trades
        if trades_made % 5 == 0 and time.time() - last_balance_check > 30:
            current_balance = get_balance()
            if current_balance:
                print(f"📊 Balance check: ${current_balance:.2f}")
                last_balance_check = time.time()
        
        # Wait between trades (avoid rate limits)
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n🛑 Trading stopped by user")
        break
    except Exception as e:
        print(f"  ⚠️ Unexpected error: {str(e)[:50]}")
        time.sleep(10)  # Wait longer on errors

# Final status
print("\n" + "=" * 60)
print(f"🏁 TRADING SESSION COMPLETE")
print(f"   Trades Made: {trades_made}")
print(f"   Capital Deployed: ${deployed_capital:.2f}")
print(f"   Session Time: {(time.time() - start_time)/60:.1f} minutes")

# Final balance check
final_balance = get_balance()
if final_balance:
    print(f"   Final USD Balance: ${final_balance:.2f}")
    if final_balance > balance:
        profit = final_balance - balance
        print(f"   🎉 PROFIT: +${profit:.2f}")
    else:
        loss = balance - final_balance
        print(f"   📉 Loss: -${loss:.2f}")

print("=" * 60)
print("\n💡 NEXT STEPS:")
print("   1. Monitor positions for profit-taking opportunities")
print("   2. Set up price alerts for your holdings")
print("   3. Plan exit strategy when positions are profitable")
print("\n🔍 Check your Coinbase account for current portfolio status")