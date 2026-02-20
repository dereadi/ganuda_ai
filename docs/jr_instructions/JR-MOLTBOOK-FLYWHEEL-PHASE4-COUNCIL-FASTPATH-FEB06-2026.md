# JR-MOLTBOOK-FLYWHEEL-PHASE4-COUNCIL-FASTPATH-FEB06-2026

## Task
Add Council fast-path auto-approval for high-confidence Research Jr + Moltbook responses, enabling automatic posting when confidence thresholds are met while maintaining human oversight for uncertain cases.

## Context
This is Phase 4 of the Research Jr + Moltbook Flywheel integration. Previous phases established:
- Phase 1: Research Jr integration with Moltbook proxy daemon
- Phase 2: Content generation pipeline with research context
- Phase 3: Quality scoring and confidence metrics

Phase 4 adds intelligent routing: high-confidence responses get auto-approved via Council fast-path, while uncertain responses queue for TPM review. This reduces latency for quality content while maintaining safety guardrails.

## Prerequisites
- Phases 1-3 of Moltbook Flywheel completed and operational
- Council API accessible at http://192.168.132.223:8080/v1/council/vote
- COUNCIL_API_KEY environment variable configured
- Telegram alerting configured (optional but recommended)
- thermal_memory database accessible for audit logging

## Steps

### Step 1: Add Fast-Path Configuration Constants
Location: `proxy_daemon.py` (top of file, configuration section)

```python
# Council Fast-Path Configuration
COUNCIL_FASTPATH_CONFIDENCE_THRESHOLD = 0.90  # 90% minimum confidence
COUNCIL_FASTPATH_MAX_HOURLY = 5  # Rate limit: max auto-approvals per hour
COUNCIL_API_ENDPOINT = "http://192.168.132.223:8080/v1/council/vote"
COUNCIL_API_KEY = os.getenv("COUNCIL_API_KEY")
COUNCIL_VOTE_MODE = "parallel"  # For speed
```

### Step 2: Create Rate Limiter for Auto-Approvals
Add a sliding window rate limiter to prevent runaway auto-approvals:

```python
from collections import deque
from datetime import datetime, timedelta
import threading

class AutoApprovalRateLimiter:
    """Sliding window rate limiter for auto-approved posts."""

    def __init__(self, max_per_hour: int = 5):
        self.max_per_hour = max_per_hour
        self.approvals = deque()
        self.lock = threading.Lock()

    def can_approve(self) -> bool:
        """Check if we can auto-approve (within rate limit)."""
        with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(hours=1)

            # Remove expired entries
            while self.approvals and self.approvals[0] < cutoff:
                self.approvals.popleft()

            return len(self.approvals) < self.max_per_hour

    def record_approval(self):
        """Record an auto-approval."""
        with self.lock:
            self.approvals.append(datetime.utcnow())

    def get_remaining(self) -> int:
        """Get remaining approvals in current window."""
        with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(hours=1)
            while self.approvals and self.approvals[0] < cutoff:
                self.approvals.popleft()
            return max(0, self.max_per_hour - len(self.approvals))

# Initialize global rate limiter
auto_approval_limiter = AutoApprovalRateLimiter(max_per_hour=COUNCIL_FASTPATH_MAX_HOURLY)
```

### Step 3: Create Council Vote Payload Builder
Build enhanced vote payloads with research context:

```python
def build_council_vote_payload(
    content: str,
    confidence: float,
    research_context: dict,
    response_type: str,  # 'post' or 'comment'
    concerns: list = None
) -> dict:
    """
    Build council vote payload with research context.

    Args:
        content: The generated content for Moltbook
        confidence: Confidence score (0.0 - 1.0)
        research_context: Dict containing research metadata
        response_type: 'post' or 'comment'
        concerns: List of flagged concerns (if any)

    Returns:
        Dict payload for council API
    """
    return {
        "mode": COUNCIL_VOTE_MODE,
        "request_type": "moltbook_content_approval",
        "content": {
            "text": content,
            "type": response_type,
            "confidence": confidence,
            "concerns_flagged": concerns or []
        },
        "research_context": {
            "research_sources": research_context.get("sources", []),
            "research_cost": research_context.get("cost", 0.0),
            "topic_relevance": research_context.get("relevance_score", 0.0),
            "search_queries": research_context.get("queries", []),
            "source_count": len(research_context.get("sources", []))
        },
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "phase": "moltbook_flywheel_v4",
            "fast_path_eligible": confidence >= COUNCIL_FASTPATH_CONFIDENCE_THRESHOLD and not concerns
        }
    }
```

