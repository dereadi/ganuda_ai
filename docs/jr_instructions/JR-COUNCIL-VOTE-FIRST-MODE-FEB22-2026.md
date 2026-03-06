# Jr Instruction: Council Vote-First Mode

**Task ID:** VOTE-FIRST
**Kanban:** #1824
**Priority:** 3
**Assigned:** Software Engineer Jr.
**Council Vote:** #0774f4580abd0cdb

---

## Overview

Add a `/v1/council/vote-first` endpoint that lets specialists vote APPROVE/REJECT/ABSTAIN with a single sentence BEFORE full deliberation. If 6/7 agree, skip the expensive consensus synthesis and return immediately. `high_stakes=true` forces full deliberation.

**Performance target:** Simple decisions (health checks, clear approvals) in <2 seconds instead of 8-12 seconds.

---

## Step 1: Add VoteFirst data class to specialist_council.py

File: `/ganuda/lib/specialist_council.py`

Find the CouncilVote class definition and add a QuickVote class after it:

<<<<<<< SEARCH
class CouncilVote:
=======
class QuickVote:
    """Result of a vote-first quick poll."""
    def __init__(self, question, votes, unanimous, recommendation, confidence, audit_hash):
        self.question = question
        self.votes = votes  # List of {specialist_id, vote, reason}
        self.unanimous = unanimous
        self.recommendation = recommendation
        self.confidence = confidence
        self.audit_hash = audit_hash
        self.skipped_deliberation = unanimous

    def to_dict(self):
        return {
            "question": self.question,
            "votes": self.votes,
            "unanimous": self.unanimous,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "audit_hash": self.audit_hash,
            "skipped_deliberation": self.skipped_deliberation
        }


class CouncilVote:
>>>>>>> REPLACE

---

## Step 2: Add vote_first method to SpecialistCouncil class

File: `/ganuda/lib/specialist_council.py`

Add this method right before the existing `vote` method:

<<<<<<< SEARCH
    def vote(self, question: str, include_responses: bool = False, high_stakes: bool = False) -> CouncilVote:
