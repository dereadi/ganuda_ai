# Jr Build Instructions: Email Job Application Automation

**Task ID:** JR-EMAIL-JOB-AUTO-001
**Priority:** P2 (High - User Productivity Enhancement)
**Date:** 2025-12-26
**Author:** TPM
**Source:** User Request - Automate job applications from email

---

## Problem Statement

The user receives job opportunity emails from ZipRecruiter and Indeed. Currently, reviewing and applying to relevant jobs requires manual effort. We need to automate:
1. Reading job opportunity emails
2. Matching jobs to user's skills/preferences
3. Auto-applying with updated resume where appropriate

---

## Solution: Email Job Application Automation

```
Email Inbox
    │
    ▼
[Email Reader Daemon]
    │
    ├─► Fetch unread job emails (ZipRecruiter, Indeed)
    │
    ▼
[Job Extractor]
    │
    ├─► Extract: Job title, company, requirements, apply link
    │
    ▼
[Job Matcher]
    │
    ├─► Score job against user profile
    ├─► TPM skills: AI/ML, distributed systems, LLM deployment
    │
    ▼
[Application Decision]
    │
    ├─► High match (>80%): Auto-apply with resume
    ├─► Medium match (50-80%): Queue for review
    ├─► Low match (<50%): Archive
    │
    ▼
[Application Executor]
    │
    ├─► Submit application via API or web automation
    ├─► Log to thermal memory
    └─► Send notification to TPM
```

---

## Implementation

### Step 1: Email Reader Configuration

Create `/ganuda/config/email_config.json`:

```json
{
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "email_account": "USER_EMAIL_PLACEHOLDER",
    "app_password": "USER_APP_PASSWORD_PLACEHOLDER",
    "job_sources": [
        {
            "name": "ZipRecruiter",
            "sender_patterns": ["@ziprecruiter.com", "noreply@ziprecruiter.com"]
        },
        {
            "name": "Indeed",
            "sender_patterns": ["@indeed.com", "@indeedemail.com"]
        }
    ],
    "check_interval_minutes": 30,
    "resume_path": "/ganuda/data/resumes/current_resume.pdf"
}
```

### Step 2: Email Reader Daemon

In `/ganuda/daemons/email_job_reader.py`:

```python
#!/usr/bin/env python3
"""
Email Job Reader Daemon for Cherokee AI Federation
Reads job opportunity emails from ZipRecruiter and Indeed
"""
import imaplib
import email
from email.header import decode_header
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2


# Load configuration
def load_config():
    with open('/ganuda/config/email_config.json', 'r') as f:
        return json.load(f)


class EmailJobReader:
    """Reads and extracts job opportunities from emails."""

    def __init__(self, config: dict):
        self.config = config
        self.imap = None

    def connect(self):
        """Connect to email server."""
        self.imap = imaplib.IMAP4_SSL(
            self.config['imap_server'],
            self.config['imap_port']
        )
        self.imap.login(
            self.config['email_account'],
            self.config['app_password']
        )

    def disconnect(self):
        """Disconnect from email server."""
        if self.imap:
            self.imap.logout()

    def get_job_emails(self) -> List[Dict]:
        """Fetch unread job opportunity emails."""
        job_emails = []

        self.imap.select('INBOX')

        for source in self.config['job_sources']:
            for pattern in source['sender_patterns']:
                # Search for unread emails from this sender
                _, message_ids = self.imap.search(
                    None,
                    f'(UNSEEN FROM "{pattern}")'
                )

                for msg_id in message_ids[0].split():
                    _, msg_data = self.imap.fetch(msg_id, '(RFC822)')
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)

                    job_info = self._extract_job_info(msg, source['name'])
                    if job_info:
                        job_emails.append(job_info)

        return job_emails

    def _extract_job_info(self, msg, source: str) -> Optional[Dict]:
        """Extract job information from email."""
        subject = self._decode_header(msg['Subject'])
        from_addr = msg['From']
        date = msg['Date']

        # Get email body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
                elif part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        # Extract job details based on source
        if source == "ZipRecruiter":
            return self._parse_ziprecruiter(subject, body)
        elif source == "Indeed":
            return self._parse_indeed(subject, body)

        return None

    def _parse_ziprecruiter(self, subject: str, body: str) -> Dict:
        """Parse ZipRecruiter job email."""
        # Extract job title from subject
        title_match = re.search(r'New job:\s*(.+?)(?:\s*-|\s*at|\s*$)', subject)
        job_title = title_match.group(1) if title_match else subject

        # Extract company
        company_match = re.search(r'at\s+([^-\n]+)', subject)
        company = company_match.group(1).strip() if company_match else "Unknown"

        # Extract apply link
        apply_link = re.search(r'https://www\.ziprecruiter\.com/[^\s"<>]+apply[^\s"<>]*', body)

        return {
            "source": "ZipRecruiter",
            "title": job_title,
            "company": company,
            "body": body[:2000],  # First 2000 chars
            "apply_link": apply_link.group(0) if apply_link else None,
            "received_at": datetime.now().isoformat()
        }

    def _parse_indeed(self, subject: str, body: str) -> Dict:
        """Parse Indeed job email."""
        # Similar parsing for Indeed
        title_match = re.search(r'(?:New job|Recommended):\s*(.+?)(?:\s*-|\s*in|\s*$)', subject)
        job_title = title_match.group(1) if title_match else subject

        company_match = re.search(r'at\s+([^-\n]+)', body)
        company = company_match.group(1).strip() if company_match else "Unknown"

        apply_link = re.search(r'https://(?:www\.)?indeed\.com/[^\s"<>]+', body)

        return {
            "source": "Indeed",
            "title": job_title,
            "company": company,
            "body": body[:2000],
            "apply_link": apply_link.group(0) if apply_link else None,
            "received_at": datetime.now().isoformat()
        }

    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        decoded = decode_header(header)
        parts = []
        for part, encoding in decoded:
            if isinstance(part, bytes):
                parts.append(part.decode(encoding or 'utf-8'))
            else:
                parts.append(part)
        return ' '.join(parts)


def log_job_opportunity(job: dict, match_score: float, action: str):
    """Log job opportunity to thermal memory."""
    try:
        conn = psycopg2.connect(
            host='192.168.132.222',
            database='zammad_production',
            user='claude',
            password='jawaseatlasers2'
        )
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO job_opportunities (
                source, job_title, company, apply_link,
                match_score, action_taken, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (
            job['source'],
            job['title'],
            job['company'],
            job.get('apply_link'),
            match_score,
            action
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[JOB] Error logging opportunity: {e}")


if __name__ == "__main__":
    config = load_config()
    reader = EmailJobReader(config)

    print("[JOB] Starting email job reader daemon...")

    while True:
        try:
            reader.connect()
            jobs = reader.get_job_emails()
            reader.disconnect()

            for job in jobs:
                print(f"[JOB] Found: {job['title']} at {job['company']}")
                # TODO: Score and apply logic

            time.sleep(config['check_interval_minutes'] * 60)

        except Exception as e:
            print(f"[JOB] Error: {e}")
            time.sleep(300)  # Wait 5 min on error
```