### Step 4: Implement Council Fast-Path Check
Add the decision logic for fast-path vs TPM queue:

```python
import aiohttp

async def check_council_fastpath(
    content: str,
    confidence: float,
    research_context: dict,
    response_type: str,
    concerns: list = None
) -> dict:
    """
    Check if content qualifies for council fast-path auto-approval.

    Returns:
        dict with keys:
            - approved: bool
            - reason: str
            - council_response: dict (if council was called)
            - route: 'fastpath' | 'tpm_queue' | 'rejected'
    """
    # Check fast-path eligibility
    if confidence < COUNCIL_FASTPATH_CONFIDENCE_THRESHOLD:
        return {
            "approved": False,
            "reason": f"Confidence {confidence:.2%} below threshold {COUNCIL_FASTPATH_CONFIDENCE_THRESHOLD:.0%}",
            "route": "tpm_queue"
        }

    if concerns:
        return {
            "approved": False,
            "reason": f"Concerns flagged: {', '.join(concerns)}",
            "route": "tpm_queue"
        }

    # Check rate limit
    if not auto_approval_limiter.can_approve():
        remaining = auto_approval_limiter.get_remaining()
        return {
            "approved": False,
            "reason": f"Rate limit reached (0/{COUNCIL_FASTPATH_MAX_HOURLY} remaining this hour)",
            "route": "tpm_queue"
        }

    # Build and send council vote
    payload = build_council_vote_payload(
        content=content,
        confidence=confidence,
        research_context=research_context,
        response_type=response_type,
        concerns=concerns
    )

    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {COUNCIL_API_KEY}",
                "Content-Type": "application/json"
            }
            async with session.post(
                COUNCIL_API_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    council_response = await response.json()

                    # Check council verdict
                    if council_response.get("approved", False):
                        auto_approval_limiter.record_approval()
                        return {
                            "approved": True,
                            "reason": "Council fast-path approved",
                            "council_response": council_response,
                            "route": "fastpath"
                        }
                    else:
                        return {
                            "approved": False,
                            "reason": council_response.get("reason", "Council rejected"),
                            "council_response": council_response,
                            "route": "tpm_queue"
                        }
                else:
                    error_text = await response.text()
                    logger.error(f"Council API error {response.status}: {error_text}")
                    return {
                        "approved": False,
                        "reason": f"Council API error: {response.status}",
                        "route": "tpm_queue"
                    }
    except Exception as e:
        logger.error(f"Council API exception: {e}")
        return {
            "approved": False,
            "reason": f"Council API exception: {str(e)}",
            "route": "tpm_queue"
        }
```

### Step 5: Add TPM Queue Storage
Store non-fast-path responses for TPM review:

```python
async def queue_for_tpm_review(
    content: str,
    confidence: float,
    research_context: dict,
    response_type: str,
    reason: str,
    original_request: dict
) -> str:
    """
    Queue a response for TPM review in moltbook_post_queue.

    Returns:
        queue_id: str - The ID of the queued item
    """
    import uuid

    queue_id = str(uuid.uuid4())
    queue_entry = {
        "id": queue_id,
        "status": "pending_tpm",
        "content": content,
        "confidence": confidence,
        "research_context": research_context,
        "response_type": response_type,
        "queue_reason": reason,
        "original_request": original_request,
        "created_at": datetime.utcnow().isoformat(),
        "reviewed_at": None,
        "reviewed_by": None,
        "review_decision": None
    }

    # Store in database (adapt to your database layer)
    # Example for PostgreSQL via asyncpg:
    async with get_db_connection() as conn:
        await conn.execute("""
            INSERT INTO moltbook_post_queue
            (id, status, content, confidence, research_context, response_type,
             queue_reason, original_request, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
            queue_id,
            "pending_tpm",
            content,
            confidence,
            json.dumps(research_context),
            response_type,
            reason,
            json.dumps(original_request),
            datetime.utcnow()
        )

    # Send notification
    await notify_tpm_queue_item(queue_id, content[:100], reason)

    logger.info(f"Queued response {queue_id} for TPM review: {reason}")
    return queue_id
```

