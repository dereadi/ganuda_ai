# Jr Instructions: ICL Implicit Weight Dynamics Measurement

**Task ID**: RESEARCH-ICL-001
**Priority**: HIGH
**Target**: redfin (vLLM/HuggingFace inference)
**Requires**: Python, PyTorch, transformers library
**Council Review**: APPROVED - Fundamental research for understanding transformer behavior

---

## Executive Summary

Recent Google Research papers (Dherin et al., 2025) prove that In-Context Learning (ICL) works through **implicit rank-1 weight updates** to MLP layers. Each context token essentially runs a mini gradient descent step on the MLP weights at inference time.

This Jr instruction implements measurement and visualization of these implicit dynamics.

---

## Mathematical Foundation

### The Core Formula (Theorem 2.2)

For a transformer block processing context tokens, the implicit weight update is:

```
ΔₓW(Y) = (W·δₐₓ(Y)) · A(C\Y,x)ᵀ / ||A(C\Y,x)||²
```

Where:
- `W` = Original MLP weight matrix
- `δₐₓ(Y)` = Contextual vector = A(C,x) - A(C\Y,x)
- `A(C,x)` = Attention output for full context C at position x
- `A(C\Y,x)` = Attention output with context portion Y removed
- The result is a **rank-1 matrix** (outer product)

### Implicit Gradient Descent (Proposition 3.1)

Sequential token processing resembles SGD:

```
Wᵢ₊₁ = Wᵢ - h·∇Lᵢ(Wᵢ)

Where:
- Learning rate: h = 1/||A(x)||²
- Loss function: Lᵢ(W) = trace(Δᵢᵀ·W)
```

---

## Implementation Architecture

### Option 1: HuggingFace Transformers (Recommended for Measurement)

Since vLLM doesn't expose attention matrices, use HuggingFace for research:

