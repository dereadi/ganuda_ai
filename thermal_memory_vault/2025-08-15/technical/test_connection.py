#!/usr/bin/env python3
"""
Quick connection test - NO HANGING
"""
import json
import signal
import sys
import time

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Timeout")

def test_with_timeout(func, timeout_seconds=3):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    try:
        result = func()
        signal.alarm(0)
        return result, True
    except TimeoutException:
        return None, False
    except Exception as e:
        signal.alarm(0)
        return str(e), False

print("🔍 QUICK CONNECTION TEST")
print("=" * 40)

# Load config
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]

from coinbase.rest import RESTClient
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=2)

print("Testing get_accounts() with 3s timeout...")
start = time.time()

def get_accounts():
    return client.get_accounts()

result, success = test_with_timeout(get_accounts, 3)
elapsed = time.time() - start

if success:
    print(f"✅ SUCCESS in {elapsed:.2f}s")
    if "accounts" in result:
        usd_accounts = [a for a in result["accounts"] if a["currency"] == "USD"]
        if usd_accounts:
            balance = float(usd_accounts[0]["available_balance"]["value"])
            print(f"💰 USD Balance: ${balance:.2f}")
            print("🚀 API is working! Ready for trading.")
        else:
            print("⚠️ No USD account found")
    else:
        print("⚠️ Unexpected response format")
else:
    print(f"❌ FAILED after {elapsed:.2f}s")
    print(f"Error: {result}")
    print("🚨 API connection issues persist")

print("=" * 40)