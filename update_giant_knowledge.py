#\!/usr/bin/env python3
"""Feed the Giant fresh portfolio data"""

import json
from datetime import datetime

# Current portfolio data
current_data = {
    "timestamp": datetime.now().isoformat(),
    "portfolio_value": 28259.85,
    "positions": {
        "ETH": {"value": 11447.99, "pct": 40.5},
        "BTC": {"value": 8222.84, "pct": 29.1},
        "XRP": {"value": 4954.94, "pct": 17.5},
        "SOL": {"value": 3400.64, "pct": 12.0}
    },
    "message": "Portfolio grew from $10k to $28k\! Flying Squirrel's fitness increasing\!"
}

# Save for Giant to consume
with open("/home/dereadi/scripts/claude/giant_fresh_knowledge.json", "w") as f:
    json.dump(current_data, f, indent=2)

print("🔥 Fresh knowledge prepared for the Giant\!")
print(f"Portfolio: ${current_data['portfolio_value']:,.2f}")
print("The Giant can now speak current truths\!")
