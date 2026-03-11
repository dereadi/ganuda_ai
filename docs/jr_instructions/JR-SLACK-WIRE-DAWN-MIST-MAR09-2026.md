# Jr Instruction: Wire Slack Notifications into Dawn Mist Standup

**Council Vote:** dae9f2a065b4f3a0 (Slack Federation Wiring — Phase 1)
**Date:** March 9, 2026
**Priority:** 2 (Phase 1 — daily standup delivery)

## Objective

Wire `slack_federation.send()` into `council_dawn_mist.py` so that the daily 6:15 AM
standup summary is posted to #dawn-mist on Slack. Chief checks his phone while glamping —
this is the morning pulse he wants to see.

Format: readable but concise. Include real numbers (thermal count, pending tasks, vote count,
paper count). Not emoji-coded — just clean text with clear sections.

## Changes

File: `/ganuda/scripts/council_dawn_mist.py`

### Step 1: Add slack import after existing imports

<<<<<<< SEARCH
from ganuda_db import get_connection, get_dict_cursor, safe_thermal_write
from specialist_council import SpecialistCouncil
=======
from ganuda_db import get_connection, get_dict_cursor, safe_thermal_write
from specialist_council import SpecialistCouncil

try:
    from slack_federation import send as slack_send
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
>>>>>>> REPLACE

### Step 2: Add Slack notification after thermal memory write, before the systemd journal log line

<<<<<<< SEARCH
        # One-line summary for systemd journal
        concern_count = len([r for r in result.responses if r.has_concern])
=======
        # Post standup to #dawn-mist Slack channel
        if SLACK_AVAILABLE:
            try:
                slack_msg = (
                    f"*DAWN MIST — {datetime.now().strftime('%A %B %d')}*\n\n"
                    f"{forward}\n\n"
                    f"{backward}\n\n"
                    f"{pulse}\n\n"
                    f"_Council vote {result.audit_hash} | confidence {result.confidence}_"
                )
                slack_send("dawn-mist", slack_msg)
            except Exception as e:
                logger.warning("Slack dawn-mist post failed: %s", e)

        # One-line summary for systemd journal
        concern_count = len([r for r in result.responses if r.has_concern])
>>>>>>> REPLACE

## Verification

After applying, the next dawn mist run (6:15 AM CT or manual trigger) should post to #dawn-mist.
Manual test:
```text
python3 /ganuda/scripts/council_dawn_mist.py
```

Check #dawn-mist channel on Slack for the standup summary.
