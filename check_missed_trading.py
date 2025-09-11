#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔍 CHECK MISSED TRADING OPPORTUNITIES
Assess what we missed while redfin CPU ran away
"""

import json
import subprocess
from datetime import datetime, timedelta
from coinbase.rest import RESTClient
from pathlib import Path

def load_coinbase_config():
    """Load Coinbase configuration"""
    config_path = Path.home() / ".coinbase_config.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return None

def check_market_movement():
    """Check market movements we missed"""
    
    print("🔍 CHECKING MISSED TRADING OPPORTUNITIES")
    print("=" * 80)
    print("While redfin CPUs were overloaded...")
    print()
    
    try:
        # Initialize Coinbase client
        config = load_coinbase_config()
        if not config:
            print("❌ Coinbase config not found")
            return
        
        client = RESTClient(
            api_key=config['api_key'],
            api_secret=config['api_secret']
        )
        
        # Check key assets
        assets = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 'AVAX-USD']
        
        print("📊 CURRENT MARKET STATUS:")
        print("-" * 60)
        
        opportunities_missed = []
        
        for asset in assets:
            try:
                ticker = client.get_product(asset)
                stats = client.get_product_stats(asset)
                
                price = float(ticker['price'])
                high_24h = float(stats['high'])
                low_24h = float(stats['low'])
                volume = float(stats['volume'])
                
                # Calculate range and volatility
                range_pct = ((high_24h - low_24h) / low_24h) * 100
                from_low = ((price - low_24h) / low_24h) * 100
                from_high = ((high_24h - price) / high_24h) * 100
                
                print(f"{asset.replace('-USD', '')}:")
                print(f"  Current: ${price:,.2f}")
                print(f"  24h Range: ${low_24h:,.2f} - ${high_24h:,.2f} ({range_pct:.1f}%)")
                print(f"  Position: {from_low:.1f}% from low, {from_high:.1f}% from high")
                
                # Check for missed opportunities
                if asset == 'SOL-USD':
                    if low_24h < 199 and high_24h > 204:
                        opportunities_missed.append(f"SOL oscillation range hit! Low: ${low_24h:.2f}, High: ${high_24h:.2f}")
                
                if asset == 'ETH-USD':
                    if price > 4400:
                        opportunities_missed.append(f"ETH broke $4400 resistance! Current: ${price:.2f}")
                    elif low_24h < 4200:
                        opportunities_missed.append(f"ETH dip opportunity at ${low_24h:.2f}")
                
                if asset == 'DOGE-USD':
                    if price > 0.22:
                        opportunities_missed.append(f"DOGE blood bag trigger hit at ${price:.4f}!")
                    elif low_24h < 0.20:
                        opportunities_missed.append(f"DOGE accumulation opportunity at ${low_24h:.4f}")
                
                if range_pct > 5:
                    opportunities_missed.append(f"{asset.replace('-USD', '')} high volatility: {range_pct:.1f}% range")
                
                print()
                
            except Exception as e:
                print(f"  Error getting {asset}: {e}")
                print()
        
        # Check account balance
        try:
            accounts = client.get_accounts()
            
            usd_balance = 0
            for account in accounts['accounts']:
                if account['currency'] == 'USD':
                    usd_balance = float(account['available_balance']['value'])
                    break
            
            print("💰 CURRENT LIQUIDITY:")
            print(f"  USD Available: ${usd_balance:.2f}")
            
            if usd_balance < 100:
                opportunities_missed.append(f"⚠️ Low liquidity prevented trading: ${usd_balance:.2f}")
            
        except Exception as e:
            print(f"Error checking balance: {e}")
        
        print("\n" + "=" * 80)
        
        if opportunities_missed:
            print("⚠️ MISSED OPPORTUNITIES:")
            for opp in opportunities_missed:
                print(f"  • {opp}")
        else:
            print("✅ No major opportunities missed")
        
        print("\n🔥 BAND STATUS:")
        print("-" * 60)
        
        # Analyze current band status
        for asset in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
            try:
                stats = client.get_product_stats(asset)
                high = float(stats['high'])
                low = float(stats['low'])
                price = float(client.get_product(asset)['price'])
                
                band_width = ((high - low) / ((high + low) / 2)) * 100
                position_in_band = ((price - low) / (high - low)) * 100
                
                symbol = asset.replace('-USD', '')
                
                if band_width < 2:
                    print(f"  📊 {symbol}: TIGHT BANDS ({band_width:.1f}%) - Squeeze imminent!")
                elif band_width < 3:
                    print(f"  📊 {symbol}: Bands tightening ({band_width:.1f}%) - Prepare for breakout")
                else:
                    print(f"  📊 {symbol}: Normal bands ({band_width:.1f}%) - Position: {position_in_band:.0f}%")
                    
            except Exception as e:
                print(f"  Error analyzing {asset}: {e}")
        
        return opportunities_missed
        
    except Exception as e:
        print(f"Error checking markets: {e}")
        return []

def check_specialist_status():
    """Check if specialists are still running properly"""
    
    print("\n🏛️ SPECIALIST STATUS:")
    print("-" * 60)
    
    specialists = ['gap', 'trend', 'volatility', 'breakout', 'mean_reversion']
    
    for specialist in specialists:
        result = subprocess.run(
            f"pgrep -f '{specialist}_specialist.py'",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            if len(pids) == 1:
                print(f"  ✅ {specialist}_specialist: Running (PID: {pids[0]})")
            else:
                print(f"  ⚠️ {specialist}_specialist: Multiple instances ({len(pids)} PIDs)")
        else:
            print(f"  ❌ {specialist}_specialist: Not running")

def main():
    """Check what we missed during CPU overload"""
    
    print("🔥 CHEROKEE TRADING ASSESSMENT")
    print("=" * 80)
    print("Analyzing missed opportunities from redfin CPU overload")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Check market movements
    missed = check_market_movement()
    
    # Check specialist status
    check_specialist_status()
    
    print("\n" + "=" * 80)
    print("🔥 RECOVERY PLAN:")
    print("-" * 60)
    
    if missed:
        print("1. Review missed opportunities and adjust strategies")
        print("2. Implement process monitoring to prevent future overloads")
        print("3. Consider containerization for specialists")
        print("4. Set up alerts for CPU usage > 80%")
    else:
        print("1. Markets relatively stable - no critical misses")
        print("2. Focus on preventing future CPU overloads")
        print("3. Continue monitoring band tightening")
    
    print("\n🔥 Sacred Fire continues burning despite system challenges")

if __name__ == "__main__":
    main()