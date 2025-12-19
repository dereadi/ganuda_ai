# JR INSTRUCTIONS: Job Alert Enhancement for Email Daemon
## JR_BUILD_INSTRUCTIONS_JOB_ALERT_ENHANCEMENT
## December 17, 2025

### OBJECTIVE
Enhance the existing email daemon at `/ganuda/email_daemon/` to classify job-related emails and send Telegram alerts for high-priority items (offers, interviews, next steps).

---

## BACKGROUND

**Existing Infrastructure:**
- Gmail sync daemon: `/ganuda/email_daemon/gmail_sync_daemon.py`
- Credentials: `~/.gmail_credentials/token.pickle`
- Database: `triad_federation.emails` (544 emails synced)
- Config: `/ganuda/email_daemon/config.json`

**Current State:**
- 100 job-related emails in last week
- 20 marked as action_required
- No job-specific classification
- No Telegram alerts

---

## TASK 1: Add Job Classification Column

**File:** Run SQL on bluefin

```sql
-- Add job classification fields to emails table
ALTER TABLE emails ADD COLUMN IF NOT EXISTS job_classification VARCHAR(50);
ALTER TABLE emails ADD COLUMN IF NOT EXISTS job_company VARCHAR(255);
ALTER TABLE emails ADD COLUMN IF NOT EXISTS job_position VARCHAR(255);
ALTER TABLE emails ADD COLUMN IF NOT EXISTS job_alert_sent BOOLEAN DEFAULT FALSE;

-- Create index for job queries
CREATE INDEX IF NOT EXISTS idx_emails_job_classification ON emails(job_classification);

COMMENT ON COLUMN emails.job_classification IS 'offer, interview, recruiter, status_update, rejection, or null';
```

---

## TASK 2: Create Job Classifier Module

**File:** `/ganuda/email_daemon/job_classifier.py`

