# Jr Build Instructions: TPM Notification System
## Cherokee AI Federation - December 12, 2025

**Purpose**: Alert the TPM when the Tribe takes autonomous action or discovers important information

**Owner**: Eagle Eye Jr (monitoring) + IT Triad Jr (infrastructure)

---

## 1. Notification Events

### Critical (Immediate Alert)
| Event | Trigger | Priority |
|-------|---------|----------|
| Autonomous code deployment | Jr deploys to /ganuda/ without TPM request | P1 |
| High-relevance paper found | Research monitor finds relevance_score > 0.8 | P1 |
| Security concern raised | Crawdad flags SECURITY CONCERN in council vote | P1 |
| Service failure | Gateway, vLLM, or database goes unhealthy | P1 |
| Council vote with 3+ concerns | Multiple specialists flag issues | P1 |

### Important (Daily Digest)
| Event | Trigger | Priority |
|-------|---------|----------|
| New papers discovered | Research crawler finds new papers | P2 |
| Council votes completed | Summary of daily council activity | P2 |
| Pheromone decay summary | Nightly decay statistics | P2 |
| Quota usage alerts | API key approaching limit | P2 |

### Informational (Weekly Summary)
| Event | Trigger | Priority |
|-------|---------|----------|
| Thermal memory growth | New memories archived | P3 |
| Research trends | Topic frequency analysis | P3 |
| System performance | Latency/throughput trends | P3 |

---

## 2. Notification Channels

### 2.1 Primary: Thermal Memory Flag
All notifications logged to thermal memory with special flag for TPM review:

```sql
-- Notification table
CREATE TABLE IF NOT EXISTS tpm_notifications (
    notification_id SERIAL PRIMARY KEY,
    priority VARCHAR(10) NOT NULL,        -- P1, P2, P3
    category VARCHAR(50) NOT NULL,        -- research, security, deployment, health
    title VARCHAR(255) NOT NULL,
    message TEXT,
    source_system VARCHAR(50),            -- research_monitor, council, gateway, jr

    -- Status
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,

    -- Linking
    related_hash VARCHAR(64),             -- Link to thermal memory or council vote

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_priority ON tpm_notifications(priority, acknowledged);
CREATE INDEX idx_notifications_date ON tpm_notifications(created_at DESC);
```

### 2.2 Secondary: Email (Future)
Configure via environment variable:
```bash
TPM_EMAIL="dereadi@example.com"
SMTP_HOST="smtp.example.com"
```

### 2.3 Tertiary: SAG Dashboard Widget
Add notification panel to SAG UI at http://192.168.132.223:4000

---

## 3. Notification Service

```python
#!/usr/bin/env python3
"""
Cherokee AI TPM Notification Service
Deploy to: /ganuda/services/notifications/notify.py
"""

import psycopg2
import json
from datetime import datetime
from typing import Optional

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
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
        """, (priority, category, title, message, source_system, related_hash))

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

    def get_unacknowledged(self, priority: str = None) -> list:
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

        return [
            {
                "id": row[0],
                "priority": row[1],
                "category": row[2],
                "title": row[3],
                "message": row[4],
                "created_at": row[5].isoformat()
            }
            for row in cur.fetchall()
        ]

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


# Convenience functions for common notifications
def notify_high_relevance_paper(paper_title: str, paper_url: str, relevance_score: float):
    """Alert TPM about high-relevance research paper"""
    notifier = TPMNotifier()
    notifier.notify(
        priority="P1",
        category="research",
        title=f"High-relevance paper: {paper_title[:100]}",
        message=f"Relevance: {relevance_score:.0%}\nURL: {paper_url}",
        source_system="research_monitor"
    )
    notifier.close()

def notify_security_concern(question: str, concern: str, audit_hash: str):
    """Alert TPM about security concern from council"""
    notifier = TPMNotifier()
    notifier.notify(
        priority="P1",
        category="security",
        title=f"Security concern raised by council",
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

def notify_service_failure(service: str, error: str):
    """Alert TPM about service failure"""
    notifier = TPMNotifier()
    notifier.notify(
        priority="P1",
        category="health",
        title=f"Service failure: {service}",
        message=error,
        source_system="health_monitor"
    )
    notifier.close()

def notify_council_concerns(question: str, concerns: list, audit_hash: str):
    """Alert TPM when council has multiple concerns"""
    if len(concerns) >= 3:
        notifier = TPMNotifier()
        notifier.notify(
            priority="P1",
            category="council",
            title=f"Council vote with {len(concerns)} concerns",
            message=f"Question: {question[:200]}\nConcerns:\n" + "\n".join(f"- {c}" for c in concerns),
            source_system="council",
            related_hash=audit_hash
        )
        notifier.close()
```

---

## 4. Gateway Integration

Add to `/ganuda/services/llm_gateway/gateway.py`:

