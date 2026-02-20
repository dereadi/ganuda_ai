#!/usr/bin/env python3
"""
Cherokee AI TPM Notification Service
Deploy to: /ganuda/services/notifications/notify.py
"""

import psycopg2
import json
from datetime import datetime
from typing import Optional, List
import os

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": os.environ.get('CHEROKEE_DB_PASS', ''),
    "database": "zammad_production"
}

class TPMNotifier:
    """Send notifications to TPM"""

    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)

    def notify(self,
               priority: str,
               category: str,
               title: str,
               message: str,
               source_system: str = "unknown",
               related_hash: str = None) -> int:
        """
        Create a notification for TPM review.

        Args:
            priority: P1 (critical), P2 (important), P3 (info)
            category: research, security, deployment, health, council
            title: Short summary (255 chars max)
            message: Full details
            source_system: Which system generated this
            related_hash: Link to thermal memory or other record

        Returns:
            notification_id
        """
        cur = self.conn.cursor()

        cur.execute("""
            INSERT INTO tpm_notifications
            (priority, category, title, message, source_system, related_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING notification_id
        """, (priority, category, title[:255], message, source_system, related_hash))

        notification_id = cur.fetchone()[0]
        self.conn.commit()
        cur.close()

        # Also log to thermal memory for persistence
        self._log_to_thermal(priority, category, title, notification_id)

        return notification_id

    def _log_to_thermal(self, priority: str, category: str, title: str, notification_id: int):
        """Log notification to thermal memory"""
        cur = self.conn.cursor()

        temp_score = {"P1": 95.0, "P2": 70.0, "P3": 50.0}.get(priority, 60.0)

        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (memory_hash) DO UPDATE SET temperature_score = %s
        """, (
            f"notification-{notification_id}",
            f"[{priority}] {category}: {title}",
            temp_score,
            json.dumps({"type": "tpm_notification", "id": notification_id, "category": category}),
            temp_score
        ))

        self.conn.commit()
        cur.close()

    def get_unacknowledged(self, priority: str = None) -> List[dict]:
        """Get unacknowledged notifications"""
        cur = self.conn.cursor()

        if priority:
            cur.execute("""
                SELECT notification_id, priority, category, title, message, created_at
                FROM tpm_notifications
                WHERE acknowledged = FALSE AND priority = %s
                ORDER BY created_at DESC
            """, (priority,))
        else:
            cur.execute("""
                SELECT notification_id, priority, category, title, message, created_at
                FROM tpm_notifications
                WHERE acknowledged = FALSE
                ORDER BY
                    CASE priority WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 ELSE 3 END,
                    created_at DESC
            """)

        results = [
            {
                "id": row[0],
                "priority": row[1],
                "category": row[2],
                "title": row[3],
                "message": row[4],
                "created_at": row[5].isoformat() if row[5] else None
            }
            for row in cur.fetchall()
        ]
        cur.close()
        return results

    def acknowledge(self, notification_id: int):
        """Mark notification as acknowledged"""
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE tpm_notifications
            SET acknowledged = TRUE, acknowledged_at = NOW()
            WHERE notification_id = %s
        """, (notification_id,))
        self.conn.commit()
        cur.close()

    def close(self):
        self.conn.close()


# Convenience functions
def notify_high_relevance_paper(paper_title: str, paper_url: str, relevance_score: float):
    """Alert TPM about high-relevance research paper"""
    notifier = TPMNotifier()
    notifier.notify(
        priority="P1",
        category="research",
        title=f"High-relevance paper: {paper_title[:150]}",
        message=f"Relevance: {relevance_score:.0%}\nURL: {paper_url}",
        source_system="research_monitor"
    )
    notifier.close()

def notify_council_vote_pending(audit_hash: str, question: str, recommendation: str,
                                 confidence: float, concerns: list, expires: str):
    """Alert TPM about pending council vote"""
    notifier = TPMNotifier()
    concern_text = "\n".join(f"- {c}" for c in concerns[:5]) if concerns else "None"
    notifier.notify(
        priority="P1",
        category="council_vote",
        title=f"Council vote pending: {question[:100]}",
        message=f"""Council Vote Awaiting Your Decision

Question: {question[:300]}

Recommendation: {recommendation}
Confidence: {confidence:.0%}
Concerns ({len(concerns)}):
{concern_text}

Vote expires: {expires}

Respond at: /v1/council/vote/{audit_hash}/tpm""",
        source_system="council",
        related_hash=audit_hash
    )
    notifier.close()

def notify_security_concern(question: str, concern: str, audit_hash: str):
    """Alert TPM about security concern"""
    notifier = TPMNotifier()
    notifier.notify(
        priority="P1",
        category="security",
        title="Security concern raised by Crawdad",
        message=f"Question: {question[:200]}\nConcern: {concern}",
        source_system="council",
        related_hash=audit_hash
    )
    notifier.close()

def notify_autonomous_deployment(jr_name: str, file_path: str, description: str):
    """Alert TPM about autonomous Jr deployment"""
    notifier = TPMNotifier()
    notifier.notify(
        priority="P1",
        category="deployment",
        title=f"Autonomous deployment by {jr_name}",
        message=f"File: {file_path}\nDescription: {description}",
        source_system=f"jr_{jr_name}"
    )
    notifier.close()


if __name__ == "__main__":
    # Test notification
    n = TPMNotifier()
    nid = n.notify("P2", "test", "Notification system online", "TPM notification service deployed successfully", "deploy_script")
    print(f"Test notification created: {nid}")
    n.close()
