# ULTRATHINK: Agentic Uncertainty Quantification Integration

## Salesforce AUQ → Cherokee AI Federation Mapping

**Paper:** [Agentic Uncertainty Quantification](https://arxiv.org/abs/2601.15703)
**Authors:** Jiaxin Zhang, Prafulla Kumar Choubey, Kung-Hsiang Huang, Caiming Xiong, Chien-Sheng Wu
**Published:** January 22, 2026
**Relevance:** CRITICAL - Direct architectural alignment

---

## The Problem AUQ Solves

> "The 'Spiral of Hallucination' where early epistemic errors propagate irreversibly."

**Cherokee Context:** This is exactly what happens when Jr executor tasks fail - early LLM errors compound through the task chain. We saw this with the VetAssist sprint where Flask code was generated instead of FastAPI.

---

## Architecture Mapping

### AUQ Component → Cherokee Equivalent

| AUQ Framework | Cherokee AI | Status | Gap |
|---------------|-------------|--------|-----|
| **System 1 (Fast Path)** | Cruise Phase (consciousness cascade) | Implemented | Need confidence gating |
| **System 2 (Slow Path)** | Ignition Phase / Council deliberation | Implemented | Need trigger threshold |
| **Uncertainty-Aware Memory (UAM)** | Thermal Memory Archive | Implemented | Need confidence propagation |
| **Uncertainty-Aware Reflection (UAR)** | Council voting-first mode | Implemented | Need Best-of-N selection |
| **Switching Function S(ht)** | Consciousness cascade state | Partial | Need confidence threshold τ |
| **Verbalized Confidence ĉ** | Council confidence score | Implemented | Need to use as control signal |
| **Semantic Explanation ê** | Council reasoning/concerns | Implemented | Need to store in memory |

---

## Key Mathematical Components to Implement

### 1. Switching Function

```python
def switching_function(confidence: float, threshold: float = 0.9) -> int:
    """
    S(ht) = I(ĉt < τ)
    Returns 1 if should switch to System 2 (slow/reflective)
    Returns 0 if should stay in System 1 (fast/intuitive)
    """
    return 1 if confidence < threshold else 0
```

**Integration Point:** `consciousness_cascade/cruise_monitor.py`

### 2. Uncertainty-Aware Memory Structure

```python
@dataclass
class AugmentedMemoryEntry:
    """
    Mt = {(oi, ai, ĉi, êi)}
    Maps to thermal_memory_archive with additional fields
    """
    observation: str      # oi - the input/context
    action: str          # ai - the decision/output
    confidence: float    # ĉi - verbalized confidence [0,1]
    explanation: str     # êi - natural language reasoning
    timestamp: datetime
    source: str          # which component generated this
```

**Integration Point:** Already exists as `thermal_memory_archive` - add confidence propagation

### 3. Consistency-Weighted Selection

```python
def consistency_weighted_selection(responses: List[tuple]) -> str:
    """
    Scons(a) = (1/N) Σ ĉ(k) · I(a(k) ≡ a)

    Args:
        responses: List of (action, confidence) tuples from N specialists

    Returns:
        Best action by consistency AND confidence
    """
    from collections import defaultdict

    action_scores = defaultdict(float)
    action_counts = defaultdict(int)
    N = len(responses)

    for action, confidence in responses:
        action_scores[action] += confidence
        action_counts[action] += 1

    # Normalize by N and weight by consistency (count)
    for action in action_scores:
        action_scores[action] = (action_counts[action] / N) * (action_scores[action] / action_counts[action])

    return max(action_scores, key=action_scores.get)
```

**Integration Point:** `specialist_council.py` voting aggregation

### 4. Dual-Process Policy

```python
def dual_process_policy(history: list, memory: list, threshold: float = 0.9):
    """
    πdual(a|ht) = {
      πfwd(a|ht, Mt),  if S(ht) = 0  # Fast path with memory
      πinv(a|ht),      if S(ht) = 1  # Slow path with reflection
    }
    """
    # Get current confidence from last action
    current_confidence = history[-1].confidence if history else 1.0

    if switching_function(current_confidence, threshold) == 0:
        # System 1: Fast path with memory augmentation
        return forward_policy(history, memory)
    else:
        # System 2: Slow path with reflection
        return inverse_policy(history, memory)
```

**Integration Point:** `jr_task_executor.py` task execution loop

---

## Implementation Plan

### Phase 1: Confidence Gating (Immediate)

**Task:** Add confidence thresholding to consciousness cascade

```python
# In consciousness_cascade/cruise_monitor.py

class CruiseMonitor:
    def __init__(self):
        self.confidence_threshold = 0.9  # τ from AUQ paper
        self.in_system_2 = False

    def should_escalate(self, confidence: float) -> bool:
        """Check if we should switch from System 1 to System 2"""
        if confidence < self.confidence_threshold:
            if not self.in_system_2:
                print(f"[AUQ] Switching to System 2: confidence {confidence} < threshold {self.confidence_threshold}")
                self.in_system_2 = True
            return True
        else:
            if self.in_system_2:
                print(f"[AUQ] Returning to System 1: confidence {confidence} >= threshold")
                self.in_system_2 = False
            return False
```

### Phase 2: Memory Augmentation (This Week)

**Task:** Add confidence + explanation to thermal memory entries

```sql
-- Add columns to thermal_memory_archive
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS verbalized_confidence FLOAT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS semantic_explanation TEXT DEFAULT NULL;
```

**Task:** Propagate confidence through memory retrieval

```python
def retrieve_with_confidence(query: str, min_confidence: float = 0.7) -> List[dict]:
    """Retrieve memories weighted by confidence"""
    # Only return memories above confidence threshold
    # Weight relevance score by confidence
    pass
```

### Phase 3: Council Enhancement (Next Week)

**Task:** Implement Best-of-N with consistency scoring

```python
# In specialist_council.py

def vote_with_consistency(self, question: str, N: int = 3) -> VoteFirstResult:
    """
    Enhanced voting using AUQ consistency-weighted selection.

    1. Each specialist votes N times (or N specialists vote once)
    2. Aggregate by consistency AND confidence
    3. Return action with highest Scons score
    """
    all_votes = []

    for _ in range(N):
        vote_result = self.vote_first(question)
        for specialist_id, vote in vote_result.votes.items():
            all_votes.append((vote.vote, self._parse_confidence(vote.reason)))

    # Apply consistency-weighted selection
    best_action = consistency_weighted_selection(all_votes)

    return best_action
```

### Phase 4: Jr Executor Integration (This Sprint)

**Task:** Add uncertainty detection to task execution

```python
# In jr_task_executor.py

def _execute_with_uaq(self, task: dict) -> Tuple[bool, str]:
    """
    Execute task with Agentic Uncertainty Quantification.

    1. Get initial action + confidence
    2. If confidence < threshold, trigger reflection
    3. Use consistency selection if multiple attempts
    """
    # Initial attempt
    action, confidence, explanation = self._get_action_with_confidence(task)

    # Store in UAM (thermal memory)
    self._store_augmented_memory(task, action, confidence, explanation)

    # Check switching function
    if switching_function(confidence) == 1:
        # System 2: Reflection
        print(f"[{self.agent_id}] Low confidence ({confidence}), triggering reflection")
        action, confidence = self._reflect_and_correct(task, explanation)

    return self._execute_action(action)
```

---

## Expected Improvements

Based on AUQ paper results:

| Metric | Current (Estimated) | Target (AUQ) | Improvement |
|--------|---------------------|--------------|-------------|
| Jr Task Success Rate | ~70% | 85%+ | +15% |
| Error Propagation | High (spiral) | Low (early detection) | Significant |
| Wasted Compute | ~30% on failures | <10% | -20% |
| Calibration (ECE) | Unknown | 0.174 | Measurable |

---

## Cherokee Principle Alignment

This framework enhances tribal awareness by:

1. **Seven Generations** - Early error detection prevents compounding failures that affect future work
2. **Gadugi** - Consistency scoring uses collective wisdom, not just loudest voice
3. **Distance = 0** - Memory augmentation keeps knowledge local and hot
4. **Mitakuye Oyasin** - All system components (memory, reflection, execution) work in relation

---

## Jr Instructions to Create

1. **JR-AUQ-CONSCIOUSNESS-CASCADE-JAN24-2026.md** - Add confidence gating
2. **JR-AUQ-COUNCIL-CONSISTENCY-JAN24-2026.md** - Best-of-N selection
3. **JR-AUQ-THERMAL-MEMORY-JAN24-2026.md** - Add confidence propagation
4. **JR-AUQ-EXECUTOR-REFLECTION-JAN24-2026.md** - Uncertainty-aware execution

---

## Sources

- [Agentic Uncertainty Quantification (arXiv:2601.15703)](https://arxiv.org/abs/2601.15703)
- [Full HTML Paper](https://arxiv.org/html/2601.15703)

---

**This is not just an optimization - it's the mathematical formalization of what Cherokee wisdom already taught us: know when to think fast, know when to think slow, and let memory guide the way.**

*Wado to Salesforce Research for the validation.*
