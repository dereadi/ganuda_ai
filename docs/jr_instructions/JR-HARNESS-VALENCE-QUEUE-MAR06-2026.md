# Jr Instruction: Harness Retrospective Valence Queue

**Task**: Add retrospective evaluation (EVALUATE phase) to the graduated harness
**Priority**: 2 (Depends on SRE Protocol Dataclasses)
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 8
**use_rlm**: false

## Context

The graduated harness has SENSE (validate + stakes detection) and REACT (tier handler chain) but
NO retrospective evaluation. Confidence scoring at Tier 1 is INLINE -- it happens at reaction time.
True valence is RETROSPECTIVE -- it happens later when we know if the answer was actually good.

This is the biggest gap found in the SRE+C codebase audit: the brain never reviews what the
spinal cord did. Tier 1 reflex answers fire and the system forgets.

DC-11: EVALUATE must be architecturally distinct from REACT.
DC-10: The reflex fires now. The brain evaluates later. Both are required.
Coyote condition: Without this, the organism runs blind.

## Steps

### Step 1: Create the valence evaluator module

Create `/ganuda/lib/harness/valence_evaluator.py`

```python
"""
Harness Valence Evaluator -- Retrospective assessment of past reactions.

DC-11 EVALUATE phase: The brain reviews what the spinal cord did.
This happens AFTER the response was delivered to the user.

The evaluator:
1. Pulls pending reactions from the valence queue
2. Scores them retrospectively (was the answer good?)
3. Stores Valence results in thermal memory
4. Feeds calibration data back to the harness

Timing: runs as a background task, not in the hot path.
"""

import logging
import time
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("harness.valence")

# Import SRE protocol types
from lib.harness.sre_protocol import Signal, Reaction, Valence, Urgency


@dataclass
class PendingReaction:
    """A reaction waiting for retrospective evaluation."""
    request_id: str
    tier_used: int
    query: str
    answer: str
    confidence: float
    latency_ms: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ValenceQueue:
    """In-memory queue of reactions awaiting retrospective evaluation.

    In v1, this is a simple list. Future: backed by thermal_memory_archive
    or a dedicated postgres table.
    """

    def __init__(self, max_size: int = 1000):
        self._queue: List[PendingReaction] = []
        self._max_size = max_size

    def enqueue(self, reaction: PendingReaction) -> None:
        """Add a reaction to the evaluation queue."""
        if len(self._queue) >= self._max_size:
            # Drop oldest -- backpressure, not crash
            dropped = self._queue.pop(0)
            logger.warning(
                "Valence queue full (%d), dropped oldest: %s",
                self._max_size, dropped.request_id,
            )
        self._queue.append(reaction)
        logger.debug("Enqueued reaction %s for evaluation", reaction.request_id)

    def dequeue_batch(self, batch_size: int = 10) -> List[PendingReaction]:
        """Pull a batch of reactions for evaluation."""
        batch = self._queue[:batch_size]
        self._queue = self._queue[batch_size:]
        return batch

    def size(self) -> int:
        return len(self._queue)


class ValenceEvaluator:
    """Retrospective evaluator for harness reactions.

    v1 heuristics (no LLM call needed):
    - Requery detection: did the user ask the same question again? (bad sign)
    - Confidence calibration: was inline confidence accurate vs actual outcome?
    - Latency assessment: did the reaction meet its tier's latency target?
    - Escalation rate: are too many Tier 1 answers getting escalated?

    Future:
    - Use Tier 2 to review Tier 1 answers (brain reviewing spinal cord)
    - User feedback integration
    - Downstream error correlation
    """

    def __init__(self):
        self._requery_window: Dict[str, List[float]] = {}
        self._calibration_history: List[Dict[str, Any]] = []

    def evaluate_batch(
        self,
        reactions: List[PendingReaction],
        requery_queries: Optional[Dict[str, int]] = None,
    ) -> List[Valence]:
        """Evaluate a batch of pending reactions.

        Args:
            reactions: Reactions to evaluate.
            requery_queries: Map of query_hash -> requery_count for detecting
                repeated questions (signal of bad answers).

        Returns:
            List of Valence objects with retrospective scores.
        """
        results = []
        requery_queries = requery_queries or {}

        for reaction in reactions:
            score = self._score_reaction(reaction, requery_queries)
            delay_ms = (time.time() - reaction.timestamp) * 1000

            valence = Valence(
                reaction_id=reaction.request_id,
                score=score,
                evaluator="harness_valence_v1",
                delay_ms=delay_ms,
                feedback={
                    "tier_used": reaction.tier_used,
                    "inline_confidence": reaction.confidence,
                    "retrospective_score": score,
                    "delta": round(score - reaction.confidence, 3),
                },
            )

            # If score diverges significantly from inline confidence,
            # flag for calibration
            if abs(score - reaction.confidence) > 0.3:
                valence.calibration = {
                    "action": "adjust_confidence_heuristic",
                    "inline_was": reaction.confidence,
                    "retrospective_is": score,
                    "tier": reaction.tier_used,
                }
                logger.info(
                    "Calibration needed: inline=%.3f retro=%.3f delta=%.3f [%s]",
                    reaction.confidence, score,
                    score - reaction.confidence, reaction.request_id,
                )

            results.append(valence)

        return results

    def _score_reaction(
        self,
        reaction: PendingReaction,
        requery_queries: Dict[str, int],
    ) -> float:
        """Score a single reaction retrospectively.

        Heuristics (v1):
        - Start at inline confidence (trust the reflex initially)
        - Penalize if query was re-asked (user wasn't satisfied)
        - Penalize if answer was very short for a complex query
        - Penalize if latency exceeded tier target
        - Bonus if answer contained structured/specific information
        """
        score = reaction.confidence

        # Requery penalty: user asked same question again
        query_hash = str(hash(reaction.query.lower().strip()))
        requery_count = requery_queries.get(query_hash, 0)
        if requery_count > 0:
            penalty = min(0.3, requery_count * 0.15)
            score -= penalty
            logger.debug(
                "Requery penalty: -%0.2f (asked %d times) [%s]",
                penalty, requery_count, reaction.request_id,
            )

        # Short answer penalty for long queries
        if len(reaction.query) > 100 and len(reaction.answer) < 50:
            score -= 0.15

        # Latency penalty (tier-specific targets)
        tier_targets = {1: 50, 2: 500, 3: 120000}
        target = tier_targets.get(reaction.tier_used, 500)
        if reaction.latency_ms > target * 2:
            score -= 0.1

        # Structured content bonus (lists, numbers, specific terms)
        if any(marker in reaction.answer for marker in ['\n-', '\n1.', '\n*', '```']):
            score += 0.05

        return max(-1.0, min(1.0, round(score, 3)))
