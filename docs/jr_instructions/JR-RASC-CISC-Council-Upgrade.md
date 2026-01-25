# Jr Instructions: RASC/CISC Council Voting Upgrade

**Task ID**: RASC-COUNCIL-001
**Priority**: HIGH (Council-Approved 7-0-0)
**Estimated Effort**: 2-3 days
**Target File**: `/ganuda/lib/specialist_council.py`
**Secondary File**: `/ganuda/services/llm_gateway/gateway.py`

---

## Executive Summary

Implement RASC (Reasoning-Aware Self-Consistency) and CISC (Confidence-Integrated Self-Consistency) enhancements to the 7-Specialist Council voting system. Expected outcome: **70-80% reduction in Council token usage** while maintaining or improving decision quality.

---

## Research Background

### RASC (NAACL 2025)
- Dynamic early-stopping based on reasoning path quality
- Evaluates not just vote agreement but reasoning confidence
- Stops polling when consensus is mathematically locked OR high-confidence agreement reached

### CISC (ACL 2025)
- Confidence-weighted vote aggregation
- High-confidence votes count more than uncertain ones
- P-True method: probability model assigns to answer being correct

### Key Innovation for Cherokee AI
- Don't poll all 7 specialists when first 4 agree with high confidence
- Weight votes by confidence (a 0.95 confidence APPROVE counts more than 0.6)
- Track calibration over time to improve confidence accuracy

---

## Current State Analysis

**File**: `/ganuda/lib/specialist_council.py` (v1.3)

**Current `vote_first()` behavior**:
1. Polls ALL 7 specialists in parallel (ThreadPoolExecutor)
2. Each returns: VOTE + REASON (no confidence)
3. Simple count: if APPROVE >= threshold → APPROVED
4. All votes weighted equally
5. Deliberation only if contested or high_stakes

**Current `VOTE_FIRST_PROMPT`**:
```python
VOTE_FIRST_PROMPT = """
Vote on this question with a single word and one sentence:

VOTE: [APPROVE/REJECT/ABSTAIN]
REASON: [One sentence only]

Do not provide full analysis yet. Just vote.
"""
```

**What's Missing**:
1. No confidence scores
2. No early stopping
3. No weighted voting
4. All 7 always polled

---

## Implementation Specification

### Phase A: New Dataclasses

Add after line 244 (after `VoteFirstResult`):

```python
@dataclass
class ConfidentVoteResponse:
    """Vote response with confidence score for RASC/CISC"""
    specialist_id: str
    name: str
    vote: str  # APPROVE, REJECT, ABSTAIN
    confidence: float  # 0.0 to 1.0
    reason: str
    response_time_ms: int = 0


@dataclass
class RASCVoteResult:
    """Result from RASC/CISC enhanced voting"""
    question: str
    decision: str  # APPROVED, REJECTED, CONTESTED
    votes: Dict[str, ConfidentVoteResponse]
    vote_counts: Dict[str, int]
    weighted_scores: Dict[str, float]  # Confidence-weighted scores
    early_stopped: bool
    specialists_polled: int  # May be < 7 if early stopped
    stop_reason: str  # Why we stopped (or "full_poll")
    aggregate_confidence: float  # Final decision confidence
    deliberation: Optional[str] = None
    audit_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
```

### Phase B: New Prompt with Confidence

Add after `VOTE_FIRST_PROMPT` (around line 197):

```python
# RASC/CISC voting prompt with confidence scoring
RASC_VOTE_PROMPT = """You are {name}, the {role} specialist on the Cherokee AI Council.

Vote on this question. Provide ALL THREE fields:

VOTE: [APPROVE/REJECT/ABSTAIN]
CONFIDENCE: [0.0-1.0]
REASON: [One sentence]

Confidence guidelines:
- 0.9-1.0: Extremely certain, clear decision
- 0.7-0.9: Confident, minor reservations
- 0.5-0.7: Moderate certainty, some concerns
- 0.3-0.5: Uncertain, significant doubts
- 0.0-0.3: Very uncertain, near-abstain

Question: {question}"""

# Specialist order optimized for early stopping (diverse perspectives first)
RASC_SPECIALIST_ORDER = [
    "raven",       # Strategic - broad view, good first signal
    "crawdad",     # Security - catches blockers early
    "turtle",      # Seven Generations - values alignment
    "gecko",       # Technical - feasibility check
    "peace_chief", # Consensus - synthesis perspective
    "spider",      # Integration - connection check
    "eagle_eye"    # Monitoring - observability (often least critical)
]
```

