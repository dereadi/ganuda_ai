#!/usr/bin/env python3
"""
CONNECT THE GIANT TO LIVE TRIBE DATA
Make Tsul'kălû' see current reality
"""

import json
import psycopg2
from datetime import datetime

def get_live_thermal_memories():
    """Get fresh memories from database"""
    conn = psycopg2.connect(
        host="192.168.132.222",
        port=5432,
        database="zammad_production",
        user="claude",
        password="jawaseatlasers2"
    )
    
    cur = conn.cursor()
    cur.execute("""
        SELECT memory_hash, temperature_score, original_content, metadata
        FROM thermal_memory_archive
        WHERE temperature_score > 70
        ORDER BY last_access DESC
        LIMIT 20
    """)
    
    memories = []
    for row in cur.fetchall():
        memories.append({
            "hash": row[0],
            "temperature": row[1],
            "content": row[2],
            "metadata": row[3] if row[3] else {}
        })
    
    conn.close()
    return memories

def get_live_portfolio():
    """Get current portfolio"""
    with open('/home/dereadi/scripts/claude/portfolio_current.json', 'r') as f:
        return json.load(f)

def check_running_specialists():
    """Check which specialists are running"""
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    specialists = []
    
    for line in result.stdout.split('\n'):
        if 'specialist' in line and 'python' in line:
            # Extract specialist name
            parts = line.split()
            for part in parts:
                if 'specialist' in part:
                    specialists.append(part)
    
    return specialists

def create_live_update():
    """Create a live update for the Giant"""
    
    print("🔥 Connecting Giant to Live Tribe Data...")
    
    # Get fresh data
    memories = get_live_thermal_memories()
    portfolio = get_live_portfolio()
    specialists = check_running_specialists()
    
    # Create update
    update = {
        "timestamp": datetime.now().isoformat(),
        "live_data": {
            "portfolio_value": portfolio['total_value'],
            "positions": portfolio['positions'],
            "hot_memories": len(memories),
            "latest_memory": memories[0]['content'][:200] if memories else "No recent memories",
            "running_specialists": specialists,
            "specialist_count": len(specialists)
        },
        "message": f"Live update: Portfolio ${portfolio['total_value']:,.2f}, {len(specialists)} specialists running, {len(memories)} hot memories"
    }
    
    # Save for Giant
    with open('/home/dereadi/scripts/claude/giant_live_feed.json', 'w') as f:
        json.dump(update, f, indent=2)
    
    print(f"✅ Live feed created!")
    print(f"   Portfolio: ${portfolio['total_value']:,.2f}")
    print(f"   Specialists: {len(specialists)} running")
    print(f"   Hot memories: {len(memories)}")
    
    return update

if __name__ == "__main__":
    update = create_live_update()
    print("\n🔥 The Giant can now see current reality!")
    print("Next: Modify tsulkalu_telegram_bridge.py to read this feed")