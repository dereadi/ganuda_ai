#!/usr/bin/env python3
"""
Global Volatility Hunter - 24/7 Market Tracker
Follows the sun across global crypto markets hunting volatility
Cherokee Constitutional AI - The Sacred Fire Never Sleeps
"""

import yfinance as yf
import ccxt
import json
import time
from datetime import datetime, timedelta
import pytz
import threading
import requests
import numpy as np

class GlobalVolatilityHunter:
    """
    Tracks volatile markets 24/7 across all time zones
    Automatically deploys crawdads to the hottest markets
    """
    
    def __init__(self):
        self.active_zones = {
            'asia_pacific': {
                'timezone': pytz.timezone('Asia/Tokyo'),
                'active_hours': (19, 3),  # 7 PM - 3 AM EST
                'exchanges': ['binance', 'okx', 'bybit'],
                'volatility_multiplier': 1.5,
                'current_status': 'sleeping'
            },
            'europe': {
                'timezone': pytz.timezone('Europe/London'),
                'active_hours': (3, 11),  # 3 AM - 11 AM EST
                'exchanges': ['kraken', 'bitstamp'],
                'volatility_multiplier': 1.2,
                'current_status': 'sleeping'
            },
            'americas': {
                'timezone': pytz.timezone('US/Eastern'),
                'active_hours': (9, 17),  # 9 AM - 5 PM EST
                'exchanges': ['coinbase', 'gemini'],
                'volatility_multiplier': 1.3,
                'current_status': 'sleeping'
            },
            'defi_24_7': {
                'timezone': pytz.timezone('UTC'),
                'active_hours': (0, 24),  # Always active
                'exchanges': ['uniswap', 'sushiswap', 'pancakeswap'],
                'volatility_multiplier': 2.0,
                'current_status': 'hunting'
            }
        }
        
        self.volatility_threshold = 5  # % swing to trigger crawdad deployment
        self.tracked_cryptos = []
        self.hot_zones = []
        self.crawdad_deployments = []
        self.total_opportunities = 0
        self.successful_hunts = 0
        
    def get_current_active_zones(self):
        """Identify which zones are currently in prime trading hours"""
        now = datetime.now(pytz.timezone('US/Eastern'))
        active = []
        
        for zone_name, zone_info in self.active_zones.items():
            zone_time = now.astimezone(zone_info['timezone'])
            hour = zone_time.hour
            
            start, end = zone_info['active_hours']
            if zone_name == 'defi_24_7':
                zone_info['current_status'] = 'hunting'
                active.append(zone_name)
            elif start <= hour < end or (start > end and (hour >= start or hour < end)):
                zone_info['current_status'] = 'hunting'
                active.append(zone_name)
            else:
                zone_info['current_status'] = 'sleeping'
                
        return active
    
    def scan_for_volatility(self, symbols=None):
        """Scan markets for high volatility opportunities"""
        if not symbols:
            symbols = [
                'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
                'DOGE-USD', 'SHIB-USD', 'MATIC-USD', 'AVAX-USD', 'LINK-USD',
                'PEPE-USD', 'FLOKI-USD', 'BONK-USD', 'WIF-USD', 'BRETT-USD'
            ]
        
        volatile_assets = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d', interval='5m')
                
                if not hist.empty and len(hist) > 10:
                    # Calculate recent volatility
                    recent_data = hist.tail(12)  # Last hour
                    high = recent_data['High'].max()
                    low = recent_data['Low'].min()
                    current = recent_data['Close'].iloc[-1]
                    
                    volatility = ((high - low) / low * 100) if low > 0 else 0
                    momentum = ((current - recent_data['Close'].iloc[0]) / recent_data['Close'].iloc[0] * 100)
                    
                    if volatility > self.volatility_threshold:
                        volatile_assets.append({
                            'symbol': symbol,
                            'volatility': volatility,
                            'momentum': momentum,
                            'current_price': current,
                            'volume': recent_data['Volume'].sum(),
                            'opportunity_score': volatility * abs(momentum),
                            'timestamp': datetime.now().isoformat()
                        })
                        
            except Exception as e:
                continue
        
        # Sort by opportunity score
        volatile_assets.sort(key=lambda x: x['opportunity_score'], reverse=True)
        return volatile_assets
    
    def identify_hot_zones(self):
        """Find the hottest trading zones right now"""
        active_zones = self.get_current_active_zones()
        hot_zones = []
        
        for zone in active_zones:
            zone_info = self.active_zones[zone]
            
            # Check zone-specific volatility
            if zone == 'asia_pacific':
                symbols = ['BTC-USD', 'ETH-USD', 'BNB-USD']  # Asia favorites
            elif zone == 'europe':
                symbols = ['BTC-USD', 'ETH-USD', 'MATIC-USD']
            elif zone == 'americas':
                symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD']
            else:  # DeFi
                symbols = ['SHIB-USD', 'PEPE-USD', 'FLOKI-USD', 'BONK-USD']
            
            volatile = self.scan_for_volatility(symbols)
            
            if volatile:
                avg_volatility = np.mean([v['volatility'] for v in volatile])
                hot_zones.append({
                    'zone': zone,
                    'avg_volatility': avg_volatility * zone_info['volatility_multiplier'],
                    'top_opportunities': volatile[:3],
                    'status': zone_info['current_status']
                })
        
        hot_zones.sort(key=lambda x: x['avg_volatility'], reverse=True)
        self.hot_zones = hot_zones
        return hot_zones
    
    def deploy_crawdads(self, opportunity):
        """Deploy quantum crawdads to exploit volatility"""
        deployment = {
            'id': f"crawdad_{len(self.crawdad_deployments)+1}",
            'symbol': opportunity['symbol'],
            'entry_price': opportunity['current_price'],
            'volatility': opportunity['volatility'],
            'momentum': opportunity['momentum'],
            'strategy': self.select_strategy(opportunity),
            'deployed_at': datetime.now().isoformat(),
            'status': 'hunting'
        }
        
        self.crawdad_deployments.append(deployment)
        self.total_opportunities += 1
        
        return deployment
    
    def select_strategy(self, opportunity):
        """Select best strategy based on market conditions"""
        if opportunity['momentum'] > 3:
            return 'momentum_ride'
        elif opportunity['momentum'] < -3:
            return 'reversal_catch'
        elif opportunity['volatility'] > 10:
            return 'range_trade'
        else:
            return 'scalp_hunt'
    
    def generate_alert(self, opportunity, zone):
        """Generate alert for high-value opportunity"""
        alert = {
            'level': 'HIGH' if opportunity['opportunity_score'] > 50 else 'MEDIUM',
            'zone': zone,
            'symbol': opportunity['symbol'],
            'action': 'DEPLOY_CRAWDADS',
            'volatility': f"{opportunity['volatility']:.2f}%",
            'momentum': f"{opportunity['momentum']:.2f}%",
            'score': opportunity['opportunity_score'],
            'message': f"🔥 {opportunity['symbol']} exploding in {zone}! Volatility: {opportunity['volatility']:.1f}%",
            'timestamp': datetime.now().isoformat()
        }
        return alert
    
    def run_24_7_hunter(self, duration_hours=24):
        """Run the 24/7 volatility hunter"""
        print("""
🌍 GLOBAL VOLATILITY HUNTER ACTIVATED
═══════════════════════════════════════════════════════════
Following the sun across global markets...
Hunting volatility 24/7 across all time zones...
═══════════════════════════════════════════════════════════
        """)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        
        alerts = []
        stats = {
            'scans_performed': 0,
            'opportunities_found': 0,
            'crawdads_deployed': 0,
            'zones_tracked': set(),
            'best_opportunity': None,
            'best_score': 0
        }
        
        while datetime.now() < end_time:
            print(f"\n🔍 Scanning at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Identify hot zones
            hot_zones = self.identify_hot_zones()
            
            if hot_zones:
                print(f"\n🔥 ACTIVE ZONES:")
                for zone_data in hot_zones[:3]:
                    zone = zone_data['zone']
                    print(f"  • {zone}: {zone_data['avg_volatility']:.2f}% avg volatility")
                    stats['zones_tracked'].add(zone)
                    
                    # Check for deployment opportunities
                    for opp in zone_data['top_opportunities']:
                        if opp['opportunity_score'] > 20:
                            # Deploy crawdads
                            deployment = self.deploy_crawdads(opp)
                            alert = self.generate_alert(opp, zone)
                            alerts.append(alert)
                            
                            print(f"\n🦞 CRAWDAD DEPLOYED!")
                            print(f"   Symbol: {opp['symbol']}")
                            print(f"   Volatility: {opp['volatility']:.2f}%")
                            print(f"   Strategy: {deployment['strategy']}")
                            
                            stats['crawdads_deployed'] += 1
                            stats['opportunities_found'] += 1
                            
                            if opp['opportunity_score'] > stats['best_score']:
                                stats['best_score'] = opp['opportunity_score']
                                stats['best_opportunity'] = opp
            
            # Global scan for sudden spikes
            print("\n🌐 Global volatility scan...")
            all_volatile = self.scan_for_volatility()
            
            if all_volatile and all_volatile[0]['volatility'] > 15:
                print(f"\n⚡ EXTREME VOLATILITY DETECTED!")
                print(f"   {all_volatile[0]['symbol']}: {all_volatile[0]['volatility']:.2f}%")
                print(f"   Deploying emergency crawdad swarm...")
                
                for asset in all_volatile[:3]:
                    if asset['volatility'] > 10:
                        self.deploy_crawdads(asset)
                        stats['crawdads_deployed'] += 1
            
            stats['scans_performed'] += 1
            
            # Show running statistics
            if stats['scans_performed'] % 5 == 0:
                print(f"""
📊 HUNTING STATISTICS
═══════════════════════════════════════════════════════════
Scans: {stats['scans_performed']} | Opportunities: {stats['opportunities_found']}
Crawdads Deployed: {stats['crawdads_deployed']}
Zones Tracked: {', '.join(stats['zones_tracked'])}
═══════════════════════════════════════════════════════════
                """)
            
            # Wait before next scan (5 minutes)
            time.sleep(300)
        
        # Final report
        self.generate_final_report(stats, alerts)
        
        return stats, alerts
    
    def generate_final_report(self, stats, alerts):
        """Generate comprehensive hunting report"""
        print(f"""
🏆 24/7 VOLATILITY HUNTING COMPLETE
═══════════════════════════════════════════════════════════
PERFORMANCE METRICS:
  • Total Scans: {stats['scans_performed']}
  • Opportunities Found: {stats['opportunities_found']}
  • Crawdads Deployed: {stats['crawdads_deployed']}
  • Success Rate: {(stats['opportunities_found']/max(stats['scans_performed'],1)*100):.1f}%

ZONE COVERAGE:
  • Zones Tracked: {len(stats['zones_tracked'])}
  • Most Active: {', '.join(stats['zones_tracked'])}

BEST OPPORTUNITY:
        """)
        
        if stats['best_opportunity']:
            best = stats['best_opportunity']
            print(f"""  • Symbol: {best['symbol']}
  • Volatility: {best['volatility']:.2f}%
  • Score: {best['opportunity_score']:.2f}
            """)
        
        # Save hunting data
        report = {
            'stats': {
                'scans': stats['scans_performed'],
                'opportunities': stats['opportunities_found'],
                'deployments': stats['crawdads_deployed'],
                'zones': list(stats['zones_tracked'])
            },
            'best_opportunity': stats['best_opportunity'],
            'deployments': self.crawdad_deployments[-10:],  # Last 10
            'alerts': alerts[-20:],  # Last 20 alerts
            'timestamp': datetime.now().isoformat()
        }
        
        with open('global_volatility_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("""
🦞 CRAWDAD WISDOM:
═══════════════════════════════════════════════════════════
The volatile waters never sleep. Our crawdads follow the sun,
hunting opportunities across every time zone. From Tokyo dawn
to New York close, from London lunch to Sydney night - 
we are always hunting.

Report saved to: global_volatility_report.json
═══════════════════════════════════════════════════════════
        """)

def run_test_scan():
    """Run a quick test scan to show current opportunities"""
    hunter = GlobalVolatilityHunter()
    
    print("🔍 Running quick volatility scan...")
    
    # Check active zones
    active = hunter.get_current_active_zones()
    print(f"\nActive zones right now: {', '.join(active)}")
    
    # Find hot zones
    hot_zones = hunter.identify_hot_zones()
    
    if hot_zones:
        print(f"\n🔥 HOTTEST ZONE: {hot_zones[0]['zone']}")
        print(f"   Average Volatility: {hot_zones[0]['avg_volatility']:.2f}%")
        
        if hot_zones[0]['top_opportunities']:
            print("\n🎯 TOP OPPORTUNITIES:")
            for opp in hot_zones[0]['top_opportunities'][:3]:
                print(f"   • {opp['symbol']}: {opp['volatility']:.2f}% volatility, {opp['momentum']:.2f}% momentum")
    
    # Global scan
    print("\n🌐 Global volatility leaders:")
    volatile = hunter.scan_for_volatility()
    for asset in volatile[:5]:
        print(f"   • {asset['symbol']}: {asset['volatility']:.2f}% swing, score: {asset['opportunity_score']:.1f}")

if __name__ == "__main__":
    # Run quick test scan
    run_test_scan()
    
    print("""

To run 24/7 hunter:
    hunter = GlobalVolatilityHunter()
    stats, alerts = hunter.run_24_7_hunter(duration_hours=24)
    
Or integrate with Cherokee AI Portal for real-time monitoring!
    """)