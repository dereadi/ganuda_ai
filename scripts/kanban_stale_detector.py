#!/usr/bin/env python3
"""Detect stale kanban tickets and flag them.
Runs as systemd timer daily. Finds tickets with no update in 14+ days."""
import os
import psycopg2
from datetime import datetime, timedelta
from typing import List, Tuple

DB_PASS = os.environ.get('CHEROKEE_DB_PASS', '')
DB_HOST = '192.168.132.222'
DB_NAME = 'zammad_production'
DB_USER = 'claude'
STALE_DAYS = 14

def main() -> None:
    """Main function to detect and move stale kanban tickets."""
    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()
    
    cutoff = datetime.now() - timedelta(days=STALE_DAYS)
    
    # Find stale open/in_progress tickets
    cur.execute("""
        SELECT id, title, status, updated_at 
        FROM duyuktv_tickets 
        WHERE status IN ('open', 'in_progress') 
          AND updated_at < %s
        ORDER BY updated_at ASC
    """, (cutoff,))
    
    stale: List[Tuple[int, str, str, datetime]] = cur.fetchall()
    
    if stale:
        print(f"Found {len(stale)} stale tickets (>{STALE_DAYS} days):")
        for ticket_id, title, status, updated in stale:
            days_old = (datetime.now() - updated).days if updated else 'unknown'
            print(f"  [{status}] #{ticket_id}: {title} ({days_old} days stale)")
        
        # Auto-move to backlog if stale > 30 days
        cur.execute("""
            UPDATE duyuktv_tickets 
            SET status = 'backlog', 
                updated_at = NOW()
            WHERE status IN ('open', 'in_progress') 
              AND updated_at < %s
            RETURNING id, title
        """, (datetime.now() - timedelta(days=30),))
        
        moved: List[Tuple[int, str]] = cur.fetchall()
        if moved:
            print(f"\nAuto-moved {len(moved)} tickets to backlog (>30 days stale):")
            for tid, ttitle in moved:
                print(f"  #{tid}: {ttitle}")
        
        conn.commit()
    else:
        print(f"No stale tickets found (all updated within {STALE_DAYS} days)")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()