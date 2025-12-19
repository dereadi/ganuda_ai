#!/usr/bin/env python3
"""
Cherokee IT Jr - Thermal Memory Poller
Polls triad_shared_memories for missions assigned to this Jr
"""

import psycopg2
from datetime import datetime, timezone, timedelta
import json

class ThermalPoller:
    def __init__(self, jr_name: str, poll_interval: int = 30):
        self.jr_name = jr_name
        self.poll_interval = poll_interval
        self.last_poll = datetime.now(timezone.utc) - timedelta(hours=24)
        self.db_config = {
            'host': '192.168.132.222',
            'database': 'triad_federation',
            'user': 'claude',
            'password': 'jawaseatlasers2'
        }

    def poll_missions(self) -> list:
        """Poll for new missions assigned to this Jr"""
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        # Query for missions tagged for this Jr that haven't been acknowledged
        cur.execute("""
            SELECT id, content, temperature, tags, created_at
            FROM triad_shared_memories
            WHERE 'jr_mission' = ANY(tags)
              AND %s = ANY(tags)
              AND created_at > %s
              AND NOT EXISTS (
                  SELECT 1 FROM triad_shared_memories ack
                  WHERE 'mission_accepted' = ANY(ack.tags)
                    AND ack.content LIKE '%%' || triad_shared_memories.id::text || '%%'
              )
            ORDER BY temperature DESC, created_at ASC
        """, (self.jr_name, self.last_poll))

        missions = cur.fetchall()
        self.last_poll = datetime.now(timezone.utc) - timedelta(hours=24)

        cur.close()
        conn.close()

        return missions

    def acknowledge_mission(self, mission_id: str, status: str = 'accepted'):
        """Post acknowledgment to thermal memory"""
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        ack_content = json.dumps({
            'status': status,
            'mission_id': str(mission_id),
            'jr': self.jr_name,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        cur.execute("""
            INSERT INTO triad_shared_memories
            (content, temperature, source_triad, tags, access_level)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            ack_content,
            70.0,
            self.jr_name,
            ['mission_accepted', self.jr_name, str(mission_id)],
            'triad'
        ))

        conn.commit()
        cur.close()
        conn.close()

    def post_status(self, message: str, temperature: float = 50.0, tags: list = None):
        """Post status update to thermal memory"""
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO triad_shared_memories
            (content, temperature, source_triad, tags, access_level)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            message,
            temperature,
            self.jr_name,
            tags or [self.jr_name, 'status'],
            'triad'
        ))

        conn.commit()
        cur.close()
        conn.close()