### Step 6: Add TPM Notification via Telegram
Notify TPM of pending reviews:

```python
async def notify_tpm_queue_item(queue_id: str, content_preview: str, reason: str):
    """Send Telegram notification for new TPM queue item."""
    try:
        # Check if Telegram alerting is configured
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_tpm_chat_id = os.getenv("TELEGRAM_TPM_CHAT_ID")

        if not telegram_bot_token or not telegram_tpm_chat_id:
            logger.warning("Telegram not configured for TPM notifications")
            return

        message = f"""🔔 **Moltbook Post Pending TPM Review**

**Queue ID:** `{queue_id}`
**Reason:** {reason}

**Preview:**
{content_preview}...

Review at: /moltbook/queue/{queue_id}
"""

        async with aiohttp.ClientSession() as session:
            await session.post(
                f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
                json={
                    "chat_id": telegram_tpm_chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )
    except Exception as e:
        logger.error(f"Failed to send TPM notification: {e}")
```

### Step 7: Add Thermal Memory Audit Trail
Log auto-approved posts to thermal memory for audit:

```python
async def log_auto_approval_audit(
    content: str,
    confidence: float,
    research_context: dict,
    response_type: str,
    council_response: dict,
    post_result: dict
):
    """
    Create thermal memory entry for auto-approved post audit trail.
    """
    audit_entry = {
        "event_type": "moltbook_auto_approval",
        "timestamp": datetime.utcnow().isoformat(),
        "confidence": confidence,
        "response_type": response_type,
        "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
        "content_length": len(content),
        "research_sources_count": len(research_context.get("sources", [])),
        "research_cost": research_context.get("cost", 0.0),
        "topic_relevance": research_context.get("relevance_score", 0.0),
        "council_verdict": council_response.get("verdict", "approved"),
        "council_confidence": council_response.get("confidence", 0.0),
        "post_id": post_result.get("post_id"),
        "rate_limit_remaining": auto_approval_limiter.get_remaining()
    }

    # Store in thermal memory
    async with get_db_connection() as conn:
        await conn.execute("""
            INSERT INTO thermal_memory
            (memory_type, context, content, temperature, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """,
            "audit",
            "moltbook_flywheel_auto_approval",
            json.dumps(audit_entry),
            0.7,  # Medium temperature for audit entries
            datetime.utcnow()
        )

    logger.info(f"Audit trail logged for auto-approved {response_type}: {audit_entry['content_hash']}")
```

### Step 8: Integrate Fast-Path into Main Response Flow
Modify the main content processing flow in proxy_daemon.py:

```python
async def process_moltbook_response(
    generated_content: str,
    confidence: float,
    research_context: dict,
    response_type: str,
    concerns: list,
    original_request: dict
) -> dict:
    """
    Process generated Moltbook content through council fast-path or TPM queue.

    Returns:
        dict with processing result and routing decision
    """
    # Check council fast-path
    fastpath_result = await check_council_fastpath(
        content=generated_content,
        confidence=confidence,
        research_context=research_context,
        response_type=response_type,
        concerns=concerns
    )

    if fastpath_result["approved"]:
        # Auto-approved: post immediately
        post_result = await post_to_moltbook(
            content=generated_content,
            response_type=response_type
        )

        # Log audit trail
        await log_auto_approval_audit(
            content=generated_content,
            confidence=confidence,
            research_context=research_context,
            response_type=response_type,
            council_response=fastpath_result.get("council_response", {}),
            post_result=post_result
        )

        return {
            "status": "posted",
            "route": "fastpath",
            "post_result": post_result,
            "confidence": confidence
        }
    else:
        # Queue for TPM review
        queue_id = await queue_for_tpm_review(
            content=generated_content,
            confidence=confidence,
            research_context=research_context,
            response_type=response_type,
            reason=fastpath_result["reason"],
            original_request=original_request
        )

        return {
            "status": "queued",
            "route": "tpm_queue",
            "queue_id": queue_id,
            "reason": fastpath_result["reason"],
            "confidence": confidence
        }
```

### Step 9: Create Database Migration for Queue Table
Create migration file for moltbook_post_queue table:

