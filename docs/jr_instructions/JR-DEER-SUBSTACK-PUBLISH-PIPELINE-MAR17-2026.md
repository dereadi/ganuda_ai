# Jr Instruction: Deer Substack Publishing Pipeline

**Ticket**: SUBSTACK-PUBLISH-001
**Estimated SP**: 3
**Assigned**: Deer (Content/Communications) + Spider (Integration Wiring)
**Blocked By**: ~~SUBSTACK-AUDIT-001~~ **CLEARED WITH CONDITIONS** (Mar 17 2026)
**Audit Report**: `/ganuda/docs/audits/AUDIT-PYTHON-SUBSTACK-MAR2026.md`
**Council Vote**: #9fc9b98bd7368cb7 — REVIEW REQUIRED → Crawdad cleared → PROCEED

---

## Crawdad Audit Conditions (MANDATORY — baked into implementation)

1. **NEVER pass untrusted input as `base_url`** — hardcode or use default
2. **Use cookie-based auth** (`cookies_path`) over email/password where possible
3. **If using `export_cookies()`** — chmod output file to 0o600 immediately
4. **Do NOT enable `debug=True`** in production — session cookies appear in debug logs
5. **Pin version** to 0.1.18 — review any updates before upgrading
6. **Store credentials in env vars** via secrets_loader, never in source code

---

## P-Day Countdown

| Step | What | Blocked By | Status |
|------|------|------------|--------|
| **P-3** | Install library (pinned 0.1.18), wire credentials, draft-only test | None — **UNBLOCKED** | READY |
| **P-2** | Build publish service — web_content DB → Substack draft pipeline + PII scrub | P-3 | WAITING |
| **P-1** | Human-in-loop approval gate, canary check, Fire Guard health check | P-2 | WAITING |
| **P-Day** | First real blog post published to Substack from federation | P-1 + Partner approval | WAITING |

**Current position: P-3 READY — Crawdad cleared Mar 17 2026**

---

## Objective

Extend Deer's content pipeline so blog posts flow from the federation to Substack automatically. Write once (web_content DB for ganuda.us) → optionally publish to Substack. Human-in-loop approval required before any post goes live on Substack. Deer owns editorial, Spider owns wiring.

## Context

- Partner has a Substack account
- `python-substack` (ma2za) supports draft creation, rich formatting, and publish workflow
- Existing pipeline: `publish_web_content.py` → `web_content` table → materializer → ganuda.us
- New pipeline adds a Substack leg: same content, second channel
- **Kill switch**: `substack.enabled: false` in harness config — Turtle's standard pattern

## Implementation

### P-3: Foundation (after Crawdad clearance)

