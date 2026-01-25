# JR Instruction: SAG Email System Enhancement

**Priority**: P1 - High
**Assigned To**: Software Engineer Jr. / UI Jr.
**Created**: January 21, 2026
**Status**: Ready for Execution
**Kanban Tasks**: SAG-EMAIL-001, SAG-EMAIL-002

## Executive Summary

Enhance the SAG Unified Interface email system with:
1. Full email client GUI in the Email tab
2. IMAP daemon controls
3. AI-powered email analysis (priority, sentiment, action detection)
4. Systemd service for reliable daemon operation

## Current State

### Existing Code
- **Email Intelligence**: `/ganuda/home/dereadi/sag_unified_interface/email_intelligence.py`
- **Email Daemon**: `/ganuda/email_daemon/email_daemon.py`
- **SAG Interface**: `/ganuda/home/dereadi/sag_unified_interface/`
- **Database**: `triad_federation.emails` table on bluefin

### What Works
- Email polling via IMAP
- Basic storage in PostgreSQL
- Simple keyword-based priority detection
- Email Intelligence Manager queries

### What's Missing
- Full email client GUI (compose, reply, folders)
- Daemon start/stop controls in UI
- AI-powered analysis (beyond keywords)
- Systemd service for daemon
- Real-time updates to dashboard

## Implementation Tasks

### Task 1: Email Client GUI Enhancement

**Location**: `/ganuda/home/dereadi/sag_unified_interface/`

Add to the Email tab:

```
┌─────────────────────────────────────────────────────────────┐
│ Email Intelligence                                    [⚙️]  │
├─────────────────────────────────────────────────────────────┤
│ Daemon: [🟢 Running] [Stop] [Restart]    Last Poll: 2m ago │
├─────────────────────────────────────────────────────────────┤
│ Folders        │ Email List              │ Preview          │
│ ────────────── │ ─────────────────────── │ ──────────────── │
│ 📥 Inbox (12)  │ ⚡ VA Claims Update     │ From: VA.gov     │
│ ⭐ Starred     │    Subject line here    │ Date: Jan 21     │
│ 📤 Sent        │    Preview text...      │                  │
│ 🗑️ Trash       │                         │ [Full content    │
│ 🏷️ Action Req  │ 📧 Email from Joe       │  displayed here] │
│ 🏷️ High Prio   │    Another subject...   │                  │
│                │                         │ [Reply] [Forward]│
└─────────────────────────────────────────────────────────────┘
```

**Features Required**:
1. Folder navigation (virtual folders based on labels/tags)
2. Email list with thermal temperature color coding
3. Email preview pane
4. Compose new email modal
5. Reply/Forward functionality
6. Mark as read/unread, star, archive
7. Action required badge

### Task 2: Daemon Control Panel

Add daemon management to the Email tab header:

**API Endpoints to Create** (Flask routes):

```python
# /ganuda/home/dereadi/sag_unified_interface/app.py

@app.route('/api/email/daemon/status')
def get_daemon_status():
    """Check if email daemon is running"""
    # Check systemd service status or PID file
    pass

@app.route('/api/email/daemon/start', methods=['POST'])
def start_daemon():
    """Start the email daemon"""
    pass

@app.route('/api/email/daemon/stop', methods=['POST'])
def stop_daemon():
    """Stop the email daemon"""
    pass

@app.route('/api/email/daemon/restart', methods=['POST'])
def restart_daemon():
    """Restart the email daemon"""
    pass
```

### Task 3: AI Email Analysis

Enhance `/ganuda/email_daemon/email_daemon.py` with LLM-powered analysis:

**Analysis Categories**:
| Category | Description |
|----------|-------------|
| `priority` | 1-5 scale (1=urgent, 5=low) |
| `sentiment` | positive, neutral, negative, urgent |
| `action_type` | reply_needed, fyi, meeting_request, approval_needed, none |
| `summary` | 1-2 sentence summary |
| `entities` | Extract names, dates, amounts mentioned |

**Integration with LLM Gateway**:

