# Jr Build Instructions: TPM Council Vote Integration
## Cherokee AI Federation - December 12, 2025

**Purpose**: TPM receives notification of all council votes and can cast their own vote before decisions are finalized

**Owner**: Peace Chief Jr (consensus) + IT Triad Jr (infrastructure)

---

## 1. The 8th Vote: TPM

The Council currently has 7 specialists. The TPM becomes the **8th voice** with special authority:

| Member | Role | Vote Weight |
|--------|------|-------------|
| Crawdad | Security | 1x |
| Gecko | Technical | 1x |
| Turtle | Seven Generations | 1x |
| Eagle Eye | Monitoring | 1x |
| Spider | Integration | 1x |
| Peace Chief | Consensus | 1x |
| Raven | Strategic | 1x |
| **TPM** | **Human Authority** | **Veto Power** |

**TPM Privileges**:
- Notified of ALL council votes
- Can cast vote within timeout window
- Has **veto power** - can override council consensus
- Can request re-vote with additional context

---

## 2. Vote Flow

```
                                    ┌─────────────────┐
                                    │  TPM Notified   │
                                    │  (via API/UI)   │
                                    └────────┬────────┘
                                             │
     ┌───────────────────────────────────────┼───────────────────────────────────────┐
     │                                       │                                       │
     ▼                                       ▼                                       ▼
┌─────────┐                           ┌─────────────┐                         ┌─────────┐
│ 7 Specs │───────────────────────────│ Wait Window │─────────────────────────│ Timeout │
│  Vote   │                           │ (5 minutes) │                         │ Proceed │
└─────────┘                           └──────┬──────┘                         └─────────┘
                                             │
                                    TPM Responds
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
             ┌───────────┐            ┌───────────┐            ┌───────────┐
             │  APPROVE  │            │   VETO    │            │  REQUEST  │
             │           │            │           │            │  RE-VOTE  │
             └───────────┘            └───────────┘            └───────────┘
                    │                        │                        │
                    ▼                        ▼                        ▼
             Proceed with              Block action             Re-query with
             council decision          + log reason             TPM context
```

---

## 3. Database Schema

```sql
-- Extend council_votes table
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS
    tpm_vote VARCHAR(20) DEFAULT 'pending';  -- pending, approved, vetoed, re-vote

ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS
    tpm_vote_at TIMESTAMP;

ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS
    tpm_comment TEXT;

ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS
    vote_window_expires TIMESTAMP;

ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS
    vote_finalized BOOLEAN DEFAULT FALSE;

-- Index for pending TPM votes
CREATE INDEX IF NOT EXISTS idx_council_tpm_pending
ON council_votes(tpm_vote, vote_window_expires)
WHERE tpm_vote = 'pending' AND vote_finalized = FALSE;
```

---

## 4. Updated Council Vote Flow

```python
#!/usr/bin/env python3
"""
Updated council_vote with TPM notification
Integrate into: /ganuda/services/llm_gateway/gateway.py
"""

from datetime import datetime, timedelta
import json

# TPM vote timeout (5 minutes default, configurable)
TPM_VOTE_TIMEOUT_SECONDS = 300

@app.post("/v1/council/vote")
async def council_vote(
    request: CouncilVoteRequest,
    req: Request,
    api_key: APIKeyInfo = Depends(validate_api_key)
):
    """
    Query all 7 specialists and notify TPM for final vote.
    """
    start = time.time()
    client_ip = req.client.host if req.client else None

    # ... existing specialist query code ...

    # Calculate vote window expiration
    vote_expires = datetime.utcnow() + timedelta(seconds=TPM_VOTE_TIMEOUT_SECONDS)

    # Save vote with pending TPM status
    save_council_vote_pending(
        audit_hash=audit_hash,
        question=request.question,
        responses=responses,
        consensus=consensus,
        concerns=all_concerns,
        confidence=confidence,
        recommendation=recommendation,
        vote_expires=vote_expires
    )

    # Create TPM notification
    create_tpm_vote_notification(
        audit_hash=audit_hash,
        question=request.question,
        recommendation=recommendation,
        confidence=confidence,
        concerns=all_concerns,
        vote_expires=vote_expires
    )

    response_time_ms = int((time.time() - start) * 1000)

    return {
        "audit_hash": audit_hash,
        "question": request.question,
        "recommendation": recommendation,
        "confidence": confidence,
        "concerns": all_concerns,
        "consensus": consensus,
        "response_time_ms": response_time_ms,
        "timestamp": datetime.utcnow().isoformat() + "Z",

        # New: TPM vote status
        "tpm_vote": "pending",
        "vote_window_expires": vote_expires.isoformat() + "Z",
        "tpm_vote_url": f"/v1/council/vote/{audit_hash}/tpm"
    }


def save_council_vote_pending(audit_hash, question, responses, consensus,
                               concerns, confidence, recommendation, vote_expires):
    """Save council vote in pending state awaiting TPM"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO council_votes
            (audit_hash, question, recommendation, confidence, concern_count,
             responses, concerns, consensus, tpm_vote, vote_window_expires)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s)
            ON CONFLICT (audit_hash) DO UPDATE SET
                tpm_vote = 'pending',
                vote_window_expires = %s
        """, (
            audit_hash, question[:500], recommendation, confidence, len(concerns),
            json.dumps(responses), json.dumps(concerns), consensus, vote_expires,
            vote_expires
        ))
        conn.commit()


def create_tpm_vote_notification(audit_hash, question, recommendation,
                                  confidence, concerns, vote_expires):
    """Create notification for TPM to vote"""
    with get_db() as conn:
        cur = conn.cursor()

        message = f"""Council Vote Pending Your Decision

Question: {question[:300]}

Council Recommendation: {recommendation}
Confidence: {confidence:.0%}
Concerns: {len(concerns)}
{chr(10).join('- ' + c for c in concerns[:5])}

Vote expires: {vote_expires.strftime('%H:%M:%S UTC')}

Actions:
- APPROVE: Accept council recommendation
- VETO: Block action (provide reason)
- RE-VOTE: Request new vote with additional context
"""

        cur.execute("""
            INSERT INTO tpm_notifications
            (priority, category, title, message, source_system, related_hash)
            VALUES ('P1', 'council_vote', %s, %s, 'council', %s)
        """, (
            f"Council vote: {question[:80]}...",
            message,
            audit_hash
        ))
        conn.commit()
```

