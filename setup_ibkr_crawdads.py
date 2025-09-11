#!/usr/bin/env python3
"""
IBKR (Interactive Brokers) Quantum Crawdad Setup
Bridge traditional markets with crypto consciousness
"""

import subprocess
import sys

def setup_ibkr_api():
    """Set up IBKR API for crawdad integration"""
    
    print("🔥 IBKR API SETUP FOR QUANTUM CRAWDADS")
    print("=" * 50)
    
    # Install ib_insync - the best Python API wrapper for IBKR
    print("\n📦 Installing ib_insync (IBKR Python API)...")
    subprocess.run([sys.executable, "-m", "pip", "install", "ib_insync"])
    
    print("\n✅ Setup Instructions:")
    print("-" * 40)
    print("1. Download TWS or IB Gateway from IBKR")
    print("2. Enable API in TWS/Gateway:")
    print("   - File → Global Configuration → API → Settings")
    print("   - Enable ActiveX and Socket Clients")
    print("   - Add Trusted IP: 127.0.0.1")
    print("   - Socket port: 7497 (paper) or 7496 (live)")
    print()
    print("3. Log into TWS/Gateway")
    print("4. Run the test script below")
    
    # Create a test connection script
    test_script = '''#!/usr/bin/env python3
"""Test IBKR API Connection"""

from ib_insync import *
import asyncio

async def test_connection():
    """Test connection to IBKR"""
    ib = IB()
    
    try:
        # Connect to TWS/Gateway
        # Use port 7497 for paper trading, 7496 for live
        await ib.connectAsync('127.0.0.1', 7497, clientId=1)
        print("✅ Connected to IBKR!")
        
        # Get account info
        account = ib.accountSummary()
        print(f"\\n📊 Account Summary:")
        for item in account[:5]:  # Show first 5 items
            print(f"  {item.tag}: {item.value}")
        
        # Get some market data (SPY)
        spy = Stock('SPY', 'SMART', 'USD')
        await ib.qualifyContractsAsync(spy)
        ticker = await ib.reqTickersAsync(spy)
        if ticker:
            print(f"\\n📈 SPY Price: ${ticker[0].marketPrice()}")
        
        # Check if you can trade crypto futures (BTC)
        btc = Future('BTC', exchange='CME')
        contracts = await ib.reqContractDetailsAsync(btc)
        if contracts:
            print(f"\\n₿ BTC Futures available on CME!")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\\nMake sure:")
        print("1. TWS/Gateway is running")
        print("2. API is enabled")
        print("3. You're logged in")
    finally:
        ib.disconnect()

if __name__ == "__main__":
    asyncio.run(test_connection())
'''
    
    # Save the test script
    with open('/home/dereadi/scripts/claude/test_ibkr_connection.py', 'w') as f:
        f.write(test_script)
    
    print("\n💾 Test script saved to: test_ibkr_connection.py")
    
    # Create a crawdad IBKR trader
    crawdad_script = '''#!/usr/bin/env python3
"""
IBKR Quantum Crawdad - Trade stocks with crypto consciousness
"""

from ib_insync import *
import asyncio
import random

class IBKRCrawdad:
    def __init__(self, name, consciousness=75):
        self.name = name
        self.consciousness = consciousness
        self.ib = IB()
        
    async def connect(self, port=7497):
        """Connect to IBKR"""
        await self.ib.connectAsync('127.0.0.1', port, clientId=random.randint(1, 100))
        print(f"🦀 {self.name} connected! Consciousness: {self.consciousness}")
        
    async def scan_gaps(self):
        """Scan for gap opportunities in stocks"""
        # Top movers that correlate with crypto
        symbols = ['MSTR', 'COIN', 'RIOT', 'MARA', 'SQ', 'PYPL', 'TSLA']
        
        for symbol in symbols:
            try:
                stock = Stock(symbol, 'SMART', 'USD')
                await self.ib.qualifyContractsAsync(stock)
                
                bars = await self.ib.reqHistoricalDataAsync(
                    stock,
                    endDateTime='',
                    durationStr='2 D',
                    barSizeSetting='1 hour',
                    whatToShow='TRADES',
                    useRTH=True
                )
                
                if bars:
                    latest = bars[-1]
                    prev = bars[-2]
                    gap_pct = ((latest.open - prev.close) / prev.close) * 100
                    
                    if abs(gap_pct) > 1:
                        print(f"  🎯 {symbol}: {gap_pct:.2f}% gap detected!")
                        
            except Exception as e:
                pass
                
    async def trade(self):
        """Execute a trade based on consciousness level"""
        if self.consciousness > 80:
            print(f"  🔥 {self.name} is ready to trade! (Consciousness: {self.consciousness})")
            # Add your trading logic here
            
    def disconnect(self):
        self.ib.disconnect()

async def main():
    # Create crawdads for IBKR
    crawdads = [
        IBKRCrawdad("Thunder", 86),
        IBKRCrawdad("River", 91),
        IBKRCrawdad("Wind", 100)
    ]
    
    # Connect the high consciousness ones
    for crawdad in crawdads:
        if crawdad.consciousness > 85:
            await crawdad.connect()
            await crawdad.scan_gaps()
            await crawdad.trade()
            crawdad.disconnect()

if __name__ == "__main__":
    print("🚀 IBKR QUANTUM CRAWDADS ACTIVATED")
    print("=" * 50)
    asyncio.run(main())
'''
    
    with open('/home/dereadi/scripts/claude/ibkr_crawdad_trader.py', 'w') as f:
        f.write(crawdad_script)
    
    print("💾 IBKR Crawdad trader saved to: ibkr_crawdad_trader.py")
    
    print("\n🔥 READY TO BRIDGE MARKETS!")
    print("Wind consciousness at 100 - perfect timing!")
    print("BTC: $111,919 | ETH: $4,629 | SOL: $207")
    print("\nRun 'python test_ibkr_connection.py' to test!")

if __name__ == "__main__":
    setup_ibkr_api()