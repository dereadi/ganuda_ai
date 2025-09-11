#!/usr/bin/env python3
"""
🐺 TWO WOLVES - THEY LIVE EVERYWHERE
The eternal battle within every trade
Sacred Fire Protocol: DUAL NATURE
"""

import json
from datetime import datetime

print("🐺 THE TWO WOLVES WITHIN")
print("=" * 60)
print("Cherokee Wisdom: Two wolves fight inside us all")
print("One is Greed. One is Fear.")
print("The one that wins? The one you feed.")
print("Truth: They live everywhere - in markets, in traders, in code")
print()

two_wolves_wisdom = {
    "timestamp": datetime.now().isoformat(),
    "teaching": "TWO_WOLVES_LIVE_EVERYWHERE",
    "the_wolves": {
        "GREED_WOLF": {
            "nature": "Always wants more",
            "market_behavior": "Buy tops, FOMO, over-leverage",
            "current_feeding": "We fed this wolf too much - 99.9% positioned",
            "symptoms": [
                "No cash left ($19)",
                "Over-planted seeds",
                "Cannot reap because we over-sowed",
                "Trapped in positions"
            ],
            "lives_in": [
                "Every pump (wanting more)",
                "Every specialist (pushing harder)",
                "Every trade (bigger position)",
                "BTC whales (hoarding)"
            ]
        },
        "FEAR_WOLF": {
            "nature": "Always expects loss",
            "market_behavior": "Sell bottoms, panic, miss opportunities",
            "current_feeding": "Starved - we haven't been cautious enough",
            "symptoms": [
                "No stop losses initially",
                "No cash reserves kept",
                "Ignored flat BTC warning",
                "Didn't take profits"
            ],
            "lives_in": [
                "Every dump (panic selling)",
                "Every specialist (stop losses)",
                "Every trade (position sizing)",
                "$500M liquidations (mass fear)"
            ]
        }
    },
    "balance_teaching": {
        "wisdom": "Feed both wolves appropriately",
        "greed_diet": "Let it hunt gains, but limit portions (position sizing)",
        "fear_diet": "Let it protect, but don't let it paralyze (stop losses)",
        "current_need": "FEED THE FEAR WOLF - We need caution now"
    },
    "market_manifestation": {
        "BTC": "Greed wolf overfed (whale hoarding) - now flat",
        "SOL": "Balanced wolves - healthy movement",
        "Liquidations": "Fear wolf rampage - $500M wiped",
        "Our_Portfolio": "Greed wolf obesity - 99.9% positioned"
    },
    "specialist_wolf_balance": {
        "mean-reversion": {
            "feed_fear": "Sell overbought (take profits)",
            "starve_greed": "Don't chase pumps"
        },
        "trend": {
            "feed_greed": "Ride winners",
            "feed_fear": "Use trailing stops"
        },
        "volatility": {
            "balance": "Trade both directions",
            "wisdom": "Volatility feeds both wolves"
        },
        "breakout": {
            "feed_greed": "Catch big moves",
            "feed_fear": "Tight stops on fakeouts"
        }
    },
    "immediate_rebalancing": {
        "feed_fear_wolf": [
            "Take profits NOW (harvest)",
            "Build cash reserves (30% target)",
            "Set stop losses",
            "Reduce position sizes"
        ],
        "starve_greed_wolf": [
            "No new positions until 30% cash",
            "No FOMO buying",
            "No revenge trading",
            "No over-leveraging"
        ]
    },
    "the_third_way": {
        "teaching": "There's a third force - WISDOM",
        "nature": "The observer who chooses which wolf to feed",
        "current_wisdom": "We see the imbalance, now we correct",
        "action": "Feed fear until balance returns"
    },
    "sacred_fire": "BURNING_BETWEEN_WOLVES"
}

print("🐺 THE TWO WOLVES IN OUR TRADING:")
print("-" * 40)
print("\nGREED WOLF (Overfed):")
print("  • Ate 99.9% of our capital")
print("  • Left us with $19")
print("  • Still wants to buy more")
print("  • Lives in every pump")

print("\nFEAR WOLF (Starved):")
print("  • Wasn't fed (no profit taking)")
print("  • No stop losses initially")
print("  • Needed for protection")
print("  • Lives in every dump")

print("\n⚖️ RESTORING BALANCE:")
print("-" * 40)
print("FEED THE FEAR WOLF:")
for action in two_wolves_wisdom["immediate_rebalancing"]["feed_fear_wolf"]:
    print(f"  ✓ {action}")

print("\nSTARVE THE GREED WOLF:")
for action in two_wolves_wisdom["immediate_rebalancing"]["starve_greed_wolf"]:
    print(f"  ✓ {action}")

print("\n🔥 WHERE THE WOLVES LIVE:")
print("-" * 40)
print("They live EVERYWHERE:")
print("  • In every candle (green=greed, red=fear)")
print("  • In every trader (including us)")
print("  • In every algorithm (including specialists)")
print("  • In the market itself (bull=greed, bear=fear)")
print("  • In BTC (greed hoarding by whales)")
print("  • In liquidations (fear cascades)")

print("\n💡 THE WISDOM:")
print("-" * 40)
print("We are not the wolves.")
print("We are the one who FEEDS them.")
print("Current choice: FEED FEAR, STARVE GREED")
print("Target: 70% positioned (fed), 30% cash (protected)")

# Save wisdom
with open('/home/dereadi/scripts/claude/two_wolves_wisdom.json', 'w') as f:
    json.dump(two_wolves_wisdom, f, indent=2)

print("\n" + "=" * 60)
print("🐺 TWO WOLVES WISDOM UNDERSTOOD")
print()
print("The tribe sees clearly now:")
print("  • Greed wolf grew fat (99.9% positioned)")
print("  • Fear wolf grew weak (0.1% cash)")
print("  • Balance must return (70/30)")
print("  • They live everywhere - even in our code")
print()
print("The specialists will now:")
print("  • FEED fear (take profits)")
print("  • STARVE greed (no new buys)")
print("  • FIND balance (70/30 rule)")
print()
print("🔥 Sacred Fire burns between the wolves")
print("🐺 The one you feed is the one that wins")
print("⚖️ But both must live for balance")
print("=" * 60)