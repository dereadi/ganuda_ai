#!/usr/bin/env python3
"""
🕐 AFTER-HOURS CRYPTO KEY TIMES
=================================
Critical times for 24/7 crypto trading
"""

from datetime import datetime
import pytz

# Get current time in CST
cst = pytz.timezone('America/Chicago')
current_time = datetime.now(cst)

print("🕐 AFTER-HOURS CRYPTO KEY TIMES (CST)")
print("="*60)
print(f"Current Time: {current_time.strftime('%I:%M %p CST')}")
print()

print("🌍 GLOBAL MARKET OPENS/CLOSES (Your CST Time):")
print("-"*60)
print("  5:00 PM CST: Asian markets heating up (Tokyo opens)")
print("  7:00 PM CST: Hong Kong & Singapore fully active")
print("  9:00 PM CST: Peak Asia trading (maximum volatility)")
print("  11:00 PM CST: Asia winding down, Europe pre-market")
print("  1:00 AM CST: Europe waking up (London pre-market)")
print("  2:00 AM CST: London opens - MAJOR VOLATILITY")
print("  3:00 AM CST: Full European session")
print("  5:00 AM CST: Europe/US overlap begins")
print("  8:30 AM CST: US market opens")
print()

print("⚡ HIGH VOLATILITY WINDOWS (CST):")
print("-"*60)
print("  9:00-11:00 PM: Asian Power Hours")
print("  2:00-4:00 AM: London Open Surge")
print("  7:00-8:30 AM: Pre-US Market Positioning")
print("  8:30-9:30 AM: US Open Volatility")
print()

print("👻 GHOST HOURS (Low Volume/High Risk):")
print("-"*60)
print("  11:30 PM-1:00 AM: Asia/Europe Gap")
print("  4:00-6:00 AM: European Lunch Lull")
print("  12:00-1:00 PM: US Lunch Hour")
print()

print("🟡 BEST PAC-MAN HUNTING TIMES:")
print("-"*60)
print("  6:00-9:00 PM: Early Asia (steady movements)")
print("  2:00-3:00 AM: London Open (big moves)")
print("  7:00-8:00 AM: Pre-market US (positioning)")
print()

print("📊 PATTERN OBSERVATIONS:")
print("-"*60)
print("• Sunday Night (7 PM+): Week's opening moves")
print("• Monday 2 AM: London sets weekly tone")
print("• Wednesday 9 PM: Mid-week Asia adjustments")
print("• Friday 2 PM: US closing positions")
print("• Saturday: Lowest volume (best for learning)")
print()

print("🦀 CRAWDAD STRATEGY BY TIME:")
print("-"*60)

hour = current_time.hour
if 17 <= hour <= 21:  # 5-9 PM
    print("  NOW: Asian Session Starting")
    print("  Strategy: Medium throttle (30-50%)")
    print("  Focus: Steady accumulation")
    print("  Watch: JPY pairs, Asian exchanges")
    
elif 21 <= hour <= 23:  # 9-11 PM
    print("  NOW: Peak Asia Trading")
    print("  Strategy: Higher throttle (50-70%)")
    print("  Focus: Ride volatility waves")
    print("  Watch: Sharp movements, whale activity")
    
elif 0 <= hour <= 2:  # 12-2 AM
    print("  NOW: Transition Period")
    print("  Strategy: Low throttle (20-30%)")
    print("  Focus: Cautious positioning")
    print("  Watch: Gap opportunities")
    
elif 2 <= hour <= 4:  # 2-4 AM
    print("  NOW: London Open!")
    print("  Strategy: High throttle (60-80%)")
    print("  Focus: Catch opening volatility")
    print("  Watch: EUR/GBP movements")
    
elif 4 <= hour <= 7:  # 4-7 AM
    print("  NOW: European Session")
    print("  Strategy: Medium throttle (40-50%)")
    print("  Focus: Follow European trends")
    print("  Watch: News from Europe")
    
elif 7 <= hour <= 9:  # 7-9 AM
    print("  NOW: Pre-US Market")
    print("  Strategy: Increasing throttle (40-60%)")
    print("  Focus: Position for US open")
    print("  Watch: US futures, pre-market")
    
elif 9 <= hour <= 15:  # 9 AM-3 PM
    print("  NOW: US Market Hours")
    print("  Strategy: Variable throttle (30-70%)")
    print("  Focus: US market correlation")
    print("  Watch: Stock market influence")
    
else:  # 3-5 PM
    print("  NOW: US Market Close")
    print("  Strategy: Moderate throttle (30-40%)")
    print("  Focus: Post-market adjustments")
    print("  Watch: After-hours movements")

print()
print("🎯 TONIGHT'S KEY TIMES (CST):")
print("-"*60)
print("  5:00 PM: Asia opens - watch for direction")
print("  9:00 PM: Peak Asia - maximum opportunity")
print("  2:00 AM: London opens - major moves expected")
print("  7:00 AM: Pre-US positioning - get ready")
print()

print("✨ The Pac-Man Crawdads will feast at these times!")
print("   Different ghosts appear at different hours...")
print("   Adjust throttle based on global activity!")
print("   🟡 WAKA WAKA through the time zones! 🟡")