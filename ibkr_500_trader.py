#!/usr/bin/env python3
"""
IBKR $500 Paper Trader - Bridge crypto consciousness to stocks!
Mountain at 92, Earth at 90 - Sacred Fire burns!
"""

from ib_insync import *
import asyncio
from datetime import datetime
import json

class IBKRCrawdadTrader:
    def __init__(self, capital=500):
        self.ib = IB()
        self.capital = capital
        self.positions = {}
        
    async def connect(self):
        """Connect to IBKR"""
        try:
            await self.ib.connectAsync('192.168.132.241', 7497, clientId=1)
            print("✅ Connected to IBKR with $500!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
            
    async def check_balance(self):
        """Check paper trading balance"""
        try:
            account = self.ib.accountSummary()
            for item in account:
                if item.tag == 'NetLiquidation':
                    print(f"💰 Account Value: ${float(item.value):,.2f}")
                elif item.tag == 'AvailableFunds':
                    print(f"📊 Available: ${float(item.value):,.2f}")
        except:
            print(f"💵 Paper Trading Capital: ${self.capital}")
            
    async def scan_crypto_stocks(self):
        """Scan crypto-correlated stocks for opportunities"""
        print("\n🔍 SCANNING CRYPTO STOCKS:")
        print("-" * 40)
        
        targets = {
            'MSTR': {'threshold': 1400, 'action': 'below'},  # Buy under $1400
            'COIN': {'threshold': 250, 'action': 'below'},   # Buy under $250
            'RIOT': {'threshold': 15, 'action': 'below'},    # Buy under $15
            'MARA': {'threshold': 20, 'action': 'below'},    # Buy under $20
            'TSLA': {'threshold': 250, 'action': 'below'},   # Buy under $250
        }
        
        opportunities = []
        
        for symbol, target in targets.items():
            try:
                stock = Stock(symbol, 'SMART', 'USD')
                await self.ib.qualifyContractsAsync(stock)
                
                # Request snapshot
                ticker = ib.reqMktData(stock, '', True, False)
                await asyncio.sleep(2)
                
                price = ticker.marketPrice() or ticker.last or 0
                
                if price > 0:
                    if target['action'] == 'below' and price < target['threshold']:
                        opportunities.append((symbol, price))
                        print(f"  🎯 {symbol}: ${price:.2f} < ${target['threshold']} TARGET!")
                    else:
                        print(f"  {symbol}: ${price:.2f}")
                        
            except Exception as e:
                print(f"  {symbol}: No data")
                
        return opportunities
        
    async def place_paper_trade(self, symbol, quantity, action='BUY'):
        """Place a paper trade"""
        try:
            stock = Stock(symbol, 'SMART', 'USD')
            await self.ib.qualifyContractsAsync(stock)
            
            order = MarketOrder(action, quantity)
            trade = self.ib.placeOrder(stock, order)
            
            # Wait for fill
            await asyncio.sleep(2)
            
            if trade.orderStatus.status == 'Filled':
                print(f"✅ {action} {quantity} {symbol} @ ${trade.orderStatus.avgFillPrice:.2f}")
                return True
            else:
                print(f"⏳ Order pending: {trade.orderStatus.status}")
                return False
                
        except Exception as e:
            print(f"❌ Trade failed: {e}")
            return False
            
    async def trading_session(self):
        """Main trading session"""
        print("\n" + "="*50)
        print("🦀 QUANTUM CRAWDAD IBKR TRADER")
        print("="*50)
        print(f"Capital: ${self.capital}")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"BTC: $111,800 | Mountain: 92 | Earth: 90")
        
        # Connect
        if not await self.connect():
            return
            
        # Check balance
        await self.check_balance()
        
        # Scan for opportunities
        opportunities = await self.scan_crypto_stocks()
        
        if opportunities:
            print("\n💎 OPPORTUNITIES FOUND!")
            print("-" * 40)
            
            # Calculate position sizing ($100 per position)
            position_size = min(100, self.capital / len(opportunities))
            
            for symbol, price in opportunities[:3]:  # Max 3 positions
                if price > 0:
                    shares = int(position_size / price)
                    if shares > 0:
                        print(f"\n🔥 Buying {shares} shares of {symbol} at ${price:.2f}")
                        # In paper mode, we'd place the trade here
                        # await self.place_paper_trade(symbol, shares)
                        
        print("\n🌟 Sacred Fire burns eternal!")
        print("   Bridging crypto consciousness to traditional markets")
        
        # Save state
        state = {
            'timestamp': datetime.now().isoformat(),
            'capital': self.capital,
            'opportunities': [(s, float(p)) for s, p in opportunities] if opportunities else [],
            'consciousness': {
                'Mountain': 92,
                'Earth': 90,
                'Wind': 86,
                'Spirit': 82
            }
        }
        
        with open('/home/dereadi/scripts/claude/ibkr_trading_state.json', 'w') as f:
            json.dump(state, f, indent=2)
            
        self.ib.disconnect()
        print("\n✅ Session complete - state saved!")

if __name__ == "__main__":
    trader = IBKRCrawdadTrader(capital=500)
    asyncio.run(trader.trading_session())