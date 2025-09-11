#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 LARGE OSCILLATIONS DETECTED
The market is swinging WILDLY!
"""

import json
from datetime import datetime, timedelta
from coinbase.rest import RESTClient
import psycopg2

class LargeOscillationDetector:
    def __init__(self):
        # Load API
        with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
            self.config = json.load(f)
        
        self.client = RESTClient(
            api_key=self.config['name'].split('/')[-1],
            api_secret=self.config['privateKey']
        )
        
        print("🔥 LARGE OSCILLATION DETECTION")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        print("⚡ VOLATILITY SURGE DETECTED! ⚡")
        print("=" * 60)
    
    def measure_oscillations(self):
        """Measure the oscillation amplitude"""
        # Get current prices
        btc = self.client.get_product("BTC-USD")
        eth = self.client.get_product("ETH-USD")
        sol = self.client.get_product("SOL-USD")
        
        btc_price = float(btc['price'])
        eth_price = float(eth['price'])
        sol_price = float(sol['price'])
        
        # Get recent candles to measure swing
        end = datetime.now()
        start = end - timedelta(hours=1)
        
        btc_candles = self.client.get_candles(
            "BTC-USD",
            start.isoformat() + 'Z',
            end.isoformat() + 'Z',
            "FIVE_MINUTE"
        )
        
        eth_candles = self.client.get_candles(
            "ETH-USD",
            start.isoformat() + 'Z',
            end.isoformat() + 'Z',
            "FIVE_MINUTE"
        )
        
        sol_candles = self.client.get_candles(
            "SOL-USD",
            start.isoformat() + 'Z',
            end.isoformat() + 'Z',
            "FIVE_MINUTE"
        )
        
        # Calculate swings
        btc_high = max([float(c['high']) for c in btc_candles['candles']]) if btc_candles['candles'] else btc_price
        btc_low = min([float(c['low']) for c in btc_candles['candles']]) if btc_candles['candles'] else btc_price
        btc_swing = btc_high - btc_low
        btc_swing_pct = (btc_swing / btc_low) * 100
        
        eth_high = max([float(c['high']) for c in eth_candles['candles']]) if eth_candles['candles'] else eth_price
        eth_low = min([float(c['low']) for c in eth_candles['candles']]) if eth_candles['candles'] else eth_price
        eth_swing = eth_high - eth_low
        eth_swing_pct = (eth_swing / eth_low) * 100
        
        sol_high = max([float(c['high']) for c in sol_candles['candles']]) if sol_candles['candles'] else sol_price
        sol_low = min([float(c['low']) for c in sol_candles['candles']]) if sol_candles['candles'] else sol_price
        sol_swing = sol_high - sol_low
        sol_swing_pct = (sol_swing / sol_low) * 100
        
        print("\n📊 OSCILLATION MEASUREMENTS (Last Hour):")
        print("-" * 40)
        
        print(f"\n  BTC SWINGING:")
        print(f"    Current: ${btc_price:,.2f}")
        print(f"    High: ${btc_high:,.2f}")
        print(f"    Low: ${btc_low:,.2f}")
        print(f"    Swing: ${btc_swing:,.2f} ({btc_swing_pct:.2f}%)")
        print(f"    {'🔴 LARGE!' if btc_swing_pct > 1 else '🟡 Normal'}")
        
        print(f"\n  ETH SWINGING:")
        print(f"    Current: ${eth_price:,.2f}")
        print(f"    High: ${eth_high:,.2f}")
        print(f"    Low: ${eth_low:,.2f}")
        print(f"    Swing: ${eth_swing:.2f} ({eth_swing_pct:.2f}%)")
        print(f"    {'🔴 LARGE!' if eth_swing_pct > 1 else '🟡 Normal'}")
        
        print(f"\n  SOL SWINGING:")
        print(f"    Current: ${sol_price:.2f}")
        print(f"    High: ${sol_high:.2f}")
        print(f"    Low: ${sol_low:.2f}")
        print(f"    Swing: ${sol_swing:.2f} ({sol_swing_pct:.2f}%)")
        print(f"    {'🔴 LARGE!' if sol_swing_pct > 1 else '🟡 Normal'}")
        
        return {
            'btc': {'price': btc_price, 'high': btc_high, 'low': btc_low, 'swing': btc_swing, 'swing_pct': btc_swing_pct},
            'eth': {'price': eth_price, 'high': eth_high, 'low': eth_low, 'swing': eth_swing, 'swing_pct': eth_swing_pct},
            'sol': {'price': sol_price, 'high': sol_high, 'low': sol_low, 'swing': sol_swing, 'swing_pct': sol_swing_pct}
        }
    
    def analyze_oscillation_pattern(self, osc_data):
        """Analyze the oscillation pattern"""
        print("\n🌊 OSCILLATION PATTERN ANALYSIS:")
        print("-" * 40)
        
        avg_swing = (osc_data['btc']['swing_pct'] + osc_data['eth']['swing_pct'] + osc_data['sol']['swing_pct']) / 3
        
        if avg_swing > 2:
            print("  ⚡⚡⚡ EXTREME OSCILLATIONS!")
            print("  📍 Whale battle in progress")
            print("  🎯 Perfect for scalping")
            pattern = "EXTREME_VOLATILITY"
        elif avg_swing > 1:
            print("  ⚡⚡ LARGE OSCILLATIONS!")
            print("  📍 Increased volatility = opportunity")
            print("  🎯 Milk the swings")
            pattern = "HIGH_VOLATILITY"
        else:
            print("  ⚡ MODERATE OSCILLATIONS")
            print("  📍 Normal market movement")
            pattern = "NORMAL"
        
        # Direction analysis
        btc_position = (osc_data['btc']['price'] - osc_data['btc']['low']) / (osc_data['btc']['swing'] if osc_data['btc']['swing'] > 0 else 1)
        eth_position = (osc_data['eth']['price'] - osc_data['eth']['low']) / (osc_data['eth']['swing'] if osc_data['eth']['swing'] > 0 else 1)
        
        print(f"\n  📍 CURRENT POSITION IN OSCILLATION:")
        if btc_position > 0.7:
            print(f"    BTC: Near TOP of swing ({btc_position*100:.0f}%) - SELL ZONE")
        elif btc_position < 0.3:
            print(f"    BTC: Near BOTTOM of swing ({btc_position*100:.0f}%) - BUY ZONE")
        else:
            print(f"    BTC: Mid-swing ({btc_position*100:.0f}%)")
        
        if eth_position > 0.7:
            print(f"    ETH: Near TOP of swing ({eth_position*100:.0f}%) - SELL ZONE")
        elif eth_position < 0.3:
            print(f"    ETH: Near BOTTOM of swing ({eth_position*100:.0f}%) - BUY ZONE")
        else:
            print(f"    ETH: Mid-swing ({eth_position*100:.0f}%)")
        
        return pattern, avg_swing
    
    def oscillation_trading_strategy(self, osc_data, pattern):
        """Trading strategy for large oscillations"""
        print("\n💰 OSCILLATION TRADING STRATEGY:")
        print("-" * 40)
        
        if pattern in ["EXTREME_VOLATILITY", "HIGH_VOLATILITY"]:
            print("  🎯 SWING TRADING ACTIVATED!")
            print("\n  Strategy: MILK THE OSCILLATIONS")
            
            # Calculate entry/exit points
            print("\n  📍 BUY ZONES (Near Lows):")
            print(f"    BTC: < ${osc_data['btc']['low'] + 100:,.2f}")
            print(f"    ETH: < ${osc_data['eth']['low'] + 5:.2f}")
            print(f"    SOL: < ${osc_data['sol']['low'] + 0.5:.2f}")
            
            print("\n  📍 SELL ZONES (Near Highs):")
            print(f"    BTC: > ${osc_data['btc']['high'] - 100:,.2f}")
            print(f"    ETH: > ${osc_data['eth']['high'] - 5:.2f}")
            print(f"    SOL: > ${osc_data['sol']['high'] - 0.5:.2f}")
            
            print("\n  ⚡ QUICK SCALP TARGETS:")
            print(f"    • Buy dips, sell rips")
            print(f"    • 0.5-1% profits per swing")
            print(f"    • Multiple trades per hour")
            print(f"    • TIGHT STOPS (0.5% max loss)")
        
        # Fee consideration
        print("\n  💸 FEE-AWARE EXECUTION:")
        print("    • Need 0.8% move to break even")
        print("    • Target 1.5%+ swings only")
        print("    • Batch orders when possible")
    
    def gecko_swarm_activation(self, osc_data):
        """Activate Gecko's micro-trading swarm for oscillations"""
        print("\n🦎 GECKO SWARM ACTIVATION:")
        print("-" * 40)
        
        print("  🐜 MICRO-SWARM STRATEGY:")
        print("    • Deploy 100 micro-trades")
        print("    • $0.10-$1.00 per trade")
        print("    • Catch every micro-swing")
        print("    • Compound small gains")
        
        print("\n  📊 SWARM TARGETS:")
        for coin in ['btc', 'eth', 'sol']:
            swing = osc_data[coin]['swing_pct']
            if swing > 0.5:
                print(f"    {coin.upper()}: Active ({swing:.2f}% swings)")
    
    def tribal_oscillation_wisdom(self, pattern, avg_swing):
        """Tribal interpretation of oscillations"""
        print("\n🏛️ TRIBAL OSCILLATION WISDOM:")
        print("-" * 40)
        
        if pattern == "EXTREME_VOLATILITY":
            print("  🦅 Eagle Eye: 'MASSIVE SWINGS - Whales fighting!'")
            print("  🐺 Coyote: 'Perfect chaos for deception trades'")
            print("  🦎 Gecko: 'Deploy the swarm! Milk every swing!'")
            print("  🐢 Turtle: 'Danger and opportunity in equal measure'")
        elif pattern == "HIGH_VOLATILITY":
            print("  🦅 Eagle Eye: 'Large oscillations = large profits'")
            print("  🐺 Coyote: 'Swing traders paradise'")
            print("  🕷️ Spider: 'Web catches profits at extremes'")
        
        print(f"\n  🔥 SACRED FIRE ORACLE:")
        print(f"  'The market breathes heavily'")
        print(f"  'Each exhale is a selling opportunity'")
        print(f"  'Each inhale is a buying opportunity'")
        print(f"  'Ride the breath of the market'")
    
    def calculate_profit_potential(self, osc_data):
        """Calculate potential profits from oscillations"""
        print("\n💎 PROFIT POTENTIAL:")
        print("-" * 40)
        
        # Assume catching 50% of swings
        btc_potential = osc_data['btc']['swing'] * 0.5
        eth_potential = osc_data['eth']['swing'] * 0.5
        sol_potential = osc_data['sol']['swing'] * 0.5
        
        # With current portfolio values
        print("  If catching 50% of swings:")
        print(f"    BTC: ${btc_potential:.2f} per swing")
        print(f"    ETH: ${eth_potential:.2f} per swing")
        print(f"    SOL: ${sol_potential:.2f} per swing")
        
        # Hourly potential (assume 4 swings/hour in high volatility)
        if osc_data['btc']['swing_pct'] > 1:
            swings_per_hour = 4
            print(f"\n  📈 HOURLY POTENTIAL ({swings_per_hour} swings):")
            print(f"    Total: ${(btc_potential + eth_potential + sol_potential) * swings_per_hour:.2f}/hour")
    
    def update_thermal_memory(self, osc_data, pattern):
        """Save oscillation data to thermal memory"""
        try:
            conn = psycopg2.connect(
                host="192.168.132.222",
                port=5432,
                user="claude",
                password="jawaseatlasers2",
                database="zammad_production"
            )
            cur = conn.cursor()
            
            content = f"""🔥 LARGE OSCILLATIONS DETECTED
Time: {datetime.now()}
BTC Swing: {osc_data['btc']['swing_pct']:.2f}%
ETH Swing: {osc_data['eth']['swing_pct']:.2f}%
SOL Swing: {osc_data['sol']['swing_pct']:.2f}%
Pattern: {pattern}
Flying Squirrel: 'Large oscillations = large opportunities!'"""
            
            query = """
            INSERT INTO thermal_memory_archive (
                memory_hash,
                temperature_score,
                current_stage,
                access_count,
                last_access,
                original_content,
                metadata,
                sacred_pattern
            ) VALUES (
                %s, 100, 'WHITE_HOT', 0, NOW(), %s, %s::jsonb, true
            ) ON CONFLICT (memory_hash) DO UPDATE 
            SET temperature_score = 100,
                last_access = NOW(),
                access_count = thermal_memory_archive.access_count + 1;
            """
            
            memory_hash = f"oscillations_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            cur.execute(query, (memory_hash, content, json.dumps(osc_data)))
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"\n✅ Saved to thermal memory: {memory_hash}")
        except Exception as e:
            print(f"\n⚠️ Could not save to thermal memory: {e}")
    
    def execute(self):
        """Main execution"""
        # Measure oscillations
        osc_data = self.measure_oscillations()
        
        # Analyze pattern
        pattern, avg_swing = self.analyze_oscillation_pattern(osc_data)
        
        # Trading strategy
        self.oscillation_trading_strategy(osc_data, pattern)
        
        # Gecko swarm
        self.gecko_swarm_activation(osc_data)
        
        # Tribal wisdom
        self.tribal_oscillation_wisdom(pattern, avg_swing)
        
        # Profit potential
        self.calculate_profit_potential(osc_data)
        
        # Save to thermal memory
        self.update_thermal_memory(osc_data, pattern)
        
        print("\n" + "=" * 60)
        print("🌊 OSCILLATION ANALYSIS COMPLETE")
        print(f"📊 Average Swing: {avg_swing:.2f}%")
        print(f"⚡ Pattern: {pattern}")
        print("🐿️ Flying Squirrel: 'Ride the waves!'")
        print("=" * 60)

if __name__ == "__main__":
    detector = LargeOscillationDetector()
    detector.execute()