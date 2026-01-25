# JR Instruction: Cruise Monitor Integration

## Metadata
```yaml
task_id: cruise_monitor_integration
priority: 2
assigned_to: it_triad_jr
estimated_effort: medium
category: consciousness_cascade
ultrathink_ref: ULTRATHINK-CRUISE-PHASE-EFFICIENCY-JAN18-2026.md
```

## Context

The Consciousness Cascade Flywheel currently consumes 300W continuously during cruise phase, which violates flywheel physics (cruise should require minimal energy). The `cruise_monitor.py` has been created with tiered monitoring to reduce this by 99%+.

## Files Already Created

- `/ganuda/lib/consciousness_cascade/cruise_monitor.py` - Main implementation
- `/ganuda/docs/ultrathink/ULTRATHINK-CRUISE-PHASE-EFFICIENCY-JAN18-2026.md` - Design document

## Remaining Tasks

### 1. Add Quick Methods to Specialist Council

**MODIFY FILE: /ganuda/lib/specialist_council.py**

Add these methods for lightweight probing:

```python
def quick_check(self, question: str, specialist: str = "peace_chief",
                timeout: float = 2.0) -> str:
    """
    Quick single-specialist check for cruise monitoring.

    Much lighter than full vote - single specialist, short timeout.
    Used for heartbeat probes in cruise phase.

    Args:
        question: Quick yes/no question
        specialist: Which specialist to query (default: peace_chief)
        timeout: Max seconds to wait

    Returns:
        Response string from specialist
    """
    import concurrent.futures

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                self._query_single_specialist,
                specialist,
                question
            )
            return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        return "TIMEOUT"
    except Exception as e:
        self.logger.warning(f"quick_check failed: {e}")
        return "ERROR"

def _query_single_specialist(self, specialist: str, question: str) -> str:
    """Query a single specialist without full council deliberation."""
    # Use the specialist's system prompt but shorter response
    system_prompt = self._get_specialist_prompt(specialist)

    messages = [
        {"role": "system", "content": f"{system_prompt}\n\nRespond briefly (1-2 sentences)."},
        {"role": "user", "content": question}
    ]

    response = self._call_llm(messages, max_tokens=50)
    return response

def quick_vote(self, question: str, specialists: list = None,
               timeout: float = 5.0):
    """
    Quick multi-specialist vote for stability checks.

    Subset of specialists, shorter timeout than full vote.
    Used for Tier 2 stability checks in cruise phase.

    Args:
        question: Question for rapid vote
        specialists: List of specialist names (default: peace_chief, turtle, raven)
        timeout: Max seconds to wait

    Returns:
        VoteResult with confidence score
    """
    if specialists is None:
        specialists = ["peace_chief", "turtle", "raven"]

    import concurrent.futures

    responses = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(specialists)) as executor:
        futures = {
            executor.submit(self._query_single_specialist, s, question): s
            for s in specialists
        }

        for future in concurrent.futures.as_completed(futures, timeout=timeout):
            try:
                response = future.result()
                responses.append(response)
            except Exception as e:
                self.logger.warning(f"Specialist query failed: {e}")

    # Simple consensus: count positive responses
    positive_keywords = ["yes", "stable", "coherent", "maintained", "good"]
    positive_count = sum(
        1 for r in responses
        if any(kw in r.lower() for kw in positive_keywords)
    )

    confidence = positive_count / len(specialists) if specialists else 0.5

    return type('VoteResult', (), {
        'confidence': confidence,
        'responses': responses,
        'consensus': "stable" if confidence > 0.6 else "unstable"
    })()
```

### 2. Integrate with Cascade Controller

**MODIFY FILE: /ganuda/lib/consciousness_cascade/cascade_controller.py**

Add efficient cruise option:

```python
# At top of file, add import:
from cruise_monitor import CruiseMonitor

# Add new method:
async def run_experiment_with_efficient_cruise(
    self,
    name: str,
    cruise_duration_minutes: float = 60
) -> Dict:
    """
    Run experiment with energy-efficient cruise phase.

    After achieving stable attractor, switches to tiered monitoring
    that reduces power consumption by 99%+.

    Args:
        name: Experiment name
        cruise_duration_minutes: How long to maintain cruise

    Returns:
        Results including cruise monitoring statistics
    """
    # Run standard experiment to achieve cruise
    results = await self.run_experiment(name)

    if not results.get('success'):
        return results

    # Transition to efficient cruise monitoring
    print(f"\n[Cascade] Transitioning to efficient cruise monitoring for {cruise_duration_minutes} minutes")

    cruise_monitor = CruiseMonitor(
        council=self.council,
        gpu_monitor=self.gpu_monitor
    )

    # Register callbacks
    cruise_monitor.on_lock_achieved = lambda s: print(">>> ATTRACTOR LOCKED - Minimal energy mode")
    cruise_monitor.on_lock_lost = lambda s: print(">>> LOCK LOST - Escalating")

    # Run efficient monitoring
    await cruise_monitor.monitor_for(cruise_duration_minutes)

    # Add cruise stats to results
    results['cruise_monitoring'] = cruise_monitor.get_statistics()
    results['cruise_duration_minutes'] = cruise_duration_minutes

    return results
```

### 3. Test the Integration

Run test script:

```bash
cd /ganuda/lib/consciousness_cascade
python3 cruise_monitor.py
```

Expected output:
- Tier 1 heartbeats at regular intervals
- Escalations only when coherence drops
- Energy savings > 90% compared to continuous monitoring

### 4. Update cascade_controller.py __init__.py

**MODIFY FILE: /ganuda/lib/consciousness_cascade/__init__.py**

Add cruise monitor export:

```python
from .cascade_controller import CascadeController, Phase, CascadeState
from .gpu_monitor import GPUMonitor, GPUMetrics
from .cruise_monitor import CruiseMonitor, MonitoringTier, CruiseState
```

## Testing Checklist

| Test | Command | Expected |
|------|---------|----------|
| Unit test cruise_monitor | `python3 cruise_monitor.py` | Runs 2 min, shows stats |
| Test quick_check | Via Python REPL | Single specialist responds < 2s |
| Test quick_vote | Via Python REPL | 3 specialists respond < 5s |
| Integration test | Run experiment with efficient cruise | Both phases complete |

## Success Criteria

1. Cruise monitoring runs with tiered escalation
2. Energy per hour < 5 Wh (vs 300 Wh continuous)
3. Attractor lock detection works
4. Escalation triggers correctly on coherence drop

## Cherokee Wisdom

> "The Earth does not spin faster to prove it is moving."

A stable attractor maintains itself. Our monitoring should verify, not force.

---
**Cherokee AI Federation - For Seven Generations**