```python
#!/usr/bin/env python3
"""
ICL Implicit Weight Dynamics Measurement
Based on Dherin et al. (2025) - "Learning without training"

Cherokee AI Federation - Research Implementation
"""

import torch
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt

class ICLDynamicsMeasurer:
    """Measure implicit weight updates during in-context learning."""

    def __init__(self, model_name: str = "Qwen/Qwen2.5-7B-Instruct"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        print(f"Loading {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            output_attentions=True,
            output_hidden_states=True
        )
        self.model.eval()

        # Storage for activations
        self.attention_outputs = {}
        self.mlp_inputs = {}
        self.mlp_outputs = {}
        self.hooks = []

    def _register_hooks(self, layer_idx: int):
        """Register forward hooks to capture intermediate activations."""

        def get_attention_hook(name):
            def hook(module, input, output):
                # output[0] is the attention output, output[1] is attention weights
                self.attention_outputs[name] = output[0].detach().cpu()
            return hook

        def get_mlp_input_hook(name):
            def hook(module, input, output):
                self.mlp_inputs[name] = input[0].detach().cpu()
            return hook

        def get_mlp_output_hook(name):
            def hook(module, input, output):
                self.mlp_outputs[name] = output.detach().cpu()
            return hook

        # Access the specific layer
        layer = self.model.model.layers[layer_idx]

        # Hook attention output
        h1 = layer.self_attn.register_forward_hook(
            get_attention_hook(f"layer_{layer_idx}_attn")
        )

        # Hook MLP input and output
        h2 = layer.mlp.register_forward_hook(
            get_mlp_input_hook(f"layer_{layer_idx}_mlp_in")
        )
        h3 = layer.mlp.register_forward_hook(
            get_mlp_output_hook(f"layer_{layer_idx}_mlp_out")
        )

        self.hooks.extend([h1, h2, h3])

    def _clear_hooks(self):
        """Remove all registered hooks."""
        for hook in self.hooks:
            hook.remove()
        self.hooks = []
        self.attention_outputs = {}
        self.mlp_inputs = {}
        self.mlp_outputs = {}

    def compute_contextual_delta(
        self,
        full_context: str,
        partial_context: str,
        layer_idx: int = 0
    ) -> Dict[str, torch.Tensor]:
        """
        Compute the contextual vector δₐₓ(Y) = A(C,x) - A(C\Y,x)

        This measures the "marginal effect" of context portion Y.
        """
        results = {}

        # Register hooks for the target layer
        self._register_hooks(layer_idx)

        # Forward pass with full context
        full_tokens = self.tokenizer(full_context, return_tensors="pt").to(self.device)
        with torch.no_grad():
            self.model(**full_tokens)

        full_attn = self.attention_outputs[f"layer_{layer_idx}_attn"].clone()

        # Clear and re-register for partial context
        self._clear_hooks()
        self._register_hooks(layer_idx)

        # Forward pass with partial context
        partial_tokens = self.tokenizer(partial_context, return_tensors="pt").to(self.device)
        with torch.no_grad():
            self.model(**partial_tokens)

        partial_attn = self.attention_outputs[f"layer_{layer_idx}_attn"].clone()

        self._clear_hooks()

        # Compute contextual delta (at last token position for both)
        # Note: sequences may have different lengths
        full_last = full_attn[0, -1, :]  # Last token of full context
        partial_last = partial_attn[0, -1, :]  # Last token of partial

        delta = full_last - partial_last

        results['full_attention'] = full_attn
        results['partial_attention'] = partial_attn
        results['contextual_delta'] = delta
        results['delta_norm'] = torch.norm(delta).item()

        return results

    def compute_implicit_weight_update(
        self,
        context_tokens: List[str],
        layer_idx: int = 0
    ) -> Dict[str, any]:
        """
        Compute the cumulative implicit weight update as tokens are added.

        Returns the sequence of rank-1 updates: ΔW = (W·δ)·Aᵀ / ||A||²
        """
        updates = []

        # Get MLP weight matrix
        mlp_layer = self.model.model.layers[layer_idx].mlp
        # For Qwen, the gate/up projection is typically the first linear layer
        W = mlp_layer.gate_proj.weight.detach().cpu().float()

        cumulative_context = ""

        for i, token in enumerate(context_tokens):
            prev_context = cumulative_context
            cumulative_context = cumulative_context + token

            if i == 0:
                # First token - no delta yet
                updates.append({
                    'token': token,
                    'token_idx': i,
                    'delta_norm': 0.0,
                    'update_frobenius_norm': 0.0,
                    'update_rank': 0
                })
                continue

            # Compute contextual delta
            self._register_hooks(layer_idx)

            # Full context attention
            full_tokens = self.tokenizer(cumulative_context, return_tensors="pt").to(self.device)
            with torch.no_grad():
                self.model(**full_tokens)
            A_full = self.attention_outputs[f"layer_{layer_idx}_attn"][0, -1, :].clone()

            self._clear_hooks()
            self._register_hooks(layer_idx)

            # Previous context attention
            prev_tokens = self.tokenizer(prev_context, return_tensors="pt").to(self.device)
            with torch.no_grad():
                self.model(**prev_tokens)
            A_prev = self.attention_outputs[f"layer_{layer_idx}_attn"][0, -1, :].clone()

            self._clear_hooks()

            # Contextual delta
            delta = A_full - A_prev
            delta_norm = torch.norm(delta).item()

            # Compute rank-1 weight update: ΔW = (W·δ)·Aᵀ / ||A||²
            A_norm_sq = torch.norm(A_full).item() ** 2

            if A_norm_sq > 1e-10:
                # W @ delta gives a column vector
                W_delta = W.float() @ delta.float()
                # Outer product: column @ row = rank-1 matrix
                delta_W = torch.outer(W_delta, A_full.float()) / A_norm_sq

                update_norm = torch.norm(delta_W).item()
                # Verify rank (should be 1)
                rank = torch.linalg.matrix_rank(delta_W).item()
            else:
                update_norm = 0.0
                rank = 0

            updates.append({
                'token': token,
                'token_idx': i,
                'delta_norm': delta_norm,
                'update_frobenius_norm': update_norm,
                'update_rank': rank,
                'implicit_learning_rate': 1.0 / A_norm_sq if A_norm_sq > 1e-10 else 0.0
            })

        return {
            'updates': updates,
            'layer_idx': layer_idx,
            'total_tokens': len(context_tokens),
            'cumulative_update_norm': sum(u['update_frobenius_norm'] for u in updates)
        }

    def visualize_update_dynamics(
        self,
        results: Dict[str, any],
        save_path: Optional[str] = None
    ):
        """Visualize the implicit weight update dynamics."""

        updates = results['updates']

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Plot 1: Delta norms over tokens
        ax1 = axes[0, 0]
        token_indices = [u['token_idx'] for u in updates]
        delta_norms = [u['delta_norm'] for u in updates]
        ax1.plot(token_indices, delta_norms, 'b-o', markersize=4)
        ax1.set_xlabel('Token Index')
        ax1.set_ylabel('Contextual Delta ||δ||')
        ax1.set_title('Marginal Context Effect per Token')
        ax1.grid(True, alpha=0.3)

        # Plot 2: Weight update norms
        ax2 = axes[0, 1]
        update_norms = [u['update_frobenius_norm'] for u in updates]
        ax2.plot(token_indices, update_norms, 'r-o', markersize=4)
        ax2.set_xlabel('Token Index')
        ax2.set_ylabel('||ΔW|| (Frobenius)')
        ax2.set_title('Implicit Weight Update Magnitude')
        ax2.grid(True, alpha=0.3)

        # Plot 3: Cumulative update
        ax3 = axes[1, 0]
        cumulative = np.cumsum(update_norms)
        ax3.plot(token_indices, cumulative, 'g-o', markersize=4)
        ax3.set_xlabel('Token Index')
        ax3.set_ylabel('Cumulative ||ΔW||')
        ax3.set_title('Cumulative Implicit Weight Change')
        ax3.grid(True, alpha=0.3)

        # Plot 4: Implicit learning rate
        ax4 = axes[1, 1]
        learning_rates = [u['implicit_learning_rate'] for u in updates]
        ax4.plot(token_indices, learning_rates, 'm-o', markersize=4)
        ax4.set_xlabel('Token Index')
        ax4.set_ylabel('h = 1/||A||²')
        ax4.set_title('Implicit Learning Rate')
        ax4.grid(True, alpha=0.3)

        plt.suptitle(f'ICL Implicit Weight Dynamics (Layer {results["layer_idx"]})',
                     fontsize=14, fontweight='bold')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved visualization to {save_path}")

        plt.show()
        return fig


def run_icl_dynamics_experiment():
    """
    Run experiment to measure ICL dynamics on a sample task.
    """

    # Initialize measurer (use smaller model for testing)
    measurer = ICLDynamicsMeasurer("Qwen/Qwen2.5-1.5B-Instruct")

    # Example: Few-shot arithmetic task
    context_tokens = [
        "You are a calculator. ",
        "Example 1: 2 + 3 = 5. ",
        "Example 2: 7 + 4 = 11. ",
        "Example 3: 9 + 6 = 15. ",
        "Now solve: 8 + 5 = "
    ]

    print("Computing implicit weight updates for few-shot arithmetic...")
    results = measurer.compute_implicit_weight_update(context_tokens, layer_idx=0)

    print("\n=== ICL Dynamics Results ===")
    for update in results['updates']:
        print(f"Token {update['token_idx']}: '{update['token'][:30]}...'")
        print(f"  Delta norm: {update['delta_norm']:.6f}")
        print(f"  Update ||ΔW||: {update['update_frobenius_norm']:.6f}")
        print(f"  Update rank: {update['update_rank']}")
        print()

    print(f"Total tokens: {results['total_tokens']}")
    print(f"Cumulative update norm: {results['cumulative_update_norm']:.6f}")

    # Visualize
    measurer.visualize_update_dynamics(
        results,
        save_path="/ganuda/data/icl_dynamics_experiment.png"
    )

    return results


if __name__ == "__main__":
    run_icl_dynamics_experiment()
```

