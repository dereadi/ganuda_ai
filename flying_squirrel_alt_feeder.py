#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 FLYING SQUIRREL'S ALT FEEDING SYSTEM
Feed on the lows, bleed on the highs - eternal cycle
"""

import json
import psycopg2
from datetime import datetime
from coinbase.rest import RESTClient

class FlyingSquirrelAltFeeder:
    def __init__(self):
        # Load API config
        with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
            self.config = json.load(f)
        
        self.client = RESTClient(
            api_key=self.config['name'].split('/')[-1],
            api_secret=self.config['privateKey']
        )
        
        # Flying Squirrel's feeding zones
        self.feeding_zones = {
            'DOGE': {
                'feed_below': 0.20,   # Accumulate below this
                'bleed_above': 0.22,  # Harvest above this
                'position_size': 100, # Units to trade
                'current_position': 96.8
            },
            'MATIC': {
                'feed_below': 0.27,
                'bleed_above': 0.30,
                'position_size': 500,
                'current_position': 6731.3
            },
            'AVAX': {
                'feed_below': 23,
                'bleed_above': 25,
                'position_size': 5,
                'current_position': 104.05
            },
            'LINK': {
                'feed_below': 22,
                'bleed_above': 25,
                'position_size': 0.5,
                'current_position': 0.38
            },
            'XRP': {
                'feed_below': 2.60,
                'bleed_above': 2.90,
                'position_size': 10,
                'current_position': 0.67
            }
        }
    
    def check_feeding_opportunities(self):
        """Check which alts need feeding or bleeding"""
        opportunities = {
            'feed': [],
            'bleed': [],
            'hold': []
        }
        
        print("🐿️ FLYING SQUIRREL ALT SCANNER")
        print("=" * 60)
        
        for coin, zones in self.feeding_zones.items():
            try:
                # Get current price
                ticker = self.client.get_product(f"{coin}-USD")
                price = float(ticker['price'])
                
                print(f"\n{coin}:")
                print(f"  Current Price: ${price:.4f}")
                print(f"  Feed Zone: < ${zones['feed_below']:.4f}")
                print(f"  Bleed Zone: > ${zones['bleed_above']:.4f}")
                print(f"  Position: {zones['current_position']}")
                
                # Determine action
                if price < zones['feed_below']:
                    action = 'FEED'
                    opportunities['feed'].append({
                        'coin': coin,
                        'price': price,
                        'action': f"Buy {zones['position_size']} {coin}",
                        'reason': f"Below feed zone ${zones['feed_below']}"
                    })
                    print(f"  🟢 ACTION: FEED! (accumulate)")
                    
                elif price > zones['bleed_above']:
                    action = 'BLEED'
                    # Only bleed if we have position
                    if zones['current_position'] > zones['position_size']:
                        opportunities['bleed'].append({
                            'coin': coin,
                            'price': price,
                            'action': f"Sell {zones['position_size']} {coin}",
                            'reason': f"Above bleed zone ${zones['bleed_above']}",
                            'expected_usd': zones['position_size'] * price
                        })
                        print(f"  🔴 ACTION: BLEED! (harvest)")
                    else:
                        print(f"  ⚠️ Would bleed but position too small")
                        
                else:
                    opportunities['hold'].append(coin)
                    print(f"  ⏳ ACTION: HOLD (mid-range)")
                    
            except Exception as e:
                print(f"  ❌ Error checking {coin}: {e}")
        
        return opportunities
    
    def execute_feeding_strategy(self, opportunities):
        """Execute the feed/bleed strategy"""
        print("\n" + "=" * 60)
        print("🎯 FLYING SQUIRREL'S EXECUTION PLAN:")
        
        total_liquidity_needed = 0
        total_liquidity_generated = 0
        
        # Calculate liquidity needs for feeding
        if opportunities['feed']:
            print("\n🟢 FEEDING OPPORTUNITIES:")
            for opp in opportunities['feed']:
                cost = self.feeding_zones[opp['coin']]['position_size'] * opp['price']
                print(f"  • {opp['action']} = ${cost:.2f} needed")
                total_liquidity_needed += cost
        
        # Calculate liquidity from bleeding
        if opportunities['bleed']:
            print("\n🔴 BLEEDING OPPORTUNITIES:")
            for opp in opportunities['bleed']:
                print(f"  • {opp['action']} = ${opp['expected_usd']:.2f} generated")
                total_liquidity_generated += opp['expected_usd']
        
        # Net liquidity calculation
        print(f"\n💰 LIQUIDITY CALCULATION:")
        print(f"  Generated from bleeds: ${total_liquidity_generated:.2f}")
        print(f"  Needed for feeds: ${total_liquidity_needed:.2f}")
        print(f"  Net: ${total_liquidity_generated - total_liquidity_needed:.2f}")
        
        # Strategy decision
        if total_liquidity_generated > 0:
            print("\n✅ EXECUTE BLEEDS FIRST - Generate liquidity")
            if total_liquidity_needed > 0:
                print("   Then FEED alts with profits")
        elif total_liquidity_needed > 0 and total_liquidity_needed < 50:
            print("\n💸 FEED OPPORTUNITIES - Need small liquidity")
        else:
            print("\n⏳ PATIENCE - Wait for better setups")
        
        return {
            'feed_opportunities': opportunities['feed'],
            'bleed_opportunities': opportunities['bleed'],
            'liquidity_generated': total_liquidity_generated,
            'liquidity_needed': total_liquidity_needed
        }
    
    def update_thermal_memory(self, strategy_result):
        """Store Flying Squirrel's feeding strategy in thermal memory"""
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            user="claude",
            password="jawaseatlasers2",
            database="zammad_production"
        )
        cur = conn.cursor()
        
        content = f"""🐿️ FLYING SQUIRREL ALT FEEDING CYCLE
        
Feed Opportunities: {len(strategy_result['feed_opportunities'])}
Bleed Opportunities: {len(strategy_result['bleed_opportunities'])}
Liquidity to Generate: ${strategy_result['liquidity_generated']:.2f}
Liquidity Needed: ${strategy_result['liquidity_needed']:.2f}

Flying Squirrel Wisdom:
"Feed when others fear, bleed when others greed"
"Small consistent cycles build the winter cache"
"""
        
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
            %s, 95, 'WHITE_HOT', 0, NOW(), %s, %s::jsonb, true
        ) ON CONFLICT (memory_hash) DO UPDATE 
        SET temperature_score = 95,
            last_access = NOW(),
            original_content = EXCLUDED.original_content,
            metadata = EXCLUDED.metadata,
            access_count = thermal_memory_archive.access_count + 1;
        """
        
        memory_hash = f"flying_squirrel_feeding_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        cur.execute(query, (memory_hash, content, json.dumps(strategy_result)))
        conn.commit()
        cur.close()
        conn.close()
        
        return memory_hash
    
    def glide(self):
        """Main feeding cycle"""
        print("🔥 FLYING SQUIRREL ALT FEEDER ACTIVATED")
        print("=" * 60)
        print("Checking alt feeding and bleeding opportunities...")
        print()
        
        # Check opportunities
        opportunities = self.check_feeding_opportunities()
        
        # Plan execution
        strategy = self.execute_feeding_strategy(opportunities)
        
        # Update thermal memory
        memory_hash = self.update_thermal_memory(strategy)
        
        print(f"\n✅ Strategy saved to thermal memory: {memory_hash}")
        print("\n🐿️ Flying Squirrel glides away to the next branch...")
        
        return strategy

if __name__ == "__main__":
    feeder = FlyingSquirrelAltFeeder()
    feeder.glide()