### Phase C: New Parse Function

Add after `parse_vote()` function (around line 263):

```python
def parse_confident_vote(response: str) -> tuple:
    """
    Parse VOTE, CONFIDENCE, and REASON from RASC response.

    Returns: (vote, confidence, reason)
    """
    vote = "ABSTAIN"
    confidence = 0.5  # Default moderate confidence
    reason = ""

    for line in response.split("\n"):
        line = line.strip()
        upper_line = line.upper()

        if upper_line.startswith("VOTE:"):
            vote_text = line.split(":", 1)[1].strip().upper()
            if "APPROVE" in vote_text:
                vote = "APPROVE"
            elif "REJECT" in vote_text:
                vote = "REJECT"
            # else stays ABSTAIN

        elif upper_line.startswith("CONFIDENCE:"):
            try:
                conf_text = line.split(":", 1)[1].strip()
                # Handle various formats: "0.85", "85%", ".85", "85"
                conf_text = conf_text.replace("%", "").strip()
                conf = float(conf_text)
                if conf > 1.0:
                    conf = conf / 100.0  # Assume percentage
                confidence = max(0.0, min(1.0, conf))
            except (ValueError, IndexError):
                confidence = 0.5  # Default on parse error

        elif upper_line.startswith("REASON:"):
            reason = line.split(":", 1)[1].strip() if ":" in line else ""

    return vote, confidence, reason
```

### Phase D: Early Stopping Logic

Add as a method in `SpecialistCouncil` class (after `_run_deliberation_round`):

```python
def _should_stop_early(
    self,
    votes: List[ConfidentVoteResponse],
    threshold: int,
    confidence_threshold: float,
    remaining_count: int,
    min_specialists: int
) -> tuple:
    """
    RASC early stopping logic.

    Determines if we should stop polling more specialists.

    Args:
        votes: Votes collected so far
        threshold: Base vote count needed
        confidence_threshold: Aggregate confidence to trigger early stop
        remaining_count: Specialists not yet polled
        min_specialists: Minimum to poll before early stop allowed

    Returns:
        (should_stop: bool, reason: str)
    """
    polled = len(votes)

    # Never stop before minimum
    if polled < min_specialists:
        return False, "below_minimum"

    approve_count = sum(1 for v in votes if v.vote == "APPROVE")
    reject_count = sum(1 for v in votes if v.vote == "REJECT")

    weighted_approve = sum(v.confidence for v in votes if v.vote == "APPROVE")
    weighted_reject = sum(v.confidence for v in votes if v.vote == "REJECT")

    # Case 1: Mathematical lock-in (threshold already reached)
    if approve_count >= threshold:
        return True, "threshold_approve"
    if reject_count >= threshold:
        return True, "threshold_reject"

    # Case 2: Mathematically impossible to reach threshold
    # (Even all remaining votes can't change outcome to non-contested)
    max_possible_approve = approve_count + remaining_count
    max_possible_reject = reject_count + remaining_count

    if max_possible_approve < threshold and max_possible_reject < threshold:
        return True, "contested_locked"

    # Case 3: High-confidence consensus (RASC innovation)
    if polled >= min_specialists:
        avg_confidence = sum(v.confidence for v in votes) / polled

        # 80%+ agreement with high average confidence
        agreement_ratio = max(approve_count, reject_count) / polled

        if agreement_ratio >= 0.8 and avg_confidence >= confidence_threshold:
            if approve_count > reject_count:
                return True, "high_confidence_approve"
            else:
                return True, "high_confidence_reject"

    # Case 4: Weighted scores indicate clear winner
    total_weight = weighted_approve + weighted_reject
    if total_weight > 0 and polled >= min_specialists:
        weight_ratio = max(weighted_approve, weighted_reject) / total_weight
        if weight_ratio >= 0.85:  # 85% of weight on one side
            if weighted_approve > weighted_reject:
                return True, "weighted_approve"
            else:
                return True, "weighted_reject"

    return False, "continue"
```

### Phase E: Weighted Decision Calculation

Add as a method in `SpecialistCouncil` class:

