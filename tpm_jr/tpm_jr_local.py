#!/usr/bin/env python3
"""
TPM Jr - Bmasass Local Instance
================================

Philosophy: "I'm not the smartest, but I know where to find wisdom."

This is the LOCAL/AIR-GAP version of TPM Jr for bmasass (Mac).

Features:
- SQLite local cache (works offline)
- Offline mission queue
- Syncs with bluefin when online
- Uses local KB mirror
- Can use local Ollama when offline

It's lightweight by design - the tribe does the heavy thinking.
"""

import os
import sys
import json
import hashlib
import logging
import socket
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path

# Try PostgreSQL for online mode
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

# Configuration
BLUEFIN_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

LOCAL_DIR = Path('/Users/Shared/ganuda/tpm_jr')
LOCAL_DB = LOCAL_DIR / 'local_cache.db'
PENDING_QUEUE = LOCAL_DIR / 'pending_missions.json'
KB_PATH = Path('/Users/Shared/ganuda/kb')
INSTANCE_ID = 'tpm_jr_bmasass'
AUTHORITY_LEVEL = 2

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TPMJrLocal')


class TPMJrLocal:
    """
    TPM Jr - Local instance for bmasass Mac.
    Works offline with SQLite cache, syncs when online.
    """

    def __init__(self):
        self.instance_id = INSTANCE_ID
        self.authority_level = AUTHORITY_LEVEL
        self.online = False
        self.pg_conn = None

        # Ensure local directories exist
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize local SQLite
        self._init_local_db()

        # Check network status
        self.online = self._check_network()
        logger.info(f"Network status: {'ONLINE' if self.online else 'OFFLINE'}")

    def _check_network(self) -> bool:
        """Check if we can reach bluefin."""
        try:
            socket.create_connection((BLUEFIN_CONFIG['host'], 5432), timeout=2)
            return True
        except (socket.timeout, socket.error):
            return False

    def _init_local_db(self):
        """Initialize local SQLite database."""
        conn = sqlite3.connect(str(LOCAL_DB))
        cur = conn.cursor()

        # Mission patterns cache
        cur.execute('''
            CREATE TABLE IF NOT EXISTS mission_patterns (
                pattern_name TEXT PRIMARY KEY,
                keywords TEXT,
                target_triad TEXT,
                typical_priority TEXT,
                confidence_score REAL,
                times_seen INTEGER,
                times_successful INTEGER,
                last_sync TEXT
            )
        ''')

        # Triad capabilities cache
        cur.execute('''
            CREATE TABLE IF NOT EXISTS triad_capabilities (
                triad_id TEXT,
                capability_area TEXT,
                confidence_score REAL,
                avg_completion_hours REAL,
                last_sync TEXT,
                PRIMARY KEY (triad_id, capability_area)
            )
        ''')

        # Decision log
        cur.execute('''
            CREATE TABLE IF NOT EXISTS decision_log (
                decision_id TEXT PRIMARY KEY,
                mission_hash TEXT,
                keywords TEXT,
                suggested_triad TEXT,
                suggested_priority TEXT,
                confidence REAL,
                reasoning TEXT,
                synced INTEGER DEFAULT 0,
                created_at TEXT
            )
        ''')

        # Pending missions queue
        cur.execute('''
            CREATE TABLE IF NOT EXISTS pending_missions (
                mission_id TEXT PRIMARY KEY,
                content TEXT,
                target_triad TEXT,
                priority TEXT,
                queued_at TEXT,
                synced INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("Local SQLite database initialized")

    def get_local_db(self):
        """Get local SQLite connection."""
        return sqlite3.connect(str(LOCAL_DB))

    def get_pg_connection(self):
        """Get PostgreSQL connection if online."""
        if not self.online or not HAS_PSYCOPG2:
            return None
        try:
            if not self.pg_conn or self.pg_conn.closed:
                self.pg_conn = psycopg2.connect(**BLUEFIN_CONFIG)
            return self.pg_conn
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            self.online = False
            return None

    # =========================================================================
    # SYNC OPERATIONS
    # =========================================================================

    def sync_patterns_from_server(self):
        """Pull pattern updates from PostgreSQL."""
        if not self.online:
            logger.info("Offline - skipping pattern sync")
            return

        try:
            pg_conn = self.get_pg_connection()
            if not pg_conn:
                return

            pg_cur = pg_conn.cursor(cursor_factory=RealDictCursor)
            pg_cur.execute('''
                SELECT pattern_name, keywords, target_triad, typical_priority,
                       confidence_score, times_seen, times_successful
                FROM tpm_mission_patterns
            ''')

            patterns = pg_cur.fetchall()

            local_conn = self.get_local_db()
            local_cur = local_conn.cursor()

            for p in patterns:
                local_cur.execute('''
                    INSERT OR REPLACE INTO mission_patterns
                    (pattern_name, keywords, target_triad, typical_priority,
                     confidence_score, times_seen, times_successful, last_sync)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    p['pattern_name'],
                    json.dumps(p['keywords']) if p['keywords'] else '[]',
                    p['target_triad'],
                    p['typical_priority'],
                    p['confidence_score'],
                    p['times_seen'],
                    p['times_successful'],
                    datetime.now().isoformat()
                ))

            local_conn.commit()
            local_conn.close()
            logger.info(f"Synced {len(patterns)} patterns from server")

        except Exception as e:
            logger.error(f"Pattern sync failed: {e}")

    def sync_capabilities_from_server(self):
        """Pull capability updates from PostgreSQL."""
        if not self.online:
            return

        try:
            pg_conn = self.get_pg_connection()
            if not pg_conn:
                return

            pg_cur = pg_conn.cursor(cursor_factory=RealDictCursor)
            pg_cur.execute('''
                SELECT triad_id, capability_area, confidence_score, avg_completion_hours
                FROM tpm_triad_capabilities
            ''')

            caps = pg_cur.fetchall()

            local_conn = self.get_local_db()
            local_cur = local_conn.cursor()

            for c in caps:
                local_cur.execute('''
                    INSERT OR REPLACE INTO triad_capabilities
                    (triad_id, capability_area, confidence_score, avg_completion_hours, last_sync)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    c['triad_id'],
                    c['capability_area'],
                    c['confidence_score'],
                    c['avg_completion_hours'],
                    datetime.now().isoformat()
                ))

            local_conn.commit()
            local_conn.close()
            logger.info(f"Synced {len(caps)} capabilities from server")

        except Exception as e:
            logger.error(f"Capability sync failed: {e}")

    def push_pending_missions(self):
        """Push queued missions to thermal memory when online."""
        if not self.online:
            logger.info("Offline - skipping mission push")
            return

        try:
            local_conn = self.get_local_db()
            local_cur = local_conn.cursor()
            local_cur.execute('''
                SELECT mission_id, content, target_triad, priority
                FROM pending_missions WHERE synced = 0
            ''')

            pending = local_cur.fetchall()
            if not pending:
                logger.info("No pending missions to push")
                return

            pg_conn = self.get_pg_connection()
            if not pg_conn:
                return

            pg_cur = pg_conn.cursor()

            for mission_id, content, target_triad, priority in pending:
                temp = 85.0 if priority == 'HIGH' else 70.0
                pg_cur.execute('''
                    INSERT INTO triad_shared_memories
                    (content, temperature, source_triad, tags)
                    VALUES (%s, %s, 'tpm_jr', %s)
                ''', (content, temp, ['tpm_jr', 'offline_sync', target_triad]))

                local_cur.execute('''
                    UPDATE pending_missions SET synced = 1 WHERE mission_id = ?
                ''', (mission_id,))

            pg_conn.commit()
            local_conn.commit()
            local_conn.close()
            logger.info(f"Pushed {len(pending)} pending missions to server")

        except Exception as e:
            logger.error(f"Mission push failed: {e}")

    def full_sync(self):
        """Perform full sync with server."""
        logger.info("Starting full sync...")
        self.online = self._check_network()

        if self.online:
            self.sync_patterns_from_server()
            self.sync_capabilities_from_server()
            self.push_pending_missions()
            logger.info("Full sync complete")
        else:
            logger.info("Offline - sync skipped")

    # =========================================================================
    # KNOWLEDGE LOOKUP (works offline)
    # =========================================================================

    def find_relevant_kb(self, keywords: List[str]) -> List[str]:
        """Find KB articles - works offline with local KB mirror."""
        relevant = []
        if not keywords or not KB_PATH.exists():
            return relevant

        try:
            for filepath in KB_PATH.glob('*.md'):
                name_lower = filepath.name.lower()
                for kw in keywords:
                    if kw.lower() in name_lower:
                        relevant.append(filepath.name)
                        break

                # Only read file if not matched by name
                if filepath.name not in relevant and len(relevant) < 3:
                    try:
                        content = filepath.read_text()[:1000].lower()
                        for kw in keywords:
                            if kw.lower() in content:
                                relevant.append(filepath.name)
                                break
                    except:
                        pass
        except Exception as e:
            logger.error(f"KB search error: {e}")

        return relevant[:5]

    def get_mission_patterns(self, keywords: List[str]) -> List[Dict]:
        """Get patterns from local cache."""
        if not keywords:
            return []

        try:
            conn = self.get_local_db()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Simple keyword matching
            results = []
            cur.execute('SELECT * FROM mission_patterns ORDER BY confidence_score DESC')
            for row in cur.fetchall():
                stored_keywords = json.loads(row['keywords']) if row['keywords'] else []
                if any(kw in stored_keywords for kw in keywords):
                    results.append(dict(row))

            conn.close()
            return results[:5]
        except Exception as e:
            logger.error(f"Pattern lookup failed: {e}")
            return []

    def get_triad_capabilities(self) -> List[Dict]:
        """Get capabilities from local cache."""
        try:
            conn = self.get_local_db()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute('SELECT * FROM triad_capabilities ORDER BY confidence_score DESC')
            results = [dict(row) for row in cur.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Capability lookup failed: {e}")
            return []

    # =========================================================================
    # ROUTING LOGIC (same as redfin)
    # =========================================================================

    def extract_keywords(self, content: str) -> List[str]:
        """Extract key terms from mission content."""
        important_terms = [
            'flask', 'api', 'css', 'theme', 'database', 'sql', 'postgresql',
            'monitoring', 'alert', 'grafana', 'systemd', 'service', 'deploy',
            'ui', 'ux', 'design', 'trading', 'stock', 'portfolio', 'kb',
            'documentation', 'infrastructure', 'server', 'python', 'javascript'
        ]

        content_lower = content.lower()
        return [term for term in important_terms if term in content_lower]

    def suggest_routing(self, mission_content: str) -> Dict:
        """Suggest routing - works offline."""
        keywords = self.extract_keywords(mission_content)
        logger.info(f"Extracted keywords: {keywords}")

        patterns = self.get_mission_patterns(keywords)
        capabilities = self.get_triad_capabilities()
        relevant_kb = self.find_relevant_kb(keywords)

        logger.info(f"Found {len(patterns)} patterns, {len(capabilities)} capabilities, {len(relevant_kb)} KB articles")

        if patterns:
            best = patterns[0]
            return {
                'suggested_triad': best['target_triad'],
                'suggested_priority': best['typical_priority'],
                'confidence': best['confidence_score'],
                'reasoning': f"Pattern '{best['pattern_name']}' (seen {best['times_seen']}x)",
                'relevant_kb': relevant_kb,
                'keywords': keywords,
                'mode': 'offline' if not self.online else 'online'
            }

        if keywords and capabilities:
            for cap in capabilities:
                for kw in keywords:
                    if kw in cap['capability_area']:
                        return {
                            'suggested_triad': cap['triad_id'],
                            'suggested_priority': 'MEDIUM',
                            'confidence': cap['confidence_score'] * 0.8,
                            'reasoning': f"Triad '{cap['triad_id']}' good at '{cap['capability_area']}'",
                            'relevant_kb': relevant_kb,
                            'keywords': keywords,
                            'mode': 'offline' if not self.online else 'online'
                        }

        return {
            'suggested_triad': 'it_triad',
            'suggested_priority': 'MEDIUM',
            'confidence': 0.4,
            'reasoning': 'No matching patterns - defaulting to IT Triad',
            'relevant_kb': relevant_kb,
            'keywords': keywords,
            'escalate': True,
            'mode': 'offline' if not self.online else 'online'
        }

    def should_auto_dispatch(self, confidence: float) -> bool:
        """Decide if we should auto-dispatch."""
        if self.authority_level >= 3:
            return True
        if self.authority_level == 2 and confidence >= 0.80:
            return True
        return False

    def queue_mission(self, mission_content: str, target_triad: str, priority: str):
        """Queue mission locally for later sync."""
        mission_id = hashlib.md5(
            f"{mission_content}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        full_content = f"""TPM JR - MISSION DISPATCH (QUEUED OFFLINE)

DATE: {datetime.now().strftime('%Y-%m-%d %H:%M')} CST
FROM: TPM Jr ({self.instance_id})
TO: {target_triad}
PRIORITY: {priority}
STATUS: Queued for sync

{mission_content}

---
Queued by TPM Jr while offline. Will sync when network available.
"""

        try:
            conn = self.get_local_db()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO pending_missions (mission_id, content, target_triad, priority, queued_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (mission_id, full_content, target_triad, priority, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            logger.info(f"Mission queued locally: {mission_id}")
            return mission_id
        except Exception as e:
            logger.error(f"Queue failed: {e}")
            return None

    def dispatch_or_queue(self, mission_content: str, target_triad: str,
                          priority: str, reasoning: str) -> Dict:
        """Dispatch to server if online, otherwise queue locally."""
        if self.online and HAS_PSYCOPG2:
            try:
                pg_conn = self.get_pg_connection()
                if pg_conn:
                    cur = pg_conn.cursor(cursor_factory=RealDictCursor)

                    full_content = f"""TPM JR - MISSION DISPATCH

DATE: {datetime.now().strftime('%Y-%m-%d %H:%M')} CST
FROM: TPM Jr ({self.instance_id})
TO: {target_triad}
PRIORITY: {priority}
ROUTING: {reasoning}

{mission_content}

---
Auto-dispatched by TPM Jr (local).
"""
                    temp = 85.0 if priority == 'HIGH' else 70.0

                    cur.execute('''
                        INSERT INTO triad_shared_memories
                        (content, temperature, source_triad, tags)
                        VALUES (%s, %s, 'tpm_jr', %s)
                        RETURNING id
                    ''', (full_content, temp, ['tpm_jr', 'auto_dispatch', target_triad]))

                    result = cur.fetchone()
                    pg_conn.commit()
                    logger.info(f"Dispatched to server: {result['id']}")
                    return {'dispatched': True, 'mission_id': str(result['id']), 'mode': 'online'}
            except Exception as e:
                logger.error(f"Server dispatch failed: {e}")

        # Fall back to local queue
        mission_id = self.queue_mission(mission_content, target_triad, priority)
        return {'dispatched': False, 'queued': True, 'mission_id': mission_id, 'mode': 'offline'}

    def process_request(self, mission_content: str, force_suggest: bool = False) -> Dict:
        """Process a mission request."""
        logger.info(f"Processing request ({len(mission_content)} chars) - Mode: {'ONLINE' if self.online else 'OFFLINE'}")

        suggestion = self.suggest_routing(mission_content)

        if not force_suggest and self.should_auto_dispatch(suggestion['confidence']):
            result = self.dispatch_or_queue(
                mission_content,
                suggestion['suggested_triad'],
                suggestion['suggested_priority'],
                suggestion['reasoning']
            )
            suggestion.update(result)
            logger.info(f"{'Dispatched' if result.get('dispatched') else 'Queued'} to {suggestion['suggested_triad']}")
        else:
            suggestion['auto_dispatched'] = False
            logger.info(f"Suggesting {suggestion['suggested_triad']} (conf: {suggestion['confidence']:.2f})")

        return suggestion

    def run(self):
        """Main run - sync if online, show status."""
        logger.info(f"TPM Jr Local ({self.instance_id}) starting - Authority Level {self.authority_level}")
        logger.info(f"Mode: {'ONLINE' if self.online else 'OFFLINE (air-gapped)'}")
        logger.info("Philosophy: I'm not the smartest, but I know where to find wisdom.")

        if self.online:
            self.full_sync()

        logger.info("TPM Jr Local ready")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='TPM Jr Local - Air-Gap Ready')
    parser.add_argument('--process', '-p', type=str, help='Process a mission')
    parser.add_argument('--suggest', '-s', action='store_true', help='Suggest only')
    parser.add_argument('--sync', action='store_true', help='Force sync with server')
    parser.add_argument('--status', action='store_true', help='Show status')

    args = parser.parse_args()

    tpm = TPMJrLocal()

    if args.status:
        print(f"TPM Jr Instance: {tpm.instance_id}")
        print(f"Authority Level: {tpm.authority_level}")
        print(f"Network: {'ONLINE' if tpm.online else 'OFFLINE'}")
        print(f"Local DB: {LOCAL_DB}")
        print(f"KB Path: {KB_PATH}")

        caps = tpm.get_triad_capabilities()
        patterns = tpm.get_mission_patterns(['flask'])
        print(f"Cached Patterns: {len(patterns)}")
        print(f"Cached Capabilities: {len(caps)}")

    elif args.sync:
        tpm.full_sync()

    elif args.process:
        result = tpm.process_request(args.process, force_suggest=args.suggest)
        print(json.dumps(result, indent=2, default=str))

    else:
        tpm.run()