=======
    def vote_first(self, question: str, high_stakes: bool = False) -> dict:
        """
        Vote-First Mode: Quick poll before full deliberation.

        Each specialist votes APPROVE/REJECT/ABSTAIN + one sentence.
        If 6/7 agree AND not high_stakes, skip full deliberation.

        Returns dict with quick_result OR falls through to full vote.
        """
        if high_stakes:
            print("[COUNCIL] high_stakes=true — forcing full deliberation")
            full = self.vote(question, include_responses=True, high_stakes=True)
            return {"mode": "full_deliberation", "result": full}

        # Quick poll: each specialist votes in <1 sentence
        vote_prompt = (
            f"Quick vote on this question. Reply with EXACTLY one of: "
            f"APPROVE, REJECT, or ABSTAIN, followed by one sentence explaining why.\n\n"
            f"Question: {question}"
        )

        votes = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {}
            for sid, spec in SPECIALISTS.items():
                futures[executor.submit(
                    self._query_specialist_quick, sid, vote_prompt
                )] = sid
            for future in as_completed(futures):
                sid = futures[future]
                try:
                    vote_text = future.result()
                    # Parse vote
                    vote_upper = vote_text.upper()
                    if "APPROVE" in vote_upper:
                        decision = "APPROVE"
                    elif "REJECT" in vote_upper:
                        decision = "REJECT"
                    elif "ABSTAIN" in vote_upper:
                        decision = "ABSTAIN"
                    else:
                        decision = "ABSTAIN"
                    votes.append({
                        "specialist_id": sid,
                        "vote": decision,
                        "reason": vote_text[:200]
                    })
                except Exception as e:
                    votes.append({
                        "specialist_id": sid,
                        "vote": "ABSTAIN",
                        "reason": f"Error: {str(e)[:100]}"
                    })

        # Count votes
        approves = sum(1 for v in votes if v["vote"] == "APPROVE")
        rejects = sum(1 for v in votes if v["vote"] == "REJECT")
        abstains = sum(1 for v in votes if v["vote"] == "ABSTAIN")
        total = len(votes)

        audit_hash = hashlib.sha256(
            f"vote-first-{question}-{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        print(f"[VOTE-FIRST] Results: {approves} approve, {rejects} reject, {abstains} abstain")

        # 6/7 threshold for quick resolution
        if approves >= 6:
            quick = QuickVote(
                question=question,
                votes=votes,
                unanimous=True,
                recommendation="PROCEED",
                confidence=round(approves / total, 3),
                audit_hash=audit_hash
            )
            print(f"[VOTE-FIRST] Quick APPROVE ({approves}/{total}) — skipping deliberation")
            return {"mode": "vote_first", "result": quick}

        elif rejects >= 6:
            quick = QuickVote(
                question=question,
                votes=votes,
                unanimous=True,
                recommendation="BLOCK",
                confidence=round(rejects / total, 3),
                audit_hash=audit_hash
            )
            print(f"[VOTE-FIRST] Quick REJECT ({rejects}/{total}) — skipping deliberation")
            return {"mode": "vote_first", "result": quick}

        else:
            # No consensus — fall through to full deliberation
            print(f"[VOTE-FIRST] No quick consensus — falling through to full deliberation")
            full = self.vote(question, include_responses=True)
            return {"mode": "full_deliberation", "result": full}

    def _query_specialist_quick(self, specialist_id: str, prompt: str) -> str:
        """Quick query to a specialist (max 50 tokens, low temperature)."""
        spec = SPECIALISTS[specialist_id]
        backend = QWEN_BACKEND  # Always use fast path for quick polls
        try:
            response = requests.post(
                f"{backend['url']}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": backend.get("model", "default"),
                    "messages": [
                        {"role": "system", "content": spec["system_prompt"][:500]},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 50,
                    "temperature": 0.3
                },
                timeout=15
            )
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"ABSTAIN: {e}"

    def vote(self, question: str, include_responses: bool = False, high_stakes: bool = False) -> CouncilVote:
>>>>>>> REPLACE

---

## Step 3: Add the /v1/council/vote-first endpoint to gateway

File: `/ganuda/lib/gateway.py`

Find the existing `/v1/council/vote` endpoint and add the vote-first endpoint after it:

<<<<<<< SEARCH
@app.post("/v1/council/vote")
=======
@app.post("/v1/council/vote-first")
async def council_vote_first(request: Request):
    """Vote-First Council Mode: Quick poll, skip deliberation if 6/7 agree."""
    try:
        data = await request.json()
        question = data.get("question", "")
        high_stakes = data.get("high_stakes", False)

        if not question:
            return JSONResponse({"error": "question is required"}, status_code=400)

        council = SpecialistCouncil()
        result = council.vote_first(question, high_stakes=high_stakes)

        mode = result.get("mode", "unknown")
        vote_result = result.get("result")

        if mode == "vote_first":
            return JSONResponse({
                "mode": "vote_first",
                "recommendation": vote_result.recommendation,
                "confidence": vote_result.confidence,
                "votes": vote_result.votes,
                "unanimous": vote_result.unanimous,
                "skipped_deliberation": vote_result.skipped_deliberation,
                "audit_hash": vote_result.audit_hash
            })
        else:
            # Full deliberation result
            return JSONResponse({
                "mode": "full_deliberation",
                "consensus": vote_result.consensus,
                "recommendation": vote_result.recommendation,
                "confidence": vote_result.confidence,
                "concerns": vote_result.concerns,
                "audit_hash": vote_result.audit_hash
            })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/v1/council/vote")
>>>>>>> REPLACE

---

## Verification

After applying, restart the gateway and test:
```text
sudo systemctl restart llm-gateway
```

Test vote-first (should be fast for simple questions):
```text
curl -s http://localhost:8080/v1/council/vote-first -X POST \
  -H 'Content-Type: application/json' \
  -d '{"question": "Should we add a /health endpoint to the VetAssist backend?"}' \
  | python3 -m json.tool
```

Test high_stakes override:
```text
curl -s http://localhost:8080/v1/council/vote-first -X POST \
  -H 'Content-Type: application/json' \
  -d '{"question": "Should we migrate to MongoDB?", "high_stakes": true}' \
  | python3 -m json.tool
```

---

## Notes

- Quick poll uses max_tokens=50 (vs 300 for full deliberation) = ~6x faster per specialist
- System prompt truncated to 500 chars for quick polls (domain identity only, not full rubric)
- Always uses QWEN_BACKEND (redfin) for quick polls — no Long Man routing overhead
- Falls through to full deliberation if no 6/7 consensus, so no accuracy loss
- `high_stakes=true` bypasses vote-first entirely