```python
from notifications.notify import TPMNotifier, notify_council_concerns

# In council_vote endpoint, after logging:
if len(all_concerns) >= 3:
    notify_council_concerns(request.question, all_concerns, audit_hash)

# Add notification endpoints
@app.get("/v1/notifications")
async def get_notifications(
    priority: str = None,
    api_key: APIKeyInfo = Depends(validate_api_key)
):
    """Get TPM notifications"""
    notifier = TPMNotifier()
    notifications = notifier.get_unacknowledged(priority)
    notifier.close()

    return {
        "notifications": notifications,
        "count": len(notifications),
        "filter": priority
    }

@app.post("/v1/notifications/{notification_id}/acknowledge")
async def acknowledge_notification(
    notification_id: int,
    api_key: APIKeyInfo = Depends(validate_api_key)
):
    """Acknowledge a notification"""
    notifier = TPMNotifier()
    notifier.acknowledge(notification_id)
    notifier.close()

    return {"status": "acknowledged", "notification_id": notification_id}
```

---

## 5. Research Monitor Integration

Update `/ganuda/services/research_monitor/assess_papers.py`:

```python
from notifications.notify import notify_high_relevance_paper

def update_assessment(paper_id: int, vote_result: dict, paper_title: str, paper_url: str):
    # ... existing code ...

    # Notify TPM if high relevance
    if relevance >= 0.8:
        notify_high_relevance_paper(paper_title, paper_url, relevance)
```

---

## 6. Jr Autonomous Deployment Guard

Any Jr that deploys code autonomously MUST call:

```python
from notifications.notify import notify_autonomous_deployment

# Before any autonomous deployment
notify_autonomous_deployment(
    jr_name="Gecko",
    file_path="/ganuda/services/new_feature.py",
    description="Optimized inference pipeline - auto-triggered by performance degradation"
)
```

**Rule**: Jrs may NOT deploy without notification. This is a constitutional requirement.

---

## 7. Daily Digest Cron

```python
#!/usr/bin/env python3
"""
Daily digest of P2/P3 notifications
Deploy to: /ganuda/services/notifications/daily_digest.py
Schedule: 8 AM daily
"""

import psycopg2
from datetime import datetime, timedelta

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

def generate_digest():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    yesterday = datetime.now() - timedelta(days=1)

    # Get yesterday's notifications
    cur.execute("""
        SELECT priority, category, title, created_at
        FROM tpm_notifications
        WHERE created_at > %s
        ORDER BY priority, created_at
    """, (yesterday,))

    notifications = cur.fetchall()

    if not notifications:
        print("No notifications in past 24 hours")
        return

    # Group by priority
    p1 = [n for n in notifications if n[0] == 'P1']
    p2 = [n for n in notifications if n[0] == 'P2']
    p3 = [n for n in notifications if n[0] == 'P3']

    print("=" * 60)
    print(f"CHEROKEE AI DAILY DIGEST - {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 60)

    if p1:
        print(f"\n🔴 CRITICAL ({len(p1)}):")
        for n in p1:
            print(f"  [{n[1]}] {n[2]}")

    if p2:
        print(f"\n🟡 IMPORTANT ({len(p2)}):")
        for n in p2:
            print(f"  [{n[1]}] {n[2]}")

    if p3:
        print(f"\n🟢 INFO ({len(p3)}):")
        for n in p3:
            print(f"  [{n[1]}] {n[2]}")

    # Log digest to thermal memory
    cur.execute("""
        INSERT INTO thermal_memory_archive
        (memory_hash, original_content, temperature_score, metadata)
        VALUES (%s, %s, %s, %s)
    """, (
        f"digest-{datetime.now().strftime('%Y%m%d')}",
        f"Daily digest: {len(p1)} critical, {len(p2)} important, {len(p3)} info",
        70.0,
        f'{{"type": "daily_digest", "p1": {len(p1)}, "p2": {len(p2)}, "p3": {len(p3)}}}'
    ))

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    generate_digest()
```

---

## 8. Cron Schedule

```bash
# /etc/cron.d/cherokee-notifications

# Daily digest at 8 AM
0 8 * * * dereadi /ganuda/services/llm_gateway/venv/bin/python /ganuda/services/notifications/daily_digest.py >> /var/log/ganuda/digest.log 2>&1
```

---

## 9. Testing

```bash
# Create test notification
python -c "
from notify import TPMNotifier
n = TPMNotifier()
n.notify('P1', 'test', 'Test notification', 'This is a test', 'test_script')
n.close()
"

# Check notifications via API
curl -s http://192.168.132.223:8080/v1/notifications \
  -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

# Acknowledge
curl -s -X POST http://192.168.132.223:8080/v1/notifications/1/acknowledge \
  -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"
```

---

## 10. Constitutional Rule

**Per Peace Chief**: No Jr may take autonomous action without TPM notification.

This is encoded in the Jr activation protocol:
1. Jr identifies action to take
2. Jr calls `notify_autonomous_deployment()`
3. Jr waits for acknowledgment OR proceeds with action logged
4. TPM reviews at next check-in

The Tribe works autonomously, but the TPM always knows what's happening.

---

**For Seven Generations.**
*Cherokee Constitutional AI Notification System*
