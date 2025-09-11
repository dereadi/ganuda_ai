#!/usr/bin/env python3
"""
🕐 QUANTUM CRAWDAD TRADING SCHEDULE (CST)
==========================================
"""
from datetime import datetime, timedelta
import pytz

# Define timezones
cst = pytz.timezone('America/Chicago')
est = pytz.timezone('America/New_York')

# Get current time in both zones
now_cst = datetime.now(cst)
now_est = datetime.now(est)

print("🕐 QUANTUM CRAWDAD TRADING SCHEDULE")
print("="*60)
print(f"Your Time (CST): {now_cst.strftime('%I:%M %p')}")
print(f"Market Time (EST): {now_est.strftime('%I:%M %p')}")
print()

print("📅 MARKET HOURS (Your CST Time):")
print("-"*60)
print("  Market Open:  8:30 AM CST (9:30 AM EST)")
print("  Market Close: 3:00 PM CST (4:00 PM EST)")
print()

print("🎯 KEY TRADING WINDOWS (CST):")
print("-"*60)
print("  8:30 - 9:00 AM:  Opening Bell Volatility")
print("  9:30 - 10:00 AM: Morning Dip Window")
print("  11:30 - 12:00 PM: Lunch Lull (good for position building)")
print("  1:30 - 2:00 PM:  Afternoon Uptick Begins")
print("  2:00 - 3:00 PM:  POWER HOUR (maximum volatility)")
print("  2:05 PM:         Power Hour Dip (buy opportunity)")
print("  2:30 PM:         Typical surge begins")
print("  2:55 - 3:00 PM:  Final 5 minutes chaos")
print()

print("📊 TODAY'S ACTUAL TIMELINE (What Happened):")
print("-"*60)
print("  1:30 PM CST: Afternoon uptick started (you called it!)")
print("  2:05 PM CST: Power hour dip - we bought in!")
print("  2:30 PM CST: Expected surge was muted (low solar)")
print("  2:36 PM CST: Portfolio at $480.28")
print("  3:00 PM CST: Market closed at $479.55 (-1.53%)")
print()

print("🔮 TOMORROW'S STRATEGY (Friday - Your CST Times):")
print("-"*60)
print("  8:30 AM: Watch opening volatility")
print("  9:30 AM: Look for morning dip to buy")
print("  1:30 PM: Afternoon uptick likely")
print("  2:00 PM: Power hour - expect strong Friday finish")
print("  2:55 PM: Final push typical on Fridays")
print()

# Calculate time until market open
now = datetime.now(cst)
tomorrow_open = now.replace(hour=8, minute=30, second=0, microsecond=0)
if now.hour >= 15:  # After market close
    tomorrow_open += timedelta(days=1)
    # Skip weekend
    if tomorrow_open.weekday() == 5:  # Saturday
        tomorrow_open += timedelta(days=2)
    elif tomorrow_open.weekday() == 6:  # Sunday
        tomorrow_open += timedelta(days=1)

time_until_open = tomorrow_open - now
hours = int(time_until_open.total_seconds() // 3600)
minutes = int((time_until_open.total_seconds() % 3600) // 60)

print(f"⏰ TIME UNTIL MARKET OPEN:")
print(f"   {hours} hours, {minutes} minutes")
print(f"   Opens at 8:30 AM CST tomorrow")
print()

print("🦀 The Quantum Crawdads now sync with YOUR timezone!")
print("   No more confusion about market hours...")
print("   Power Hour = 2:00-3:00 PM your time!")
print("   Set your alarms accordingly! 🔔")