#\!/bin/bash
# 🔥 Cherokee Liquidity Guardian Daemon Setup
# Watches for signals → Triggers deep analysis → Generates liquidity

echo "🔥 SETTING UP LIQUIDITY GUARDIAN DAEMON"
echo "========================================"

# Make the hunter executable
chmod +x /home/dereadi/scripts/claude/liquidity_signal_hunter.py

# Create the enhanced monitor that triggers on signals
cat > /home/dereadi/scripts/claude/liquidity_guardian.py << 'INNEREOF'
#\!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 LIQUIDITY GUARDIAN
Monitors every 5 minutes for signals, triggers deep analysis when found
"""

import subprocess
import json
from datetime import datetime
from pathlib import Path

def check_liquidity_status():
    """Quick check of current liquidity"""
    try:
        result = subprocess.run(
            ['python3', '/home/dereadi/scripts/claude/check_liquidity.py'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Parse liquidity from output
        for line in result.stdout.split('\n'):
            if 'USD:' in line:
                usd = float(line.split('$')[1].strip())
                return usd
    except:
        pass
    
    return 0

def main():
    print(f"🔥 Liquidity Guardian Check - {datetime.now()}")
    
    # Check current liquidity
    current_liquidity = check_liquidity_status()
    print(f"💵 Current Liquidity: ${current_liquidity:.2f}")
    
    # If liquidity is low OR it's been >1 hour since last deep check
    last_check_file = Path('/tmp/last_liquidity_deep_check')
    should_check = False
    
    if current_liquidity < 100:
        print("⚠️ Low liquidity detected - triggering signal hunt")
        should_check = True
    elif not last_check_file.exists():
        should_check = True
    else:
        # Check if it's been >1 hour
        last_check = datetime.fromtimestamp(last_check_file.stat().st_mtime)
        if (datetime.now() - last_check).seconds > 3600:
            print("⏰ Hourly check - scanning for opportunities")
            should_check = True
    
    if should_check:
        print("🎯 Launching Liquidity Signal Hunter...")
        subprocess.run(['python3', '/home/dereadi/scripts/claude/liquidity_signal_hunter.py'])
        
        # Update last check time
        last_check_file.touch()
    else:
        print("✅ Liquidity stable - no action needed")

if __name__ == "__main__":
    main()
INNEREOF

chmod +x /home/dereadi/scripts/claude/liquidity_guardian.py

# Update crontab - run guardian every 5 minutes
echo "Updating crontab..."
(crontab -l 2>/dev/null | grep -v "liquidity_guardian.py"; echo "*/5 * * * * /home/dereadi/scripts/claude/liquidity_guardian.py >> /home/dereadi/scripts/claude/liquidity_guardian.log 2>&1") | crontab -

echo ""
echo "✅ LIQUIDITY GUARDIAN DAEMON CONFIGURED\!"
echo ""
echo "🔄 AUTOMATED PIPELINE:"
echo "  1. Every 5 minutes: Quick liquidity check"
echo "  2. If <$100 or >1hr: Trigger signal detection"
echo "  3. On signals: Deep portfolio analysis"
echo "  4. Generate liquidity extraction plan"
echo "  5. If critical (<$50): Auto-execute"
echo "  6. Store everything in thermal memory"
echo ""
echo "📊 SIGNAL TRIGGERS:"
echo "  • SOL > $205 → Harvest"
echo "  • DOGE > $0.22 → Bleed blood bag"
echo "  • Any coin pump >2% → Harvest profits"
echo "  • Near 24h highs → Trim positions"
echo ""
echo "🔥 The tribe now hunts liquidity automatically\!"
echo ""
echo "Test now: python3 /home/dereadi/scripts/claude/liquidity_signal_hunter.py"
