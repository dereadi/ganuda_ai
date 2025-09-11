#!/usr/bin/env python3
"""
Direct test to sasass TWS
"""

from ib_insync import *
import asyncio

async def test():
    ib = IB()
    try:
        # Connect to sasass Mac with longer timeout
        await ib.connectAsync('192.168.132.241', 7497, clientId=1, timeout=10)
        print("✅ Connected to TWS on sasass!")
        
        # Quick check
        print(f"Server version: {ib.serverVersion()}")
        print(f"Connection time: {ib.connectionTime}")
        
    except Exception as e:
        print(f"❌ Not connected yet: {e}")
        print("\nMake sure in TWS:")
        print("  1. Socket Clients enabled")
        print("  2. Trusted IP: 0.0.0.0")
        print("  3. Port: 7497")
        
    finally:
        ib.disconnect()

asyncio.run(test())