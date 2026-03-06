# JR Instruction: Fix Council Vote Response Persistence

**Task**: Fix _log_vote() to persist specialist responses and consensus to council_votes table
**Priority**: 8 (data integrity — audit trail gap)
**Sacred Fire**: No
**Assigned Jr**: Software Engineer Jr.
**Use RLM**: false
**TEG Plan**: false

## Context

The `_log_vote()` method in specialist_council.py does NOT store `responses`, `consensus`, or `concern_count` in the council_votes INSERT. Only 603 of 8,771 votes (6.9%) have these fields populated (from an older code path). The data exists in memory but is silently dropped.

The `responses` column is JSONB. Working examples store a dict keyed by specialist name with response text, concerns, backend, and timing. The `consensus` column is TEXT. The `concern_count` column is INTEGER.

## Changes

File: `lib/specialist_council.py`

### Step 1: Fix the INSERT statement in _log_vote()

<<<<<<< SEARCH
            # Log to council_votes with metacognition
            cur.execute("""
                INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concerns, metacognition, voted_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (vote.audit_hash, vote.question, vote.recommendation, vote.confidence, json.dumps(vote.concerns), json.dumps(metacognition) if metacognition else None))
=======
            # Serialize specialist responses for audit trail
            responses_dict = {}
            for resp in vote.responses:
                responses_dict[resp.name] = {
                    "response": resp.response,
                    "concerns": resp.concerns if hasattr(resp, 'concerns') else [],
                    "has_concern": resp.has_concern,
                    "concern_types": [resp.concern_type] if resp.has_concern and resp.concern_type else [],
                    "backend": resp.backend if hasattr(resp, 'backend') else "unknown",
                    "response_time_ms": resp.response_time_ms if hasattr(resp, 'response_time_ms') else None,
                }

            # Log to council_votes with metacognition + responses + consensus
            cur.execute("""
                INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concern_count, responses, concerns, consensus, metacognition, voted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (vote.audit_hash, vote.question, vote.recommendation, vote.confidence, len(vote.concerns), json.dumps(responses_dict), json.dumps(vote.concerns), vote.consensus, json.dumps(metacognition) if metacognition else None))
>>>>>>> REPLACE

## Verification

After applying, the next council vote should populate all three fields. Verify with:

```text
SELECT audit_hash, responses IS NOT NULL as has_responses, consensus IS NOT NULL as has_consensus, concern_count
FROM council_votes ORDER BY voted_at DESC LIMIT 5;
```

## Notes

- The `vote.responses` list may be empty when `include_responses=False` is passed to `vote()`. This is fine — an empty dict `{}` is better than NULL for audit purposes.
- The existing format in working rows uses specialist name as key with response text and metadata. This matches what we build above.
- The SpecialistResponse dataclass attributes used: `name`, `response`, `has_concern`, `concern_type`, `response_time_ms`. The `backend` and `concerns` attributes may not exist on all SpecialistResponse objects — hence the hasattr guards.
