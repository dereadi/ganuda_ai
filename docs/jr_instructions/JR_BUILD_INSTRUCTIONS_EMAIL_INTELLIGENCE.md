# JR INSTRUCTIONS: Email Intelligence Assistant
## JR_BUILD_INSTRUCTIONS_EMAIL_INTELLIGENCE
## December 17, 2025

### OBJECTIVE
Build an Email Intelligence Assistant that monitors Gmail for job offers, interview requests, and high-priority career-related emails, with alerts via Telegram.

---

## BACKGROUND

User needs proactive monitoring of Gmail inbox for:
- Job offers and salary negotiations
- Interview scheduling requests
- Recruiter outreach
- Application status updates
- Contract/offer documents

The assistant should:
1. Poll Gmail periodically (every 5 minutes)
2. Classify emails using LLM Gateway
3. Alert via Telegram for high-priority items
4. Track job application pipeline in database

---

## TASK 1: Create Gmail API Credentials

**Manual Step (User):**
1. Go to https://console.cloud.google.com/
2. Create new project: "Cherokee-Email-Intelligence"
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials.json to `/ganuda/secrets/gmail_credentials.json`

---

## TASK 2: Create Database Schema

**File:** Create SQL migration

```sql
-- Email Intelligence Tables
CREATE TABLE IF NOT EXISTS email_classifications (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    thread_id VARCHAR(255),
    from_address VARCHAR(255),
    from_name VARCHAR(255),
    subject TEXT,
    snippet TEXT,
    received_at TIMESTAMP,
    classification VARCHAR(50),  -- job_offer, interview, recruiter, status_update, contract, other
    priority INTEGER DEFAULT 5,  -- 1=urgent, 5=normal
    confidence FLOAT,
    company_name VARCHAR(255),
    position_title VARCHAR(255),
    salary_mentioned TEXT,
    action_required TEXT,
    alert_sent BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS job_pipeline (
    id SERIAL PRIMARY KEY,
    company VARCHAR(255) NOT NULL,
    position VARCHAR(255),
    status VARCHAR(50) DEFAULT 'applied',  -- applied, phone_screen, interview, offer, negotiation, accepted, rejected
    salary_range TEXT,
    source VARCHAR(100),  -- linkedin, indeed, direct, referral
    applied_at TIMESTAMP,
    last_contact TIMESTAMP,
    next_action TEXT,
    notes TEXT,
    email_thread_ids TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_email_class_received ON email_classifications(received_at DESC);
CREATE INDEX idx_email_class_classification ON email_classifications(classification);
CREATE INDEX idx_job_pipeline_status ON job_pipeline(status);
CREATE INDEX idx_job_pipeline_company ON job_pipeline(company);
```

---

## TASK 3: Create Email Monitor Service

**File:** `/ganuda/services/email_intelligence/email_monitor.py`