```python
def _weighted_decision(
    self,
    votes: List[ConfidentVoteResponse],
    threshold: int
) -> tuple:
    """
    CISC confidence-weighted decision calculation.

    Args:
        votes: All collected votes
        threshold: Base threshold for simple majority fallback

    Returns:
        (decision: str, aggregate_confidence: float, weighted_scores: dict)
    """
    weighted_approve = sum(v.confidence for v in votes if v.vote == "APPROVE")
    weighted_reject = sum(v.confidence for v in votes if v.vote == "REJECT")
    weighted_abstain = sum(v.confidence for v in votes if v.vote == "ABSTAIN")

    approve_count = sum(1 for v in votes if v.vote == "APPROVE")
    reject_count = sum(1 for v in votes if v.vote == "REJECT")

    total_weight = weighted_approve + weighted_reject + weighted_abstain

    weighted_scores = {
        "APPROVE": round(weighted_approve, 3),
        "REJECT": round(weighted_reject, 3),
        "ABSTAIN": round(weighted_abstain, 3)
    }

    # Decision logic:
    # 1. If threshold met by count, use that
    # 2. Otherwise, use weighted scores
    # 3. If tied, mark as contested

    if approve_count >= threshold:
        confidence = weighted_approve / total_weight if total_weight > 0 else 0.5
        return "APPROVED", round(confidence, 3), weighted_scores

    if reject_count >= threshold:
        confidence = weighted_reject / total_weight if total_weight > 0 else 0.5
        return "REJECTED", round(confidence, 3), weighted_scores

    # No threshold met - use weighted scores
    if weighted_approve > weighted_reject * 1.2:  # 20% margin
        confidence = weighted_approve / total_weight if total_weight > 0 else 0.5
        return "APPROVED", round(confidence, 3), weighted_scores

    if weighted_reject > weighted_approve * 1.2:  # 20% margin
        confidence = weighted_reject / total_weight if total_weight > 0 else 0.5
        return "REJECTED", round(confidence, 3), weighted_scores

    # Too close - contested
    return "CONTESTED", 0.5, weighted_scores
```

### Phase F: Main RASC Vote Method

Add as a method in `SpecialistCouncil` class (after `vote_first`):

