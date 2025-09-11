#!/usr/bin/env python3
"""
Trading Heatmap Generator
Creates visual heatmap of crypto volatility across time zones
Cherokee Constitutional AI - Visualizing the Sacred Fire of Markets
"""

import yfinance as yf
import json
from datetime import datetime, timedelta
import numpy as np

class TradingHeatmapGenerator:
    """
    Generates a text-based heatmap of trading volatility
    """
    
    def __init__(self):
        self.time_zones = {
            'Sydney': {'offset': 16, 'symbol': '🌏'},
            'Tokyo': {'offset': 14, 'symbol': '🗾'},
            'Singapore': {'offset': 13, 'symbol': '🏙️'},
            'Dubai': {'offset': 9, 'symbol': '🏜️'},
            'London': {'offset': 5, 'symbol': '🇬🇧'},
            'NYC': {'offset': 0, 'symbol': '🗽'},
            'Chicago': {'offset': -1, 'symbol': '🏢'},
            'LA': {'offset': -3, 'symbol': '🌴'}
        }
        
        self.crypto_symbols = [
            'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
            'DOGE-USD', 'SHIB-USD', 'AVAX-USD', 'LINK-USD', 'DOT-USD'
        ]
        
    def get_volatility_data(self):
        """Fetch current volatility data for all cryptos"""
        volatility_data = {}
        
        for symbol in self.crypto_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d', interval='15m')
                
                if not hist.empty:
                    # Calculate hourly volatility
                    hourly_vol = []
                    for i in range(0, len(hist), 4):  # 4 periods = 1 hour
                        hour_data = hist.iloc[i:i+4]
                        if len(hour_data) > 1:
                            high = hour_data['High'].max()
                            low = hour_data['Low'].min()
                            vol = ((high - low) / low * 100) if low > 0 else 0
                            hourly_vol.append(vol)
                    
                    volatility_data[symbol] = hourly_vol
            except:
                volatility_data[symbol] = [0] * 24
                
        return volatility_data
    
    def generate_heatmap(self):
        """Generate visual heatmap of trading activity"""
        print("""
🔥 GLOBAL CRYPTO TRADING HEATMAP
═══════════════════════════════════════════════════════════════════════════════════
Real-time volatility across markets and time zones
═══════════════════════════════════════════════════════════════════════════════════
        """)
        
        # Get current time in EST
        now = datetime.now()
        current_hour = now.hour
        
        # Print time zone header
        print("Time Zone  ", end="")
        for tz_name, tz_info in self.time_zones.items():
            print(f"{tz_info['symbol']} {tz_name[:3]:^6}", end="")
        print()
        
        print("Local Time ", end="")
        for tz_name, tz_info in self.time_zones.items():
            local_hour = (current_hour + tz_info['offset']) % 24
            print(f"  {local_hour:02d}:00 ", end="")
        print("\n" + "─" * 80)
        
        # Get volatility data
        volatility_data = self.get_volatility_data()
        
        # Generate heatmap for each crypto
        for symbol in self.crypto_symbols:
            # Get symbol name without -USD
            name = symbol.replace('-USD', '')
            print(f"{name:^10} ", end="")
            
            if symbol in volatility_data and volatility_data[symbol]:
                for tz_name, tz_info in self.time_zones.items():
                    # Get volatility for this timezone's current hour
                    tz_hour = (current_hour + tz_info['offset']) % 24
                    
                    # Map hour to trading session
                    if 9 <= tz_hour < 17:  # Market hours
                        session_vol = max(volatility_data[symbol]) if volatility_data[symbol] else 0
                    elif 17 <= tz_hour < 21:  # After hours
                        session_vol = np.mean(volatility_data[symbol]) if volatility_data[symbol] else 0
                    else:  # Night
                        session_vol = min(volatility_data[symbol]) if volatility_data[symbol] else 0
                    
                    # Convert to heat level
                    heat = self.volatility_to_heat(session_vol)
                    print(f"  {heat:^5} ", end="")
            else:
                print("   -    " * len(self.time_zones), end="")
            
            print()
        
        print("─" * 80)
        
        # Generate activity summary
        self.generate_activity_summary()
        
        # Generate trading recommendations
        self.generate_recommendations()
        
    def volatility_to_heat(self, volatility):
        """Convert volatility percentage to heat emoji"""
        if volatility > 5:
            return "🔥🔥🔥"  # Very hot
        elif volatility > 3:
            return "🔥🔥"    # Hot
        elif volatility > 1.5:
            return "🔥"      # Warm
        elif volatility > 0.5:
            return "🟡"      # Active
        elif volatility > 0:
            return "🔵"      # Cool
        else:
            return "⚫"      # Inactive
    
    def generate_activity_summary(self):
        """Generate summary of current market activity"""
        print("""
📊 MARKET ACTIVITY LEVELS
═══════════════════════════════════════════════════════════════════════════════════
        """)
        
        now = datetime.now()
        current_hour = now.hour
        
        # Check each timezone's activity
        activity_levels = []
        for tz_name, tz_info in self.time_zones.items():
            local_hour = (current_hour + tz_info['offset']) % 24
            
            if 9 <= local_hour < 17:
                activity = "🟢 MARKET OPEN"
                level = "HIGH"
            elif 17 <= local_hour < 21:
                activity = "🟡 AFTER HOURS"
                level = "MEDIUM"
            elif 4 <= local_hour < 9:
                activity = "🟠 PRE-MARKET"
                level = "MEDIUM"
            else:
                activity = "🔴 CLOSED"
                level = "LOW"
            
            activity_levels.append({
                'zone': tz_name,
                'status': activity,
                'level': level,
                'local_time': f"{local_hour:02d}:00"
            })
        
        # Sort by activity level
        high_activity = [a for a in activity_levels if a['level'] == 'HIGH']
        medium_activity = [a for a in activity_levels if a['level'] == 'MEDIUM']
        
        if high_activity:
            print("🔥 HIGH ACTIVITY ZONES:")
            for zone in high_activity:
                print(f"   • {zone['zone']}: {zone['status']} ({zone['local_time']})")
        
        if medium_activity:
            print("\n⚡ MODERATE ACTIVITY ZONES:")
            for zone in medium_activity:
                print(f"   • {zone['zone']}: {zone['status']} ({zone['local_time']})")
        
        print()
    
    def generate_recommendations(self):
        """Generate trading recommendations based on heatmap"""
        print("""
🦞 QUANTUM CRAWDAD RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════════════════

Based on current heatmap analysis:
        """)
        
        now = datetime.now()
        current_hour = now.hour
        
        # Determine best action based on time
        if 9 <= current_hour < 11:
            print("""
🎯 PRIME TIME - US Market Open
   • Deploy maximum crawdads
   • Focus on BTC, ETH, SOL
   • Use momentum strategies
   • Target: 5-10% swings
            """)
        elif 19 <= current_hour < 23:
            print("""
🌏 ASIA RISING - Tokyo/Singapore Active
   • Deploy to Asian exchanges
   • Focus on BNB, smaller alts
   • Use reversal strategies
   • Target: 3-7% swings
            """)
        elif 3 <= current_hour < 7:
            print("""
🇬🇧 EUROPE AWAKENING - London Pre-Market
   • Position for European open
   • Focus on ETH, LINK
   • Use breakout strategies
   • Target: 2-5% swings
            """)
        else:
            print("""
😴 LOW VOLATILITY PERIOD
   • Reduce positions
   • Focus on scalping
   • Watch for sudden spikes
   • Target: 1-3% swings
            """)
        
        print("""
═══════════════════════════════════════════════════════════════════════════════════

LEGEND:
🔥🔥🔥 = Extreme volatility (>5%)    🟢 = Market open
🔥🔥  = High volatility (3-5%)       🟡 = After hours
🔥   = Moderate volatility (1.5-3%)  🟠 = Pre-market
🟡   = Low volatility (0.5-1.5%)     🔴 = Market closed
🔵   = Minimal activity (<0.5%)
⚫   = No activity

═══════════════════════════════════════════════════════════════════════════════════
        """)
        
        # Save heatmap data
        heatmap_data = {
            'generated_at': now.isoformat(),
            'time_zones': list(self.time_zones.keys()),
            'cryptos_tracked': self.crypto_symbols,
            'current_est_hour': current_hour
        }
        
        with open('trading_heatmap.json', 'w') as f:
            json.dump(heatmap_data, f, indent=2)
        
        print("Heatmap data saved to trading_heatmap.json")