```python
#!/usr/bin/env python3
"""
Email Intelligence Monitor for Cherokee AI Federation

Monitors Gmail for job-related emails and sends alerts via Telegram.
Uses LLM Gateway for email classification.

For Seven Generations - Cherokee AI Federation
"""

import os
import json
import pickle
import base64
import requests
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Configuration
CONFIG = {
    'credentials_file': '/ganuda/secrets/gmail_credentials.json',
    'token_file': '/ganuda/secrets/gmail_token.pickle',
    'db_host': '192.168.132.222',
    'db_name': 'zammad_production',
    'db_user': 'claude',
    'db_password': 'jawaseatlasers2',
    'gateway_url': 'http://192.168.132.223:8080',
    'telegram_bot_token': os.environ.get('TELEGRAM_BOT_TOKEN', ''),
    'telegram_chat_id': os.environ.get('TELEGRAM_CHAT_ID', ''),
    'poll_interval': 300,  # 5 minutes
    'lookback_hours': 24
}

# Classification prompt
CLASSIFICATION_PROMPT = """Analyze this email and classify it for job search monitoring.

From: {from_address}
Subject: {subject}
Preview: {snippet}

Respond in JSON format:
{{
    "classification": "job_offer|interview|recruiter|status_update|contract|other",
    "priority": 1-5 (1=urgent action needed, 5=informational),
    "confidence": 0.0-1.0,
    "company_name": "extracted company name or null",
    "position_title": "extracted position or null",
    "salary_mentioned": "any salary/compensation info or null",
    "action_required": "brief action needed or null",
    "reasoning": "brief explanation"
}}

Classification Guide:
- job_offer: Explicit job offer, compensation package, offer letter
- interview: Interview scheduling, availability requests, interview confirmation
- recruiter: Initial recruiter outreach, LinkedIn connection follow-up
- status_update: Application received, under review, moving forward/not moving forward
- contract: Employment contracts, NDAs, background check requests
- other: Not job-related or spam
"""


class EmailIntelligence:
    """Gmail monitoring and classification service."""

    def __init__(self):
        self.service = None
        self.db_conn = None

    def authenticate_gmail(self) -> bool:
        """Authenticate with Gmail API."""
        creds = None

        if os.path.exists(CONFIG['token_file']):
            with open(CONFIG['token_file'], 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CONFIG['credentials_file']):
                    print(f"ERROR: Credentials file not found: {CONFIG['credentials_file']}")
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(
                    CONFIG['credentials_file'], SCOPES)
                creds = flow.run_local_server(port=0)

            with open(CONFIG['token_file'], 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)
        return True

    def connect_db(self):
        """Connect to PostgreSQL database."""
        self.db_conn = psycopg2.connect(
            host=CONFIG['db_host'],
            database=CONFIG['db_name'],
            user=CONFIG['db_user'],
            password=CONFIG['db_password']
        )

    def get_recent_emails(self, hours: int = 24) -> List[Dict]:
        """Fetch recent unprocessed emails."""
        after_date = (datetime.now() - timedelta(hours=hours)).strftime('%Y/%m/%d')
        query = f'after:{after_date}'

        results = self.service.users().messages().list(
            userId='me', q=query, maxResults=50
        ).execute()

        messages = results.get('messages', [])
        emails = []

        for msg in messages:
            # Check if already processed
            if self._is_processed(msg['id']):
                continue

            full_msg = self.service.users().messages().get(
                userId='me', id=msg['id'], format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in full_msg['payload']['headers']}

            emails.append({
                'message_id': msg['id'],
                'thread_id': full_msg.get('threadId'),
                'from_address': headers.get('From', ''),
                'subject': headers.get('Subject', ''),
                'snippet': full_msg.get('snippet', ''),
                'received_at': datetime.fromtimestamp(int(full_msg['internalDate']) / 1000)
            })

        return emails

    def _is_processed(self, message_id: str) -> bool:
        """Check if email already processed."""
        with self.db_conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM email_classifications WHERE message_id = %s",
                (message_id,)
            )
            return cur.fetchone() is not None

    def classify_email(self, email: Dict) -> Dict:
        """Use LLM Gateway to classify email."""
        prompt = CLASSIFICATION_PROMPT.format(
            from_address=email['from_address'],
            subject=email['subject'],
            snippet=email['snippet']
        )

        try:
            response = requests.post(
                f"{CONFIG['gateway_url']}/v1/chat/completions",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {os.environ.get('CHEROKEE_API_KEY', '')}"
                },
                json={
                    'model': 'cherokee-nemotron',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.3
                },
                timeout=30
            )

            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                # Extract JSON from response
                import re
                json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())

        except Exception as e:
            print(f"Classification error: {e}")

        return {
            'classification': 'other',
            'priority': 5,
            'confidence': 0.0,
            'company_name': None,
            'position_title': None,
            'salary_mentioned': None,
            'action_required': None
        }

    def save_classification(self, email: Dict, classification: Dict):
        """Save email classification to database."""
        with self.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO email_classifications
                (message_id, thread_id, from_address, subject, snippet, received_at,
                 classification, priority, confidence, company_name, position_title,
                 salary_mentioned, action_required)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_id) DO NOTHING
            """, (
                email['message_id'],
                email.get('thread_id'),
                email['from_address'],
                email['subject'],
                email['snippet'],
                email['received_at'],
                classification['classification'],
                classification['priority'],
                classification['confidence'],
                classification.get('company_name'),
                classification.get('position_title'),
                classification.get('salary_mentioned'),
                classification.get('action_required')
            ))
        self.db_conn.commit()

    def send_telegram_alert(self, email: Dict, classification: Dict):
        """Send Telegram notification for high-priority emails."""
        if not CONFIG['telegram_bot_token'] or not CONFIG['telegram_chat_id']:
            print("Telegram not configured, skipping alert")
            return

        priority_emoji = {1: '🔴', 2: '🟠', 3: '🟡', 4: '🔵', 5: '⚪'}
        class_emoji = {
            'job_offer': '💼',
            'interview': '📅',
            'recruiter': '👤',
            'status_update': '📊',
            'contract': '📝'
        }

        emoji = class_emoji.get(classification['classification'], '📧')
        priority = priority_emoji.get(classification['priority'], '⚪')

        message = f"""{emoji} {priority} **Email Alert**

**Type:** {classification['classification'].replace('_', ' ').title()}
**From:** {email['from_address']}
**Subject:** {email['subject']}

{f"**Company:** {classification['company_name']}" if classification.get('company_name') else ""}
{f"**Position:** {classification['position_title']}" if classification.get('position_title') else ""}
{f"**Salary:** {classification['salary_mentioned']}" if classification.get('salary_mentioned') else ""}
{f"**Action:** {classification['action_required']}" if classification.get('action_required') else ""}

_Confidence: {classification['confidence']*100:.0f}%_
"""

        try:
            requests.post(
                f"https://api.telegram.org/bot{CONFIG['telegram_bot_token']}/sendMessage",
                json={
                    'chat_id': CONFIG['telegram_chat_id'],
                    'text': message,
                    'parse_mode': 'Markdown'
                },
                timeout=10
            )

            # Mark alert sent
            with self.db_conn.cursor() as cur:
                cur.execute(
                    "UPDATE email_classifications SET alert_sent = TRUE WHERE message_id = %s",
                    (email['message_id'],)
                )
            self.db_conn.commit()

        except Exception as e:
            print(f"Telegram alert error: {e}")

    def process_emails(self):
        """Main processing loop."""
        emails = self.get_recent_emails(CONFIG['lookback_hours'])
        print(f"[{datetime.now()}] Processing {len(emails)} new emails")

        for email in emails:
            classification = self.classify_email(email)
            self.save_classification(email, classification)

            # Alert for job-related emails with priority <= 3
            if classification['classification'] != 'other' and classification['priority'] <= 3:
                self.send_telegram_alert(email, classification)
                print(f"  ALERT: {classification['classification']} - {email['subject']}")
            else:
                print(f"  Classified: {classification['classification']} - {email['subject'][:50]}")

    def run_daemon(self, poll_interval: int = 300):
        """Run as daemon with periodic polling."""
        print(f"Email Intelligence starting (poll every {poll_interval}s)")

        if not self.authenticate_gmail():
            print("Gmail authentication failed")
            return

        self.connect_db()
        print("Connected to database")

        import time
        while True:
            try:
                self.process_emails()
            except Exception as e:
                print(f"Error in processing loop: {e}")
            time.sleep(poll_interval)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Email Intelligence Monitor')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=300, help='Poll interval in seconds')
    args = parser.parse_args()

    monitor = EmailIntelligence()

    if args.once:
        monitor.authenticate_gmail()
        monitor.connect_db()
        monitor.process_emails()
    else:
        monitor.run_daemon(args.interval)
```

