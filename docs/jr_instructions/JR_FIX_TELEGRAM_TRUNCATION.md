# JR INSTRUCTIONS: Fix Telegram Message Truncation
## Priority: 1 (Urgent)
## December 17, 2025

### PROBLEM
Telegram messages are getting truncated when email subjects or sender addresses contain Markdown special characters (`*`, `_`, `[`, `]`, `` ` ``, etc.). The Markdown parser breaks and truncates the message.

### SOLUTION
Escape Markdown special characters in user-provided content OR switch to HTML parse mode (more forgiving).

---

## TASK 1: Update telegram_alerts.py on redfin

**File:** `/ganuda/email_daemon/telegram_alerts.py`

**Replace entire file with:**

```python
#!/usr/bin/env python3
"""Telegram Alert Module for Job Emails - Fixed for Markdown escaping"""

import os
import re
import requests

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '8025375307')

CLASS_EMOJI = {'offer': '💰', 'interview': '📅', 'next_steps': '➡️', 'recruiter': '👤', 'application': '📝', 'rejection': '❌'}
PRIORITY_EMOJI = {1: '🔴', 2: '🟠', 3: '🟡', 4: '🔵', 5: '⚪'}

def escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram HTML parse mode."""
    if not text:
        return ''
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;'))

def send_job_alert(email: dict, classification: str, priority: int) -> bool:
    """Send job alert via Telegram using HTML parse mode (more forgiving)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    emoji = CLASS_EMOJI.get(classification, '📧')
    prio = PRIORITY_EMOJI.get(priority, '⚪')

    # Use HTML parse mode - more forgiving than Markdown
    from_addr = escape_html(email.get('from_address', 'Unknown'))
    subject = escape_html(email.get('subject', 'No subject'))
    company = escape_html(email.get('job_company', ''))
    position = escape_html(email.get('job_position', ''))

    message = f"{emoji} {prio} <b>Job Alert: {classification.replace('_', ' ').title()}</b>\n\n"
    message += f"<b>From:</b> {from_addr}\n"
    message += f"<b>Subject:</b> {subject}\n"
    if company:
        message += f"<b>Company:</b> {company}\n"
    if position:
        message += f"<b>Position:</b> {position}\n"

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'  # Changed from Markdown to HTML
            },
            timeout=10
        )
        if response.status_code != 200:
            print(f"Telegram API error: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def send_plain_alert(message: str) -> bool:
    """Send a plain text alert (no formatting) - guaranteed to work."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message
                # No parse_mode = plain text
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False
```

---

## TASK 2: Test the fix

```bash
# SSH to redfin and test
cd /ganuda/email_daemon
python3 -c "
from telegram_alerts import send_job_alert, send_plain_alert

# Test with problematic characters
test_email = {
    'from_address': 'jobs@company_name.com',
    'subject': 'RE: Your Application [Senior Dev] - Next Steps!',
    'job_company': 'Tech*Corp',
    'job_position': 'Senior_Developer (Remote)'
}
result = send_job_alert(test_email, 'interview', 1)
print(f'Alert sent: {result}')
"
```

---

## TASK 3: Sync to tpm-macbook

```bash
scp /ganuda/email_daemon/telegram_alerts.py dereadi@<tpm-macbook-ip>:/Users/Shared/ganuda/email_daemon/
```

---

## SUCCESS CRITERIA
1. Telegram messages no longer truncate
2. Special characters in subjects display correctly
3. HTML formatting renders properly (bold labels)

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*
