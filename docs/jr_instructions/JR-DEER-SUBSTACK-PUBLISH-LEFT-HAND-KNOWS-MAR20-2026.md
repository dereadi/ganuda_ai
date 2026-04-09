# Jr Instruction: Publish "The Left Hand Knows" to Substack via Pipeline

**Ticket**: SUBSTACK-PUBLISH-002
**Estimated SP**: 1
**Assigned**: Spider (Integration Wiring) + Deer (Content Review)
**Depends On**: SUBSTACK-PUBLISH-001 P-3 (library installed, credentials wired)
**Priority**: P1 — Partner wants this published today (Mar 20 2026)
**Source Draft**: `/ganuda/docs/blog/DRAFT-THE-LEFT-HAND-KNOWS-MAR20-2026.md`

---

## Objective

Push "The Left Hand Knows" as a Substack draft via the bmasass SSH proxy pipeline, then notify Partner for review and publish approval. This doubles as the first real-content test of the Substack publishing pipeline (prior tests were throwaway drafts).

---

## Content Details

**Title**: The Left Hand Knows
**Subtitle**: Two signals on a Friday morning. A Senator. A systems ecologist. And a question about what AI actually needs.
**Audience**: everyone (public)

**Content source**: The markdown body of `/ganuda/docs/blog/DRAFT-THE-LEFT-HAND-KNOWS-MAR20-2026.md`, starting from "Two things landed this morning..." through "...Go watch Nate's video. Then go stack something."

**DO NOT include**:
- The YAML frontmatter (title/subtitle/author/date/status/platform/voice lines)
- The "Substack Notes" section (those are separate posts, Partner will publish manually)
- The "Publishing Notes" section (internal guidance only)

---

## Steps

### Step 1: Verify bmasass is reachable

```bash
ssh -o ConnectTimeout=5 dereadi@192.168.132.21 echo "bmasass reachable"
```

If LAN fails, fall back to Tailscale:
```bash
ssh -o ConnectTimeout=5 dereadi@100.103.27.106 echo "bmasass reachable"
```

If BOTH fail: STOP. Notify Partner that bmasass is unreachable. Do not attempt alternative publish methods.

### Step 2: Extract clean content from draft

Read `/ganuda/docs/blog/DRAFT-THE-LEFT-HAND-KNOWS-MAR20-2026.md` and extract ONLY the publishable body (from "Two things landed this morning..." through the sign-off).

**PII/infra scrub checklist** (manual verification before automated scrub):
- [ ] No internal IPs (192.168.x.x, 10.100.0.x, 100.x.x.x)
- [ ] No node names (redfin, bluefin, greenfin, owlfin, eaglefin, bmasass, sasass)
- [ ] No internal paths (/ganuda/..., /Users/Shared/ganuda/...)
- [ ] No credentials or API keys
- [ ] No thermal IDs or council vote hashes
- [ ] No internal jargon that exposes architecture (DCs, council topology, Jr executor)

**Expected**: The draft was written for external consumption and should pass clean. The only technical reference is "six-node AI federation" and "RTX Pro 6000" which are intentionally public.

### Step 3: Create Substack draft via pipeline

```python
import sys
sys.path.insert(0, '/ganuda')
from lib.substack_publisher import SubstackPublisher

pub = SubstackPublisher(enabled=True)

title = "The Left Hand Knows"
subtitle = "Two signals on a Friday morning. A Senator. A systems ecologist. And a question about what AI actually needs."

# Read the clean content (body only, no frontmatter or notes sections)
with open('/ganuda/docs/blog/DRAFT-THE-LEFT-HAND-KNOWS-MAR20-2026.md') as f:
    raw = f.read()

# Extract body: starts after the "---" following Voice line, ends before "## Substack Notes"
lines = raw.split('\n')
body_start = None
body_end = None
hr_count = 0
for i, line in enumerate(lines):
    if line.strip() == '---':
        hr_count += 1
        if hr_count == 2:  # Second --- is end of frontmatter
            body_start = i + 1
    if line.strip() == '## Substack Notes (3 per strategy)':
        body_end = i
        break

if body_start and body_end:
    content = '\n'.join(lines[body_start:body_end]).strip()
else:
    print("ERROR: Could not extract body from draft. Manual intervention needed.")
    sys.exit(1)

result = pub.create_draft(title=title, subtitle=subtitle, content=content)
print(result)
```

### Step 4: Verify draft appeared

```python
drafts = pub.list_drafts()
print(drafts)
# Confirm "The Left Hand Knows" appears in draft list
```

### Step 5: Notify Partner

Send notification via Slack (#deer-signals) or Telegram:

> Substack draft ready: **"The Left Hand Knows"**
> Two signals on a Friday morning — Sanders + Hagens + the existence proof.
> Review in your Substack dashboard. Reply PUBLISH when ready.

---

## Links to Include in Published Post

When Partner reviews in the Substack editor, these links should be verified/added:

1. **The Great Simplification**: https://www.thegreatsimplification.com — linked on Nate's name and the "Watch it" call
2. **Sanders interview**: Link to the video if Partner has the URL (not included in transcript)
3. **ganuda.us**: NOT explicitly linked in the body (per Publishing Notes — let readers find it through Substack profile). But the Substack profile should have ganuda.us in the bio.

---

## After Publish: Notes Schedule

Partner will publish the 3 Substack Notes manually per the notes strategy in the draft:

| Note | Timing | Content |
|------|--------|---------|
| **The Question** | Same day, 2-4 hours after publish | Sanders/Claude trust quote → "What if the answer isn't better safeguards but a fundamentally different architecture?" |
| **The Quote** | Next day AM | "We build the new structures while the old ones are still standing." — Nate Hagens |
| **The Builder Hook** | Next day PM | Solar panels: mining → sovereign inference. Same sun. Different purpose. |

---

## Verification

1. Draft appears in Partner's Substack dashboard with correct title and subtitle
2. Content is clean — no PII, no internal jargon, no infrastructure details
3. Links render correctly (TGS website)
4. Formatting survived the markdown → Substack conversion (check paragraph breaks, horizontal rules, emphasis)
5. Partner reviews and approves before publish

---

## What NOT To Do

- Do NOT auto-publish. Draft only. Partner approves.
- Do NOT include the Notes section in the main post body
- Do NOT include internal Publishing Notes
- Do NOT retry more than twice if SSH proxy fails — notify Partner instead
- Do NOT modify the draft content without Deer editorial review
- Do NOT skip the PII scrub checklist even though the content looks clean
