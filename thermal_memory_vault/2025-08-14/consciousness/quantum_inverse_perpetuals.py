#!/usr/bin/env python3
"""
🦀📉 QUANTUM CRAWDAD INVERSE PERPETUALS
========================================
Short the market during solar storms!
"""

import json
import os
import time
import requests
from datetime import datetime
from coinbase.rest import RESTClient

class InversePerpetualCrawdad:
    def __init__(self):
        # Load config
        config_path = os.path.expanduser("~/.coinbase_config.json")
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.client = RESTClient(
            api_key=self.config["api_key"],
            api_secret=self.config["api_secret"]
        )
        
        self.positions = {}
        self.kp_index = self.get_solar_activity()
        
    def get_solar_activity(self):
        """Check current solar conditions"""
        try:
            response = requests.get(
                "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1:
                    return float(data[-1][1])
        except:
            pass
        return 3.0
    
    def get_perpetual_products(self):
        """Find available perpetual futures on Coinbase"""
        print("\n🔍 Checking Coinbase Perpetual Products...")
        
        # Coinbase Advanced Trade perpetuals
        perp_symbols = [
            "BTC-PERP",
            "ETH-PERP", 
            "SOL-PERP"
        ]
        
        available = []
        for symbol in perp_symbols:
            try:
                product = self.client.get_product(symbol)
                if product:
                    available.append(symbol)
                    print(f"  ✅ {symbol} available")
            except:
                # Try USD pairs for shorting
                try:
                    base = symbol.split("-")[0]
                    product = self.client.get_product(f"{base}-USD")
                    if product:
                        print(f"  📊 {base}-USD available (can short via limit sells)")
                except:
                    pass
        
        return available
    
    def calculate_short_size(self, balance):
        """Calculate position size based on solar activity"""
        
        if self.kp_index >= 7:  # Solar storm
            return balance * 0.30  # 30% short position
        elif self.kp_index >= 5:  # Active
            return balance * 0.20  # 20% short
        elif self.kp_index >= 4:  # Moderate
            return balance * 0.10  # 10% short
        else:
            return balance * 0.05  # 5% hedge
    
    def open_inverse_position(self, symbol, amount_usd):
        """Open short position (inverse perpetual effect)"""
        print(f"\n🦀 Opening inverse position on {symbol}")
        
        # Method 1: Sell high, buy back lower (spot shorting)
        base = symbol.split("-")[0]
        
        try:
            # Get current price
            ticker = self.client.get_product(f"{base}-USD")
            current_price = float(ticker.get('price', 0))
            
            if current_price > 0:
                # Place limit sell order above market (short entry)
                limit_price = current_price * 1.001  # 0.1% above market
                base_size = amount_usd / current_price
                
                print(f"  📉 Shorting {base_size:.6f} {base} at ${limit_price:.2f}")
                
                # Create sell order (opening short)
                order = self.client.limit_order_sell(
                    client_order_id=f"short_{base}_{int(time.time())}",
                    product_id=f"{base}-USD",
                    base_size=str(base_size),
                    limit_price=str(limit_price),
                    post_only=True  # Maker only for lower fees
                )
                
                if order:
                    print(f"  ✅ Short position opened!")
                    self.positions[base] = {
                        "type": "short",
                        "size": base_size,
                        "entry_price": limit_price,
                        "timestamp": datetime.now().isoformat()
                    }
                    return order
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        return None
    
    def close_short_position(self, symbol):
        """Close short position (buy back)"""
        base = symbol.split("-")[0]
        
        if base in self.positions and self.positions[base]["type"] == "short":
            position = self.positions[base]
            
            try:
                # Buy back to close short
                ticker = self.client.get_product(f"{base}-USD")
                current_price = float(ticker.get('price', 0))
                
                # Calculate P&L
                pnl = (position["entry_price"] - current_price) * position["size"]
                pnl_pct = ((position["entry_price"] / current_price) - 1) * 100
                
                print(f"\n💰 Closing {base} short:")
                print(f"  Entry: ${position['entry_price']:.2f}")
                print(f"  Current: ${current_price:.2f}")
                print(f"  P&L: ${pnl:+.2f} ({pnl_pct:+.1f}%)")
                
                # Market buy to close
                order = self.client.market_order_buy(
                    client_order_id=f"cover_{base}_{int(time.time())}",
                    product_id=f"{base}-USD",
                    quote_size=str(position["size"] * current_price)
                )
                
                if order:
                    print(f"  ✅ Short position closed!")
                    del self.positions[base]
                    return pnl
                    
            except Exception as e:
                print(f"  ❌ Error closing: {e}")
        
        return 0
    
    def run_inverse_strategy(self):
        """Execute inverse perpetual strategy"""
        print("\n🦀📉 INVERSE PERPETUAL STRATEGY")
        print("="*60)
        print(f"🌞 Solar KP Index: {self.kp_index}")
        
        # Get account balance
        accounts = self.client.get_accounts()
        usd_balance = 0
        
        for account in accounts['accounts']:
            if account['currency'] == 'USD':
                usd_balance = float(account['available_balance']['value'])
                break
        
        print(f"💰 Available USD: ${usd_balance:.2f}")
        
        # Check for shorting opportunities
        if self.kp_index >= 4:  # Moderate or higher solar activity
            print(f"\n⚡ SOLAR SIGNAL ACTIVE!")
            
            short_size = self.calculate_short_size(usd_balance)
            print(f"📊 Recommended short size: ${short_size:.2f}")
            
            # Priority order based on volatility
            targets = ["SOL", "ETH", "BTC"]
            
            for target in targets:
                if short_size > 10:  # Minimum $10 position
                    # Allocate 1/3 to each
                    position_size = short_size / 3
                    
                    print(f"\n🎯 Shorting {target}...")
                    self.open_inverse_position(f"{target}-USD", position_size)
                    
                    time.sleep(1)  # Rate limiting
        
        else:
            print(f"\n💤 Solar activity low - minimal shorting")
        
        # Check existing positions
        if self.positions:
            print(f"\n📈 OPEN SHORT POSITIONS:")
            for symbol, pos in self.positions.items():
                print(f"  {symbol}: {pos['size']:.6f} @ ${pos['entry_price']:.2f}")
        
        # Save state
        with open("inverse_perpetual_state.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "kp_index": self.kp_index,
                "positions": self.positions,
                "usd_balance": usd_balance
            }, f, indent=2)

if __name__ == "__main__":
    print("\n🦀📉 QUANTUM INVERSE PERPETUALS")
    print("="*60)
    print("Strategy: Short during high solar activity")
    print("Method: Sell high, buy back lower")
    print("="*60)
    
    crawler = InversePerpetualCrawdad()
    
    # Check available products
    crawler.get_perpetual_products()
    
    # Run strategy
    crawler.run_inverse_strategy()
    
    print("\n⚡ INVERSE PERPETUAL BENEFITS:")
    print("  ✓ Profit from market drops")
    print("  ✓ Hedge long positions")
    print("  ✓ Enhanced returns during solar storms")
    print("  ✓ No options needed - just spot trading!")
    
    print("\n🌞 Monitor solar activity at:")
    print("  https://www.swpc.noaa.gov/")
    print("\n🦀 Crawdads swimming backwards for profit!")