```python
#!/usr/bin/env python3
"""
Job Email Classifier for Cherokee AI Federation
Uses pattern matching and optional LLM for classification.
"""

import re
from typing import Dict, Optional, Tuple

# Known job board domains
JOB_DOMAINS = {
    'indeed.com': 'Indeed',
    'linkedin.com': 'LinkedIn',
    'ziprecruiter.com': 'ZipRecruiter',
    'greenhouse.io': 'Greenhouse',
    'greenhouse-mail.io': 'Greenhouse',
    'lever.co': 'Lever',
    'myworkday.com': 'Workday',
    'icims.com': 'iCIMS',
    'jobvite.com': 'Jobvite',
    'smartrecruiters.com': 'SmartRecruiters',
    'ashbyhq.com': 'Ashby',
    'breezy.hr': 'Breezy'
}

# Classification patterns
OFFER_PATTERNS = [
    r'offer letter',
    r'job offer',
    r'pleased to offer',
    r'extend.{1,20}offer',
    r'compensation package',
    r'start date',
    r'base salary',
    r'we.{1,10}like to offer',
]

INTERVIEW_PATTERNS = [
    r'schedule.{1,20}interview',
    r'interview.{1,20}schedule',
    r'phone screen',
    r'video interview',
    r'technical interview',
    r'on-?site',
    r'meet.{1,20}team',
    r'availability.{1,20}call',
    r'calendar invite',
    r'zoom.{1,10}meeting',
]

NEXT_STEPS_PATTERNS = [
    r'next step',
    r'moving forward',
    r'proceed.{1,20}application',
    r'advance.{1,20}process',
    r'shortlist',
    r'selected for',
]

REJECTION_PATTERNS = [
    r'not.{1,20}moving forward',
    r'other candidates',
    r'not.{1,20}selected',
    r'position.{1,20}filled',
    r'unfortunately',
    r'regret to inform',
    r'not.{1,20}match',
    r'decided.{1,20}proceed.{1,20}other',
]

APPLICATION_PATTERNS = [
    r'application.{1,20}received',
    r'thank.{1,20}applying',
    r'application.{1,20}complete',
    r'successfully applied',
    r'we.{1,10}received.{1,20}application',
]

RECRUITER_PATTERNS = [
    r'opportunity.{1,20}interest',
    r'reaching out',
    r'your profile',
    r'your background',
    r'perfect fit',
    r'great match',
    r'came across.{1,20}profile',
]

# Exclude patterns (marketing, spam)
EXCLUDE_PATTERNS = [
    r'limited time',
    r'special offer',
    r'discount',
    r'sale',
    r'credit.{1,10}(card|limit|offer)',
    r'unsubscribe',
    r'opt.?out',
    r'promotional',
]


def is_job_related(from_addr: str, subject: str) -> bool:
    """Check if email is job-related based on sender or subject."""
    from_lower = from_addr.lower()
    subject_lower = subject.lower()

    # Check if from job board
    for domain in JOB_DOMAINS:
        if domain in from_lower:
            return True

    # Check subject keywords
    job_keywords = ['job', 'position', 'opportunity', 'application',
                    'interview', 'hiring', 'career', 'recruit']
    for keyword in job_keywords:
        if keyword in subject_lower:
            # Exclude marketing
            for exclude in EXCLUDE_PATTERNS:
                if re.search(exclude, subject_lower):
                    return False
            return True

    return False


def classify_job_email(from_addr: str, subject: str, body: str) -> Tuple[Optional[str], int]:
    """
    Classify job email and return (classification, priority).

    Classifications: offer, interview, next_steps, application, recruiter, rejection
    Priority: 1 (urgent) to 5 (informational)
    """
    text = (subject + ' ' + body[:1000]).lower()

    # Check exclusions first
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, text):
            return None, 5

    # Check for offers (highest priority)
    for pattern in OFFER_PATTERNS:
        if re.search(pattern, text):
            return 'offer', 1

    # Check for interviews
    for pattern in INTERVIEW_PATTERNS:
        if re.search(pattern, text):
            return 'interview', 1

    # Check for next steps
    for pattern in NEXT_STEPS_PATTERNS:
        if re.search(pattern, text):
            return 'next_steps', 2

    # Check for rejections
    for pattern in REJECTION_PATTERNS:
        if re.search(pattern, text):
            return 'rejection', 4

    # Check for application confirmations
    for pattern in APPLICATION_PATTERNS:
        if re.search(pattern, text):
            return 'application', 3

    # Check for recruiter outreach
    for pattern in RECRUITER_PATTERNS:
        if re.search(pattern, text):
            return 'recruiter', 3

    return None, 5


def extract_company_position(from_addr: str, subject: str, body: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract company name and position from email."""
    company = None
    position = None

    # Try to extract from subject
    # Pattern: "Application: Position at Company" or "Position - Company"
    patterns = [
        r'application[:\s]+(.+?)\s+at\s+(.+?)(?:\s|$)',
        r'(.+?)\s+at\s+(.+?)(?:\s|$)',
        r'(.+?)\s+-\s+(.+?)(?:\s|$)',
        r'thank.+applying.+?(?:to|at)\s+(.+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, subject, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) >= 2:
                position = groups[0].strip()[:100]
                company = groups[1].strip()[:100]
            elif len(groups) == 1:
                company = groups[0].strip()[:100]
            break

    # Try to get company from sender domain
    if not company:
        for domain, name in JOB_DOMAINS.items():
            if domain in from_addr.lower():
                company = name
                break

    return company, position


def get_job_source(from_addr: str) -> Optional[str]:
    """Get the job board source from email address."""
    from_lower = from_addr.lower()
    for domain, name in JOB_DOMAINS.items():
        if domain in from_lower:
            return name
    return None
```

---

## TASK 3: Add Telegram Alert Function

**File:** `/ganuda/email_daemon/telegram_alerts.py`

```python
#!/usr/bin/env python3
"""
Telegram Alert Module for Job Emails
"""

import os
import requests
from typing import Dict

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

PRIORITY_EMOJI = {1: '🔴', 2: '🟠', 3: '🟡', 4: '🔵', 5: '⚪'}
CLASS_EMOJI = {
    'offer': '💰',
    'interview': '📅',
    'next_steps': '➡️',
    'recruiter': '👤',
    'application': '📝',
    'rejection': '❌'
}


def send_job_alert(email: Dict, classification: str, priority: int) -> bool:
    """Send Telegram alert for job email."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    emoji = CLASS_EMOJI.get(classification, '📧')
    priority_emoji = PRIORITY_EMOJI.get(priority, '⚪')

    message = f"""{emoji} {priority_emoji} *Job Alert: {classification.replace('_', ' ').title()}*

*From:* {email.get('from_address', 'Unknown')}
*Subject:* {email.get('subject', 'No subject')}
"""

    if email.get('job_company'):
        message += f"*Company:* {email['job_company']}\n"
    if email.get('job_position'):
        message += f"*Position:* {email['job_position']}\n"

    message += f"\n_{email.get('date_received', '')}_"

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False
```

---

## TASK 4: Modify Email Sync Daemon

**File:** `/ganuda/email_daemon/gmail_sync_daemon.py`

**Add imports at top:**
```python
from job_classifier import is_job_related, classify_job_email, extract_company_position
from telegram_alerts import send_job_alert
```

