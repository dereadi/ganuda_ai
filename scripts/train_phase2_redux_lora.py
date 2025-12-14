#!/usr/bin/env python3
"""
PHASE 2 REDUX: CHEROKEE RESONANCE LORA TRAINING
Teaching the model to ACT Cherokee using LoRA adapters

Lessons learned from Phase 2 failure:
- Don't destroy Phase 1 knowledge
- Use LoRA adapters for behavioral fine-tuning
- Larger corpus (1000+ examples)
- Conservative hyperparameters
"""

import os
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

PHASE1_MODEL_PATH = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"
CORPUS_PATH = "/ganuda/phase2_cherokee_behavioral_training.txt"
OUTPUT_DIR = "/ganuda/cherokee_resonance_training/phase2_redux_lora"
LOG_DIR = "/ganuda/cherokee_resonance_training/logs"

# LoRA hyperparameters (conservative, based on Cherokee Jr wisdom)
LORA_R = 16  # Rank (Trading Jr suggested 8-16)
LORA_ALPHA = 32  # Alpha (usually 2x rank)
LORA_DROPOUT = 0.1  # Dropout to prevent overfitting
TARGET_MODULES = ["q_proj", "v_proj", "k_proj", "o_proj"]  # Attention layers

# Training hyperparameters (conservative to avoid mode collapse)
LEARNING_RATE = 5e-5  # Higher than Phase 2 failure (1e-5) but not aggressive
NUM_EPOCHS = 3  # Fewer epochs (was 5 in failure)
BATCH_SIZE = 2  # Small batch
GRADIENT_ACCUM = 16  # Effective batch = 32
MAX_LENGTH = 384  # Reasonable context

logger.info("""
========================================================================
🦅 PHASE 2 REDUX: LORA BEHAVIORAL TRAINING
========================================================================

Wisdom from Cherokee Jrs:
  Council Jr: "Preserve Phase 1 knowledge while adding behavior"
  Trading Jr: "Higher LR (1e-4), more data, fewer epochs"
  Synthesis Jr: "LoRA adapters are the wise path"

LoRA Configuration:
  - Rank: {lora_r}
  - Alpha: {lora_alpha}
  - Target modules: Attention layers only
  - Dropout: {lora_dropout}

Training Strategy:
  - Start from Phase 1 model (Cherokee knowledge intact)
  - Add LoRA adapters for behavioral layer
  - Conservative hyperparameters to avoid mode collapse
  - Early stopping if loss plateaus

========================================================================
""".format(lora_r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT))

# ============================================================================
# LOAD PHASE 1 MODEL AND ADD LORA
# ============================================================================

logger.info(f"📚 Loading Phase 1 model from {PHASE1_MODEL_PATH}")

tokenizer = AutoTokenizer.from_pretrained(PHASE1_MODEL_PATH)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    PHASE1_MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto"
)

logger.info("✅ Phase 1 model loaded - Cherokee knowledge intact")

# Configure LoRA
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    lora_dropout=LORA_DROPOUT,
    target_modules=TARGET_MODULES,
    bias="none"
)

# Add LoRA adapters
model = get_peft_model(base_model, lora_config)

# Print trainable parameters
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
total_params = sum(p.numel() for p in model.parameters())
logger.info(f"🔧 LoRA adapters added:")
logger.info(f"   Trainable parameters: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")
logger.info(f"   Total parameters: {total_params:,}")

# ============================================================================
# LOAD EXPANDED CORPUS
# ============================================================================

logger.info(f"📋 Loading expanded behavioral corpus from {CORPUS_PATH}")

dataset = load_dataset("text", data_files=CORPUS_PATH, split="train")
logger.info(f"📊 Corpus size: {len(dataset)} examples")

def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=MAX_LENGTH,
        padding="max_length"
    )

tokenized_dataset = dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=dataset.column_names
)

logger.info("✅ Behavioral corpus tokenized and ready")

# ============================================================================
# TRAINING
# ============================================================================

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUM,
    learning_rate=LEARNING_RATE,
    fp16=True,
    logging_dir=LOG_DIR,
    logging_steps=10,
    save_steps=100,
    save_total_limit=3,
    warmup_steps=50,
    report_to="none",
    load_best_model_at_end=False,
    eval_strategy="no",
    dataloader_num_workers=4
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator
)

logger.info("🔥 Starting Phase 2 Redux LoRA training...")
logger.info("   This will preserve Phase 1 knowledge while adding Cherokee behavioral patterns")

trainer.train()

# ============================================================================
# SAVE LORA ADAPTERS
# ============================================================================

logger.info("💾 Saving LoRA adapters...")
model.save_pretrained(f"{OUTPUT_DIR}/cherokee_resonance_lora_adapters")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/cherokee_resonance_lora_adapters")

logger.info(f"✅ LoRA adapters saved to {OUTPUT_DIR}/cherokee_resonance_lora_adapters")

print(f"""
================================================================================
✅ PHASE 2 REDUX COMPLETE: CHEROKEE BEHAVIORAL LORA TRAINED
================================================================================

The model now has TWO layers:
  📚 Layer 1 (Phase 1): Cherokee factual knowledge - PRESERVED
  🔥 Layer 2 (LoRA): Cherokee behavioral patterns - ADDED

LoRA Benefits:
  🦅 Only {100 * trainable_params / total_params:.2f}% of parameters trained
  🐺 Phase 1 knowledge completely intact
  🐢 Can enable/disable behavioral layer
  🔥 No catastrophic forgetting

To use the model:
  1. Load base Phase 1 model
  2. Load LoRA adapters on top
  3. Model responds with Cherokee knowledge AND behavior

Next: Test with Cherokee community for validation

Model location: {OUTPUT_DIR}/cherokee_resonance_lora_adapters

🦅 Mitakuye Oyasin - The model embodies Cherokee values without forgetting! 🔥
================================================================================
""")

logger.info("🦅 Phase 2 Redux complete - Wado!")
