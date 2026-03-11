# Jr Instruction: Wire Slack Notifications into Fire Guard

**Council Vote:** dae9f2a065b4f3a0 (Slack Federation Wiring — Phase 1)
**Date:** March 9, 2026
**Priority:** 1 (Phase 1 — critical alerting)

## Objective

Wire `slack_federation.notify_fire_guard()` into `fire_guard.py` so that service alerts
are pushed to the #fire-guard Slack channel in addition to thermal memory storage.

Messages should be terse with real numbers — e.g. "3 ALERT(S): LOCAL DOWN: vllm.service; REMOTE DOWN: bluefin/PostgreSQL (192.168.132.222:5432)"

## Changes

File: `/ganuda/scripts/fire_guard.py`

### Step 1: Add import after existing imports

<<<<<<< SEARCH
import hashlib
import json
import os
import re
import socket
import subprocess
from datetime import datetime
=======
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, '/ganuda/lib')
>>>>>>> REPLACE

### Step 2: Add Slack notification in store_alerts function, after thermal memory write

<<<<<<< SEARCH
    cur.execute("""INSERT INTO thermal_memory_archive
        (original_content, temperature_score, sacred_pattern, memory_hash, domain_tag, tags, metadata)
        VALUES (%s, 85, false, %s, 'fire_guard', %s, %s::jsonb)
        ON CONFLICT (memory_hash) DO NOTHING""",
        (content, memory_hash,
         ['fire_guard', 'alert', 'health'],
         json.dumps({"source": "fire_guard", "alerts": results["alerts"]})))
    conn.commit()
    cur.close()
    conn.close()
=======
    cur.execute("""INSERT INTO thermal_memory_archive
        (original_content, temperature_score, sacred_pattern, memory_hash, domain_tag, tags, metadata)
        VALUES (%s, 85, false, %s, 'fire_guard', %s, %s::jsonb)
        ON CONFLICT (memory_hash) DO NOTHING""",
        (content, memory_hash,
         ['fire_guard', 'alert', 'health'],
         json.dumps({"source": "fire_guard", "alerts": results["alerts"]})))
    conn.commit()
    cur.close()
    conn.close()

    # Slack notification — terse, real numbers, urgent bypass for silent hours
    try:
        from slack_federation import notify_fire_guard
        alert_count = len(results["alerts"])
        slack_msg = f"{alert_count} ALERT(S): " + "; ".join(results["alerts"])
        notify_fire_guard(slack_msg, urgent=True)
    except Exception as e:
        # Slack is best-effort — never let it break Fire Guard
        import logging
        logging.getLogger("fire_guard").warning("Slack notify failed: %s", e)
>>>>>>> REPLACE

## Verification

After applying, run:
```text
python3 /ganuda/scripts/fire_guard.py
```

If there are active alerts, they should appear in #fire-guard on Slack.
If all services are healthy, no Slack message is sent (by design — no noise).