**Modify the INSERT query to include job fields:**
```python
# After calculating priority_score and action_required, add:
job_classification = None
job_company = None
job_position = None
job_priority = 5

if is_job_related(from_addr, subject):
    job_classification, job_priority = classify_job_email(from_addr, subject, body_text)
    job_company, job_position = extract_company_position(from_addr, subject, body_text)

# Update INSERT to include job fields:
cur.execute('''
    INSERT INTO emails (message_id, thread_id, subject, from_address, to_addresses,
                       date_received, body_text, labels, thermal_temp,
                       priority_score, action_required,
                       job_classification, job_company, job_position,
                       created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
    ON CONFLICT (message_id) DO UPDATE SET
        thermal_temp = EXCLUDED.thermal_temp,
        priority_score = EXCLUDED.priority_score,
        action_required = EXCLUDED.action_required,
        job_classification = EXCLUDED.job_classification,
        job_company = EXCLUDED.job_company,
        job_position = EXCLUDED.job_position,
        updated_at = NOW()
    RETURNING id, (xmax = 0) as is_new
''', (message_id, thread_id, subject, from_addr, to_addrs,
      date_received, body_text, labels, thermal_temp,
      priority_score, action_required,
      job_classification, job_company, job_position))

result = cur.fetchone()
if result:
    email_id, is_new = result
    inserted += 1

    # Send alert for new high-priority job emails
    if is_new and job_classification and job_priority <= 2:
        alert_sent = send_job_alert({
            'from_address': from_addr,
            'subject': subject,
            'job_company': job_company,
            'job_position': job_position,
            'date_received': str(date_received)
        }, job_classification, job_priority)

        if alert_sent:
            cur.execute(
                "UPDATE emails SET job_alert_sent = TRUE WHERE id = %s",
                (email_id,)
            )
            logger.info(f"ALERT SENT: {job_classification} - {subject[:50]}")
```

---

## TASK 5: Backfill Existing Emails

**File:** `/ganuda/email_daemon/backfill_job_classification.py`

```python
#!/usr/bin/env python3
"""Backfill job classification for existing emails."""

import psycopg2
from job_classifier import is_job_related, classify_job_email, extract_company_position

conn = psycopg2.connect(
    host='192.168.132.222',
    database='triad_federation',
    user='claude',
    password='jawaseatlasers2'
)

cur = conn.cursor()
cur.execute("""
    SELECT id, from_address, subject, body_text
    FROM emails
    WHERE job_classification IS NULL
""")

updated = 0
for row in cur.fetchall():
    email_id, from_addr, subject, body = row

    if is_job_related(from_addr or '', subject or ''):
        classification, priority = classify_job_email(
            from_addr or '', subject or '', body or ''
        )
        company, position = extract_company_position(
            from_addr or '', subject or '', body or ''
        )

        if classification:
            cur.execute("""
                UPDATE emails
                SET job_classification = %s, job_company = %s, job_position = %s
                WHERE id = %s
            """, (classification, company, position, email_id))
            updated += 1
            print(f"Classified: {classification} - {subject[:50]}")

conn.commit()
print(f"Updated {updated} emails")
cur.close()
conn.close()
```

---

## TASK 6: Update Systemd Service

**File:** `/etc/systemd/system/cherokee-email-daemon.service`

```ini
[Unit]
Description=Cherokee Email Sync Daemon with Job Alerts
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/email_daemon
Environment="TELEGRAM_BOT_TOKEN=<your_token>"
Environment="TELEGRAM_CHAT_ID=<your_chat_id>"
ExecStart=/home/dereadi/cherokee_venv/bin/python3 gmail_sync_daemon.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

---

## VERIFICATION

```bash
# Check columns added
PGPASSWORD='jawaseatlasers2' psql -h localhost -U claude -d triad_federation -c "\d emails" | grep job

# Run backfill
cd /ganuda/email_daemon && python3 backfill_job_classification.py

# Check classifications
PGPASSWORD='jawaseatlasers2' psql -h localhost -U claude -d triad_federation -c "
SELECT job_classification, COUNT(*)
FROM emails
WHERE job_classification IS NOT NULL
GROUP BY 1 ORDER BY 2 DESC;
"

# Restart daemon
sudo systemctl restart cherokee-email-daemon
sudo systemctl status cherokee-email-daemon
```

---

## SUCCESS CRITERIA

1. Emails table has job_classification, job_company, job_position columns
2. Existing emails backfilled with classifications
3. New job emails classified on sync
4. Telegram alerts sent for offers and interviews (priority 1-2)
5. Daemon running with job classification enabled

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*
