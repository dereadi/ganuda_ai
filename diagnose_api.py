#!/usr/bin/env python3
"""Diagnose Coinbase API connection issues"""

import json
import time
from datetime import datetime

print("🔍 DIAGNOSING COINBASE API...")
print("=" * 60)

# Test 1: Load config
print("1. Loading config...")
try:
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    print("  ✅ Config loaded")
    key = config["api_key"].split("/")[-1]
    print(f"  API Key: ...{key[-8:]}")
except Exception as e:
    print(f"  ❌ Config error: {e}")
    exit(1)

# Test 2: Import library
print("\n2. Importing coinbase library...")
try:
    from coinbase.rest import RESTClient
    print("  ✅ Library imported")
except Exception as e:
    print(f"  ❌ Import error: {e}")
    exit(1)

# Test 3: Create client with short timeout
print("\n3. Creating client (5 second timeout)...")
try:
    client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)
    print("  ✅ Client created")
except Exception as e:
    print(f"  ❌ Client error: {e}")
    exit(1)

# Test 4: Simple API call
print("\n4. Testing get_accounts (should be fast)...")
start = time.time()
try:
    accounts = client.get_accounts()
    elapsed = time.time() - start
    print(f"  ✅ Accounts retrieved in {elapsed:.2f} seconds")
    
    # Count accounts
    if "accounts" in accounts:
        usd_acct = [a for a in accounts["accounts"] if a["currency"] == "USD"]
        if usd_acct:
            balance = float(usd_acct[0]["available_balance"]["value"])
            print(f"  USD Balance: ${balance:.2f}")
except Exception as e:
    elapsed = time.time() - start
    print(f"  ❌ Failed after {elapsed:.2f} seconds: {e}")

# Test 5: Product ticker
print("\n5. Testing get_product (BTC-USD)...")
start = time.time()
try:
    ticker = client.get_product("BTC-USD")
    elapsed = time.time() - start
    print(f"  ✅ Ticker retrieved in {elapsed:.2f} seconds")
    if "price" in ticker:
        print(f"  BTC Price: ${float(ticker['price']):,.2f}")
except Exception as e:
    elapsed = time.time() - start
    print(f"  ❌ Failed after {elapsed:.2f} seconds: {e}")

# Test 6: The problematic call - get_fills
print("\n6. Testing get_fills (THIS MIGHT HANG)...")
print("  ⏱️ Starting test with 3 second timeout...")
start = time.time()
try:
    # Create new client with very short timeout
    test_client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)
    fills = test_client.get_fills(limit=1)
    elapsed = time.time() - start
    print(f"  ✅ Fills retrieved in {elapsed:.2f} seconds")
except Exception as e:
    elapsed = time.time() - start
    print(f"  ❌ Failed after {elapsed:.2f} seconds: {e}")
    print("  💡 This is likely the hanging call!")

print("\n" + "=" * 60)
print("📊 DIAGNOSIS COMPLETE")
print("\nRECOMMENDATION:")
print("  Avoid using get_fills() - it seems to hang")
print("  Use only get_accounts() and market orders")
print("  Keep timeout at 5 seconds or less")