# JR INSTRUCTION: Publish "The Left Hand Knows" to Substack

**Task ID**: SUBSTACK-PUBLISH-002
**Priority**: P3
**SP**: 1
**Depends On**: P-3 pipeline verified Mar 26 2026 (draft 192273361 created/deleted successfully)
**Approval Gate**: Partner MUST approve before publish. Draft-only until then.

## Context

P-3 pipeline test passed. redfin → SSH (Tailscale) → bmasass → Chrome → Substack API is working.
Profile confirmed: derpatodiablo, pub_id 8354801, user_id 396174216.
Kill switch verified. PII scrub logged warning (presidio not installed — content is hand-written by Deer so no PII risk on this post).

## Step 1: Create Draft

The content is at `/ganuda/docs/blog/DRAFT-THE-LEFT-HAND-KNOWS-MAR20-2026.md`.

**IMPORTANT**: Only lines 13-67 go to Substack. Lines 1-11 are metadata. Lines 69-95 are internal publishing notes and Substack Notes strategy — these NEVER leave the federation.

```python
import sys
sys.path.insert(0, '/ganuda/lib')
from substack_publisher import SubstackPublisher

pub = SubstackPublisher(enabled=True)

# Content from lines 13-67 of the draft
title = "The Left Hand Knows"
subtitle = "Two signals on a Friday morning. A Senator. A systems ecologist. And a question about what AI actually needs."

# Read content from file, extract lines 13-67 only
with open('/ganuda/docs/blog/DRAFT-THE-LEFT-HAND-KNOWS-MAR20-2026.md') as f:
    lines = f.readlines()
content = ''.join(lines[12:67])  # 0-indexed: lines 13-67

result = pub.create_draft(title, subtitle, content)
print(result)
```

## Step 2: Notify Partner

After draft is created, notify via Slack or Telegram:
- "Deer draft 'The Left Hand Knows' is in your Substack dashboard. Review and approve for publish."
- Include the draft ID from the result.

## Step 3: Partner Approves → Publish

Substack publish is manual from the dashboard (the proxy does not have a publish endpoint — by design, per Crawdad audit condition). Partner clicks Publish in the Substack editor.

## Step 4: Post-Publish Notes (Manual, per strategy)

After publish, three Notes per `/ganuda/docs/content/substack_notes_strategy.md`:
1. **Same day, 2-4 hours after**: The Question (Sanders/Claude quote + "What if the answer isn't better safeguards?")
2. **Next day AM**: The Quote (Hagens: "We build the new structures while the old ones are still standing.")
3. **Next day PM**: The Builder Hook (Solar panels → AI federation)

These are manual posts from the Substack Notes UI.

## Step 5: Close SUBSTACK-DEER ticket

After publish + all 3 Notes:
- Update kanban_ticket_log status to 'done'
- Thermalize with tags [substack, deer, left_hand_knows, first_publish], temp 65
