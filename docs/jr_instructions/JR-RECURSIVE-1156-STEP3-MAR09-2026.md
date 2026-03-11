# [RECURSIVE] Wire Slack into Council vote pipeline - Step 3

**Parent Task**: #1156
**Auto-decomposed**: 2026-03-09T14:13:24.665591
**Original Step Title**: Add Slack notification after the SECOND council_votes INSERT (full deliberation path)

---

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
