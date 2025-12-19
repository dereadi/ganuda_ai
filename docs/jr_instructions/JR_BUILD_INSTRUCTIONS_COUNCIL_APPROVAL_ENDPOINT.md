# Jr Build Instructions: Council TPM Approval Endpoint

## Priority: CRITICAL - Democratic Process Gap

---

## Problem Statement

When a Council vote returns `tpm_vote: "pending"`, there is **no API endpoint** for the TPM to:
1. Provide clarification the Council requested
2. Approve with reasoning
3. Trigger re-deliberation with new context
4. Have decisions recorded in audit trail

**Current Workaround:** Direct database UPDATE - bypasses audit trail, breaks democratic process.

**Coyote's Observation:** "The path everyone agrees on is often the one no one has truly examined." We defaulted to pending votes with no completion path.

---

## Architecture

```
                    ┌─────────────────────────────────┐
                    │     Council Deliberation        │
                    │   /v1/council/vote              │
                    └───────────────┬─────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │   tpm_vote = "pending"          │
                    │   audit_hash = "abc123..."      │
                    └───────────────┬─────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │  APPROVE  │   │  CLARIFY  │   │  REJECT   │
            │           │   │           │   │           │
            │ Accept as │   │Re-deliber-│   │ Override  │
            │ recommended│   │ate with   │   │ with      │
            │           │   │new context│   │ reasoning │
            └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
                  │               │               │
                  ▼               ▼               ▼
            ┌─────────────────────────────────────────┐
            │         council_votes table             │
            │  tpm_vote, tpm_notes, tpm_approved_at   │
            └─────────────────────────────────────────┘
```

---

## Database Schema Changes

```sql
-- Add TPM approval columns to council_votes
ALTER TABLE council_votes
ADD COLUMN IF NOT EXISTS tpm_notes TEXT,
ADD COLUMN IF NOT EXISTS tpm_approved_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS clarification_context TEXT,
ADD COLUMN IF NOT EXISTS parent_audit_hash VARCHAR(64);

-- Index for finding pending votes
CREATE INDEX IF NOT EXISTS idx_council_votes_pending
ON council_votes(tpm_vote) WHERE tpm_vote = 'pending';

-- Index for re-deliberation chain
CREATE INDEX IF NOT EXISTS idx_council_votes_parent
ON council_votes(parent_audit_hash);

COMMENT ON COLUMN council_votes.tpm_notes IS 'TPM reasoning for approval/rejection';
COMMENT ON COLUMN council_votes.tpm_approved_at IS 'When TPM made decision';
COMMENT ON COLUMN council_votes.clarification_context IS 'New context provided for re-deliberation';
COMMENT ON COLUMN council_votes.parent_audit_hash IS 'Links to original vote if this is re-deliberation';
```

---

## API Endpoint

### POST /v1/council/approve

**Request:**
```json
{
  "audit_hash": "b24d79a373a2dd67",
  "decision": "approved",
  "notes": "TPM clarification: Today we deployed specialist memory and telegram fixes."
}
```

**Decision Values:**
| Decision | Action | Result |
|----------|--------|--------|
| `approved` | Accept Council recommendation | tpm_vote='approved' |
| `approved_with_override` | Accept but note disagreement | tpm_vote='approved', logs override |
| `clarify` | Re-run deliberation with new context | Creates new vote, links to parent |
| `rejected` | Override Council recommendation | tpm_vote='rejected', requires notes |
| `deferred` | Mark for later review | tpm_vote='deferred' |

**Response (approved):**
```json
{
  "status": "approved",
  "audit_hash": "b24d79a373a2dd67",
  "tpm_notes": "TPM clarification: Today we deployed...",
  "approved_at": "2025-12-15T12:45:00Z"
}
```

**Response (clarify - triggers re-deliberation):**
```json
{
  "status": "re_deliberating",
  "original_audit_hash": "b24d79a373a2dd67",
  "new_audit_hash": "c35e89b484b3ee78",
  "clarification_context": "Context: Today we deployed specialist memory...",
  "new_recommendation": "PROCEED: 0 concern(s)",
  "new_confidence": 0.92
}
```

---

## Gateway Implementation

