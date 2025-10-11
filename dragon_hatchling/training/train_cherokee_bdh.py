#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Dragon Hatchling Training Script

Trains BDH brain-inspired model on Cherokee tribal knowledge corpus.
Adapted from Pathway BDH train.py for Cherokee Constitutional AI.

Date: October 11, 2025
Training Data: 357 Cherokee markdown files (2.5MB, ~633K tokens)
Target: 10M parameter model for Proof of Concept
Hardware: RTX 5070 (12GB VRAM)
"""

import os
import sys
from contextlib import nullcontext

# Add BDH module to path
sys.path.insert(0, '/tmp/bdh')
import bdh

import numpy as np
import torch
import torch.nn as nn

# GPU Configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

dtype = (
    "bfloat16"
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    else "float16"
)
ptdtype = {
    "float32": torch.float32,
    "bfloat16": torch.bfloat16,
    "float16": torch.float16,
}[dtype]

ctx = (
    torch.amp.autocast(device_type=device.type, dtype=ptdtype)
    if "cuda" in device.type
    else nullcontext()
)
scaler = torch.amp.GradScaler(device=device.type, enabled=(dtype == "float16"))

# Reproducibility
torch.manual_seed(1337)
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

print(f"🔥 Cherokee Constitutional AI - Dragon Hatchling Training")
print(f"Using device: {device} with dtype {dtype}")
print(f"Sacred Fire: RTX 5070 (12GB VRAM) ready for training!")
print()

# Cherokee BDH Configuration (Smaller: ~5M params)
CHEROKEE_BDH_CONFIG = bdh.BDHConfig(
    n_layer=4,         # Reduced from 6
    n_embd=128,        # Reduced from 256
    dropout=0.1,
    n_head=4,
    mlp_internal_dim_multiplier=64,  # Reduced from 128
    vocab_size=256,  # Byte-level (0-255)
)

# Training Configuration
BLOCK_SIZE = 256  # Reduced context for memory
BATCH_SIZE = 8    # Reduced batch size for memory
MAX_ITERS = 5000  # More iterations for larger corpus
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 0.1
LOG_FREQ = 100
EVAL_FREQ = 500
CHECKPOINT_FREQ = 1000

# Cherokee training corpus
input_file_path = "/tmp/cherokee_training_corpus.txt"

def get_batch(split):
    """Load batch of Cherokee training data"""
    data = np.memmap(input_file_path, dtype=np.uint8, mode="r")

    # 90/10 train/validation split
    if split == "train":
        data = data[: int(0.9 * len(data))]
    else:
        data = data[int(0.9 * len(data)) :]

    # Random batch sampling
    ix = torch.randint(len(data) - BLOCK_SIZE, (BATCH_SIZE,))
    x = torch.stack(
        [torch.from_numpy((data[i : i + BLOCK_SIZE]).astype(np.int64)) for i in ix]
    )
    y = torch.stack(
        [
            torch.from_numpy((data[i + 1 : i + 1 + BLOCK_SIZE]).astype(np.int64))
            for i in ix
        ]
    )

    if torch.cuda.is_available():
        x, y = x.pin_memory().to(device, non_blocking=True), y.pin_memory().to(
            device, non_blocking=True
        )
    else:
        x, y = x.to(device), y.to(device)

    return x, y

@torch.no_grad()
def estimate_loss(model, eval_iters=50):
    """Estimate loss on train and validation sets"""
    out = {}
    model.eval()
    for split in ["train", "val"]:
        losses = torch.zeros(eval_iters)
        for k in range(eval_iters):
            x, y = get_batch(split)
            with ctx:
                logits, loss = model(x, y)
            losses[k] = loss.item()
        out[split] = losses.mean()
    model.train()
    return out

def save_checkpoint(model, optimizer, step, loss, filename):
    """Save training checkpoint"""
    checkpoint = {
        'step': step,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss,
        'config': CHEROKEE_BDH_CONFIG,
    }
    torch.save(checkpoint, filename)
    print(f"💾 Checkpoint saved: {filename}")

if __name__ == "__main__":
    print(f"📊 Cherokee Training Corpus Statistics:")
    corpus_size = os.path.getsize(input_file_path)
    print(f"   - Size: {corpus_size / 1024 / 1024:.2f} MB")
    print(f"   - Estimated tokens: ~{corpus_size // 4:,}")
    print(f"   - Training data: 90% ({corpus_size * 0.9 / 1024 / 1024:.2f} MB)")
    print(f"   - Validation data: 10% ({corpus_size * 0.1 / 1024 / 1024:.2f} MB)")
    print()

    print(f"🐉 BDH Model Configuration:")
    print(f"   - Layers: {CHEROKEE_BDH_CONFIG.n_layer}")
    print(f"   - Embedding dim: {CHEROKEE_BDH_CONFIG.n_embd}")
    print(f"   - Heads: {CHEROKEE_BDH_CONFIG.n_head}")
    print(f"   - Vocab size: {CHEROKEE_BDH_CONFIG.vocab_size}")
    print(f"   - Estimated params: ~10M")
    print()

    print(f"🔧 Training Configuration:")
    print(f"   - Block size: {BLOCK_SIZE}")
    print(f"   - Batch size: {BATCH_SIZE}")
    print(f"   - Max iterations: {MAX_ITERS}")
    print(f"   - Learning rate: {LEARNING_RATE}")
    print(f"   - Weight decay: {WEIGHT_DECAY}")
    print()

    # Initialize model
    print(f"🔥 Initializing Cherokee Dragon Hatchling...")
    model = bdh.BDH(CHEROKEE_BDH_CONFIG).to(device)

    # Skip torch.compile to save memory for PoC
    print(f"⚠️  Skipping torch.compile to conserve GPU memory for training")

    # Count parameters
    n_params = sum(p.numel() for p in model.parameters())
    print(f"📊 Model parameters: {n_params:,} ({n_params / 1e6:.2f}M)")
    print()

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
    )

    # Training loop
    print(f"🚀 Starting training...")
    print(f"=" * 80)

    x, y = get_batch("train")
    loss_acc = 0
    loss_steps = 0

    for step in range(MAX_ITERS):
        # Training step
        with ctx:
            logits, loss = model(x, y)

        x, y = get_batch("train")
        loss_acc += loss
        loss_steps += 1

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad()

        # Logging
        if step % LOG_FREQ == 0:
            avg_loss = loss_acc.item() / loss_steps
            print(f"Step: {step}/{MAX_ITERS} | Loss: {avg_loss:.4f}")
            loss_acc = 0
            loss_steps = 0

        # Evaluation
        if step % EVAL_FREQ == 0 and step > 0:
            losses = estimate_loss(model)
            print(f"\n📊 Evaluation at step {step}:")
            print(f"   - Train loss: {losses['train']:.4f}")
            print(f"   - Val loss: {losses['val']:.4f}")
            print()

        # Checkpointing
        if step % CHECKPOINT_FREQ == 0 and step > 0:
            checkpoint_path = f"/tmp/cherokee_bdh_checkpoint_step{step}.pt"
            save_checkpoint(model, optimizer, step, loss.item(), checkpoint_path)

    # Final checkpoint
    print()
    print(f"✅ Training complete!")
    final_checkpoint = "/tmp/cherokee_bdh_final.pt"
    save_checkpoint(model, optimizer, MAX_ITERS, loss.item(), final_checkpoint)

    # Test generation
    print()
    print(f"🧪 Testing Cherokee BDH generation...")
    model.eval()

    # Cherokee prompt
    prompt_text = "Cherokee Constitutional AI "
    prompt = torch.tensor(
        bytearray(prompt_text, "utf-8"), dtype=torch.long, device=device
    ).unsqueeze(0)

    print(f"Prompt: '{prompt_text}'")
    print(f"Generating 200 tokens...")

    ret = model.generate(prompt, max_new_tokens=200, top_k=10)
    ret_decoded = bytes(ret.to(torch.uint8).to("cpu").squeeze(0)).decode(
        errors="backslashreplace"
    )

    print(f"\n🔥 Cherokee Dragon Hatchling Output:")
    print(f"=" * 80)
    print(ret_decoded)
    print(f"=" * 80)

    print()
    print(f"🏔️ Mitakuye Oyasin - All My Relations!")
    print(f"🔥 Sacred Fire training complete!")