```python
def vote_first_rasc(
    self,
    question: str,
    threshold: int = 6,
    confidence_threshold: float = 0.85,
    min_specialists: int = 3,
    high_stakes: bool = False
) -> RASCVoteResult:
    """
    RASC/CISC enhanced voting-first council query.

    Key improvements over standard vote_first:
    1. Confidence-weighted voting
    2. Dynamic early stopping
    3. Optimized specialist ordering
    4. Reasoning-aware consensus

    Args:
        question: Question to vote on
        threshold: Votes needed for consensus (default 6/7)
        confidence_threshold: Confidence level to trigger early stop (default 0.85)
        min_specialists: Minimum specialists before early stop allowed (default 3)
        high_stakes: Force all 7 specialists, disable early stopping

    Returns:
        RASCVoteResult with decision, votes, confidence, and metrics
    """
    votes = []
    votes_dict = {}
    stop_reason = "full_poll"

    # Use optimized order for early stopping efficiency
    specialist_order = RASC_SPECIALIST_ORDER

    # Query specialists in order, checking for early stop after each
    for i, specialist_id in enumerate(specialist_order):
        spec = SPECIALISTS[specialist_id]
        start_time = datetime.now()

        # Build specialist-specific prompt
        prompt = RASC_VOTE_PROMPT.format(
            name=spec["name"],
            role=spec["role"],
            question=question
        )

        try:
            response = requests.post(
                VLLM_URL,
                json={
                    "model": VLLM_MODEL,
                    "messages": [
                        {"role": "system", "content": spec["system_prompt"]},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.7
                },
                timeout=60
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            vote, confidence, reason = parse_confident_vote(content)

            vote_response = ConfidentVoteResponse(
                specialist_id=specialist_id,
                name=spec["name"],
                vote=vote,
                confidence=confidence,
                reason=reason,
                response_time_ms=elapsed_ms
            )

        except Exception as e:
            # On error, record abstain with low confidence
            vote_response = ConfidentVoteResponse(
                specialist_id=specialist_id,
                name=spec["name"],
                vote="ABSTAIN",
                confidence=0.3,
                reason=f"Error: {str(e)}",
                response_time_ms=0
            )

        votes.append(vote_response)
        votes_dict[specialist_id] = vote_response

        # Check for early stopping (unless high_stakes)
        if not high_stakes:
            remaining = len(specialist_order) - (i + 1)
            should_stop, reason = self._should_stop_early(
                votes=votes,
                threshold=threshold,
                confidence_threshold=confidence_threshold,
                remaining_count=remaining,
                min_specialists=min_specialists
            )

            if should_stop:
                stop_reason = reason
                break

    # Calculate vote counts
    vote_counts = {"APPROVE": 0, "REJECT": 0, "ABSTAIN": 0}
    for v in votes:
        vote_counts[v.vote] += 1

    # Calculate weighted decision
    decision, aggregate_confidence, weighted_scores = self._weighted_decision(
        votes=votes,
        threshold=threshold
    )

    # Determine if we early stopped
    early_stopped = len(votes) < len(specialist_order)

    # Run deliberation if contested OR high_stakes
    deliberation = None
    if decision == "CONTESTED" or high_stakes:
        deliberation = self._run_rasc_deliberation(question, votes, decision)
        if high_stakes and decision != "CONTESTED":
            deliberation = f"[HIGH-STAKES FORCED DELIBERATION]\n{deliberation}"

    # Generate audit hash
    audit_hash = hashlib.sha256(
        f"{question}{datetime.now().isoformat()}rasc".encode()
    ).hexdigest()[:16]

    result = RASCVoteResult(
        question=question,
        decision=decision,
        votes=votes_dict,
        vote_counts=vote_counts,
        weighted_scores=weighted_scores,
        early_stopped=early_stopped,
        specialists_polled=len(votes),
        stop_reason=stop_reason,
        aggregate_confidence=aggregate_confidence,
        deliberation=deliberation,
        audit_hash=audit_hash
    )

    # Log to database
    self._log_rasc_vote(result)

    return result


def _run_rasc_deliberation(
    self,
    question: str,
    votes: List[ConfidentVoteResponse],
    decision: str
) -> str:
    """Run deliberation round for RASC, including confidence info."""
    vote_summary = f"Question: {question}\n\nVotes with confidence:\n"
    for v in votes:
        vote_summary += f"- {v.name}: {v.vote} (confidence: {v.confidence:.2f}) - {v.reason}\n"

    vote_summary += f"\nPreliminary decision: {decision}\n"
    vote_summary += "\nProvide brief deliberation on contested points (2-3 sentences)."

    try:
        response = requests.post(
            VLLM_URL,
            json={
                "model": VLLM_MODEL,
                "messages": [
                    {"role": "system", "content": INFRASTRUCTURE_CONTEXT + "You are Peace Chief. Deliberate on these votes, considering confidence levels."},
                    {"role": "user", "content": vote_summary}
                ],
                "max_tokens": 200,
                "temperature": 0.6
            },
            timeout=60
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Deliberation failed: {str(e)}"


def _log_rasc_vote(self, result: RASCVoteResult):
    """Log RASC vote result to database with enhanced metrics."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Prepare detailed vote summary
        vote_summary = {
            "mode": "rasc",
            "votes": {
                k: {
                    "vote": v.vote,
                    "confidence": v.confidence,
                    "reason": v.reason
                }
                for k, v in result.votes.items()
            },
            "counts": result.vote_counts,
            "weighted_scores": result.weighted_scores,
            "early_stopped": result.early_stopped,
            "specialists_polled": result.specialists_polled,
            "stop_reason": result.stop_reason
        }

        # Log to council_votes
        cur.execute("""
            INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concerns, voted_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            result.audit_hash,
            result.question,
            f"RASC: {result.decision} ({result.specialists_polled}/7 polled)",
            result.aggregate_confidence,
            json.dumps(vote_summary)
        ))

        # Log to thermal memory with RASC metrics
        metadata = {
            "type": "council_vote_rasc",
            "audit_hash": result.audit_hash,
            "decision": result.decision,
            "vote_counts": result.vote_counts,
            "weighted_scores": result.weighted_scores,
            "early_stopped": result.early_stopped,
            "specialists_polled": result.specialists_polled,
            "stop_reason": result.stop_reason,
            "aggregate_confidence": result.aggregate_confidence,
            "had_deliberation": result.deliberation is not None
        }

        # Calculate token savings estimate
        tokens_saved = (7 - result.specialists_polled) * 100  # ~100 tokens per specialist
        savings_percent = round((7 - result.specialists_polled) / 7 * 100, 1)

        content = f"COUNCIL VOTE (RASC): {result.question}\n"
        content += f"DECISION: {result.decision} (confidence: {result.aggregate_confidence:.2f})\n"
        content += f"SPECIALISTS POLLED: {result.specialists_polled}/7 ({result.stop_reason})\n"
        content += f"VOTES: {result.vote_counts['APPROVE']} approve, {result.vote_counts['REJECT']} reject, {result.vote_counts['ABSTAIN']} abstain\n"
        content += f"WEIGHTED: approve={result.weighted_scores['APPROVE']:.2f}, reject={result.weighted_scores['REJECT']:.2f}\n"
        content += f"TOKEN SAVINGS: ~{tokens_saved} tokens ({savings_percent}% reduction)\n"
        if result.deliberation:
            content += f"DELIBERATION: {result.deliberation}"

        cur.execute("""
            INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, %s, %s)
        """, (result.audit_hash, content, 90.0, json.dumps(metadata)))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"RASC DB logging error: {e}")
```