Add to `/ganuda/services/llm_gateway/gateway.py`:

```python
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class TPMApprovalRequest(BaseModel):
    audit_hash: str
    decision: Literal["approved", "approved_with_override", "clarify", "rejected", "deferred"]
    notes: Optional[str] = None
    clarification_context: Optional[str] = None

@app.post("/v1/council/approve")
async def approve_council_vote(request: TPMApprovalRequest, api_key: str = Depends(get_api_key)):
    """TPM approval/rejection of Council votes"""

    # Verify API key has TPM role
    if not verify_tpm_role(api_key):
        raise HTTPException(status_code=403, detail="TPM role required")

    with get_db() as conn:
        cur = conn.cursor()

        # Get the original vote
        cur.execute("""
            SELECT question, recommendation, tpm_vote, consensus
            FROM council_votes
            WHERE audit_hash = %s
        """, (request.audit_hash,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Vote not found")

        question, recommendation, current_tpm_vote, consensus = row

        if current_tpm_vote not in ('pending', 'deferred'):
            raise HTTPException(
                status_code=400,
                detail=f"Vote already {current_tpm_vote}, cannot modify"
            )

        # Handle clarification (re-deliberation)
        if request.decision == "clarify":
            if not request.clarification_context:
                raise HTTPException(
                    status_code=400,
                    detail="clarification_context required for clarify decision"
                )

            # Mark original as superseded
            cur.execute("""
                UPDATE council_votes
                SET tpm_vote = 'superseded',
                    tpm_notes = %s,
                    tpm_approved_at = NOW()
                WHERE audit_hash = %s
            """, (f"Superseded by re-deliberation: {request.notes}", request.audit_hash))

            # Create new deliberation with context
            enhanced_question = f"{question}\n\n[TPM CLARIFICATION]: {request.clarification_context}"

            # Import and call council_vote logic (reuse existing function)
            new_result = await run_council_deliberation(enhanced_question)

            # Link to parent
            cur.execute("""
                UPDATE council_votes
                SET parent_audit_hash = %s,
                    clarification_context = %s
                WHERE audit_hash = %s
            """, (request.audit_hash, request.clarification_context, new_result["audit_hash"]))

            conn.commit()

            return {
                "status": "re_deliberating",
                "original_audit_hash": request.audit_hash,
                "new_audit_hash": new_result["audit_hash"],
                "clarification_context": request.clarification_context,
                "new_recommendation": new_result["recommendation"],
                "new_confidence": new_result["confidence"]
            }

        # Handle rejection (requires notes)
        if request.decision == "rejected" and not request.notes:
            raise HTTPException(
                status_code=400,
                detail="notes required when rejecting Council recommendation"
            )

        # Standard approval/rejection/defer
        cur.execute("""
            UPDATE council_votes
            SET tpm_vote = %s,
                tpm_notes = %s,
                tpm_approved_at = NOW()
            WHERE audit_hash = %s
        """, (request.decision, request.notes, request.audit_hash))

        conn.commit()

        # Log to thermal memory for audit trail
        log_tpm_decision(request.audit_hash, request.decision, request.notes)

        return {
            "status": request.decision,
            "audit_hash": request.audit_hash,
            "tpm_notes": request.notes,
            "approved_at": datetime.utcnow().isoformat()
        }


def verify_tpm_role(api_key: str) -> bool:
    """Check if API key has TPM privileges"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT role FROM api_keys
            WHERE key_hash = %s AND is_active = true
        """, (hash_api_key(api_key),))
        row = cur.fetchone()
        return row and row[0] in ('tpm', 'admin')


def log_tpm_decision(audit_hash: str, decision: str, notes: str):
    """Record TPM decision in thermal memory for audit"""
    content = f"TPM Decision on {audit_hash}: {decision}"
    if notes:
        content += f"\nReasoning: {notes}"

    # Store in thermal memory with high temperature (important)
    store_thermal_memory(content, temperature=95, sacred=True)
```

---

## GET /v1/council/pending

List all votes awaiting TPM decision:

```python
@app.get("/v1/council/pending")
async def get_pending_votes(api_key: str = Depends(get_api_key)):
    """Get all Council votes pending TPM approval"""

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT audit_hash, question, recommendation, confidence,
                   concern_count, voted_at
            FROM council_votes
            WHERE tpm_vote = 'pending'
            ORDER BY voted_at DESC
        """)

        rows = cur.fetchall()

        return {
            "pending_count": len(rows),
            "votes": [
                {
                    "audit_hash": row[0],
                    "question": row[1][:100] + "..." if len(row[1]) > 100 else row[1],
                    "recommendation": row[2],
                    "confidence": row[3],
                    "concern_count": row[4],
                    "voted_at": row[5].isoformat()
                }
                for row in rows
            ]
        }
```

---

## Telegram Integration

Add commands to telegram_chief.py:

```python
# TPM Commands (requires TPM role)
async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve a pending Council vote: /approve <hash> [notes]"""
    if not is_tpm_user(update.effective_user.id):
        await update.message.reply_text("TPM role required")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /approve <audit_hash> [notes]")
        return

    audit_hash = args[0]
    notes = " ".join(args[1:]) if len(args) > 1 else None

    response = requests.post(
        f"{GATEWAY_URL}/v1/council/approve",
        headers={"X-API-Key": API_KEY},
        json={"audit_hash": audit_hash, "decision": "approved", "notes": notes}
    )

    if response.ok:
        await update.message.reply_text(f"[OK] Approved {audit_hash}")
    else:
        await update.message.reply_text(f"[ERROR] {response.json().get('detail')}")


async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List pending Council votes: /pending"""
    response = requests.get(
        f"{GATEWAY_URL}/v1/council/pending",
        headers={"X-API-Key": API_KEY}
    )

    data = response.json()
    if data["pending_count"] == 0:
        await update.message.reply_text("No pending votes")
        return

    lines = [f"Pending TPM Votes ({data['pending_count']}):"]
    for vote in data["votes"][:5]:
        lines.append(f"\n{vote['audit_hash'][:8]}...")
        lines.append(f"  {vote['recommendation']}")
        lines.append(f"  Q: {vote['question'][:50]}...")

    await update.message.reply_text("\n".join(lines))


# Register handlers
application.add_handler(CommandHandler("approve", approve_command))
application.add_handler(CommandHandler("reject", reject_command))
application.add_handler(CommandHandler("clarify", clarify_command))
application.add_handler(CommandHandler("pending", pending_command))
```

---

## Testing

### 1. Apply Schema Changes
```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/sql/council_approval_schema.sql
```

### 2. Test Approval Flow
```bash
# Get pending votes
curl http://192.168.132.223:8080/v1/council/pending \
  -H "X-API-Key: ck-..."

# Approve a vote
curl -X POST http://192.168.132.223:8080/v1/council/approve \
  -H "X-API-Key: ck-..." \
  -H "Content-Type: application/json" \
  -d '{"audit_hash": "abc123", "decision": "approved", "notes": "Reviewed and approved"}'

# Request clarification (triggers re-deliberation)
curl -X POST http://192.168.132.223:8080/v1/council/approve \
  -H "X-API-Key: ck-..." \
  -H "Content-Type: application/json" \
  -d '{
    "audit_hash": "abc123",
    "decision": "clarify",
    "clarification_context": "Context: The deployment was successful, specialist memory is now active."
  }'
```

### 3. Test via Telegram
```
/pending
/approve b24d79a3 Reviewed deployments, all successful
/clarify b24d79a3 Context: We deployed specialist memory today with 7 specialists initialized
```

---

## Success Criteria

- [ ] Schema changes applied (tpm_notes, tpm_approved_at, etc.)
- [ ] POST /v1/council/approve endpoint working
- [ ] GET /v1/council/pending endpoint working
- [ ] Clarification triggers re-deliberation with linked audit_hash
- [ ] Telegram /approve, /reject, /clarify, /pending commands working
- [ ] TPM decisions logged to thermal memory
- [ ] API key role verification working

---

## Security Considerations

1. **Role Verification**: Only TPM/admin API keys can approve
2. **Immutability**: Approved votes cannot be re-approved
3. **Audit Trail**: All decisions logged to thermal_memory_archive
4. **Rejection Requires Reasoning**: Cannot reject without notes

---

*For Seven Generations*