---

## Experiment Design

### Experiment 1: Few-Shot Learning Dynamics

**Goal**: Measure how implicit weight updates accumulate during few-shot examples

```python
# Context structure
contexts = [
    "Example 1: input → output",
    "Example 2: input → output",
    "Example 3: input → output",
    "Query: new_input → "
]

# Hypothesis: Each example adds a rank-1 update
# Expected: Updates should converge (smaller deltas) as pattern is learned
```

### Experiment 2: Council Deliberation as Weight Updates

**Goal**: Measure how specialist reasoning affects implicit weights

```python
# Specialist responses as context
specialist_context = [
    "[Crawdad Security Analysis]: This approach has no vulnerabilities...",
    "[Gecko Technical Review]: Integration looks clean...",
    "[Turtle 7Gen Wisdom]: This serves future generations...",
    # ... each specialist adds implicit weight update
]

# Measure cumulative update after each specialist
# Compare to vote outcome correlation
```

### Experiment 3: Thermal Memory Retrieval Quality

**Goal**: Correlate memory retrieval quality with implicit update magnitude

```python
# Retrieve memories from thermal_memory_archive
# Measure implicit weight update for:
# 1. Highly relevant memories (high temperature)
# 2. Tangentially relevant memories
# 3. Irrelevant memories (control)

# Hypothesis: Better memories = larger, more focused updates
```