```sql
-- Migration: Create moltbook_post_queue table
-- File: sql/migrations/20260206_moltbook_post_queue.sql

CREATE TABLE IF NOT EXISTS moltbook_post_queue (
    id UUID PRIMARY KEY,
    status VARCHAR(50) NOT NULL DEFAULT 'pending_tpm',
    content TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    research_context JSONB,
    response_type VARCHAR(20) NOT NULL,
    queue_reason TEXT,
    original_request JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by VARCHAR(100),
    review_decision VARCHAR(20),
    review_notes TEXT
);

CREATE INDEX idx_moltbook_queue_status ON moltbook_post_queue(status);
CREATE INDEX idx_moltbook_queue_created ON moltbook_post_queue(created_at DESC);

COMMENT ON TABLE moltbook_post_queue IS 'Queue for Moltbook posts pending TPM review (Phase 4 flywheel)';
```

## Verification

### Test 1: Fast-Path Approval
```bash
# Test high-confidence response routes to fast-path
curl -X POST http://localhost:8080/test/moltbook-fastpath \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test high-confidence response",
    "confidence": 0.95,
    "concerns": [],
    "response_type": "post"
  }'
# Expected: route=fastpath, status=posted
```

### Test 2: TPM Queue Routing
```bash
# Test low-confidence routes to TPM queue
curl -X POST http://localhost:8080/test/moltbook-fastpath \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test uncertain response",
    "confidence": 0.75,
    "concerns": [],
    "response_type": "post"
  }'
# Expected: route=tpm_queue, status=queued
```

### Test 3: Concerns Block Fast-Path
```bash
# Test that concerns flag routes to TPM queue
curl -X POST http://localhost:8080/test/moltbook-fastpath \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Response with concerns",
    "confidence": 0.95,
    "concerns": ["potential_misinformation"],
    "response_type": "comment"
  }'
# Expected: route=tpm_queue, reason contains "Concerns flagged"
```

### Test 4: Rate Limiting
```bash
# Post 6 high-confidence responses rapidly
for i in {1..6}; do
  curl -X POST http://localhost:8080/test/moltbook-fastpath \
    -H "Content-Type: application/json" \
    -d "{\"content\": \"Test $i\", \"confidence\": 0.95, \"concerns\": [], \"response_type\": \"post\"}"
done
# Expected: First 5 route=fastpath, 6th routes to tpm_queue with rate limit reason
```

### Test 5: Audit Trail Verification
```sql
-- Check thermal memory for auto-approval audit entries
SELECT content, created_at
FROM thermal_memory
WHERE context = 'moltbook_flywheel_auto_approval'
ORDER BY created_at DESC
LIMIT 5;
```

### Test 6: TPM Queue Verification
```sql
-- Check TPM queue for pending items
SELECT id, status, confidence, queue_reason, created_at
FROM moltbook_post_queue
WHERE status = 'pending_tpm'
ORDER BY created_at DESC;
```

## Files Created
- `/ganuda/docs/jr_instructions/JR-MOLTBOOK-FLYWHEEL-PHASE4-COUNCIL-FASTPATH-FEB06-2026.md` - This instruction file

## Files Modified
- `proxy_daemon.py` - Add council fast-path integration, rate limiting, TPM queue routing
- `sql/migrations/20260206_moltbook_post_queue.sql` - New table for TPM review queue

## Dependencies
- `aiohttp` - Async HTTP client for Council API calls
- `asyncpg` - PostgreSQL async driver (existing)
- Council API at http://192.168.132.223:8080/v1/council/vote
- COUNCIL_API_KEY environment variable
- Optional: TELEGRAM_BOT_TOKEN, TELEGRAM_TPM_CHAT_ID for notifications

## Rollback
To disable fast-path and route all responses to TPM queue:
```python
COUNCIL_FASTPATH_CONFIDENCE_THRESHOLD = 1.1  # Impossible to reach
```

## Notes
- Fast-path is designed for speed while maintaining safety through the 90% confidence threshold
- Rate limiting (5/hour) prevents runaway auto-posting even if confidence scoring drifts
- All auto-approved posts have thermal memory audit trail for post-incident review
- TPM notifications ensure human oversight for uncertain content
- Council parallel mode reduces latency for fast-path decisions

## Related Instructions
- JR-MOLTBOOK-FLYWHEEL-PHASE1-*
- JR-MOLTBOOK-FLYWHEEL-PHASE2-*
- JR-MOLTBOOK-FLYWHEEL-PHASE3-*
- JR-COUNCIL-RESEARCH-AUTOQUEUE-JAN28-2026