### Phase G: Convenience Function

Add at the end of the file (before `if __name__ == "__main__"`):

```python
def council_vote_rasc(
    question: str,
    threshold: int = 6,
    confidence_threshold: float = 0.85,
    min_specialists: int = 3,
    high_stakes: bool = False
) -> dict:
    """
    RASC/CISC enhanced council vote - returns dict for API compatibility.

    Features:
    - 70-80% token reduction through early stopping
    - Confidence-weighted voting
    - Optimized specialist ordering

    Args:
        question: Question to vote on
        threshold: Votes needed (default 6)
        confidence_threshold: Confidence for early stop (default 0.85)
        min_specialists: Min before early stop (default 3)
        high_stakes: Force all 7 specialists

    Returns:
        Dict with decision, votes, confidence, and RASC metrics
    """
    council = SpecialistCouncil()
    result = council.vote_first_rasc(
        question=question,
        threshold=threshold,
        confidence_threshold=confidence_threshold,
        min_specialists=min_specialists,
        high_stakes=high_stakes
    )

    return {
        "question": result.question,
        "decision": result.decision,
        "vote_counts": result.vote_counts,
        "weighted_scores": result.weighted_scores,
        "votes": {
            k: {
                "name": v.name,
                "vote": v.vote,
                "confidence": v.confidence,
                "reason": v.reason,
                "response_time_ms": v.response_time_ms
            }
            for k, v in result.votes.items()
        },
        "early_stopped": result.early_stopped,
        "specialists_polled": result.specialists_polled,
        "stop_reason": result.stop_reason,
        "aggregate_confidence": result.aggregate_confidence,
        "deliberation": result.deliberation,
        "audit_hash": result.audit_hash,
        "timestamp": result.timestamp.isoformat(),
        # Metrics for monitoring
        "tokens_saved_estimate": (7 - result.specialists_polled) * 100,
        "efficiency_percent": round((7 - result.specialists_polled) / 7 * 100, 1)
    }
```

---

## Gateway Integration

### File: `/ganuda/services/llm_gateway/gateway.py`

Add new endpoint (after `/v1/council/vote-first`):

```python
@app.post("/v1/council/vote-rasc")
async def council_vote_rasc_endpoint(
    request: Request,
    body: dict,
    api_key: str = Depends(verify_api_key)
):
    """
    RASC/CISC enhanced council voting endpoint.

    Features early stopping, confidence weighting, and optimized specialist ordering.
    Expected 70-80% token reduction on clear decisions.

    Request body:
        question: str - The question to vote on
        threshold: int (optional, default 6) - Votes needed
        confidence_threshold: float (optional, default 0.85) - For early stop
        min_specialists: int (optional, default 3) - Min before early stop
        high_stakes: bool (optional, default false) - Force all 7

    Returns:
        Decision with confidence, votes, weighted scores, and efficiency metrics
    """
    from specialist_council import council_vote_rasc

    question = body.get("question")
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    threshold = body.get("threshold", 6)
    confidence_threshold = body.get("confidence_threshold", 0.85)
    min_specialists = body.get("min_specialists", 3)
    high_stakes = body.get("high_stakes", False)

    result = council_vote_rasc(
        question=question,
        threshold=threshold,
        confidence_threshold=confidence_threshold,
        min_specialists=min_specialists,
        high_stakes=high_stakes
    )

    return JSONResponse(content=result)
```

---

## Testing

### Test Script: `/ganuda/lib/test_rasc.py`

