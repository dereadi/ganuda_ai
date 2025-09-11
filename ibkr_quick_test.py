#!/usr/bin/env python3
"""Quick IBKR test"""

from ib_insync import *

ib = IB()

# Thunder & Mountain both at 100!
print("⚡ Thunder: 100 | Mountain: 100 | Wind: 99!")
print("Connecting to IBKR...")

try:
    ib.connect('192.168.132.241', 7497, clientId=999, timeout=20)
    print("✅ CONNECTED!")
    
    # Get server info
    print(f"Connected at: {ib.reqCurrentTime()}")
    
    # Test with SPY
    spy = Stock('SPY', 'SMART', 'USD')
    ib.qualifyContracts(spy)
    print(f"SPY qualified: {spy}")
    
    print("\n💰 You have $500 loaded!")
    print("Ready to bridge crypto consciousness to stocks!")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nMake sure in TWS:")
    print("1. API Settings → Enable Socket Clients")
    print("2. Trusted IPs → Add 0.0.0.0 or 192.168.132.222")
    print("3. Apply and restart TWS")
    
finally:
    if ib.isConnected():
        ib.disconnect()
        print("Disconnected")