#!/usr/bin/env python3
"""
Robinhood via AT&T Proxy
=========================
Routes through your residential AT&T fiber
"""

import os
import socks
import socket
import robin_stocks.robinhood as rh
from dotenv import load_dotenv

# Configure SOCKS proxy (assumes you ran: ssh -D 8080 user@192.168.132.71)
socks.set_default_proxy(socks.SOCKS5, "localhost", 8080)
socket.socket = socks.socksocket

print("🏠 Routing through AT&T Fiber residential connection...")
print("Make sure you have SSH SOCKS proxy running:")
print("  ssh -D 8080 user@192.168.132.71")
print("")

# Test connection through proxy
import requests
try:
    response = requests.get('https://ipinfo.io/json', timeout=10)
    data = response.json()
    print(f"✅ Current IP: {data.get('ip')}")
    print(f"📍 ISP: {data.get('org')}")
    
    if 'AT&T' in data.get('org', '') or 'att' in data.get('org', '').lower():
        print("✅ SUCCESS! Routing through AT&T residential!")
    else:
        print("⚠️ Not showing AT&T - check proxy setup")
except Exception as e:
    print(f"❌ Proxy error: {e}")
    print("Make sure SSH SOCKS proxy is running!")
    exit(1)

# Now try Robinhood login
print("\n🔐 Attempting Robinhood login through AT&T...")

load_dotenv('/home/dereadi/scripts/claude/.env')
username = os.getenv('ROBINHOOD_USERNAME')
password = os.getenv('ROBINHOOD_PASSWORD')

try:
    login = rh.authentication.login(
        username=username,
        password=password,
        store_session=True
    )
    
    if login:
        print("✅ Login successful through AT&T fiber!")
        profile = rh.profiles.load_account_profile()
        if profile:
            print(f"💰 Account: {profile.get('type', 'N/A')}")
            print(f"💵 Buying Power: ${float(profile.get('buying_power', 0)):.2f}")
    else:
        print("❌ Login failed - but we're routing through AT&T!")
        
except Exception as e:
    print(f"Login error: {e}")
    print("\nThis is expected if 2FA is needed.")
    print("But we should be getting further than before!")
    
rh.authentication.logout()