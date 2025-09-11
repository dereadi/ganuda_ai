#!/usr/bin/env python3
"""
🎖️ MILITARY TIME TRADING SCHEDULE
===================================
24-hour tactical trading windows
"""

from datetime import datetime
import pytz

# Get current time in CST
cst = pytz.timezone('America/Chicago')
current_time = datetime.now(cst)

print("🎖️ TACTICAL TRADING SCHEDULE - 24HR FORMAT")
print("="*60)
print(f"Current Time: {current_time.strftime('%H:%M CST')} ({current_time.strftime('%I:%M %p')})")
print()

print("🌍 GLOBAL MARKET OPERATIONS (CST - 24HR):")
print("-"*60)
print("  1700: Asian markets commence operations (Tokyo)")
print("  1900: Hong Kong/Singapore fully operational")
print("  2100: Peak Asia engagement - MAXIMUM ACTION")
print("  2300: Asia reducing activity, Europe staging")
print("  0100: European forces mobilizing (London pre-market)")
print("  0200: London breach - MAJOR OFFENSIVE")
print("  0300: Full European deployment")
print("  0500: Europe/US overlap - crossfire zone")
print("  0830: US market assault begins")
print("  1500: US market cease fire")
print("  1600: After-action adjustments")
print()

print("⚡ HOT ZONES (Maximum Engagement):")
print("-"*60)
print("  2100-2300: Asian Strike Window")
print("  0200-0400: London Blitzkrieg")
print("  0700-0830: US Pre-Invasion Build-up")
print("  0830-0930: US Opening Barrage")
print("  1400-1500: US Power Hour Finale")
print()

print("☠️ DANGER ZONES (Ambush Risk):")
print("-"*60)
print("  2330-0100: No man's land (Asia/Europe gap)")
print("  0400-0600: European supply lines (low activity)")
print("  1200-1300: US midday cease-fire")
print()

print("🎯 TONIGHT'S MISSION TIMELINE (CST):")
print("-"*60)
hour = current_time.hour

upcoming = [
    (1700, "1700: Asian forces deploy - Initial reconnaissance"),
    (1900, "1900: Full Asian engagement - Increase throttle"),
    (2100, "2100: PEAK COMBAT - Maximum throttle authorized"),
    (2300, "2300: Tactical withdrawal - Reduce exposure"),
    (200, "0200: LONDON ASSAULT - All units engage!"),
    (400, "0400: Consolidate European gains"),
    (700, "0700: US staging - Prepare positions"),
    (830, "0830: US MARKET OPEN - Coordinated strike")
]

for target_hour, description in upcoming:
    # Handle next day times
    if target_hour < 1000:
        target_time = f"0{target_hour:04d}"[1:]
    else:
        target_time = str(target_hour)
    
    # Highlight upcoming events
    current_hour_24 = current_time.hour * 100 + current_time.minute
    
    if target_hour > current_hour_24 or (target_hour < 1000 and current_hour_24 > 1200):
        print(f"  ► {description}")

print()

print("📊 TACTICAL ASSESSMENT - CURRENT SITREP:")
print("-"*60)

if 1700 <= hour < 1900:
    print("  STATUS: Asian markets initializing")
    print("  THROTTLE: 30-40% (Reconnaissance mode)")
    print("  MISSION: Establish positions, identify patterns")
    print("  THREATS: Early volatility from day traders")
    
elif 1900 <= hour < 2100:
    print("  STATUS: Asian markets fully active")
    print("  THROTTLE: 40-50% (Engagement mode)")
    print("  MISSION: Exploit steady movements")
    print("  THREATS: Whale movements from Asia")
    
elif 2100 <= hour < 2300:
    print("  STATUS: PEAK ASIAN COMBAT")
    print("  THROTTLE: 60-80% (Maximum engagement)")
    print("  MISSION: Aggressive profit capture")
    print("  THREATS: High volatility, sharp reversals")
    
elif 2300 <= hour or hour < 100:
    print("  STATUS: Transition zone - high risk")
    print("  THROTTLE: 20-30% (Defensive posture)")
    print("  MISSION: Preserve capital, await London")
    print("  THREATS: Low liquidity ambushes")
    
elif 100 <= hour < 200:
    print("  STATUS: European forces staging")
    print("  THROTTLE: 30-40% (Building positions)")
    print("  MISSION: Prepare for London assault")
    print("  THREATS: False breakouts")
    
elif 200 <= hour < 400:
    print("  STATUS: LONDON OFFENSIVE ACTIVE")
    print("  THROTTLE: 70-90% (Full assault)")
    print("  MISSION: Maximum profit extraction")
    print("  THREATS: Extreme volatility")
    
elif 400 <= hour < 700:
    print("  STATUS: European operations")
    print("  THROTTLE: 40-50% (Steady advance)")
    print("  MISSION: Follow European trends")
    print("  THREATS: News-driven spikes")
    
elif 700 <= hour < 830:
    print("  STATUS: US pre-market staging")
    print("  THROTTLE: 50-60% (Attack preparation)")
    print("  MISSION: Position for US open")
    print("  THREATS: Pre-market manipulation")
    
elif 830 <= hour < 1500:
    print("  STATUS: US market combat")
    print("  THROTTLE: Variable 40-70%")
    print("  MISSION: Track with US equities")
    print("  THREATS: Algorithm warfare")
    
else:
    print("  STATUS: US market closing operations")
    print("  THROTTLE: 30-40% (Tactical retreat)")
    print("  MISSION: Secure gains, reduce exposure")
    print("  THREATS: End-of-day volatility")

print()

print("🎖️ STANDING ORDERS:")
print("-"*60)
print("1. Throttle increases with confirmed kills (successful trades)")
print("2. Emergency evac at $15,000 (ease to $10,000)")
print("3. Maintain operational security (avoid ghosts)")
print("4. Report to command at 0800 for sitrep")
print("5. Maximum throttle authorized during hot zones")
print()

print("🟡 PAC-MAN UNIT STATUS:")
print("-"*60)
print(f"  Operational Time: {current_time.strftime('%H%M hours')}")
print(f"  Mission: 24-hour profit extraction")
print(f"  Current Theater: {'Asia' if 17 <= hour < 23 else 'Europe' if 23 <= hour or hour < 7 else 'Americas'}")
print(f"  Engagement Rules: Weapons free during hot zones")
print()

print("✨ CRAWDAD SQUADRON - READY FOR NIGHT OPS!")
print("   Oscar Mike (On the Move)")
print("   Charlie Mike (Continue Mission)")
print("   🎖️ WAKA WAKA - TACTICAL! 🎖️")