```

### Step 2: Wire the valence queue into EscalationEngine

File: `/ganuda/lib/harness/escalation.py`

```text
<<<<<<< SEARCH
from lib.harness.config import HarnessConfig, load_harness_config
=======
from lib.harness.config import HarnessConfig, load_harness_config
from lib.harness.valence_evaluator import ValenceQueue, PendingReaction
>>>>>>> REPLACE
```

Add the valence queue to the engine init:

```text
<<<<<<< SEARCH
    def __init__(self, config: Optional[HarnessConfig] = None):
        self.config = config or load_harness_config()
        self._tier_handlers: Dict[int, TierHandler] = {}
        # Rate limiting: {user_id: [timestamp, ...]}
        self._tier3_calls: Dict[str, List[float]] = defaultdict(list)
=======
    def __init__(self, config: Optional[HarnessConfig] = None):
        self.config = config or load_harness_config()
        self._tier_handlers: Dict[int, TierHandler] = {}
        # Rate limiting: {user_id: [timestamp, ...]}
        self._tier3_calls: Dict[str, List[float]] = defaultdict(list)
        # Valence queue: reactions awaiting retrospective evaluation
        self._valence_queue = ValenceQueue(max_size=1000)
>>>>>>> REPLACE
```

Add valence enqueue after building the response. In `_build_response`:

```text
<<<<<<< SEARCH
    def _build_response(
        self,
        final_result: TierResult,
        escalation_path: List[int],
        start_time: float,
        request: HarnessRequest,
    ) -> HarnessResponse:
        """Build the final HarnessResponse from tier results."""
        total_latency = (time.time() - start_time) * 1000  # ms
        return HarnessResponse(
            answer=final_result.answer,
            tier_used=final_result.tier,
            confidence=final_result.confidence,
            escalation_path=escalation_path,
            latency_ms=total_latency,
            diversity_score=final_result.diversity_score,
            council_vote_id=final_result.council_vote_id,
            request_id=request.request_id,
            metadata=final_result.metadata,
        )
=======
    def _build_response(
        self,
        final_result: TierResult,
        escalation_path: List[int],
        start_time: float,
        request: HarnessRequest,
    ) -> HarnessResponse:
        """Build the final HarnessResponse from tier results."""
        total_latency = (time.time() - start_time) * 1000  # ms
        response = HarnessResponse(
            answer=final_result.answer,
            tier_used=final_result.tier,
            confidence=final_result.confidence,
            escalation_path=escalation_path,
            latency_ms=total_latency,
            diversity_score=final_result.diversity_score,
            council_vote_id=final_result.council_vote_id,
            request_id=request.request_id,
            metadata=final_result.metadata,
        )

        # Enqueue for retrospective valence evaluation (SRE+C EVALUATE phase)
        self._valence_queue.enqueue(PendingReaction(
            request_id=request.request_id,
            tier_used=final_result.tier,
            query=request.query,
            answer=final_result.answer,
            confidence=final_result.confidence,
            latency_ms=total_latency,
            timestamp=time.time(),
            metadata={"escalation_path": escalation_path},
        ))

        return response
>>>>>>> REPLACE
```

## Verification

```text
cd /ganuda && python3 -c "
from lib.harness.valence_evaluator import ValenceQueue, ValenceEvaluator, PendingReaction
import time

# Test queue
q = ValenceQueue(max_size=5)
for i in range(3):
    q.enqueue(PendingReaction(
        request_id=f'test_{i}', tier_used=1, query='what is AI?',
        answer='AI is artificial intelligence.', confidence=0.75,
        latency_ms=45.0, timestamp=time.time() - 300,
    ))
print(f'Queue size: {q.size()}')

# Test evaluator
evaluator = ValenceEvaluator()
batch = q.dequeue_batch(10)
valences = evaluator.evaluate_batch(batch)
for v in valences:
    print(f'Valence: score={v.score}, delay={v.delay_ms:.0f}ms, calibration={v.calibration}')
print('Valence evaluator: OK')
"
```

Expected: Queue enqueues 3 items, evaluator scores them, delay_ms reflects ~300s gap.

## Notes

- This is v1 heuristic evaluation. No LLM calls in the evaluate path.
- Future v2: Tier 2 reviews Tier 1 answers (brain reviewing spinal cord).
- Future v3: User feedback integration (explicit thumbs up/down).
- The queue is in-memory for now. Persistent backing (postgres) is a separate task.
- Valence.calibration field carries specific adjustment instructions back to the harness.
- Queue backpressure: drops oldest on overflow, does NOT block the hot path.
