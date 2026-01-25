# JR Instruction: VetAssist Notification System

## Metadata
```yaml
task_id: vetassist_notifications
priority: 2
assigned_to: VetAssist Jr.
target: backend + frontend
estimated_effort: medium
```

## Overview

Implement email notifications for important events. Future: SMS and push notifications.

## Notification Types

| Type | Trigger | Default |
|------|---------|---------|
| Welcome | User registration | ON |
| Claim reminder | Workbench claim inactive 7 days | ON |
| ITF expiration | Intent to file expires in 30 days | ON |
| Document uploaded | New document added | OFF |
| Profile incomplete | Profile < 50% complete after 7 days | ON |
| Security alert | New device login | ON |

## Database Schema (bluefin)

```sql
-- Notification preferences
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id),
    email_enabled BOOLEAN DEFAULT TRUE,

    -- Per-type preferences
    welcome BOOLEAN DEFAULT TRUE,
    claim_reminder BOOLEAN DEFAULT TRUE,
    itf_expiration BOOLEAN DEFAULT TRUE,
    document_uploaded BOOLEAN DEFAULT FALSE,
    profile_incomplete BOOLEAN DEFAULT TRUE,
    security_alert BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Notification log
CREATE TABLE notifications_sent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    notification_type VARCHAR(50),
    channel VARCHAR(20),  -- 'email', 'sms', 'push'
    subject VARCHAR(255),
    sent_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20),  -- 'sent', 'failed', 'bounced'
    error_message TEXT
);

-- Scheduled notifications
CREATE TABLE scheduled_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    notification_type VARCHAR(50),
    scheduled_for TIMESTAMP,
    data JSONB,
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'sent', 'cancelled'
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Backend Implementation

### Email Service

```python
# services/notifications.py
from email.mime.text import MIMEText
import aiosmtplib

class NotificationService:
    def __init__(self, smtp_host, smtp_port, smtp_user, smtp_pass):
        self.smtp_config = {...}

    async def send_email(self, to: str, subject: str, body: str, html: str = None):
        # Send via SMTP
        pass

    async def send_notification(self, user_id: UUID, notification_type: str, data: dict):
        user = await get_user(user_id)
        prefs = await get_notification_prefs(user_id)

        if not prefs.email_enabled:
            return

        if not getattr(prefs, notification_type, False):
            return

        template = self.get_template(notification_type)
        subject, body = template.render(data)

        await self.send_email(user.email, subject, body)
        await self.log_notification(user_id, notification_type, 'email', subject)
```

### Email Templates

```python
# templates/notifications/
TEMPLATES = {
    'welcome': {
        'subject': 'Welcome to VetAssist',
        'body': '''
Hello {first_name},

Welcome to VetAssist! We're here to help you navigate your VA disability claim.

Get started:
- Complete your profile: {profile_url}
- Try our calculator: {calculator_url}
- Chat with our AI: {chat_url}

Thank you for your service.

- The VetAssist Team
'''
    },
    'claim_reminder': {
        'subject': 'Your claim "{claim_name}" needs attention',
        'body': '''
Hello {first_name},

Your claim "{claim_name}" hasn't been updated in {days} days.

Continue working on it: {claim_url}

- The VetAssist Team
'''
    },
    'itf_expiration': {
        'subject': 'Your Intent to File expires in {days} days',
        'body': '''
Hello {first_name},

Your Intent to File (ITF) expires on {expiration_date}.

Make sure to submit your claim before then to protect your effective date.

Review your claim: {claim_url}

- The VetAssist Team
'''
    },
    'security_alert': {
        'subject': 'New login to your VetAssist account',
        'body': '''
Hello {first_name},

We detected a new login to your account:

- Time: {login_time}
- Location: {location}
- Device: {device}

If this wasn't you, please change your password immediately: {security_url}

- The VetAssist Team
'''
    }
}
```

### API Endpoints

```python
# Get notification preferences
@router.get("/notifications/preferences")
async def get_preferences(user: User = Depends(get_current_user)):
    return await get_notification_prefs(user.id)

# Update preferences
@router.put("/notifications/preferences")
async def update_preferences(prefs: NotificationPrefsUpdate, user: User = Depends(get_current_user)):
    return await update_notification_prefs(user.id, prefs)

# Get notification history
@router.get("/notifications/history")
async def get_history(user: User = Depends(get_current_user), limit: int = 20):
    return await get_sent_notifications(user.id, limit)
```

### Background Worker

```python
# workers/notification_worker.py
async def process_scheduled_notifications():
    """Run every 15 minutes via cron/systemd timer"""
    pending = await get_pending_notifications()
    for notif in pending:
        if notif.scheduled_for <= datetime.utcnow():
            await notification_service.send_notification(
                notif.user_id,
                notif.notification_type,
                notif.data
            )
            await mark_notification_sent(notif.id)
```

## Frontend

### Settings Page

```tsx
<NotificationSettings>
  <Toggle
    label="Email notifications"
    checked={prefs.email_enabled}
    onChange={toggleEmail}
  />

  <h3>Notification Types</h3>

  <Toggle label="Claim reminders" checked={prefs.claim_reminder} />
  <Toggle label="ITF expiration warnings" checked={prefs.itf_expiration} />
  <Toggle label="Security alerts" checked={prefs.security_alert} />
  <Toggle label="Document uploads" checked={prefs.document_uploaded} />
</NotificationSettings>
```

## Environment Variables

```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=vetassist@cherokee.ai
SMTP_PASS=<secret>
SMTP_FROM=VetAssist <noreply@vetassist.cherokee.ai>
```

## Success Criteria

- [ ] Welcome email sent on registration
- [ ] Users can manage notification preferences
- [ ] Claim reminders sent after 7 days inactivity
- [ ] Security alerts on new device login
- [ ] All sent notifications logged
- [ ] Unsubscribe link in every email

---

*Cherokee AI Federation - For the Seven Generations*
