# JR INSTRUCTION: S-PATH-RAG P-Day — Cross-Attention Injection into vLLM

**Task**: Inject graph topology directly into Qwen2.5-72B attention layers via cross-attention KV matrices. The core S-PATH-RAG innovation.
**Priority**: P1 (the payoff)
**Date**: 2026-03-30
**TPM**: Claude Opus
**Story Points**: 8
**Depends On**: JR-SPATH-RAG-P1-GNN-PATH-SEARCH (working retrieval pipeline with scored paths)

## Problem Statement

Current RAG stuffs retrieved text into the context window. S-PATH-RAG injects graph topology directly into the LLM's attention mechanism as key-value matrices. This means:
- Zero token bloat (graph data doesn't consume context window)
- Zero topological loss (GNN-encoded structure preserved in attention space)
- LLM attention heads can scan graph paths directly

This requires modifying how vLLM serves Qwen2.5-72B on redfin. This is local-model-only capability — sovereign inference advantage.

## Architecture

```
Query → GNN Encoder → Path Search → Path Scorer → Selected Paths
                                                         ↓
                                              Path Encoder (learned)
                                                         ↓
                                              Z_context tensor [num_paths, dim]
                                                         ↓
                                              Project to K_graph, V_graph
                                                         ↓
                                    Inject into Qwen2.5 attention layers
                                                         ↓
                                    LLM text tokens attend to graph KV
                                                         ↓
                                              Answer + Diagnostic
                                                         ↓
                                    If low confidence → expand graph → repeat
```

## Task 1: Path Encoder — Paths to Z_context (2 SP)

**Create**: `/ganuda/lib/kg_path_encoder.py`

Convert scored paths into a single continuous context tensor.

```python
class PathEncoder(torch.nn.Module):
    """Encode selected graph paths into Z_context for LLM injection.

    Takes GNN-encoded path representations and selection weights,
    produces a tensor suitable for projection into LLM KV space.
    """
    def __init__(self, gnn_dim=256, llm_dim=8192):
        # Qwen2.5-72B hidden_size = 8192
        super().__init__()
        self.path_proj = torch.nn.Linear(gnn_dim, llm_dim)

    def forward(self, path_encodings, selection_weights):
        """
        path_encodings: [num_paths, gnn_dim]  (from GNN + path aggregation)
        selection_weights: [num_paths] (from Gumbel-Softmax scorer)

        Returns: Z_context [num_paths, llm_dim]
        """
        # Project each path to LLM dimensionality
        projected = self.path_proj(path_encodings)  # [num_paths, llm_dim]

        # Weight by selection scores (soft attention over paths)
        weighted = projected * selection_weights.unsqueeze(-1)

        return weighted  # [num_paths, llm_dim]
```

## Task 2: KV Projection for Cross-Attention (2 SP)

Project Z_context into key and value matrices that the LLM's attention heads can attend to.

```python
class GraphKVProjection(torch.nn.Module):
    """Project Z_context into K_graph and V_graph matrices.

    These replace/augment the KV cache in the LLM's attention layers.
    """
    def __init__(self, llm_dim=8192, num_heads=64, head_dim=128):
        # Qwen2.5-72B: 64 heads, 128 dim per head
        super().__init__()
        self.k_proj = torch.nn.Linear(llm_dim, num_heads * head_dim)
        self.v_proj = torch.nn.Linear(llm_dim, num_heads * head_dim)
        self.num_heads = num_heads
        self.head_dim = head_dim

    def forward(self, z_context):
        """
        z_context: [num_paths, llm_dim]
        Returns: K_graph [num_heads, num_paths, head_dim], V_graph [same]
        """
        k = self.k_proj(z_context)  # [num_paths, num_heads * head_dim]
        v = self.v_proj(z_context)

        # Reshape for multi-head attention
        k = k.view(-1, self.num_heads, self.head_dim).transpose(0, 1)
        v = v.view(-1, self.num_heads, self.head_dim).transpose(0, 1)

        return k, v  # [num_heads, num_paths, head_dim]
```

## Task 3: vLLM Integration — Attention Injection (3 SP)

This is the hardest part. We need to modify how vLLM handles attention for Qwen2.5-72B to include our graph KV matrices.

### Option A: Prefix Token Injection (simpler, less pure)
Encode graph paths as "virtual tokens" prepended to the KV cache. vLLM supports custom prefix caching. This doesn't modify attention code — it just adds virtual prefixes that look like regular KV pairs to the model.

```python
# Generate virtual prefix tokens from graph paths
prefix_tokens = graph_kv_projection(z_context)  # [num_paths, dim]
# Prepend to the prompt's KV cache in vLLM
# The LLM will attend to these as if they were part of the prompt
```

**Pros**: Works with unmodified vLLM. No custom CUDA kernels.
**Cons**: Technically uses token positions (but not text tokens).

### Option B: Custom Attention Hook (pure S-PATH-RAG, harder)
Hook into vLLM's attention computation to add cross-attention with graph KV matrices alongside the standard self-attention.

This requires forking or patching vLLM's model runner. Only attempt if Option A doesn't produce good results.

### Recommendation: Start with Option A. It's 80% of the benefit with 20% of the complexity. Option B is a follow-up if we need it.

## Task 4: Socratic Diagnostic Loop (1 SP)

Adapt the consultation ring pattern:

1. LLM generates answer + confidence score
2. If confidence < threshold (0.7):
   - LLM emits diagnostic: "I need more information about [entity/relationship]"
   - Parse diagnostic into graph expansion query
   - Expand subgraph with new nodes/edges
   - Re-run GNN encoding + path search on expanded graph
   - Re-inject and re-query LLM
3. Repeat up to 5 rounds

This maps directly to our existing consultation ring loop. The new piece is the graph expansion step.

## Evaluation

### Benchmark: Compare S-PATH-RAG vs Current Text RAG

Prepare 20 multi-hop thermal memory queries:
1. "What council decisions led to the circuit breaker role exemption?"
2. "Trace the connection from the transducer hypothesis to the Lilien temporal operators"
3. "What Jr tasks were blocked by the DB tuning work?"
4. "How does the chirality thesis connect to VetAssist?"
... etc.

For each query, run both:
- Current: pgvector similarity → HyDE → CRAG → text injection
- S-PATH-RAG: GNN → path search → scored paths → cross-attention injection

Score on:
- **Completeness**: Did the answer include all relevant connections?
- **Accuracy**: Were the connections factually correct?
- **Token efficiency**: How many context tokens were consumed?
- **Latency**: End-to-end response time

If S-PATH-RAG wins on completeness and accuracy with lower token usage, it's the new default retrieval path for local model queries.

## Rollback

If the cross-attention injection degrades model quality:
- Remove prefix tokens / attention hook
- Fall back to current text-based RAG
- The KG and GNN encoder remain useful for other purposes (visualization, relationship analysis)

## Notes

- This runs ONLY on redfin (RTX PRO 6000, Qwen2.5-72B via vLLM). Not on Claude API.
- Start with Option A (prefix injection). Measure before attempting Option B.
- The Socratic loop should be capped at 5 rounds to prevent infinite expansion.
- All graph operations (subgraph extraction, GNN encoding, path search) should complete in <2 seconds to keep latency reasonable.

---

FOR SEVEN GENERATIONS