### Step 3: Job Matcher

In `/ganuda/lib/job_matcher.py`:

```python
"""
Job Matching Algorithm for Cherokee AI Federation
Scores jobs against user profile for auto-application
"""
from typing import Dict, List


# User profile - TPM focused
USER_PROFILE = {
    "target_roles": [
        "Technical Program Manager",
        "TPM",
        "Senior TPM",
        "Staff TPM",
        "Principal TPM",
        "AI/ML Program Manager",
        "Engineering Program Manager"
    ],
    "skills": [
        "AI", "ML", "Machine Learning", "LLM", "Large Language Model",
        "distributed systems", "kubernetes", "docker",
        "python", "golang", "rust",
        "program management", "agile", "scrum",
        "cloud", "AWS", "GCP", "Azure",
        "API", "microservices", "infrastructure"
    ],
    "preferred_companies": [
        "Anthropic", "OpenAI", "Google", "Meta", "Microsoft",
        "Amazon", "Apple", "NVIDIA"
    ],
    "min_salary": 200000,
    "locations": [
        "remote", "hybrid", "San Francisco", "Bay Area",
        "Seattle", "New York"
    ],
    "exclusions": [
        "contractor", "contract", "part-time", "internship"
    ]
}


def score_job(job: Dict) -> float:
    """
    Score a job opportunity against user profile.
    Returns 0.0 - 1.0 where 1.0 is perfect match.
    """
    score = 0.0
    max_score = 0.0

    title = job.get('title', '').lower()
    body = job.get('body', '').lower()
    company = job.get('company', '').lower()

    # Role match (40 points max)
    max_score += 40
    for role in USER_PROFILE['target_roles']:
        if role.lower() in title:
            score += 40
            break
    else:
        # Partial role match
        if any(kw in title for kw in ['program manager', 'tpm', 'technical']):
            score += 20

    # Skills match (30 points max)
    max_score += 30
    skill_matches = sum(1 for skill in USER_PROFILE['skills']
                       if skill.lower() in body or skill.lower() in title)
    skill_score = min(30, skill_matches * 3)  # 3 points per skill, max 30
    score += skill_score

    # Company preference (15 points max)
    max_score += 15
    for preferred in USER_PROFILE['preferred_companies']:
        if preferred.lower() in company:
            score += 15
            break

    # Location match (10 points max)
    max_score += 10
    for loc in USER_PROFILE['locations']:
        if loc.lower() in body:
            score += 10
            break

    # Exclusions (-50 points)
    for exclusion in USER_PROFILE['exclusions']:
        if exclusion.lower() in title or exclusion.lower() in body:
            score -= 50

    # Normalize to 0-1
    final_score = max(0.0, min(1.0, score / max_score))
    return round(final_score, 2)


def categorize_job(score: float) -> str:
    """Categorize job based on match score."""
    if score >= 0.80:
        return "auto_apply"
    elif score >= 0.50:
        return "review"
    else:
        return "archive"
```