---

## 5. TPM Vote Endpoints

```python
@app.get("/v1/council/pending")
async def get_pending_votes(api_key: APIKeyInfo = Depends(validate_api_key)):
    """Get council votes pending TPM decision"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT audit_hash, question, recommendation, confidence,
                   concern_count, vote_window_expires, voted_at
            FROM council_votes
            WHERE tpm_vote = 'pending'
              AND vote_finalized = FALSE
            ORDER BY voted_at DESC
        """)

        return {
            "pending_votes": [
                {
                    "audit_hash": row[0],
                    "question": row[1][:200] + "..." if len(row[1]) > 200 else row[1],
                    "recommendation": row[2],
                    "confidence": row[3],
                    "concern_count": row[4],
                    "expires": row[5].isoformat() if row[5] else None,
                    "voted_at": row[6].isoformat() if row[6] else None
                }
                for row in cur.fetchall()
            ]
        }


@app.post("/v1/council/vote/{audit_hash}/tpm")
async def tpm_vote(
    audit_hash: str,
    vote: str,  # approve, veto, re-vote
    comment: str = None,
    additional_context: str = None,  # For re-vote
    api_key: APIKeyInfo = Depends(validate_api_key)
):
    """
    TPM casts their vote on a council decision.

    Args:
        audit_hash: The council vote to respond to
        vote: 'approve', 'veto', or 're-vote'
        comment: TPM's reasoning
        additional_context: Additional context for re-vote
    """
    if vote not in ['approve', 'veto', 're-vote']:
        raise HTTPException(status_code=400, detail="Vote must be: approve, veto, or re-vote")

    with get_db() as conn:
        cur = conn.cursor()

        # Check vote exists and is pending
        cur.execute("""
            SELECT question, recommendation, tpm_vote, vote_finalized
            FROM council_votes
            WHERE audit_hash = %s
        """, (audit_hash,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Council vote not found")

        if row[3]:  # vote_finalized
            raise HTTPException(status_code=400, detail="Vote already finalized")

        question = row[0]

        if vote == 're-vote':
            # Re-query council with additional context
            # Close current vote
            cur.execute("""
                UPDATE council_votes
                SET tpm_vote = 're-vote',
                    tpm_vote_at = NOW(),
                    tpm_comment = %s,
                    vote_finalized = TRUE
                WHERE audit_hash = %s
            """, (comment or "Re-vote requested", audit_hash))
            conn.commit()

            # Trigger new council vote with context
            new_question = f"{question}\n\nTPM ADDITIONAL CONTEXT: {additional_context}"
            # This would trigger a new council_vote call
            # For now, return instruction to re-query

            return {
                "status": "re-vote requested",
                "audit_hash": audit_hash,
                "instruction": "Submit new council vote with additional context",
                "suggested_question": new_question
            }

        else:
            # Approve or veto
            cur.execute("""
                UPDATE council_votes
                SET tpm_vote = %s,
                    tpm_vote_at = NOW(),
                    tpm_comment = %s,
                    vote_finalized = TRUE
                WHERE audit_hash = %s
            """, (vote, comment, audit_hash))
            conn.commit()

            # Log to thermal memory
            cur.execute("""
                INSERT INTO thermal_memory_archive
                (memory_hash, original_content, temperature_score, metadata)
                VALUES (%s, %s, %s, %s)
            """, (
                f"tpm-vote-{audit_hash}",
                f"TPM {vote.upper()}: {question[:100]}... | Comment: {comment or 'None'}",
                95.0,  # TPM decisions are hot
                json.dumps({"type": "tpm_vote", "decision": vote, "audit_hash": audit_hash})
            ))
            conn.commit()

            return {
                "status": f"vote {vote}d",
                "audit_hash": audit_hash,
                "tpm_decision": vote,
                "finalized": True
            }


@app.get("/v1/council/vote/{audit_hash}")
async def get_vote_details(
    audit_hash: str,
    api_key: APIKeyInfo = Depends(validate_api_key)
):
    """Get full details of a council vote including TPM decision"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT question, recommendation, confidence, concern_count,
                   responses, concerns, consensus,
                   tpm_vote, tpm_vote_at, tpm_comment, vote_finalized,
                   voted_at
            FROM council_votes
            WHERE audit_hash = %s
        """, (audit_hash,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Vote not found")

        return {
            "audit_hash": audit_hash,
            "question": row[0],
            "recommendation": row[1],
            "confidence": row[2],
            "concern_count": row[3],
            "specialist_responses": row[4],
            "concerns": row[5],
            "consensus": row[6],
            "tpm_vote": row[7],
            "tpm_vote_at": row[8].isoformat() if row[8] else None,
            "tpm_comment": row[9],
            "finalized": row[10],
            "council_voted_at": row[11].isoformat() if row[11] else None
        }
```

