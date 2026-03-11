# [RECURSIVE] Wire Slack into Council vote pipeline - Step 1

**Parent Task**: #1156
**Auto-decomposed**: 2026-03-09T14:13:24.658214
**Original Step Title**: Add slack import at module level, near existing imports

---

### Step 1: Add slack import at module level, near existing imports

Find the block of imports near the top of the file and add the slack import.

<<<<<<< SEARCH
import hashlib
import json
import logging
=======
import hashlib
import json
import logging

try:
    from slack_federation import notify_council_vote as _slack_notify_vote
    _SLACK_AVAILABLE = True
except ImportError:
    _SLACK_AVAILABLE = False
>>>>>>> REPLACE
