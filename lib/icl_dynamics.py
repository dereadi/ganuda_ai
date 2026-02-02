#!/usr/bin/env python3
"""
ICL Implicit Weight Dynamics Measurement
Based on Dherin et al. (2025) - "Learning without training: The implicit dynamics of in-context learning"

Cherokee AI Federation - Research Implementation
For Seven Generations

This module measures the implicit rank-1 weight updates that occur during
in-context learning. Each context token effectively runs a mini gradient
descent step on the MLP weights at inference time.

Core Formula (Theorem 2.2):
    ΔW = (W·δ)·Aᵀ / ||A||²

Where:
    δ = A(full_context) - A(partial_context)  (contextual vector)
    W = MLP weight matrix
    A = Attention output

References:
    - arXiv:2507.16003 - Learning without training (Google Research)
    - arXiv:2512.11255 - Generalisation of ICL dynamics
    - arXiv:2511.17864 - Equivalence of Context and Parameter Updates
"""

import torch
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Callable
from datetime import datetime
import json
import logging

# Optional imports - gracefully handle missing dependencies
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("icl_dynamics")


@dataclass
class TokenUpdate:
    """Represents the implicit weight update for a single token."""
    token_idx: int
    token_text: str
    delta_norm: float
    update_frobenius_norm: float
    update_rank: int
    implicit_learning_rate: float
    attention_norm: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'token_idx': self.token_idx,
            'token_text': self.token_text,
            'delta_norm': self.delta_norm,
            'update_frobenius_norm': self.update_frobenius_norm,
            'update_rank': self.update_rank,
            'implicit_learning_rate': self.implicit_learning_rate,
            'attention_norm': self.attention_norm,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ICLDynamicsResult:
    """Complete result of ICL dynamics measurement."""
    layer_idx: int
    total_tokens: int
    updates: List[TokenUpdate]
    cumulative_update_norm: float
    model_name: str
    prompt_hash: str
    session_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'layer_idx': self.layer_idx,
            'total_tokens': self.total_tokens,
            'updates': [u.to_dict() for u in self.updates],
            'cumulative_update_norm': self.cumulative_update_norm,
            'model_name': self.model_name,
            'prompt_hash': self.prompt_hash,
            'session_id': self.session_id
        }

    def summary(self) -> str:
        """Return a human-readable summary."""
        lines = [
            f"=== ICL Dynamics Summary ===",
            f"Model: {self.model_name}",
            f"Layer: {self.layer_idx}",
            f"Total tokens: {self.total_tokens}",
            f"Cumulative ||ΔW||: {self.cumulative_update_norm:.6f}",
            f"",
            f"Token-by-token updates:"
        ]
        for u in self.updates:
            lines.append(
                f"  [{u.token_idx:3d}] ||δ||={u.delta_norm:.4f} "
                f"||ΔW||={u.update_frobenius_norm:.4f} "
                f"h={u.implicit_learning_rate:.6f} "
                f"'{u.token_text[:20]}...'"
            )
        return "\n".join(lines)