### Step 4: Application Executor

In `/ganuda/lib/job_applicator.py`:

```python
"""
Job Application Executor for Cherokee AI Federation
Handles auto-applying to matched job opportunities
"""
import requests
from typing import Dict, Optional
import time


class JobApplicator:
    """Executes job applications."""

    def __init__(self, resume_path: str):
        self.resume_path = resume_path

    def apply(self, job: Dict) -> Dict:
        """
        Apply to a job opportunity.
        Returns result dict with success status.
        """
        source = job.get('source')
        apply_link = job.get('apply_link')

        if not apply_link:
            return {"success": False, "reason": "No apply link found"}

        if source == "ZipRecruiter":
            return self._apply_ziprecruiter(job)
        elif source == "Indeed":
            return self._apply_indeed(job)
        else:
            return {"success": False, "reason": f"Unknown source: {source}"}

    def _apply_ziprecruiter(self, job: Dict) -> Dict:
        """
        Apply via ZipRecruiter.
        Note: ZipRecruiter has 1-click apply for some jobs.
        For others, we need web automation or API.
        """
        # ZipRecruiter API integration would go here
        # For now, return pending for manual review
        return {
            "success": False,
            "reason": "ZipRecruiter automation not yet implemented",
            "action": "queue_for_manual",
            "link": job.get('apply_link')
        }

    def _apply_indeed(self, job: Dict) -> Dict:
        """
        Apply via Indeed.
        Indeed has Easy Apply for some jobs.
        """
        # Indeed API integration would go here
        return {
            "success": False,
            "reason": "Indeed automation not yet implemented",
            "action": "queue_for_manual",
            "link": job.get('apply_link')
        }


def send_application_notification(job: Dict, result: Dict):
    """Send notification about application result."""
    try:
        # Use Cherokee notification system
        requests.post(
            "http://192.168.132.223:8080/v1/notifications",
            json={
                "type": "job_application",
                "title": f"Job: {job['title']} at {job['company']}",
                "message": result.get('reason', 'Application processed'),
                "severity": "info" if result['success'] else "warning",
                "source": "job_automation"
            }
        )
    except Exception as e:
        print(f"[JOB] Notification error: {e}")
```

---

## Schema Addition

```sql
CREATE TABLE IF NOT EXISTS job_opportunities (
    id SERIAL PRIMARY KEY,
    source VARCHAR(32),
    job_title VARCHAR(256),
    company VARCHAR(128),
    apply_link TEXT,
    match_score FLOAT,
    action_taken VARCHAR(32),
    applied_at TIMESTAMP,
    result TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_job_source ON job_opportunities(source);
CREATE INDEX idx_job_score ON job_opportunities(match_score);
CREATE INDEX idx_job_action ON job_opportunities(action_taken);
```

---

## Security Considerations

1. **Email Credentials**: Store app password in environment variable, not config file
2. **Resume Protection**: Resume file should not be world-readable
3. **Rate Limiting**: Don't apply too fast - looks like bot behavior
4. **Logging**: Log all applications for audit trail

---

## Validation

```bash
# Test email reading (dry run)
python3 /ganuda/daemons/email_job_reader.py --dry-run

# Test job scoring
python3 -c "
from job_matcher import score_job
job = {'title': 'Senior TPM - AI/ML Platform', 'company': 'Google', 'body': 'LLM kubernetes python distributed systems'}
print(f'Score: {score_job(job)}')
"
```

---

## Files to Create

1. `/ganuda/config/email_config.json` - Email and job source configuration
2. `/ganuda/daemons/email_job_reader.py` - Email reader daemon
3. `/ganuda/lib/job_matcher.py` - Job scoring algorithm
4. `/ganuda/lib/job_applicator.py` - Application executor

## SQL to Run

1. Create `job_opportunities` table on bluefin

---

## Important Notes

- User MUST provide their email app password (not regular password)
- Gmail requires an "App Password" from Google security settings
- ZipRecruiter and Indeed API integrations require separate accounts/keys
- Initial version queues jobs for manual review rather than auto-applying

---

*For Seven Generations - Cherokee AI Federation*
*"The hunt that feeds many requires patience and precision"*