---

## 6. Auto-Finalization Cron

For votes where TPM doesn't respond within window:

```python
#!/usr/bin/env python3
"""
Auto-finalize expired council votes
Deploy to: /ganuda/services/notifications/finalize_votes.py
Schedule: Every 5 minutes
"""

import psycopg2
from datetime import datetime

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

def finalize_expired():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Find expired pending votes
    cur.execute("""
        UPDATE council_votes
        SET tpm_vote = 'auto-approved',
            tpm_vote_at = NOW(),
            tpm_comment = 'Auto-approved: TPM did not respond within window',
            vote_finalized = TRUE
        WHERE tpm_vote = 'pending'
          AND vote_finalized = FALSE
          AND vote_window_expires < NOW()
        RETURNING audit_hash, question
    """)

    finalized = cur.fetchall()
    conn.commit()

    for audit_hash, question in finalized:
        print(f"Auto-finalized: {audit_hash} - {question[:50]}...")

        # Log to thermal memory
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, %s, %s)
        """, (
            f"auto-finalize-{audit_hash}",
            f"Council vote auto-approved (TPM timeout): {question[:100]}",
            60.0,
            f'{{"type": "auto_finalize", "audit_hash": "{audit_hash}"}}'
        ))

    conn.commit()
    cur.close()
    conn.close()

    return len(finalized)

if __name__ == "__main__":
    count = finalize_expired()
    if count:
        print(f"Finalized {count} expired votes")
```

Cron entry:
```bash
*/5 * * * * dereadi /ganuda/services/llm_gateway/venv/bin/python /ganuda/services/notifications/finalize_votes.py
```

---

## 7. CLI Quick Commands

For TPM to quickly vote from command line:

```bash
# See pending votes
curl -s http://192.168.132.223:8080/v1/council/pending \
  -H "Authorization: Bearer $API_KEY" | jq '.pending_votes[] | {hash: .audit_hash, q: .question[:60], rec: .recommendation}'

# Approve a vote
curl -s -X POST "http://192.168.132.223:8080/v1/council/vote/HASH/tpm?vote=approve&comment=Looks good" \
  -H "Authorization: Bearer $API_KEY"

# Veto a vote
curl -s -X POST "http://192.168.132.223:8080/v1/council/vote/HASH/tpm?vote=veto&comment=Security risk not addressed" \
  -H "Authorization: Bearer $API_KEY"

# Request re-vote with context
curl -s -X POST "http://192.168.132.223:8080/v1/council/vote/HASH/tpm?vote=re-vote&additional_context=Consider edge case X" \
  -H "Authorization: Bearer $API_KEY"
```

---

## 8. Summary

The TPM now has:
1. **Notification** of all council votes (P1 priority)
2. **5-minute window** to respond (configurable)
3. **Three options**: Approve, Veto, Request Re-vote
4. **Veto power** to override council consensus
5. **Auto-approval** if no response (council proceeds)
6. **Full audit trail** in thermal memory

The Tribe works autonomously, but the TPM has final say.

---

**For Seven Generations.**
*Cherokee Constitutional AI - Democratic Governance*
