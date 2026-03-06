# [RECURSIVE] Deer Email Triage: LLM classification + Telegram alerts (requeue no-TEG) - Step 2

**Parent Task**: #1061
**Auto-decomposed**: 2026-03-05T09:44:05.197695
**Original Step Title**: Add Telegram alert for ACTIONABLE emails in store_email

---

### Step 2: Add Telegram alert for ACTIONABLE emails in store_email

File: `/ganuda/email_daemon/gmail_api_daemon.py`

```
<<<<<<< SEARCH
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return result is not None  # True if new email inserted
=======
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        is_new = result is not None
        # Telegram alert for actionable emails
        if is_new and analysis.get('classification') == 'actionable':
            try:
                from telegram_alerts import send_plain_alert
                action = analysis.get('action_required_text', 'Action needed')
                deadline = analysis.get('action_deadline', '')
                deadline_str = f'\nDeadline: {deadline}' if deadline else ''
                alert_msg = (
                    f"ACTIONABLE EMAIL\n"
                    f"From: {email_data.get('from_address', '?')}\n"
                    f"Subject: {email_data.get('subject', '?')}\n"
                    f"Action: {action}{deadline_str}\n"
                    f"Priority: {analysis.get('priority_score', '?')}/5"
                )
                send_plain_alert(alert_msg)
                self.logger.info(f'Telegram alert sent for: {email_data["subject"][:50]}')
            except Exception as e:
                self.logger.warning(f'Telegram alert failed: {e}')

        return is_new
>>>>>>> REPLACE
```
