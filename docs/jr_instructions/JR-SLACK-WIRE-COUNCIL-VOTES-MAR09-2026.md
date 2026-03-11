# Jr Instruction: Wire Slack Notifications into Council Vote Pipeline

**Council Vote:** dae9f2a065b4f3a0 (Slack Federation Wiring — Phase 1)
**Date:** March 9, 2026
**Priority:** 3 (Phase 1 — council vote transparency)

## Objective

Wire `slack_federation.notify_council_vote()` into `specialist_council.py` so that every
council vote result is posted to #council-votes on Slack. Chief wants to see the organism
making decisions autonomously. Format: terse with real numbers (hash, confidence %, concerns).

## Changes

File: `/ganuda/lib/specialist_council.py`

### Step 1: Add slack import at module level, near existing imports

Find the block of imports near the top of the file and add the slack import.

<<<<<<< SEARCH
import hashlib
import psycopg2
=======
import hashlib
import psycopg2

try:
    from slack_federation import notify_council_vote as _slack_notify_vote
    _SLACK_AVAILABLE = True
except ImportError:
    _SLACK_AVAILABLE = False
>>>>>>> REPLACE

### Step 2: Add Slack notification after the FIRST council_votes INSERT (vote-first path)

Find the first INSERT INTO council_votes block (the vote-first path around line 1777) and add the Slack call after the commit.

<<<<<<< SEARCH
            cur.execute("""
                INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concerns, voted_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                result.audit_hash,
                result.question,
                f"VOTE-FIRST: {result.decision}",
                1.0 if result.decision != "CONTESTED" else 0.5,
                json.dumps(vote_summary)
            ))
=======
            cur.execute("""
                INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concerns, voted_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                result.audit_hash,
                result.question,
                f"VOTE-FIRST: {result.decision}",
                1.0 if result.decision != "CONTESTED" else 0.5,
                json.dumps(vote_summary)
            ))

            # Post to #council-votes Slack channel
            if _SLACK_AVAILABLE:
                try:
                    _vote_confidence = 1.0 if result.decision != "CONTESTED" else 0.5
                    _slack_notify_vote(
                        vote_hash=result.audit_hash,
                        question=result.question[:200],
                        decision=f"VOTE-FIRST: {result.decision}",
                        confidence=_vote_confidence,
                        concerns=[f"{k}: {v.vote}" for k, v in result.votes.items() if v.vote != "APPROVE"],
                    )
                except Exception:
                    pass  # Slack is best-effort
>>>>>>> REPLACE

### Step 3: Add Slack notification after the SECOND council_votes INSERT (full deliberation path)

Find the second INSERT INTO council_votes block (the full deliberation path around line 1840) and add the Slack call after it.

<<<<<<< SEARCH
            cur.execute("""
                INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concern_count, responses, concerns, consensus, metacognition, voted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (vote.audit_hash, vote.question, vote.recommendation, vote.confidence, len(vote.concerns), json.dumps(responses_dict), json.dumps(vote.concerns), vote.consensus, json.dumps(metacognition) if metacognition else None))
=======
            cur.execute("""
                INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concern_count, responses, concerns, consensus, metacognition, voted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (vote.audit_hash, vote.question, vote.recommendation, vote.confidence, len(vote.concerns), json.dumps(responses_dict), json.dumps(vote.concerns), vote.consensus, json.dumps(metacognition) if metacognition else None))

            # Post to #council-votes Slack channel
            if _SLACK_AVAILABLE:
                try:
                    _slack_notify_vote(
                        vote_hash=vote.audit_hash,
                        question=vote.question[:200],
                        decision=vote.recommendation,
                        confidence=vote.confidence,
                        concerns=vote.concerns,
                    )
                except Exception:
                    pass  # Slack is best-effort
>>>>>>> REPLACE

## Verification

After applying, run a test council vote:
```text
python3 -c "
import sys; sys.path.insert(0, '/ganuda/lib')
from specialist_council import council_vote
result = council_vote('Test vote: is Slack wiring working?', max_tokens=50)
print(result['audit_hash'], result['confidence'])
"
```

Check #council-votes channel on Slack for the vote notification with Block Kit formatting.