---

## Integration with Cherokee AI Federation

### Database Schema Addition

```sql
-- Store ICL dynamics measurements
CREATE TABLE icl_dynamics_log (
    id SERIAL PRIMARY KEY,
    session_id UUID,
    prompt_hash TEXT,
    layer_idx INTEGER,
    token_idx INTEGER,
    token_text TEXT,
    delta_norm FLOAT,
    update_frobenius_norm FLOAT,
    implicit_learning_rate FLOAT,
    cumulative_update_norm FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for analysis
CREATE INDEX idx_icl_session ON icl_dynamics_log(session_id);
CREATE INDEX idx_icl_layer ON icl_dynamics_log(layer_idx);
```

### API Endpoint (Future)

```python
@app.post("/v1/inference/analyze-icl")
async def analyze_icl_dynamics(request: ICLAnalysisRequest):
    """
    Analyze implicit weight dynamics for a given prompt.
    Returns per-token update magnitudes and visualizations.
    """
    pass
```

---

## Expected Outcomes

1. **Quantified ICL**: Numerical measurement of "how much" a model learns from context
2. **Optimal Context Length**: Identify when updates saturate (diminishing returns)
3. **Context Quality Metric**: Larger focused updates = better context
4. **Council Optimization**: Understand why some deliberations converge faster
5. **Memory Retrieval Validation**: Prove that good memories = good implicit training

---

## References

1. [Learning without training: The implicit dynamics of in-context learning](https://arxiv.org/abs/2507.16003) - Dherin et al., Google Research (2025)
2. [A Simple Generalisation of the Implicit Dynamics of In-Context Learning](https://arxiv.org/abs/2512.11255) - Innocenti & Achour (2025)
3. [Equivalence of Context and Parameter Updates in Modern Transformer Blocks](https://arxiv.org/abs/2511.17864) - Goldwaser et al. (2025)
4. [Intermediate Activations — the forward hook](https://web.stanford.edu/~nanbhas/blog/forward-hooks-pytorch/) - Stanford (2024)

---

## Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| ICL Measurer Python module | `/ganuda/lib/icl_dynamics.py` | To implement |
| Experiment notebook | `/ganuda/notebooks/icl_dynamics_experiments.ipynb` | To implement |
| Results visualization | `/ganuda/data/icl_dynamics/` | To implement |
| Database schema | `zammad_production.icl_dynamics_log` | To implement |
| API endpoint | LLM Gateway v1.3 | Future |

---

*For Seven Generations - Understanding how transformers truly learn*