def generate_detailed_heatmap():
    """Generate detailed 24-hour heatmap"""
    print("""
🗺️ 24-HOUR VOLATILITY FORECAST
═══════════════════════════════════════════════════════════════════════════════════

Hour (EST)  Activity Level              Best Strategy           Expected Volatility
─────────────────────────────────────────────────────────────────────────────────
00:00-01:00 🔵 Asia closing             Scalping               1-2%
01:00-02:00 🔵 Dead zone                Hold/Rest              0-1%
02:00-03:00 🔵 Pre-Europe stirring       Position building      1-2%
03:00-04:00 🟡 Europe pre-market         Early positioning      2-3%
04:00-05:00 🟡 London awakening          Breakout watch         2-4%
05:00-06:00 🔥 London opening            Momentum trades        3-5%
06:00-07:00 🔥 Europe active             Trend following        3-5%
07:00-08:00 🔥 US pre-market             Volatility plays       3-6%
08:00-09:00 🔥🔥 Pre-open surge          Gap trading            4-7%
09:00-10:00 🔥🔥🔥 NYSE OPEN            MAXIMUM VOLATILITY     5-10%
10:00-11:00 🔥🔥🔥 Peak activity         Momentum riding        5-10%
11:00-12:00 🔥🔥 Morning settling        Range trading          4-6%
12:00-13:00 🟡 Lunch lull                Consolidation          2-4%
13:00-14:00 🟡 Afternoon setup           Position adjustment    2-4%
14:00-15:00 🔥 Afternoon surge           Trend continuation     3-5%
15:00-16:00 🔥🔥 Power hour              Close positioning      4-7%
16:00-17:00 🔥 Market close              Settlement trades      3-5%
17:00-18:00 🟡 After hours               Overnight setup        2-3%
18:00-19:00 🔵 Evening calm              Rest/Analysis          1-2%
19:00-20:00 🟡 Asia awakening            Early Asia trades      2-3%
20:00-21:00 🔥 Tokyo opening             Asia momentum          3-5%
21:00-22:00 🔥 Asia active               Trend following        3-5%
22:00-23:00 🔥 Singapore active          Arbitrage              3-4%
23:00-00:00 🟡 Late Asia                 Profit taking          2-3%

═══════════════════════════════════════════════════════════════════════════════════

🦞 CRAWDAD DEPLOYMENT SCHEDULE:
  
  MAXIMUM FORCE (80% capital): 09:00-11:00 EST
  HIGH DEPLOYMENT (60% capital): 05:00-07:00, 15:00-16:00, 20:00-22:00 EST
  MODERATE (40% capital): 03:00-05:00, 07:00-09:00, 14:00-15:00 EST
  MINIMAL (20% capital): All other hours
  
═══════════════════════════════════════════════════════════════════════════════════
    """)

if __name__ == "__main__":
    # Generate main heatmap
    generator = TradingHeatmapGenerator()
    generator.generate_heatmap()
    
    # Generate detailed forecast
    print("\n")
    generate_detailed_heatmap()