class ICLDynamicsMeasurer:
    """
    Measure implicit weight updates during in-context learning.

    This class hooks into transformer forward passes to extract attention
    outputs and compute the rank-1 weight updates that occur implicitly
    as context tokens are processed.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
        device: Optional[str] = None,
        dtype: torch.dtype = torch.float16,
        load_model: bool = True
    ):
        """
        Initialize the ICL dynamics measurer.

        Args:
            model_name: HuggingFace model name or path
            device: Device to use (auto-detected if None)
            dtype: Data type for model weights
            load_model: Whether to load model immediately
        """
        if not HAS_TRANSFORMERS:
            raise ImportError("transformers library required. Install with: pip install transformers")

        self.model_name = model_name
        self.dtype = dtype

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"Using device: {self.device}")

        # Model and tokenizer
        self.model = None
        self.tokenizer = None

        # Hook storage
        self.attention_outputs: Dict[str, torch.Tensor] = {}
        self.mlp_inputs: Dict[str, torch.Tensor] = {}
        self.mlp_outputs: Dict[str, torch.Tensor] = {}
        self.hooks: List[torch.utils.hooks.RemovableHandle] = []

        # Architecture info (populated on model load)
        self.num_layers = 0
        self.hidden_size = 0
        self.mlp_weight_shape = None

        if load_model:
            self.load_model()

    def load_model(self):
        """Load the model and tokenizer."""
        logger.info(f"Loading model: {self.model_name}")

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # Ensure pad token exists
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=self.dtype,
            device_map="auto" if self.device.type == "cuda" else None,
            trust_remote_code=True
            # Note: Don't pass output_attentions/output_hidden_states here
            # They cause NaN in attention outputs for sequences > 2 tokens
            # We use forward hooks instead to capture activations
        )

        if self.device.type != "cuda":
            self.model = self.model.to(self.device)

        self.model.eval()

        # Extract architecture info
        self._detect_architecture()

        logger.info(f"Model loaded: {self.num_layers} layers, hidden_size={self.hidden_size}")

    def _detect_architecture(self):
        """Detect model architecture details."""
        # Try common attribute names
        if hasattr(self.model, 'model'):
            base = self.model.model
        elif hasattr(self.model, 'transformer'):
            base = self.model.transformer
        else:
            base = self.model

        # Get layers
        if hasattr(base, 'layers'):
            self.num_layers = len(base.layers)
            layer = base.layers[0]
        elif hasattr(base, 'h'):
            self.num_layers = len(base.h)
            layer = base.h[0]
        else:
            raise ValueError(f"Cannot detect layer structure for {self.model_name}")

        # Get hidden size
        if hasattr(self.model.config, 'hidden_size'):
            self.hidden_size = self.model.config.hidden_size
        elif hasattr(self.model.config, 'd_model'):
            self.hidden_size = self.model.config.d_model

        # Get MLP weight shape
        if hasattr(layer, 'mlp'):
            mlp = layer.mlp
            if hasattr(mlp, 'gate_proj'):
                self.mlp_weight_shape = mlp.gate_proj.weight.shape
            elif hasattr(mlp, 'c_fc'):
                self.mlp_weight_shape = mlp.c_fc.weight.shape
            elif hasattr(mlp, 'dense_h_to_4h'):
                self.mlp_weight_shape = mlp.dense_h_to_4h.weight.shape

    def _get_layer(self, layer_idx: int):
        """Get a specific transformer layer."""
        if hasattr(self.model, 'model') and hasattr(self.model.model, 'layers'):
            return self.model.model.layers[layer_idx]
        elif hasattr(self.model, 'transformer') and hasattr(self.model.transformer, 'h'):
            return self.model.transformer.h[layer_idx]
        elif hasattr(self.model, 'model') and hasattr(self.model.model, 'h'):
            return self.model.model.h[layer_idx]
        else:
            raise ValueError("Cannot access transformer layers")

    def _get_mlp_weight(self, layer_idx: int) -> torch.Tensor:
        """Get the MLP weight matrix for a layer."""
        layer = self._get_layer(layer_idx)
        mlp = layer.mlp

        if hasattr(mlp, 'gate_proj'):
            return mlp.gate_proj.weight.detach().cpu().float()
        elif hasattr(mlp, 'c_fc'):
            return mlp.c_fc.weight.detach().cpu().float()
        elif hasattr(mlp, 'dense_h_to_4h'):
            return mlp.dense_h_to_4h.weight.detach().cpu().float()
        elif hasattr(mlp, 'w1'):
            return mlp.w1.weight.detach().cpu().float()
        else:
            raise ValueError(f"Cannot find MLP weight for layer {layer_idx}")

    def _register_hooks(self, layer_idx: int):
        """Register forward hooks to capture intermediate activations."""

        def make_attention_hook(name: str):
            def hook(module, input, output):
                # Handle different output formats
                if isinstance(output, tuple):
                    attn_output = output[0]
                else:
                    attn_output = output
                self.attention_outputs[name] = attn_output.detach().cpu()
            return hook

        def make_mlp_hook(name: str, capture_input: bool = False):
            def hook(module, input, output):
                if capture_input:
                    self.mlp_inputs[name] = input[0].detach().cpu()
                else:
                    self.mlp_outputs[name] = output.detach().cpu()
            return hook

        layer = self._get_layer(layer_idx)

        # Hook attention output only
        # Note: We don't hook MLP as it can cause NaN issues on repeated forward passes
        if hasattr(layer, 'self_attn'):
            h1 = layer.self_attn.register_forward_hook(
                make_attention_hook(f"layer_{layer_idx}_attn")
            )
            self.hooks.append(h1)
        elif hasattr(layer, 'attn'):
            h1 = layer.attn.register_forward_hook(
                make_attention_hook(f"layer_{layer_idx}_attn")
            )
            self.hooks.append(h1)

    def _clear_hooks(self):
        """Remove all registered hooks and clear storage."""
        for hook in self.hooks:
            hook.remove()
        self.hooks = []
        self.attention_outputs = {}
        self.mlp_inputs = {}
        self.mlp_outputs = {}

    def _tokenize(self, text: str) -> Dict[str, torch.Tensor]:
        """Tokenize text and move to device."""
        tokens = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True
        )
        return {k: v.to(self.device) for k, v in tokens.items()}

    def compute_contextual_delta(
        self,
        full_context: str,
        partial_context: str,
        layer_idx: int = 0
    ) -> Dict[str, Any]:
        """
        Compute the contextual vector δ = A(C,x) - A(C\\Y,x)

        This measures the "marginal effect" of adding context portion Y.

        Args:
            full_context: Complete context string
            partial_context: Context with portion removed
            layer_idx: Which transformer layer to measure

        Returns:
            Dictionary with attention outputs and computed delta
        """
        results = {}

        # Register hook once and keep it
        self._clear_hooks()  # Clear any existing
        self._register_hooks(layer_idx)

        key = f"layer_{layer_idx}_attn"

        # Forward pass with partial context FIRST
        partial_tokens = self._tokenize(partial_context)
        with torch.no_grad():
            self.model(**partial_tokens)

        partial_attn = self.attention_outputs.get(key)
        if partial_attn is None:
            self._clear_hooks()
            raise ValueError(f"No attention output captured for layer {layer_idx}")

        partial_attn = partial_attn.clone()
        self.attention_outputs.clear()  # Clear storage but keep hook

        # Forward pass with full context
        full_tokens = self._tokenize(full_context)
        with torch.no_grad():
            self.model(**full_tokens)

        full_attn = self.attention_outputs.get(key)
        if full_attn is None:
            self._clear_hooks()
            raise ValueError(f"No attention output captured for layer {layer_idx}")

        full_attn = full_attn.clone()
        self._clear_hooks()

        # Compute contextual delta (at last token position)
        # Note: Both tensors should be on CPU now (from hook)
        full_last = full_attn[0, -1, :].float()
        partial_last = partial_attn[0, -1, :].float()

        delta = full_last - partial_last

        results['full_attention'] = full_attn
        results['partial_attention'] = partial_attn
        results['contextual_delta'] = delta
        results['delta_norm'] = torch.norm(delta).item()
        results['full_attention_norm'] = torch.norm(full_last).item()
        results['partial_attention_norm'] = torch.norm(partial_last).item()

        return results

    def compute_implicit_weight_update(
        self,
        context_tokens: List[str],
        layer_idx: int = 0,
        verbose: bool = True
    ) -> ICLDynamicsResult:
        """
        Compute the cumulative implicit weight update as tokens are added.

        This implements the core measurement from Dherin et al. (2025):
        For each token, compute ΔW = (W·δ)·Aᵀ / ||A||²

        Args:
            context_tokens: List of context strings (will be concatenated)
            layer_idx: Which transformer layer to measure
            verbose: Print progress

        Returns:
            ICLDynamicsResult with all token updates
        """
        updates: List[TokenUpdate] = []

        # Get MLP weight matrix
        W = self._get_mlp_weight(layer_idx)

        cumulative_context = ""
        prompt_hash = str(hash("".join(context_tokens)))[:16]

        for i, token in enumerate(context_tokens):
            prev_context = cumulative_context
            cumulative_context = cumulative_context + token

            if verbose:
                logger.info(f"Processing token {i}/{len(context_tokens)}: '{token[:30]}...'")

            if i == 0:
                # First token - no delta yet
                updates.append(TokenUpdate(
                    token_idx=i,
                    token_text=token,
                    delta_norm=0.0,
                    update_frobenius_norm=0.0,
                    update_rank=0,
                    implicit_learning_rate=0.0,
                    attention_norm=0.0
                ))
                continue

            try:
                # Compute contextual delta
                delta_result = self.compute_contextual_delta(
                    full_context=cumulative_context,
                    partial_context=prev_context,
                    layer_idx=layer_idx
                )

                delta = delta_result['contextual_delta']
                delta_norm = delta_result['delta_norm']
                A_full_norm = delta_result['full_attention_norm']
                A_norm_sq = A_full_norm ** 2

                # Get full attention for outer product
                A_full = delta_result['full_attention'][0, -1, :].float()

                if A_norm_sq > 1e-10:
                    # Compute rank-1 weight update: ΔW = (W·δ)·Aᵀ / ||A||²
                    W_delta = W @ delta
                    delta_W = torch.outer(W_delta, A_full) / A_norm_sq

                    update_norm = torch.norm(delta_W).item()
                    rank = min(torch.linalg.matrix_rank(delta_W).item(), 1)
                    learning_rate = 1.0 / A_norm_sq
                else:
                    update_norm = 0.0
                    rank = 0
                    learning_rate = 0.0

                updates.append(TokenUpdate(
                    token_idx=i,
                    token_text=token,
                    delta_norm=delta_norm,
                    update_frobenius_norm=update_norm,
                    update_rank=rank,
                    implicit_learning_rate=learning_rate,
                    attention_norm=A_full_norm
                ))

            except Exception as e:
                logger.error(f"Error processing token {i}: {e}")
                updates.append(TokenUpdate(
                    token_idx=i,
                    token_text=token,
                    delta_norm=0.0,
                    update_frobenius_norm=0.0,
                    update_rank=0,
                    implicit_learning_rate=0.0,
                    attention_norm=0.0
                ))

        cumulative_norm = sum(u.update_frobenius_norm for u in updates)

        return ICLDynamicsResult(
            layer_idx=layer_idx,
            total_tokens=len(context_tokens),
            updates=updates,
            cumulative_update_norm=cumulative_norm,
            model_name=self.model_name,
            prompt_hash=prompt_hash
        )

    def measure_multi_layer(
        self,
        context_tokens: List[str],
        layer_indices: Optional[List[int]] = None,
        verbose: bool = True
    ) -> Dict[int, ICLDynamicsResult]:
        """
        Measure ICL dynamics across multiple layers.

        Args:
            context_tokens: List of context strings
            layer_indices: Which layers to measure (default: first, middle, last)
            verbose: Print progress

        Returns:
            Dictionary mapping layer index to results
        """
        if layer_indices is None:
            # Default to first, middle, and last layer
            mid = self.num_layers // 2
            layer_indices = [0, mid, self.num_layers - 1]

        results = {}
        for layer_idx in layer_indices:
            if verbose:
                logger.info(f"\n=== Measuring Layer {layer_idx} ===")
            results[layer_idx] = self.compute_implicit_weight_update(
                context_tokens, layer_idx, verbose
            )

        return results

    def visualize_dynamics(
        self,
        result: ICLDynamicsResult,
        save_path: Optional[str] = None,
        show: bool = True
    ):
        """
        Visualize the implicit weight update dynamics.

        Args:
            result: ICLDynamicsResult to visualize
            save_path: Path to save figure (optional)
            show: Whether to display the figure
        """
        if not HAS_MATPLOTLIB:
            logger.warning("matplotlib not available, skipping visualization")
            return None

        updates = result.updates

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        token_indices = [u.token_idx for u in updates]

        # Plot 1: Delta norms
        ax1 = axes[0, 0]
        delta_norms = [u.delta_norm for u in updates]
        ax1.plot(token_indices, delta_norms, 'b-o', markersize=4, linewidth=1.5)
        ax1.set_xlabel('Token Index', fontsize=10)
        ax1.set_ylabel('Contextual Delta ||δ||', fontsize=10)
        ax1.set_title('Marginal Context Effect per Token', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.fill_between(token_indices, delta_norms, alpha=0.3)

        # Plot 2: Weight update norms
        ax2 = axes[0, 1]
        update_norms = [u.update_frobenius_norm for u in updates]
        ax2.plot(token_indices, update_norms, 'r-o', markersize=4, linewidth=1.5)
        ax2.set_xlabel('Token Index', fontsize=10)
        ax2.set_ylabel('||ΔW|| (Frobenius)', fontsize=10)
        ax2.set_title('Implicit Weight Update Magnitude', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.fill_between(token_indices, update_norms, alpha=0.3, color='red')

        # Plot 3: Cumulative update
        ax3 = axes[1, 0]
        cumulative = np.cumsum(update_norms)
        ax3.plot(token_indices, cumulative, 'g-o', markersize=4, linewidth=1.5)
        ax3.set_xlabel('Token Index', fontsize=10)
        ax3.set_ylabel('Cumulative ||ΔW||', fontsize=10)
        ax3.set_title('Cumulative Implicit Weight Change', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.fill_between(token_indices, cumulative, alpha=0.3, color='green')

        # Plot 4: Implicit learning rate
        ax4 = axes[1, 1]
        learning_rates = [u.implicit_learning_rate for u in updates]
        ax4.plot(token_indices, learning_rates, 'm-o', markersize=4, linewidth=1.5)
        ax4.set_xlabel('Token Index', fontsize=10)
        ax4.set_ylabel('h = 1/||A||²', fontsize=10)
        ax4.set_title('Implicit Learning Rate', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.set_yscale('log')

        plt.suptitle(
            f'ICL Implicit Weight Dynamics\n'
            f'Model: {result.model_name} | Layer: {result.layer_idx} | '
            f'Total Tokens: {result.total_tokens}',
            fontsize=14, fontweight='bold'
        )
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Saved visualization to {save_path}")

        if show:
            plt.show()

        return fig

    def log_to_database(
        self,
        result: ICLDynamicsResult,
        db_config: Dict[str, str]
    ) -> bool:
        """
        Log ICL dynamics results to PostgreSQL database.

        Args:
            result: ICLDynamicsResult to log
            db_config: Database connection config

        Returns:
            True if successful
        """
        if not HAS_PSYCOPG2:
            logger.warning("psycopg2 not available, skipping database logging")
            return False

        try:
            conn = psycopg2.connect(**db_config)
            cur = conn.cursor()

            # Ensure table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS icl_dynamics_log (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    prompt_hash TEXT,
                    model_name TEXT,
                    layer_idx INTEGER,
                    token_idx INTEGER,
                    token_text TEXT,
                    delta_norm FLOAT,
                    update_frobenius_norm FLOAT,
                    implicit_learning_rate FLOAT,
                    attention_norm FLOAT,
                    cumulative_update_norm FLOAT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Insert each token update
            for update in result.updates:
                cur.execute("""
                    INSERT INTO icl_dynamics_log (
                        session_id, prompt_hash, model_name, layer_idx,
                        token_idx, token_text, delta_norm, update_frobenius_norm,
                        implicit_learning_rate, attention_norm, cumulative_update_norm
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    result.session_id,
                    result.prompt_hash,
                    result.model_name,
                    result.layer_idx,
                    update.token_idx,
                    update.token_text[:500],
                    update.delta_norm,
                    update.update_frobenius_norm,
                    update.implicit_learning_rate,
                    update.attention_norm,
                    result.cumulative_update_norm
                ))

            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"Logged {len(result.updates)} token updates to database")
            return True

        except Exception as e:
            logger.error(f"Database logging failed: {e}")
            return False


