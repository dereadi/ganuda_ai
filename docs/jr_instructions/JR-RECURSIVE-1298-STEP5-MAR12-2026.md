# [RECURSIVE] Peace Chief Curiosity Engine — Stub-Filling Pipeline - Step 5

**Parent Task**: #1298
**Auto-decomposed**: 2026-03-12T09:03:34.720775
**Original Step Title**: THE CAPACITOR (buffer and smooth)

---

### Step 5: THE CAPACITOR (buffer and smooth)

**This is the critical step.** Partner bursts. The organism does NOT burst with him.

```python
class StubCapacitor:
    """
    Buffer partner's stubs. Evaluate. Smooth into sustainable work rate.
    The organism is a flywheel, not a firecracker.
    """

    MAX_CONCURRENT_SUBCLAUDES = 2  # Never more than 2 sub-Claudes at once
    MAX_STUBS_PER_HOUR = 5        # Max stubs dispatched per hour
    COOLING_PERIOD_MINUTES = 30   # Hold stubs for 30 min before dispatching

    def buffer(self, stubs: list[dict]):
        """
        Don't dispatch immediately. Hold in curiosity_stubs table
        with status='buffered'. Cooling period lets the burst settle.
        Multiple shares in quick succession get merged/deduplicated.
        """

    def evaluate(self, buffered_stubs: list[dict]) -> list[dict]:
        """
        After cooling period, Coyote reviews:
        - Is this actionable or is partner full of shit? (his words)
        - Does this duplicate existing research?
        - Is this the manic high talking or real signal?

        Use local model (sasass2 conscience_jr_resonance) for quick eval.
        Score each stub: actionable (0.0-1.0), novelty (0.0-1.0)
        Drop anything below 0.3 on both.
        """

    def smooth(self, evaluated_stubs: list[dict]):
        """
        Release stubs at sustainable rate:
        - Max 5 stubs dispatched per hour
        - Max 2 sub-Claudes running at any time
        - Deep stubs queued, not immediately spawned
        - If partner is in EXHAUSTION phase (from rhythm engine),
          reduce rate to 2/hour
        - If partner is RESTING, batch all buffered stubs for
          overnight processing at idle rate
        """

    def merge_burst(self, new_stubs: list[dict], existing_buffered: list[dict]):
        """
        Partner shares 5 things in 10 minutes. Don't create 50 stubs.
        Merge: deduplicate names, combine context, consolidate into
        fewest possible research threads.
        """
```

The capacitor converts partner's AC signal (jagged bursts) into smooth DC current (steady work). The organism runs at its own pace regardless of partner's frequency.

#