```python
def analyze_email_with_llm(email_data: dict) -> dict:
    """
    Analyze email using Cherokee LLM Gateway

    Endpoint: http://192.168.132.223:8080/v1/chat/completions
    API Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5
    """
    prompt = f"""Analyze this email and respond with JSON only:

Subject: {email_data['subject']}
From: {email_data['from_address']}
Body: {email_data['body_text'][:1000]}

Respond with:
{{
    "priority": 1-5,
    "sentiment": "positive|neutral|negative|urgent",
    "action_type": "reply_needed|fyi|meeting_request|approval_needed|none",
    "summary": "1-2 sentence summary",
    "entities": ["extracted names, dates, etc"]
}}
"""
    # Call LLM Gateway
    # Parse JSON response
    # Return analysis dict
```

**Database Schema Update**:

```sql
-- Add columns to emails table if not exists
ALTER TABLE emails ADD COLUMN IF NOT EXISTS ai_priority INTEGER;
ALTER TABLE emails ADD COLUMN IF NOT EXISTS ai_sentiment VARCHAR(20);
ALTER TABLE emails ADD COLUMN IF NOT EXISTS ai_action_type VARCHAR(30);
ALTER TABLE emails ADD COLUMN IF NOT EXISTS ai_summary TEXT;
ALTER TABLE emails ADD COLUMN IF NOT EXISTS ai_entities JSONB;
ALTER TABLE emails ADD COLUMN IF NOT EXISTS ai_analyzed_at TIMESTAMP;
```

### Task 4: Systemd Service

Create systemd service for email daemon.

**Service File**: `/etc/systemd/system/cherokee-email-daemon.service`

```ini
[Unit]
Description=Cherokee Email Intelligence Daemon
After=network.target postgresql.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/email_daemon
Environment=PYTHONPATH=/ganuda
ExecStart=/home/dereadi/cherokee_venv/bin/python3 /ganuda/email_daemon/email_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Deployment Script**: `/ganuda/scripts/deploy_email_daemon_service.sh`

```bash
#!/bin/bash
# Deploy email daemon systemd service

sudo cp /ganuda/scripts/systemd/cherokee-email-daemon.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cherokee-email-daemon
sudo systemctl start cherokee-email-daemon
sudo systemctl status cherokee-email-daemon
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `/ganuda/home/dereadi/sag_unified_interface/templates/email_tab.html` | Modify | Enhanced email client UI |
| `/ganuda/home/dereadi/sag_unified_interface/static/js/email.js` | Create | Email client JavaScript |
| `/ganuda/home/dereadi/sag_unified_interface/app.py` | Modify | Add daemon control endpoints |
| `/ganuda/email_daemon/email_daemon.py` | Modify | Add AI analysis |
| `/ganuda/email_daemon/email_ai_analyzer.py` | Create | LLM analysis module |
| `/ganuda/scripts/systemd/cherokee-email-daemon.service` | Create | Systemd service |
| `/ganuda/scripts/deploy_email_daemon_service.sh` | Create | Deployment script |

## Testing

### Test 1: Daemon Controls
```bash
# Via API
curl http://192.168.132.223:4000/api/email/daemon/status
curl -X POST http://192.168.132.223:4000/api/email/daemon/restart
```

### Test 2: AI Analysis
```bash
# Test email analysis
cd /ganuda/email_daemon && python3 -c "
from email_ai_analyzer import analyze_email_with_llm
result = analyze_email_with_llm({
    'subject': 'URGENT: VA Claim Status Update',
    'from_address': 'va.gov',
    'body_text': 'Your claim has been approved...'
})
print(result)
"
```

### Test 3: Systemd Service
```bash
sudo systemctl status cherokee-email-daemon
journalctl -u cherokee-email-daemon -f
```

## Success Criteria

- [ ] Email client GUI displays emails from database
- [ ] Folder navigation works (Inbox, Starred, Action Required)
- [ ] Daemon start/stop/restart from UI works
- [ ] AI analysis populates priority, sentiment, action fields
- [ ] Systemd service starts on boot
- [ ] Real-time email count updates in dashboard

## Dependencies

- LLM Gateway running at http://192.168.132.223:8080
- PostgreSQL on bluefin with emails table
- SAG Unified Interface running at port 4000

---

*Cherokee AI Federation - For Seven Generations*
