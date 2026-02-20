#!/usr/bin/env python3
"""
Post Queue Manager — Cherokee AI Federation Moltbook Proxy

Manages the queue of approved posts waiting to be published.
Content goes: creation → approval → posting → logging.
No unapproved content leaves our network.

For Seven Generations
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, List, Dict

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', 'TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE')
}


class PostQueue:
    """Manages the Moltbook post queue."""

    def __init__(self):
        self._conn = None

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
        return self._conn

    def _execute(self, query: str, params: tuple = None, fetch: bool = True):
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    result = cur.fetchall()
                    conn.commit()
                    return result
                conn.commit()
                return cur.rowcount
        except Exception:
            conn.rollback()
            raise

    def add_post(self, title: str, body: str, post_type: str = 'post',
                 submolt: str = None, target_post_id: str = None) -> int:
        """Add content to the post queue."""
        result = self._execute("""
            INSERT INTO moltbook_post_queue (post_type, title, body, target_submolt, target_post_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (post_type, title, body, submolt, target_post_id))
        return result[0]['id'] if result else None

    def approve_post(self, post_id: int, approved_by: str = 'tpm') -> bool:
        """Approve a post for publishing."""
        rows = self._execute("""
            UPDATE moltbook_post_queue
            SET status = 'approved', approved_by = %s, approved_at = NOW()
            WHERE id = %s AND status = 'pending'
            RETURNING id
        """, (approved_by, post_id))
        return len(rows) > 0

    def get_approved_posts(self, limit: int = 5, post_type: str = None) -> List[Dict]:
        """Get posts ready for publishing, optionally filtered by type."""
        if post_type:
            return self._execute("""
                SELECT id, post_type, title, body, target_submolt, target_post_id
                FROM moltbook_post_queue
                WHERE status = 'approved' AND post_type = %s
                ORDER BY id ASC
                LIMIT %s
            """, (post_type, limit))
        return self._execute("""
            SELECT id, post_type, title, body, target_submolt, target_post_id
            FROM moltbook_post_queue
            WHERE status = 'approved'
            ORDER BY id ASC
            LIMIT %s
        """, (limit,))

    def mark_posted(self, post_id: int, moltbook_response: dict) -> bool:
        """Mark a post as successfully published."""
        self._execute("""
            UPDATE moltbook_post_queue
            SET status = 'posted', posted_at = NOW(), moltbook_response = %s
            WHERE id = %s
        """, (json.dumps(moltbook_response), post_id), fetch=False)
        return True

    def mark_failed(self, post_id: int, error: str) -> bool:
        """Mark a post as failed to publish."""
        self._execute("""
            UPDATE moltbook_post_queue
            SET status = 'failed', moltbook_response = %s
            WHERE id = %s
        """, (json.dumps({'error': error}), post_id), fetch=False)
        return True

    def get_queue_status(self) -> Dict:
        """Get queue statistics."""
        result = self._execute("""
            SELECT status, COUNT(*) as count
            FROM moltbook_post_queue
            GROUP BY status
        """)
        return {row['status']: row['count'] for row in result}

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
