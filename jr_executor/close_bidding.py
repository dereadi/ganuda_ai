#!/usr/bin/env python3
"""
Close bidding on tasks with sufficient bids and assign to winners.
Run via cron every minute.

For Seven Generations - Cherokee AI Federation
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

BIDDING_WINDOW_MINUTES = 2  # Close bidding after 2 minutes


def main():
    conn = psycopg2.connect(**DB_CONFIG)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Find tasks open for more than BIDDING_WINDOW_MINUTES with bids
        cur.execute("""
            SELECT a.task_id, a.task_content, a.announced_at
            FROM jr_task_announcements a
            WHERE a.status = 'open'
              AND a.announced_at < NOW() - INTERVAL '%s minutes'
              AND EXISTS (
                  SELECT 1 FROM jr_task_bids b WHERE b.task_id = a.task_id
              )
        """, (BIDDING_WINDOW_MINUTES,))

        tasks = cur.fetchall()

        for task in tasks:
            task_id = task['task_id']

            # Get winning bid
            cur.execute("""
                SELECT agent_id, node_name, composite_score
                FROM jr_task_bids
                WHERE task_id = %s
                ORDER BY composite_score DESC
                LIMIT 1
            """, (task_id,))

            winner = cur.fetchone()

            if winner:
                # Assign task to winner
                cur.execute("""
                    UPDATE jr_task_announcements
                    SET status = 'assigned',
                        assigned_to = %s
                    WHERE task_id = %s
                """, (winner['agent_id'], task_id))

                print(f"[{datetime.now()}] Assigned {task_id} to {winner['agent_id']} "
                      f"(score: {winner['composite_score']:.2f})")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
