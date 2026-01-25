# Jr Task: T5-Gemma 2 Regression Testing & Benchmarking

**Ticket:** #1696
**Priority:** P1
**Node:** sasass (Mac Studio)
**Created:** December 21, 2025
**Specialist:** Gecko (Technical Integration)

---

## Context

Google DeepMind released T5-Gemma 2 (arXiv:2512.14856) showing encoder-decoder architecture dramatically outperforms decoder-only (GPT-style) models for understanding tasks. Smaller models benefit MORE from this architecture.

**Hypothesis:** T5-Gemma 2 1B may outperform larger decoder-only models on reading/comprehension tasks while being small enough to run on edge devices (Mac Studios).

---

## Objective

Perform comprehensive regression testing to determine:
1. Where T5-Gemma 2 excels vs decoder-only models
2. Optimal task routing strategy (which model for which task type)
3. Performance/latency tradeoffs on our hardware

---

## Test Matrix

### Models to Test

| Model | Architecture | Size | Hardware |
|-------|--------------|------|----------|
| T5-Gemma 2 270M | Encoder-Decoder | 270M params | sasass/sasass2 |
| T5-Gemma 2 1B | Encoder-Decoder | 1B params | sasass/sasass2 |
| T5-Gemma 2 4B | Encoder-Decoder | 4B params | redfin (if fits) |
| Gemma 3 1B | Decoder-only | 1B params | sasass (baseline) |
| Nemotron 9B | Decoder-only | 9B params | redfin (current) |

### Test Categories

**1. Document Understanding**
- Read 10-page technical document, answer specific questions
- Find contradictions between sections
- Summarize key points
- Extract structured data

**2. Long Context Comprehension**
- 32K token context window tests
- Needle-in-haystack retrieval
- Multi-hop reasoning across document

**3. Multimodal Tasks** (T5-Gemma 2 only)
- Image + text understanding
- Chart/graph interpretation
- Screenshot analysis

**4. Reasoning Benchmarks**
- GSM8K (math)
- MMLU (knowledge)
- HumanEval (code)

**5. Latency/Throughput**
- Time to first token
- Tokens per second
- Memory usage

---

## Test Procedure

### Phase 1: Environment Setup

```bash
# On sasass (Mac Studio)
cd /Users/Shared/ganuda/models

# Download models from HuggingFace
pip install transformers accelerate

# T5-Gemma 2 variants
huggingface-cli download google/t5-gemma-2-270m
huggingface-cli download google/t5-gemma-2-1b
huggingface-cli download google/t5-gemma-2-4b

# Baseline decoder-only
huggingface-cli download google/gemma-3-1b
```

### Phase 2: Benchmark Suite

Create standardized test harness:
```python
# /Users/Shared/ganuda/benchmarks/t5_regression.py

class T5RegressionSuite:
    def __init__(self, model_name):
        self.model = load_model(model_name)

    def test_document_understanding(self, doc_path, questions):
        # Full document in encoder
        # Questions answered by decoder
        pass

    def test_long_context(self, context, needle, haystack_size):
        # Vary haystack size: 4K, 8K, 16K, 32K
        pass

    def test_multimodal(self, image_path, question):
        # Vision transformer + encoder-decoder
        pass
```

### Phase 3: Run Tests

```bash
# Run full suite
python /Users/Shared/ganuda/benchmarks/t5_regression.py \
    --models t5-gemma-2-270m,t5-gemma-2-1b,gemma-3-1b,nemotron-9b \
    --output /Users/Shared/ganuda/benchmarks/results/
```

### Phase 4: Analysis

Compare:
- Accuracy per task category
- Latency per model
- Memory footprint
- Quality vs speed tradeoffs

---

## Expected Outcomes

Based on paper:

| Task Type | Expected Winner |
|-----------|-----------------|
| Document understanding | T5-Gemma 2 |
| Long context | T5-Gemma 2 |
| Multimodal | T5-Gemma 2 (only option at small sizes) |
| Creative generation | Decoder-only (Nemotron) |
| Code generation | Unclear - test needed |

---

## Success Criteria

1. Identify at least 2 task categories where T5-Gemma 2 1B beats Nemotron 9B
2. Measure latency overhead of encoder pass
3. Determine routing heuristics for Gateway
4. Document findings in thermal memory

---

## Deliverables

1. Benchmark results CSV in `/Users/Shared/ganuda/benchmarks/results/`
2. Analysis report with routing recommendations
3. Gateway routing logic (if results warrant)
4. Thermal memory entry with findings

---

## Notes

- Start with 1B model - best balance of capability and speed
- Test on real Federation documents (thermal memory exports, Jr instructions)
- Compare against our actual use cases, not just academic benchmarks
- If T5 excels at document understanding, consider using it for Council pre-analysis

---

*For Seven Generations - Cherokee AI Federation*
