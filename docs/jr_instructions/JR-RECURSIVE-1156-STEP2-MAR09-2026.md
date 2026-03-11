# [RECURSIVE] Wire Slack into Council vote pipeline - Step 2

**Parent Task**: #1156
**Auto-decomposed**: 2026-03-09T14:13:24.664908
**Original Step Title**: Add Slack notification after the FIRST council_votes INSERT (vote-first path)

---

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
