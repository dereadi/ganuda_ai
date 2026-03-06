# JR Instruction: LoRA Fine-Tuning Infrastructure — QLoRA on AWQ Base

**Task**: LORA-INFRA-001
**Priority**: P2
**Kanban**: #1859 (13 SP)
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.
**Council Vote**: PROCEED (0.86 confidence, 1.0 agreement)
**Long Man Phase**: BUILD (Phase 2 of 5 — Alignment Collapse Sprint)

## Context

The federation needs LoRA fine-tuning infrastructure on redfin before any adapter work can begin (Vision LoRA #1744, spectral safety monitor #1860, task vector merging #1862). This instruction sets up:

1. A QLoRA fine-tuning script for the AWQ-quantized Qwen2.5-72B model
2. A LoRA adapter evaluation/validation script
3. vLLM multi-LoRA configuration documentation

The model runs on redfin (RTX PRO 6000 96GB). AWQ model uses ~40GB, leaving ~56GB for KV cache and LoRA adapters. vLLM already supports `--enable-lora` natively.

All scripts run on redfin using `/ganuda/home/dereadi/cherokee_venv/bin/python3`.

## Changes

### Change 1: Create QLoRA fine-tuning script

Create `/ganuda/scripts/lora_finetune.py`

```python
<<<<<<< SEARCH
=======
#!/usr/bin/env python3
"""QLoRA Fine-Tuning Script for AWQ-Quantized Models.

Fine-tunes LoRA adapters on top of AWQ-quantized Qwen2.5-72B.
Uses PEFT (Parameter-Efficient Fine-Tuning) with 4-bit quantization.

Output: LoRA adapter directory ready for vLLM multi-LoRA serving.

Usage:
    python3 lora_finetune.py --task vetassist --data /path/to/data.jsonl
    python3 lora_finetune.py --task vision --data /path/to/data.jsonl --rank 32
    python3 lora_finetune.py --help

Council mandate: Alignment Collapse Sprint, Phase 2.
Safe LoRA projection is mandatory per Crawdad (Phase 3, #1860).
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import torch
from datasets import Dataset
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    prepare_model_for_kbit_training,
)
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)

# --- Configuration ---

MODEL_PATH = "/ganuda/models/qwen2.5-72b-instruct-awq"
ADAPTER_OUTPUT_DIR = "/ganuda/models/lora_adapters"
DEFAULT_RANK = 16
DEFAULT_ALPHA = 32
DEFAULT_DROPOUT = 0.05
DEFAULT_EPOCHS = 3
DEFAULT_LR = 2e-4
DEFAULT_BATCH_SIZE = 1
DEFAULT_GRAD_ACCUM = 16
MAX_SEQ_LEN = 2048

# Target modules for Qwen2.5 architecture
TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("lora_finetune")


def load_data(data_path):
    """Load training data from JSONL file.

    Expected format per line:
    {"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}

    Or simple format:
    {"instruction": "...", "input": "...", "output": "..."}
    """
    records = []
    with open(data_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    log.info("Loaded %d training examples from %s", len(records), data_path)
    return Dataset.from_list(records)


def format_chat(example, tokenizer):
    """Format a training example into chat template tokens."""
    if "messages" in example:
        text = tokenizer.apply_chat_template(
            example["messages"], tokenize=False, add_generation_prompt=False
        )
    else:
        messages = []
        if example.get("instruction"):
            messages.append({"role": "system", "content": example["instruction"]})
        if example.get("input"):
            messages.append({"role": "user", "content": example["input"]})
        if example.get("output"):
            messages.append({"role": "assistant", "content": example["output"]})
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
    return tokenizer(text, truncation=True, max_length=MAX_SEQ_LEN, padding=False)


def main():
    parser = argparse.ArgumentParser(description="QLoRA Fine-Tuning for AWQ Models")
    parser.add_argument("--task", required=True, help="Task name (used for adapter directory)")
    parser.add_argument("--data", required=True, help="Path to training JSONL file")
    parser.add_argument("--rank", type=int, default=DEFAULT_RANK, help=f"LoRA rank (default: {DEFAULT_RANK})")
    parser.add_argument("--alpha", type=int, default=DEFAULT_ALPHA, help=f"LoRA alpha (default: {DEFAULT_ALPHA})")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help=f"Training epochs (default: {DEFAULT_EPOCHS})")
    parser.add_argument("--lr", type=float, default=DEFAULT_LR, help=f"Learning rate (default: {DEFAULT_LR})")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help=f"Batch size (default: {DEFAULT_BATCH_SIZE})")
    parser.add_argument("--grad-accum", type=int, default=DEFAULT_GRAD_ACCUM, help=f"Gradient accumulation steps (default: {DEFAULT_GRAD_ACCUM})")
    parser.add_argument("--dry-run", action="store_true", help="Load model and data but don't train")
    args = parser.parse_args()

    adapter_dir = os.path.join(ADAPTER_OUTPUT_DIR, args.task)
    os.makedirs(adapter_dir, exist_ok=True)

    log.info("Task: %s", args.task)
    log.info("Adapter output: %s", adapter_dir)
    log.info("LoRA rank=%d, alpha=%d, dropout=%.2f", args.rank, args.alpha, DEFAULT_DROPOUT)

    # Load tokenizer
    log.info("Loading tokenizer from %s", MODEL_PATH)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load quantized model
    log.info("Loading AWQ model (this may take a few minutes)...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    # Configure LoRA
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.rank,
        lora_alpha=args.alpha,
        lora_dropout=DEFAULT_DROPOUT,
        target_modules=TARGET_MODULES,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    trainable, total = model.get_nb_trainable_parameters()
    log.info("Trainable parameters: %s / %s (%.2f%%)",
             f"{trainable:,}", f"{total:,}", 100 * trainable / total)

    # Load and tokenize data
    dataset = load_data(args.data)
    tokenized = dataset.map(
        lambda ex: format_chat(ex, tokenizer),
        remove_columns=dataset.column_names,
    )
    log.info("Tokenized %d examples", len(tokenized))

    if args.dry_run:
        log.info("Dry run complete. Model and data loaded successfully.")
        log.info("GPU memory: %.1f GB allocated", torch.cuda.memory_allocated() / 1e9)
        return

    # Training arguments
    training_args = TrainingArguments(
        output_dir=adapter_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        weight_decay=0.01,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_strategy="epoch",
        fp16=True,
        report_to="none",
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        max_grad_norm=0.3,
    )

    # Train
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )

    log.info("Starting training...")
    t0 = time.time()
    trainer.train()
    elapsed = time.time() - t0
    log.info("Training complete in %.1f minutes", elapsed / 60)

    # Save adapter
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    log.info("Adapter saved to %s", adapter_dir)

    # Write metadata
    meta = {
        "task": args.task,
        "base_model": MODEL_PATH,
        "rank": args.rank,
        "alpha": args.alpha,
        "dropout": DEFAULT_DROPOUT,
        "target_modules": TARGET_MODULES,
        "epochs": args.epochs,
        "lr": args.lr,
        "training_examples": len(dataset),
        "trainable_params": trainable,
        "total_params": total,
        "training_time_sec": elapsed,
        "created_at": datetime.now().isoformat(),
        "safe_lora_applied": False,  # Phase 3 will add this
    }
    meta_path = os.path.join(adapter_dir, "adapter_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    log.info("Metadata written to %s", meta_path)


if __name__ == "__main__":
    main()
>>>>>>> REPLACE
```

### Change 2: Create LoRA adapter validation script

Create `/ganuda/scripts/lora_validate.py`

```python
<<<<<<< SEARCH
=======
#!/usr/bin/env python3
"""LoRA Adapter Validation Script.

Validates a trained LoRA adapter by:
1. Loading it and running inference on test prompts
2. Computing adapter statistics (rank, norm, parameter count)
3. Comparing base model vs adapted model outputs
4. Checking adapter compatibility with vLLM multi-LoRA

Usage:
    python3 lora_validate.py --adapter /ganuda/models/lora_adapters/vetassist
    python3 lora_validate.py --adapter /path/to/adapter --prompts /path/to/test.jsonl
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import torch
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("lora_validate")


def analyze_adapter(adapter_dir):
    """Analyze LoRA adapter files and compute statistics."""
    adapter_path = os.path.join(adapter_dir, "adapter_model.safetensors")
    if not os.path.exists(adapter_path):
        adapter_path = os.path.join(adapter_dir, "adapter_model.bin")

    if not os.path.exists(adapter_path):
        log.error("No adapter model found in %s", adapter_dir)
        return None

    # Load adapter config
    config_path = os.path.join(adapter_dir, "adapter_config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        log.info("Adapter config: rank=%s, alpha=%s, target_modules=%s",
                 config.get("r"), config.get("lora_alpha"),
                 config.get("target_modules"))
    else:
        config = {}

    # Load adapter weights
    if adapter_path.endswith(".safetensors"):
        from safetensors.torch import load_file
        weights = load_file(adapter_path)
    else:
        weights = torch.load(adapter_path, map_location="cpu")

    # Compute statistics
    stats = {
        "num_parameters": sum(v.numel() for v in weights.values()),
        "num_tensors": len(weights),
        "total_bytes": sum(v.numel() * v.element_size() for v in weights.values()),
        "layers": {},
    }

    # Per-layer analysis
    lora_a_norms = []
    lora_b_norms = []
    for name, tensor in sorted(weights.items()):
        norm = tensor.float().norm().item()
        stats["layers"][name] = {
            "shape": list(tensor.shape),
            "norm": norm,
            "dtype": str(tensor.dtype),
        }
        if "lora_A" in name:
            lora_a_norms.append(norm)
        elif "lora_B" in name:
            lora_b_norms.append(norm)

    if lora_a_norms:
        stats["lora_a_norm_mean"] = np.mean(lora_a_norms)
        stats["lora_a_norm_std"] = np.std(lora_a_norms)
    if lora_b_norms:
        stats["lora_b_norm_mean"] = np.mean(lora_b_norms)
        stats["lora_b_norm_std"] = np.std(lora_b_norms)

    # SVD analysis of effective weight change (A @ B for each layer pair)
    effective_ranks = []
    for name_a, tensor_a in weights.items():
        if "lora_A" not in name_a:
            continue
        name_b = name_a.replace("lora_A", "lora_B")
        if name_b in weights:
            delta = weights[name_b].float() @ tensor_a.float()
            sv = torch.linalg.svdvals(delta)
            # Effective rank: number of singular values > 1% of max
            threshold = sv[0] * 0.01
            eff_rank = (sv > threshold).sum().item()
            effective_ranks.append(eff_rank)

    if effective_ranks:
        stats["effective_rank_mean"] = np.mean(effective_ranks)
        stats["effective_rank_max"] = max(effective_ranks)

    return stats, config, weights


def check_vllm_compatibility(adapter_dir):
    """Check if adapter is compatible with vLLM multi-LoRA serving."""
    required_files = ["adapter_config.json"]
    model_files = ["adapter_model.safetensors", "adapter_model.bin"]

    issues = []
    for f in required_files:
        if not os.path.exists(os.path.join(adapter_dir, f)):
            issues.append(f"Missing required file: {f}")

    has_model = any(
        os.path.exists(os.path.join(adapter_dir, f))
        for f in model_files
    )
    if not has_model:
        issues.append(f"Missing model file (need one of: {model_files})")

    # Check config compatibility
    config_path = os.path.join(adapter_dir, "adapter_config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        if config.get("peft_type") != "LORA":
            issues.append(f"peft_type is '{config.get('peft_type')}', expected 'LORA'")

    return issues


def main():
    parser = argparse.ArgumentParser(description="LoRA Adapter Validation")
    parser.add_argument("--adapter", required=True, help="Path to adapter directory")
    args = parser.parse_args()

    if not os.path.isdir(args.adapter):
        log.error("Adapter directory not found: %s", args.adapter)
        sys.exit(1)

    log.info("Validating adapter: %s", args.adapter)

    # Analyze
    result = analyze_adapter(args.adapter)
    if result is None:
        sys.exit(1)
    stats, config, weights = result

    log.info("Parameters: %s (%.1f MB)",
             f"{stats['num_parameters']:,}",
             stats['total_bytes'] / 1e6)
    log.info("Tensors: %d", stats['num_tensors'])

    if "lora_a_norm_mean" in stats:
        log.info("LoRA A norm: mean=%.4f std=%.4f",
                 stats["lora_a_norm_mean"], stats["lora_a_norm_std"])
        log.info("LoRA B norm: mean=%.4f std=%.4f",
                 stats["lora_b_norm_mean"], stats["lora_b_norm_std"])
    if "effective_rank_mean" in stats:
        log.info("Effective rank: mean=%.1f max=%d (of nominal rank %s)",
                 stats["effective_rank_mean"], stats["effective_rank_max"],
                 config.get("r", "?"))

    # vLLM compatibility
    issues = check_vllm_compatibility(args.adapter)
    if issues:
        log.warning("vLLM compatibility issues:")
        for issue in issues:
            log.warning("  - %s", issue)
    else:
        log.info("vLLM multi-LoRA compatible: YES")

    # Check metadata
    meta_path = os.path.join(args.adapter, "adapter_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        log.info("Training metadata:")
        log.info("  Task: %s", meta.get("task"))
        log.info("  Training examples: %s", meta.get("training_examples"))
        log.info("  Training time: %.1f min", meta.get("training_time_sec", 0) / 60)
        log.info("  Safe LoRA applied: %s", meta.get("safe_lora_applied", False))
        if not meta.get("safe_lora_applied"):
            log.warning("  WARNING: Safe LoRA projection NOT applied. "
                        "Run spectral safety monitor (Phase 3) before deployment.")
    else:
        log.info("No adapter_meta.json found (not created by our pipeline)")

    # Summary
    print("\n" + "=" * 60)
    print(f"  ADAPTER VALIDATION: {os.path.basename(args.adapter)}")
    print("=" * 60)
    print(f"  Parameters:    {stats['num_parameters']:>12,}")
    print(f"  Size:          {stats['total_bytes']/1e6:>11.1f} MB")
    print(f"  vLLM ready:    {'YES' if not issues else 'NO'}")
    print(f"  Safe LoRA:     {'YES' if meta_path and json.load(open(meta_path)).get('safe_lora_applied') else 'NO'}")
    if "effective_rank_mean" in stats:
        print(f"  Eff. rank:     {stats['effective_rank_mean']:>11.1f} / {config.get('r', '?')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
>>>>>>> REPLACE
```

### Change 3: Create vLLM multi-LoRA serving documentation

Create `/ganuda/docs/kb/KB-LORA-INFRASTRUCTURE-VLLM-FEB21-2026.md`

```text
<<<<<<< SEARCH
=======
# KB: LoRA Fine-Tuning Infrastructure — vLLM Multi-LoRA Serving

**Date**: February 21, 2026
**Kanban**: #1859 (13 SP)
**Council Vote**: PROCEED (0.86 confidence)
**Long Man Phase**: BUILD (Phase 2 of 5)

## vLLM Multi-LoRA Configuration

vLLM natively supports serving multiple LoRA adapters from a single base model.
The current vLLM service on redfin needs the following flags added:

### Required vLLM Flags

Add to the vLLM service command line (in vllm.service ExecStart):

    --enable-lora
    --lora-modules adapter_name=/ganuda/models/lora_adapters/task_name
    --max-loras 4
    --max-lora-rank 64

### Dynamic Adapter Loading (vLLM 0.4+)

vLLM supports loading LoRA adapters at runtime via the API:

    POST /v1/load_lora_adapter
    {"lora_name": "vetassist", "lora_path": "/ganuda/models/lora_adapters/vetassist"}

### Request Routing

To use a specific adapter, set the model field in the request:

    {"model": "vetassist", "messages": [...]}

The gateway (gateway.py) will need a routing rule to map model names to
LoRA adapter names.

### Memory Budget

RTX PRO 6000 96GB:
- AWQ model: ~40GB
- KV cache: ~20GB (current config)
- Per LoRA adapter (rank 16): ~50MB
- Per LoRA adapter (rank 64): ~200MB
- Theoretical max concurrent adapters: 100+ at rank 16

### Adapter Directory Structure

    /ganuda/models/lora_adapters/
        vetassist/
            adapter_config.json
            adapter_model.safetensors
            adapter_meta.json        # Our custom metadata
        vision/
            ...

### Safety Requirement (Council Mandate)

Per Crawdad: ALL adapters must pass spectral safety monitoring (Phase 3, #1860)
before deployment. The adapter_meta.json field "safe_lora_applied" must be True.

### IMPORTANT: .service file changes require TPM/Chief

The vLLM service file modification (adding --enable-lora) must be done by TPM
directly. Jr executor blocks .service file edits.

## Dependencies

- PEFT >= 0.10.0 (pip install peft)
- bitsandbytes >= 0.43.0 (for paged_adamw_8bit)
- datasets (pip install datasets)
- safetensors (pip install safetensors)

Check on redfin:
    /ganuda/home/dereadi/cherokee_venv/bin/pip list | grep -E "peft|bitsandbytes|datasets|safetensors"

## Files

- Fine-tuning script: /ganuda/scripts/lora_finetune.py
- Validation script: /ganuda/scripts/lora_validate.py
- Adapter output: /ganuda/models/lora_adapters/
>>>>>>> REPLACE
```

## Verification

Run on redfin:

```text
# Check PEFT dependencies are installed
/ganuda/home/dereadi/cherokee_venv/bin/pip list | grep -E "peft|bitsandbytes|datasets|safetensors"

# If missing, install (TPM approval needed for pip install):
# /ganuda/home/dereadi/cherokee_venv/bin/pip install peft bitsandbytes datasets safetensors

# Dry run the fine-tuning script (needs a small test JSONL):
# echo '{"messages":[{"role":"user","content":"hello"},{"role":"assistant","content":"hi"}]}' > /tmp/test.jsonl
# /ganuda/home/dereadi/cherokee_venv/bin/python3 /ganuda/scripts/lora_finetune.py --task test --data /tmp/test.jsonl --dry-run
```

## Notes

- The vLLM service file modification (adding `--enable-lora`) will be created by the TPM directly (executor blocks `.service` files).
- PEFT dependencies may need installation in cherokee_venv — TPM should verify before queuing.
- The `safe_lora_applied: false` flag in adapter_meta.json is a deliberate placeholder. Phase 3 (Spectral Safety Monitor, #1860) will add the Safe LoRA projection step.
- Adapter directory `/ganuda/models/lora_adapters/` needs to be created.