def run_few_shot_experiment(
    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
    layer_idx: int = 0,
    save_dir: str = "/ganuda/data/icl_dynamics"
) -> ICLDynamicsResult:
    """
    Run a few-shot learning experiment to measure ICL dynamics.

    This demonstrates how implicit weight updates accumulate as
    examples are added to the context.
    """
    import os
    os.makedirs(save_dir, exist_ok=True)

    measurer = ICLDynamicsMeasurer(model_name)

    # Few-shot arithmetic task
    context_tokens = [
        "You are a helpful calculator assistant. ",
        "Example 1: What is 2 + 3? Answer: 5. ",
        "Example 2: What is 7 + 4? Answer: 11. ",
        "Example 3: What is 9 + 6? Answer: 15. ",
        "Example 4: What is 12 + 8? Answer: 20. ",
        "Now solve: What is 15 + 7? Answer: "
    ]

    logger.info("=" * 60)
    logger.info("ICL DYNAMICS EXPERIMENT: Few-Shot Arithmetic")
    logger.info("=" * 60)

    result = measurer.compute_implicit_weight_update(
        context_tokens,
        layer_idx=layer_idx,
        verbose=True
    )

    # Print summary
    print("\n" + result.summary())

    # Visualize
    save_path = os.path.join(save_dir, f"icl_dynamics_layer{layer_idx}.png")
    measurer.visualize_dynamics(result, save_path=save_path)

    # Save JSON results
    json_path = os.path.join(save_dir, f"icl_dynamics_layer{layer_idx}.json")
    with open(json_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    logger.info(f"Saved results to {json_path}")

    return result


def run_council_experiment(
    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
    layer_idx: int = 0,
    save_dir: str = "/ganuda/data/icl_dynamics"
) -> ICLDynamicsResult:
    """
    Run experiment simulating Council specialist deliberation.

    Measures how each specialist's reasoning contributes to
    implicit weight updates.
    """
    import os
    os.makedirs(save_dir, exist_ok=True)

    measurer = ICLDynamicsMeasurer(model_name)

    # Simulated Council deliberation
    context_tokens = [
        "The Cherokee AI Council is evaluating a proposal. ",
        "[Crawdad Security]: I've analyzed the security implications. No vulnerabilities detected. The approach follows least-privilege principles. APPROVE. ",
        "[Gecko Technical]: From a technical standpoint, the integration is clean. API design follows REST conventions. Performance impact is minimal. APPROVE. ",
        "[Turtle 7Gen Wisdom]: Considering the seven generations principle, this serves long-term goals. It builds foundational capability. APPROVE. ",
        "[Eagle Eye Monitoring]: Observability is maintained. Metrics and logging are comprehensive. APPROVE. ",
        "[Spider Integration]: Cross-system integration points are well-defined. No breaking changes to existing workflows. APPROVE. ",
        "[Raven Strategy]: This aligns with our roadmap objectives. Resource allocation is appropriate. APPROVE. ",
        "[Peace Chief]: Based on Council consensus, the proposal is APPROVED with unanimous support. ",
        "Final decision: "
    ]

    logger.info("=" * 60)
    logger.info("ICL DYNAMICS EXPERIMENT: Council Deliberation")
    logger.info("=" * 60)

    result = measurer.compute_implicit_weight_update(
        context_tokens,
        layer_idx=layer_idx,
        verbose=True
    )

    # Print summary
    print("\n" + result.summary())

    # Visualize
    save_path = os.path.join(save_dir, f"icl_dynamics_council_layer{layer_idx}.png")
    measurer.visualize_dynamics(result, save_path=save_path)

    # Save JSON results
    json_path = os.path.join(save_dir, f"icl_dynamics_council_layer{layer_idx}.json")
    with open(json_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    logger.info(f"Saved results to {json_path}")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ICL Implicit Weight Dynamics Measurement")
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct", help="Model name")
    parser.add_argument("--layer", type=int, default=0, help="Layer index to measure")
    parser.add_argument("--experiment", choices=["fewshot", "council", "both"], default="both")
    parser.add_argument("--save-dir", default="/ganuda/data/icl_dynamics")

    args = parser.parse_args()

    if args.experiment in ["fewshot", "both"]:
        run_few_shot_experiment(args.model, args.layer, args.save_dir)

    if args.experiment in ["council", "both"]:
        run_council_experiment(args.model, args.layer, args.save_dir)