1. **Install python-substack** on redfin (Deer's home node), **pinned to audited version**:
```bash
pip install --user python-substack==0.1.18
```

2. **Wire credentials** through secrets_loader (three-tier: file → env → vault):
Add to `/ganuda/config/secrets.env`:
```bash
SUBSTACK_EMAIL=<partner's email>
SUBSTACK_PASSWORD=<set via Substack "Set a new password" flow>
SUBSTACK_PUBLICATION_URL=<partner's substack URL>
SUBSTACK_COOKIES_PATH=/ganuda/config/.substack_cookies.json
```

**NOTE**: After first successful login, the publisher exports session cookies to `SUBSTACK_COOKIES_PATH` with 0600 permissions. Subsequent connections use cookies (Crawdad condition #2). Password is only needed for initial auth or cookie expiry.

3. **Create `/ganuda/lib/substack_publisher.py`**:
```python
"""
Substack Publisher — Deer's content pipeline extension.
Publishes blog posts to Substack via python-substack (v0.1.18, pinned).
Council vote #9fc9b98bd7368cb7. Crawdad audit CLEARED WITH CONDITIONS Mar 17 2026.
Audit: /ganuda/docs/audits/AUDIT-PYTHON-SUBSTACK-MAR2026.md

DRAFT-ONLY in P-3. Publish enabled at P-1.

Crawdad conditions enforced:
  - base_url hardcoded (never from untrusted input)
  - Cookie auth preferred over password auth
  - debug=False always in production
  - Version pinned to 0.1.18
  - Credentials from secrets_loader only
"""

from substack import Api, Post
from lib.secrets_loader import get_secret
from lib.chain_protocol import tag_provenance, meter_call
from lib.ganuda_pii.service import PIIService
import logging
import os

logger = logging.getLogger('substack_publisher')

# Crawdad condition #1: hardcoded base_url, NEVER from user input
SUBSTACK_BASE_URL = "https://substack.com/api/v1"

# Crawdad condition #4: NEVER enable debug in production
SUBSTACK_DEBUG = False


class SubstackPublisher:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._api = None
        self._pii = PIIService()  # Outbound PII scrub

    def _connect(self):
        if self._api is None:
            publication_url = get_secret('SUBSTACK_PUBLICATION_URL')
            cookies_path = get_secret('SUBSTACK_COOKIES_PATH')

            # Crawdad condition #2: prefer cookie auth over password
            if cookies_path and os.path.exists(cookies_path):
                self._api = Api(
                    cookies_path=cookies_path,
                    publication_url=publication_url,
                    debug=SUBSTACK_DEBUG,
                )
                logger.info("Substack connected via cookie auth")
            else:
                # Fallback to password auth
                self._api = Api(
                    email=get_secret('SUBSTACK_EMAIL'),
                    password=get_secret('SUBSTACK_PASSWORD'),
                    publication_url=publication_url,
                    debug=SUBSTACK_DEBUG,
                )
                logger.info("Substack connected via password auth (cookie file not found)")

                # Crawdad condition #3: export cookies with restricted permissions
                if cookies_path:
                    self._api.export_cookies(cookies_path)
                    os.chmod(cookies_path, 0o600)
                    logger.info(f"Session cookies exported to {cookies_path} (0600)")

        return self._api

    def _scrub_content(self, content: str) -> str:
        """PII + infrastructure scrub before content leaves the federation."""
        # Scrub PII (SSN, phone, email, etc.)
        scrubbed = self._pii.scrub(content)
        # TODO P-2: wire chain_protocol.outbound_scrub() for infra terms
        return scrubbed

    def create_draft(self, title: str, subtitle: str, content: str,
                     audience: str = "everyone") -> dict:
        """Create a draft on Substack. Does NOT publish."""
        if not self.enabled:
            logger.info("Substack publishing disabled (kill switch)")
            return {"status": "disabled"}

        # Scrub before anything leaves the federation
        clean_title = self._scrub_content(title)
        clean_subtitle = self._scrub_content(subtitle)
        clean_content = self._scrub_content(content)

        api = self._connect()
        user_id = api.get_user_id()

        post = Post(
            title=clean_title,
            subtitle=clean_subtitle,
            user_id=user_id,
            audience=audience,
            write_comment_permissions="everyone",
        )

        # Add content as paragraph blocks
        # TODO P-2: Parse HTML to Substack block format
        post.add({'type': 'paragraph', 'content': clean_content})

        draft = api.post_draft(post.get_draft())
        draft_id = draft.get("id")

        logger.info(f"Substack draft created: {draft_id} — '{clean_title}'")
        meter_call("substack_publisher", cost_estimate=0.0)

        return {
            "status": "draft_created",
            "draft_id": draft_id,
            "title": clean_title,
        }

    def publish_draft(self, draft_id: str) -> dict:
        """Publish an existing draft. Requires human approval first."""
        if not self.enabled:
            return {"status": "disabled"}

        api = self._connect()
        api.prepublish_draft(draft_id)
        api.publish_draft(draft_id)

        tag_provenance(
            source="substack_publisher",
            action="publish",
            metadata={"draft_id": draft_id}
        )
        logger.info(f"Substack draft {draft_id} PUBLISHED")

        return {"status": "published", "draft_id": draft_id}
```

4. **Test draft-only mode** with a throwaway post:
```python
pub = SubstackPublisher(enabled=True)
result = pub.create_draft(
    title="[TEST] Federation Pipeline Test — Delete Me",
    subtitle="Automated draft creation test",
    html_content="This is a test draft from the federation content pipeline. Safe to delete."
)
print(result)
# Verify draft appears in Partner's Substack dashboard
# DELETE the test draft manually
```

### P-2: Core Pipeline

1. **HTML-to-Substack block converter**: Parse the HTML from web_content into Substack's block format (paragraphs, headings, images, links). The `python-substack` library supports:
   - `paragraph`, `heading`, `captionedImage`, `paywall`
   - Markdown-to-post conversion (may be easier than HTML parsing)

2. **Wire into web_content pipeline**: Add optional `publish_to_substack` flag to the web_content workflow:
   - When a blog post is published to ganuda.us AND `publish_to_substack=true`
   - Create a Substack draft automatically
   - Do NOT auto-publish — draft only, awaiting human approval

3. **Canary draft**: Every draft gets a verification step — fetch it back from Substack API and compare title/content to confirm it arrived intact. Eagle Eye's silent-publish-failure concern.

### P-1: Guardrails + Integration

1. **Human-in-loop approval gate**:
   - Draft created → Telegram/Slack notification to Partner: "New Substack draft ready: [title]. Reply PUBLISH to go live."
   - Partner replies PUBLISH → `publish_draft()` called
   - Partner replies DELETE → draft removed
   - No response after 48 hours → draft expires, Deer notified

2. **Fire Guard health check**:
   - Add Substack API connectivity check to necklace
   - Check: Can we authenticate? Is the session valid?
   - Alert if session cookie expires or auth fails

3. **Kill switch verification**:
   - `substack.enabled: false` → service returns "disabled" on all calls
   - Test: Disable → attempt publish → verify nothing reaches Substack

4. **Owl pre-flight**:
   - Content must pass PII scrub before Substack (Crawdad's gate, reuse ganuda_pii)
   - No internal IPs, node names, or credentials in published content
   - chain_protocol.outbound_scrub() on all content before it leaves the federation

### P-Day: First Real Publish

- Deer selects a blog post (e.g., "The Federation Learns to Talk" or the week-in-review)
- Draft created automatically from web_content
- Partner reviews in Substack dashboard
- Partner approves via Telegram/Slack
- Post goes live on Substack
- Thermalize: temp 60, tags: [substack, deer, content_pipeline, first_publish]

## Verification

1. **Draft creation**: Blog post in web_content → Substack draft appears in Partner's dashboard
2. **Content fidelity**: Draft content matches ganuda.us version (canary check)
3. **Human gate**: No post publishes without explicit Partner approval
4. **Kill switch**: `enabled: false` → zero Substack API calls
5. **PII scrub**: Internal IPs, node names, credentials stripped before Substack
6. **Fire Guard**: Substack auth health shows green in necklace
7. **Provenance**: Published posts tagged in chain_protocol with source=substack_publisher

## What NOT To Do

- Do NOT auto-publish anything — drafts only until Partner approves
- ~~Do NOT start any P-3 work until Crawdad's audit clears~~ **CLEARED Mar 17 2026**
- Do NOT store Substack credentials anywhere except secrets_loader pipeline
- Do NOT publish sacred or internal-only content to Substack — Deer curates what goes external
- Do NOT skip the PII/outbound scrub — internal infrastructure details must NEVER reach Substack
- Do NOT build a custom Substack API wrapper — use python-substack as-is (less code to audit)
- Do NOT upgrade python-substack past 0.1.18 without a new Crawdad review (audit condition #5)
- Do NOT pass `debug=True` to the Api constructor — session cookies leak to logs (audit condition #4)
- Do NOT pass untrusted input as `base_url` — hardcoded in publisher (audit condition #1)
- Do NOT store cookie file with default permissions — must be 0o600 (audit condition #3)
