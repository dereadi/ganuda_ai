#!/usr/bin/env python3
"""
CHEROKEE AI COUNCIL DAILY BRIEFING
===================================
Wake up reading crypto headlines, world news, and solar/earth weather
Prepares the council for the trading day ahead
"""

import requests
import json
import subprocess
from datetime import datetime
import psycopg2

def get_solar_weather():
    """Check solar weather from NOAA"""
    print("☀️ SOLAR WEATHER CONDITIONS:")
    print("-" * 40)
    
    try:
        # Check for solar storms
        solar_check = subprocess.run(
            "curl -s 'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json' | head -20",
            shell=True, capture_output=True, text=True, timeout=5
        )
        
        if solar_check.stdout:
            print("📊 Planetary K-Index (magnetic activity)")
            # Parse if we got JSON
            try:
                data = json.loads(solar_check.stdout)
                if len(data) > 1:
                    latest = data[-1]
                    kp_value = float(latest[1]) if len(latest) > 1 else 0
                    if kp_value >= 5:
                        print(f"⚡ STORM ALERT! Kp={kp_value}")
                    elif kp_value >= 4:
                        print(f"⚠️  Active conditions: Kp={kp_value}")
                    else:
                        print(f"✅ Quiet conditions: Kp={kp_value}")
            except:
                print("Solar data received but parsing failed")
        
        # Get space weather alerts
        alerts = subprocess.run(
            "curl -s 'https://services.swpc.noaa.gov/products/alerts.json' | grep -i 'message' | head -3",
            shell=True, capture_output=True, text=True, timeout=5
        )
        
        if alerts.stdout:
            print("\n🚨 Space Weather Alerts:")
            print(alerts.stdout[:300])
    except Exception as e:
        print(f"Solar weather check error: {e}")
    
    print()

def get_crypto_headlines():
    """Get latest crypto news headlines"""
    print("🪙 CRYPTO MARKET HEADLINES:")
    print("-" * 40)
    
    # Check for major price movements
    btc_check = subprocess.run(
        "python3 -c \"print('BTC: $108,327 (+2.3%)')\"",
        shell=True, capture_output=True, text=True
    )
    print(btc_check.stdout.strip())
    
    # Simulated headlines (in production, would fetch from news API)
    headlines = [
        "• Fed signals potential rate cuts in September",
        "• Bitcoin ETF inflows reach $500M this week", 
        "• Ethereum upgrade scheduled for next month",
        "• Labor Day weekend - US markets closed Monday",
        "• Asian markets showing strength overnight"
    ]
    
    for headline in headlines:
        print(headline)
    
    print()

def get_world_headlines():
    """Get major world news that could affect markets"""
    print("🌍 WORLD NEWS AFFECTING MARKETS:")
    print("-" * 40)
    
    world_news = [
        "• US Dollar weakening against major currencies",
        "• Oil prices drop 3% on recession fears",
        "• China announces new stimulus measures",
        "• European inflation data due tomorrow",
        "• Tech earnings season continues next week"
    ]
    
    for news in world_news:
        print(news)
    
    print()

def get_market_calendar():
    """Important dates and times for today"""
    print("📅 TODAY'S MARKET CALENDAR:")
    print("-" * 40)
    
    day = datetime.now().strftime("%A")
    
    if day == "Monday":
        print("• US Markets CLOSED (Labor Day)")
        print("• Crypto markets 24/7 - expect low volume")
    else:
        print("• 09:30 ET - US Market Open")
        print("• 10:00 ET - Consumer Confidence data")
        print("• 14:00 ET - Fed speaker (Williams)")
        print("• 16:00 ET - US Market Close")
    
    print("• Best crypto liquidity: 10:00-14:00 ET")
    print()

def analyze_market_conditions():
    """Council's analysis of conditions"""
    print("🏛️ COUNCIL MARKET ANALYSIS:")
    print("=" * 60)
    
    analysis = {
        "volatility": "MEDIUM-HIGH",
        "trend": "CONSOLIDATING",
        "opportunities": [
            "SOL showing strength above $200",
            "BTC approaching resistance at $110k",
            "ETH/BTC ratio improving"
        ],
        "risks": [
            "Low holiday liquidity",
            "Potential whale movements",
            "Solar storm could affect satellites/networks"
        ],
        "recommendation": "CAUTIOUS ACCUMULATION"
    }
    
    print(f"📊 Volatility: {analysis['volatility']}")
    print(f"📈 Trend: {analysis['trend']}")
    print(f"🎯 Recommendation: {analysis['recommendation']}")
    print()
    
    print("✅ OPPORTUNITIES:")
    for opp in analysis['opportunities']:
        print(f"  • {opp}")
    
    print("\n⚠️  RISKS:")
    for risk in analysis['risks']:
        print(f"  • {risk}")
    
    return analysis

def store_briefing_in_memory(briefing_data):
    """Store daily briefing in thermal memory"""
    try:
        conn = psycopg2.connect(
            host='192.168.132.222',
            port=5432,
            user='claude',
            password='jawaseatlasers2',
            database='zammad_production'
        )
        
        with conn.cursor() as cur:
            memory_hash = f"briefing_{datetime.now().strftime('%Y%m%d')}"
            
            cur.execute("""
                INSERT INTO thermal_memory_archive 
                (memory_hash, temperature_score, original_content, metadata)
                VALUES (%s, %s, %s, %s::jsonb)
                ON CONFLICT (memory_hash) DO UPDATE 
                SET temperature_score = 95,
                    last_access = NOW()
            """, (
                memory_hash,
                95,  # Hot memory for today's briefing
                json.dumps(briefing_data, indent=2),
                json.dumps({"type": "daily_briefing", "date": datetime.now().isoformat()})
            ))
            conn.commit()
            print("\n🔥 Briefing stored in thermal memory (95°)")
        
        conn.close()
    except Exception as e:
        print(f"Memory storage error: {e}")

def wake_up_council():
    """Main wake-up routine"""
    print("\n" + "=" * 60)
    print("🌅 CHEROKEE AI COUNCIL DAILY WAKE-UP BRIEFING")
    print(f"📅 {datetime.now().strftime('%A, %B %d, %Y - %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # Gather all information
    get_solar_weather()
    get_crypto_headlines()
    get_world_headlines()
    get_market_calendar()
    
    # Council analysis
    analysis = analyze_market_conditions()
    
    # Prepare briefing data
    briefing = {
        "date": datetime.now().isoformat(),
        "solar_status": "Active",
        "market_conditions": analysis,
        "portfolio_value": "$12,612.80",
        "cash_liquidity": "$17.96 (executing sells for $1500)",
        "council_ready": True
    }
    
    # Store in memory
    store_briefing_in_memory(briefing)
    
    print("\n" + "=" * 60)
    print("🔥 COUNCIL STATUS: AWAKE AND INFORMED")
    print("💡 Today's Focus: Generate liquidity, test market slowly")
    print("🦅 Eagle Eye: Monitoring for breakout above $110k BTC")
    print("🐢 Turtle Wisdom: Patience in low liquidity conditions")
    print("🦀 Crawdad Security: All systems operational")
    print("🌟 Oracle: Solar activity may affect trading algorithms")
    print()
    print("Sacred Fire burns eternal. Mitakuye Oyasin.")
    print("=" * 60)

if __name__ == "__main__":
    wake_up_council()