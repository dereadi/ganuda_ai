#!/usr/bin/env python3
"""
TPM Jr - Redfin Primary Instance
=================================

Philosophy: "I'm not the smartest, but I know where to find wisdom."

This is the PRIMARY instance of TPM Jr for redfin.

Features:
- Direct PostgreSQL access (always online)
- Pattern matching from learned database
- KB article lookup
- Triad capability awareness
- Auto-dispatch for high-confidence routing

It's lightweight by design - the tribe does the heavy thinking.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

KB_PATH = Path('/ganuda/kb')
INSTANCE_ID = 'tpm_jr_redfin'
AUTHORITY_LEVEL = 2

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TPMJrRedfin')


class TPMJrRedfin:
    """
    TPM Jr - Primary server instance.
    Always online, direct PostgreSQL access.
    """

    def __init__(self):
        self.instance_id = INSTANCE_ID
        self.authority_level = AUTHORITY_LEVEL
        self.conn = None

    def get_connection(self):
        """Get database connection."""
        try:
            if not self.conn or self.conn.closed:
                self.conn = psycopg2.connect(**DB_CONFIG)
            return self.conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None

    # =========================================================================
    # KNOWLEDGE LOOKUP
    # =========================================================================

    def find_relevant_kb(self, keywords: List[str]) -> List[str]:
        """Find KB articles relevant to keywords."""
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
        """Get matching patterns from database."""
        if not keywords:
            return []

        try:
            conn = self.get_connection()
            if not conn:
                return []

            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('''
                SELECT pattern_name, keywords, target_triad, typical_priority,
                       confidence_score, times_seen, times_successful
                FROM tpm_mission_patterns
                ORDER BY confidence_score DESC
            ''')

            all_patterns = cur.fetchall()
            matched = []
            for p in all_patterns:
                if p['keywords']:
                    for kw in keywords:
                        if kw in p['keywords']:
                            matched.append(dict(p))
                            break
            return matched[:5]
        except Exception as e:
            logger.error(f"Pattern lookup failed: {e}")
            return []

    def get_triad_capabilities(self) -> List[Dict]:
        """Get triad capabilities from database."""
        try:
            conn = self.get_connection()
            if not conn:
                return []

            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('''
                SELECT triad_id, capability_area, confidence_score, avg_completion_hours
                FROM tpm_triad_capabilities
                ORDER BY confidence_score DESC
            ''')
            return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Capability lookup failed: {e}")
            return []

    # =========================================================================
    # ROUTING LOGIC
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
        """Suggest routing based on patterns, capabilities, and KB."""
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
                'reasoning': f"Pattern '{best['pattern_name']}' seen {best['times_seen']}x, {best['times_successful']} successful",
                'relevant_kb': relevant_kb,
                'keywords': keywords
            }

        if keywords and capabilities:
            for cap in capabilities:
                for kw in keywords:
                    if kw in cap['capability_area'].lower():
                        return {
                            'suggested_triad': cap['triad_id'],
                            'suggested_priority': 'MEDIUM',
                            'confidence': cap['confidence_score'] * 0.8,
                            'reasoning': f"Triad '{cap['triad_id']}' good at '{cap['capability_area']}'",
                            'relevant_kb': relevant_kb,
                            'keywords': keywords
                        }

        return {
            'suggested_triad': 'it_triad',
            'suggested_priority': 'MEDIUM',
            'confidence': 0.4,
            'reasoning': 'No matching patterns - defaulting to IT Triad',
            'relevant_kb': relevant_kb,
            'keywords': keywords,
            'escalate': True
        }

    def should_auto_dispatch(self, confidence: float) -> bool:
        """Decide if we should auto-dispatch."""
        if self.authority_level >= 3:
            return True
        if self.authority_level == 2 and confidence >= 0.80:
            return True
        return False

    def dispatch_to_triad(self, content: str, triad: str, priority: str, reasoning: str) -> str:
        """Dispatch mission to thermal memory."""
        try:
            conn = self.get_connection()
            if not conn:
                return None

            full_content = f"""TPM JR - MISSION DISPATCH

DATE: {datetime.now().strftime('%Y-%m-%d %H:%M')} CST
FROM: TPM Jr ({self.instance_id})
TO: {triad}
PRIORITY: {priority}
ROUTING: {reasoning}

{content}

---
Auto-dispatched by TPM Jr (redfin primary).
"""
            temp = 85.0 if priority == 'HIGH' else 70.0

            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('''
                INSERT INTO triad_shared_memories
                (content, temperature, source_triad, tags)
                VALUES (%s, %s, 'tpm_jr', %s)
                RETURNING id
            ''', (full_content, temp, ['tpm_jr', 'auto_dispatch', triad]))

            result = cur.fetchone()
            conn.commit()
            logger.info(f"Dispatched to {triad}: {result['id']}")
            return str(result['id'])

        except Exception as e:
            logger.error(f"Dispatch failed: {e}")
            return None

    def process_request(self, mission_content: str, force_suggest: bool = False) -> Dict:
        """Process a mission request."""
        logger.info(f"Processing request ({len(mission_content)} chars)")

        suggestion = self.suggest_routing(mission_content)

        if not force_suggest and self.should_auto_dispatch(suggestion['confidence']):
            mission_id = self.dispatch_to_triad(
                mission_content,
                suggestion['suggested_triad'],
                suggestion['suggested_priority'],
                suggestion['reasoning']
            )
            suggestion['auto_dispatched'] = True
            suggestion['mission_id'] = mission_id
            logger.info(f"Auto-dispatched to {suggestion['suggested_triad']}")
        else:
            suggestion['auto_dispatched'] = False
            logger.info(f"Suggesting {suggestion['suggested_triad']} (conf: {suggestion['confidence']:.2f})")

        return suggestion

    def run(self):
        """Main run - show status."""
        logger.info(f"TPM Jr Redfin ({self.instance_id}) starting - Authority Level {self.authority_level}")
        logger.info("Philosophy: I'm not the smartest, but I know where to find wisdom.")
        logger.info("TPM Jr Redfin ready")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='TPM Jr Redfin - Primary Server Instance')
    parser.add_argument('--process', '-p', type=str, help='Process a mission')
    parser.add_argument('--suggest', '-s', action='store_true', help='Suggest only (dont dispatch)')
    parser.add_argument('--status', action='store_true', help='Show status')

    args = parser.parse_args()

    tpm = TPMJrRedfin()

    if args.status:
        print(f"TPM Jr Instance: {tpm.instance_id}")
        print(f"Authority Level: {tpm.authority_level}")
        print(f"KB Path: {KB_PATH}")
        caps = tpm.get_triad_capabilities()
        patterns = tpm.get_mission_patterns(['flask'])
        print(f"Patterns for 'flask': {len(patterns)}")
        print(f"Total Capabilities: {len(caps)}")

    elif args.process:
        result = tpm.process_request(args.process, force_suggest=args.suggest)
        print(json.dumps(result, indent=2, default=str))

    else:
        tpm.run()