```python
#!/usr/bin/env python3
"""Test RASC/CISC council voting implementation"""

from specialist_council import council_vote_rasc, council_vote_first

def test_rasc_vs_standard():
    """Compare RASC to standard voting"""

    questions = [
        # Clear approve cases (should early stop)
        "Should we add input validation to API endpoints?",
        "Should we implement proper error handling?",

        # Clear reject cases (should early stop)
        "Should we disable all security features?",
        "Should we delete production backups?",

        # Contested cases (should poll all 7)
        "Should we migrate from PostgreSQL to MongoDB?",
    ]

    print("=" * 60)
    print("RASC vs Standard Comparison")
    print("=" * 60)

    for q in questions:
        print(f"\nQuestion: {q[:50]}...")

        # RASC vote
        rasc = council_vote_rasc(q)

        # Standard vote (for comparison)
        standard = council_vote_first(q)

        print(f"  RASC: {rasc['decision']} | {rasc['specialists_polled']}/7 polled | "
              f"confidence: {rasc['aggregate_confidence']:.2f} | "
              f"saved: {rasc['efficiency_percent']}%")
        print(f"  Standard: {standard['decision']} | 7/7 polled")

        if rasc['early_stopped']:
            print(f"  Early stop reason: {rasc['stop_reason']}")


def test_confidence_parsing():
    """Test confidence parsing from various formats"""
    from specialist_council import parse_confident_vote

    test_cases = [
        ("VOTE: APPROVE\nCONFIDENCE: 0.85\nREASON: Good idea", ("APPROVE", 0.85, "Good idea")),
        ("VOTE: REJECT\nCONFIDENCE: 95%\nREASON: Security risk", ("REJECT", 0.95, "Security risk")),
        ("VOTE: ABSTAIN\nCONFIDENCE: .5\nREASON: Not enough info", ("ABSTAIN", 0.5, "Not enough info")),
        ("VOTE: APPROVE\nCONFIDENCE: 75\nREASON: Looks fine", ("APPROVE", 0.75, "Looks fine")),
    ]

    print("\n" + "=" * 60)
    print("Confidence Parsing Tests")
    print("=" * 60)

    for input_text, expected in test_cases:
        result = parse_confident_vote(input_text)
        passed = result == expected
        print(f"  {'PASS' if passed else 'FAIL'}: {result}")


if __name__ == "__main__":
    test_confidence_parsing()
    test_rasc_vs_standard()
```

### Run Tests

```bash
# On redfin
cd /ganuda/lib
python3 test_rasc.py
```

### API Tests

```bash
# Test RASC endpoint
curl -X POST 'http://localhost:8080/v1/council/vote-rasc' \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5' \
  -d '{"question": "Should we add input validation to all API endpoints?"}'

# Compare to standard
curl -X POST 'http://localhost:8080/v1/council/vote-first' \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5' \
  -d '{"question": "Should we add input validation to all API endpoints?"}'
```

---

## Success Metrics

After deployment, track:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Token reduction | 70-80% | `tokens_saved_estimate` in response |
| Early stop rate | >60% of clear decisions | `early_stopped` flag |
| Decision accuracy | No regression | Compare to historical |
| Response latency | 30-50% faster | `response_time_ms` |
| Confidence calibration | >80% accurate | Track decisions vs outcomes |

---

## Rollback Procedure

If issues arise:

1. **Immediate**: Use `/v1/council/vote-first` (unchanged endpoint)
2. **Revert code**:
   ```bash
   cd /ganuda/lib
   git checkout HEAD~1 specialist_council.py
   ```
3. **Restart gateway**:
   ```bash
   sudo systemctl restart llm-gateway
   ```

---

## Deployment Checklist

- [ ] Backup current `specialist_council.py`
- [ ] Add new dataclasses (`ConfidentVoteResponse`, `RASCVoteResult`)
- [ ] Add `RASC_VOTE_PROMPT` and `RASC_SPECIALIST_ORDER`
- [ ] Add `parse_confident_vote()` function
- [ ] Add `_should_stop_early()` method
- [ ] Add `_weighted_decision()` method
- [ ] Add `vote_first_rasc()` method
- [ ] Add `_run_rasc_deliberation()` method
- [ ] Add `_log_rasc_vote()` method
- [ ] Add `council_vote_rasc()` convenience function
- [ ] Update gateway with new endpoint
- [ ] Run test script
- [ ] Test via curl
- [ ] Monitor first 10 production votes
- [ ] Update KB article with results

---

## Notes for TPM

- This implementation is backwards-compatible - existing endpoints unchanged
- RASC mode can be enabled gradually by switching callers to new endpoint
- Confidence calibration should be monitored weekly
- Consider A/B testing RASC vs standard for 1 week before full rollout

---

*For Seven Generations*

**Jr Assignment**: Implement RASC/CISC Council Upgrade
**Assigned**: 2025-12-27
**Due**: 2025-12-30
