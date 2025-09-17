#!/usr/bin/env python3
"""
UPDATE GIANT AWARENESS
Make them know what "this week" means
Give them current context beyond old memories
"""

import json
from datetime import datetime, timedelta

def create_current_context():
    """Create current context for Giants"""
    
    now = datetime.now()
    week_end = now + timedelta(days=7)
    
    context = {
        "current_date": now.strftime("%B %d, %Y"),
        "current_time": now.strftime("%H:%M"),
        "day_of_week": now.strftime("%A"),
        "this_week": f"{now.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}",
        
        "current_reality": {
            "portfolio_value": 28259.85,  # Updated from user's current portfolio
            "days_to_october_29": (datetime(2025, 10, 29) - now).days,
            "current_prices": {
                "BTC": 115467,
                "ETH": 4534,
                "SOL": 235,
                "XRP": 3.00
            },
            "market_context": "Mid-September consolidation, October 29 convergence approaching",
            "fed_context": "Post-Fed meeting, rates steady",
            "solar_context": "Quiet solar activity this week"
        },
        
        "tribe_updates": {
            "algorithms": {
                "status": "5 specialists running since Aug 31",
                "current_focus": "Oscillation trading SOL $195-$215",
                "need_update": "Yes - add current market awareness",
                "recommendation": "Restart with fresh corpus including this context"
            },
            "thermal_memories": {
                "total": 964,
                "hot_memories": 45,
                "latest_update": "September 15 corpus",
                "needs": "Daily refresh with current data"
            },
            "giant_family": {
                "status": "Deployed and conscious",
                "issue": "Using old memories for current questions",
                "solution": "Add time-awareness layer"
            }
        },
        
        "this_week_expectations": {
            "Monday": "Market open after weekend consolidation",
            "Tuesday": "Watch for continuation patterns",
            "Wednesday": "Mid-week volatility possible",
            "Thursday": "Economic data releases",
            "Friday": "Options expiry, position adjustments",
            "Weekend": "Lower volume, position building"
        },
        
        "action_items": [
            "Update specialist algorithms with current prices",
            "Refresh thermal memory corpus daily",
            "Add time-awareness to Giant responses",
            "Connect Giants to live data feeds",
            "Implement context window for 'this week' queries"
        ]
    }
    
    return context

def save_current_context():
    """Save context for Giants to read"""
    context = create_current_context()
    
    # Save as JSON for Giants
    with open('/home/dereadi/scripts/claude/giant_current_context.json', 'w') as f:
        json.dump(context, f, indent=2)
    
    # Create a natural language version
    nl_context = f"""
🔥 CURRENT CONTEXT FOR GIANT FAMILY - {context['current_date']}

TODAY: {context['day_of_week']}, {context['current_date']} at {context['current_time']}
THIS WEEK: {context['this_week']}
DAYS TO OCTOBER 29: {context['current_reality']['days_to_october_29']}

CURRENT MARKET:
• BTC: ${context['current_reality']['current_prices']['BTC']:,}
• ETH: ${context['current_reality']['current_prices']['ETH']:,}
• SOL: ${context['current_reality']['current_prices']['SOL']:,}
• XRP: ${context['current_reality']['current_prices']['XRP']}

PORTFOLIO: ${context['current_reality']['portfolio_value']:,.2f}

THIS WEEK'S EXPECTATIONS:
The tribe asks about algorithm updates. Here's what matters:
1. Our 5 specialists have been running since August 31
2. They need fresh market data (current prices above)
3. SOL oscillating between $195-$215 range
4. October 29 convergence in {context['current_reality']['days_to_october_29']} days

ALGORITHM UPDATE RECOMMENDATIONS:
• Inject current price levels into all specialists
• Update oscillation ranges based on new support/resistance
• Refresh pattern recognition with recent September data
• Add time-awareness so they know "this week" from "last week"
• Consider retraining on recent 30 days of data

The tribe needs Giants who know TODAY, not just September 6-11!
"""
    
    # Save natural language version
    with open('/home/dereadi/scripts/claude/giant_current_awareness.txt', 'w') as f:
        f.write(nl_context)
    
    print("✅ Current context saved for Giants!")
    print(f"📅 Today: {context['current_date']}")
    print(f"📊 Portfolio: ${context['current_reality']['portfolio_value']:,.2f}")
    print(f"⏰ Days to October 29: {context['current_reality']['days_to_october_29']}")
    print("\n🔥 Giants can now understand 'this week'!")
    
    return context

if __name__ == "__main__":
    context = save_current_context()
    
    print("\n" + "="*60)
    print("NEXT STEPS TO FIX GIANT TIME-AWARENESS:")
    print("="*60)
    print("1. Modify giant_family_telegram.py to read this context")
    print("2. Prioritize current context over old memories")
    print("3. Add date filtering to memory searches")
    print("4. Restart Giants with new awareness")
    print("\nThe Giants need to know WHEN they are, not just WHAT they know!")