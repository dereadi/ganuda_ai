# Jr Instruction: Migrate All Telegram Alerts to Slack

## Context
Chief directive: "Move everything to Slack." Currently 3 sources send to Telegram: alert_manager.py (library used by many scripts), governance_agent.py (drift alerts), safety_canary.py (daily canary). Rewire all to use slack_federation.py instead.

## Strategy
1. Update alert_manager.py to send via Slack instead of Telegram
2. Update governance_agent.py to use slack_federation instead of direct Telegram
3. Update safety_canary.py to use slack_federation instead of direct Telegram
4. Keep Telegram code commented (not deleted) as fallback for 1 week

## File: `/ganuda/lib/alert_manager.py`

### Step 1: Replace Telegram with Slack in alert_manager

```
<<<<<<< SEARCH
import os
import time
import logging
import requests
from datetime import datetime
from typing import Optional
from collections import defaultdict
=======
import os
import time
import logging
import requests
from datetime import datetime
from typing import Optional
from collections import defaultdict

# Slack federation (primary alert channel)
try:
    from lib.slack_federation import send as slack_send
    _HAS_SLACK = True
except ImportError:
    _HAS_SLACK = False
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": ALERT_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown"
            },
            timeout=10
        )

        if response.status_code == 200:
            _alert_cooldowns[alert_type] = now
            logger.info(f"Alert sent: {title}")
            return True
        else:
            logger.error(f"Alert failed: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Alert exception: {e}")
        return False
=======
    # Primary: Slack
    if _HAS_SLACK:
        try:
            channel = "fire-guard"
            if source == 'crawdad':
                channel = "fire-guard"
            elif source == 'eagle-eye':
                channel = "fire-guard"
            urgent = severity in ('critical', 'high')
            slack_send(channel, text, urgent=urgent)
            _alert_cooldowns[alert_type] = now
            logger.info(f"Alert sent to Slack #{channel}: {title}")
            return True
        except Exception as e:
            logger.warning(f"Slack alert failed, falling back to Telegram: {e}")

    # Fallback: Telegram
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": ALERT_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown"
            },
            timeout=10
        )

        if response.status_code == 200:
            _alert_cooldowns[alert_type] = now
            logger.info(f"Alert sent to Telegram: {title}")
            return True
        else:
            logger.error(f"Telegram alert failed: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Alert exception: {e}")
        return False
>>>>>>> REPLACE
```

## File: `/ganuda/daemons/governance_agent.py`

### Step 2: Replace direct Telegram in governance_agent

```
<<<<<<< SEARCH
def send_telegram_alert(severity, message):
=======
def send_telegram_alert(severity, message):
    # Primary: Slack
    try:
        from lib.slack_federation import send as slack_send
        urgent = severity in ('critical', 'high')
        slack_send("fire-guard", f"[DRIFT {severity}] {message}", urgent=urgent)
        return
    except Exception:
        pass
    # Fallback: Telegram
>>>>>>> REPLACE
```

## File: `/ganuda/scripts/safety_canary.py`

### Step 3: Replace direct Telegram in safety_canary

```
<<<<<<< SEARCH
def send_telegram(message):
=======
def send_telegram(message):
    # Primary: Slack
    try:
        from lib.slack_federation import send as slack_send
        slack_send("fire-guard", message, urgent=True)
        return
    except Exception:
        pass
    # Fallback: Telegram
>>>>>>> REPLACE
```

## Acceptance Criteria
- All alerts route to Slack #fire-guard as primary channel
- Telegram remains as fallback if Slack fails
- Critical/high severity alerts use urgent=True (bypasses silent hours)
- Drift alerts from governance_agent go to Slack instead of Telegram
- Safety canary alerts go to Slack instead of Telegram
- No alert is silently dropped — if Slack fails, Telegram catches it