---

## TASK 4: Create SAG UI Email Dashboard

**File:** Update SAG UI to show email classifications

Add API endpoint to gateway.py:
```python
@app.get("/api/email/recent")
async def get_recent_emails(limit: int = 50):
    """Get recent classified emails."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT message_id, from_address, subject, received_at,
               classification, priority, company_name, position_title, action_required
        FROM email_classifications
        ORDER BY received_at DESC
        LIMIT %s
    """, (limit,))

    emails = []
    for row in cur.fetchall():
        emails.append({
            'message_id': row[0],
            'from': row[1],
            'subject': row[2],
            'received': row[3].isoformat() if row[3] else None,
            'classification': row[4],
            'priority': row[5],
            'company': row[6],
            'position': row[7],
            'action': row[8]
        })

    cur.close()
    conn.close()
    return {'emails': emails}

@app.get("/api/email/pipeline")
async def get_job_pipeline():
    """Get job application pipeline."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT company, position, status, salary_range, last_contact, next_action
        FROM job_pipeline
        ORDER BY
            CASE status
                WHEN 'offer' THEN 1
                WHEN 'negotiation' THEN 2
                WHEN 'interview' THEN 3
                WHEN 'phone_screen' THEN 4
                WHEN 'applied' THEN 5
                ELSE 6
            END,
            last_contact DESC
    """)

    pipeline = []
    for row in cur.fetchall():
        pipeline.append({
            'company': row[0],
            'position': row[1],
            'status': row[2],
            'salary_range': row[3],
            'last_contact': row[4].isoformat() if row[4] else None,
            'next_action': row[5]
        })

    cur.close()
    conn.close()
    return {'pipeline': pipeline}
```

---

## TASK 5: Create Systemd Service

**File:** `/etc/systemd/system/email-intelligence.service`

```ini
[Unit]
Description=Cherokee Email Intelligence Monitor
After=network.target postgresql.service

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/email_intelligence
Environment="TELEGRAM_BOT_TOKEN=your_token_here"
Environment="TELEGRAM_CHAT_ID=your_chat_id_here"
Environment="CHEROKEE_API_KEY=ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"
ExecStart=/home/dereadi/cherokee_venv/bin/python3 email_monitor.py --interval 300
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

---

## VERIFICATION

```bash
# Check service directory
ls -la /ganuda/services/email_intelligence/

# Test Gmail auth (will open browser first time)
cd /ganuda/services/email_intelligence
python3 email_monitor.py --once

# Check database tables
PGPASSWORD='jawaseatlasers2' psql -h localhost -U claude -d zammad_production -c "\dt email*"
PGPASSWORD='jawaseatlasers2' psql -h localhost -U claude -d zammad_production -c "SELECT COUNT(*) FROM email_classifications;"

# Check service status
sudo systemctl status email-intelligence
```

---

## SUCCESS CRITERIA

1. Gmail API authenticated and token saved
2. Database tables created (email_classifications, job_pipeline)
3. Email monitor can fetch and classify emails
4. Telegram alerts sent for priority emails
5. SAG UI displays email classifications
6. Systemd service running and auto-restarts

---

## DEPENDENCIES

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*
