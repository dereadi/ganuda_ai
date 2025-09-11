#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE BALANCE CHECKER
Check all Coinbase accounts and positions
Find the missing $7,491.17
"""

import json
import subprocess
import time
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                🔍 COMPREHENSIVE ACCOUNT AUDIT 🔍                          ║
║               Finding Missing $7,491.17                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

def run_balance_check():
    """Get detailed account information"""
    script = '''
import json
import sys
try:
    from coinbase.rest import RESTClient
    
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    key = config["api_key"].split("/")[-1]
    client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)
    
    # Get all accounts
    accounts_data = client.get_accounts()
    
    total_value_usd = 0
    account_details = []
    
    for account in accounts_data.get("accounts", []):
        currency = account.get("currency", "UNKNOWN")
        available = float(account.get("available_balance", {}).get("value", 0))
        hold = float(account.get("hold", {}).get("value", 0))
        total = available + hold
        
        if total > 0.001:  # Only show accounts with meaningful balances
            account_info = {
                "currency": currency,
                "available": available,
                "hold": hold,
                "total": total
            }
            account_details.append(account_info)
            
            # For USD, add directly to total
            if currency == "USD":
                total_value_usd += total
            # For crypto, we'd need current prices (skip for now)
    
    result = {
        "accounts": account_details,
        "usd_total": total_value_usd,
        "timestamp": str(datetime.now())
    }
    
    print(json.dumps(result, indent=2))
    
except Exception as e:
    error_result = {
        "error": str(e),
        "timestamp": str(datetime.now())
    }
    print(json.dumps(error_result, indent=2))
    sys.exit(1)
'''

    try:
        # Write temporary script
        temp_file = f"/tmp/balance_check_{int(time.time())}.py"
        with open(temp_file, "w") as f:
            f.write(script)
        
        # Run with timeout
        result = subprocess.run([
            "python3", temp_file
        ], capture_output=True, text=True, timeout=10)
        
        # Cleanup
        subprocess.run(["rm", temp_file], capture_output=True)
        
        if result.returncode == 0:
            return json.loads(result.stdout.strip()), True
        else:
            return {"error": result.stderr.strip()}, False
            
    except Exception as e:
        return {"error": str(e)}, False

print("🔍 Checking all account balances...")
balance_data, success = run_balance_check()

if success and "accounts" in balance_data:
    print("✅ Account data retrieved successfully")
    print("\n" + "=" * 60)
    print("📊 COMPLETE ACCOUNT SUMMARY")
    print("=" * 60)
    
    total_found = 0
    has_crypto_positions = False
    
    for account in balance_data["accounts"]:
        currency = account["currency"]
        available = account["available"]
        hold = account["hold"]
        total = account["total"]
        
        print(f"\n{currency}:")
        print(f"  Available: {available:,.6f}")
        if hold > 0:
            print(f"  On Hold:   {hold:,.6f}")
        print(f"  Total:     {total:,.6f}")
        
        if currency == "USD":
            total_found += total
        elif total > 0:
            has_crypto_positions = True
            print(f"  💡 Crypto position detected - needs price conversion")
    
    print("\n" + "=" * 60)
    print(f"💰 USD FOUND: ${total_found:.2f}")
    print(f"📊 Crypto Positions: {'Yes' if has_crypto_positions else 'No'}")
    
    missing = 7508 - total_found
    print(f"❓ Still Missing: ${missing:.2f}")
    
    if has_crypto_positions:
        print("\n💡 CRYPTO POSITIONS DETECTED")
        print("   Your funds may be tied up in crypto holdings")
        print("   Check Coinbase.com portfolio for current values")
        print("   Consider selling positions to free up USD for trading")
    
    if total_found < 50:
        print(f"\n🚨 CRITICAL: Only ${total_found:.2f} USD available")
        print("   Cannot execute recovery strategy with current balance")
        print("   RECOMMENDED ACTIONS:")
        print("   1. Check Coinbase Pro account separately")
        print("   2. Check Coinbase Wallet (different from exchange)")
        print("   3. Verify if funds were transferred out")
        print("   4. Contact Coinbase support if funds are missing")
    
    # Save detailed report
    with open("/home/dereadi/scripts/claude/account_audit_report.json", "w") as f:
        json.dump(balance_data, f, indent=2)
    
    print(f"\n📁 Detailed report saved: account_audit_report.json")
    
else:
    print("❌ Failed to retrieve account data")
    print(f"Error: {balance_data.get('error', 'Unknown error')}")
    
    print(f"\n🚨 API STILL HAS ISSUES")
    print("   Manual verification required:")
    print("   1. Open Coinbase.com")
    print("   2. Check Portfolio tab")
    print("   3. Verify all account balances")
    print("   4. Look for held/pending transactions")

print("\n" + "=" * 60)
print("🔍 AUDIT COMPLETE")
print("Next: Review account_audit_report.json and Coinbase.com")
print("=" * 60)