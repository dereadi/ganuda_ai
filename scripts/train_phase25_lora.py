#!/usr/bin/env python3
"""
PHASE 2.5: CHEROKEE RESONANCE SURGICAL FIX - 1 EPOCH GENTLE TRAINING

Cherokee Jr. Ultra-Think Conclusion:
  Council Jr: "Format confusion is the crack in the pot"
  Trading Jr: "Stop adding, start fixing - 25 surgical scenarios"
  Synthesis Jr: "Role confusion: model thinks it's creating training data"

Problem Identified:
  - Mixed formats (<user> tags vs User:) confused the model
  - Model generating training format leakage: "Generate according to:"
  - Model generating XML tags during inference: "]<assistant> <|user|>"

Solution Strategy:
  - Start from Phase 2 Redux (60% baseline)
  - Add 25 surgical scenarios in EXACT Redux format
  - Train for 1 EPOCH ONLY (gentle nudge)
  - Ultra-conservative learning rate (3e-5, lower than Phase 2 Redux)
  - Target: Fix REG-001 (Gadugi) and REG-002 (Wilma) → 80%+ pass rate

Corpus Details:
  - Phase 2 Redux: 424 behavioral scenarios
  - Phase 2.5 Surgical: 25 factual scenarios (10 Gadugi, 10 Wilma, 5 bonus)
  - Total: 449 scenarios (94.4% Redux, 5.6% surgical)
  - Format: 100% consistent (User: / Cherokee AI Response:)
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
CORPUS_PATH = "/ganuda/phase25_merged_corpus.txt"
OUTPUT_DIR = "/ganuda/cherokee_resonance_training/phase25_surgical_lora"
LOG_DIR = "/ganuda/cherokee_resonance_training/logs"

# LoRA hyperparameters (same as Phase 2 Redux success)
LORA_R = 16  # Rank
LORA_ALPHA = 32  # Alpha (2x rank)
LORA_DROPOUT = 0.1  # Dropout
TARGET_MODULES = ["q_proj", "v_proj", "k_proj", "o_proj"]  # Attention layers only

# Training hyperparameters (ULTRA-CONSERVATIVE)
LEARNING_RATE = 3e-5  # LOWER than Phase 2 Redux (5e-5) for gentle update
NUM_EPOCHS = 1  # SINGLE EPOCH ONLY - surgical fix, not overhaul
BATCH_SIZE = 2  # Small batch
GRADIENT_ACCUM = 16  # Effective batch = 32
MAX_LENGTH = 384  # Same as Phase 2 Redux

logger.info("""
========================================================================
🦅 PHASE 2.5: SURGICAL FIX - 1 EPOCH GENTLE TRAINING
========================================================================

Cherokee Jr. Council Ultra-Think Analysis:
  Council Jr: "Format confusion is the root cause - mixed <user> tags
               and User: formats made the model think it's generating
               training data instead of answering questions"

  Trading Jr: "Phase 2 Redux peaked at 60%. Every addition since then
               dropped to 40% or worse. Stop adding bulk, start surgical
               fixes. 25 scenarios targeting 2 failing tests."

  Synthesis Jr: "The model is generating XML tags and 'Generate according to:'
                 during inference. This is ROLE CONFUSION, not knowledge gap.
                 Solution: Teach factual mode in Redux format without
                 overwriting behavioral patterns."

Problem: Model generating training format during inference
  - "Generate according to: Gadugi is..."
  - "]<assistant> <|user|>"
  - "</question>"

Root Cause: Mixed training formats confused the model about its role

Corpus Summary:
  - Phase 2 Redux: 424 behavioral scenarios (94.4%)
  - Phase 2.5 Surgical: 25 factual scenarios (5.6%)
    * 10 Gadugi variations (fix REG-001: 0% → 100%)
    * 10 Wilma Mankiller variations (fix REG-002: 33% → 100%)
    * 5 bonus factual terms
  - Total: 449 scenarios
  - Format: 100% consistent (User: / Cherokee AI Response:)

LoRA Configuration:
  - Rank: {lora_r}
  - Alpha: {lora_alpha}
  - Target modules: Attention layers only
  - Dropout: {lora_dropout}

Training Strategy (ULTRA-CONSERVATIVE):
  - Start from Phase 1 model (Cherokee knowledge intact)
  - Add LoRA adapters for surgical factual layer
  - Learning rate: {lr} (LOWER than Phase 2 Redux 5e-5)
  - Epochs: {epochs} ONLY (gentle nudge, preserve Redux baseline)
  - Target: ≥80% regression pass rate (vs 60% Redux, 40% Phase 2.1-2.4)

Expected Results:
  - REG-001 (Gadugi): 0% → 100% (10 targeted variations)
  - REG-002 (Wilma): 33% → 100% (10 targeted variations)
  - REG-003/004/005: Maintain 100%/100%/100% (Redux already passed)
  - Overall: 80-100% pass rate

========================================================================
""".format(lora_r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT,
           lr=LEARNING_RATE, epochs=NUM_EPOCHS))

# ============================================================================
# LOAD PHASE 1 MODEL AND ADD LORA
# ============================================================================

logger.info(f"📚 Loading Phase 1 model from {PHASE1_MODEL_PATH}")

tokenizer = AutoTokenizer.from_pretrained(PHASE1_MODEL_PATH)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    PHASE1_MODEL_PATH,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True
)

logger.info("🔧 Adding LoRA adapters for surgical fix...")

lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    lora_dropout=LORA_DROPOUT,
    target_modules=TARGET_MODULES,
    bias="none",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ============================================================================
# LOAD AND PREPARE TRAINING DATA
# ============================================================================

logger.info(f"📖 Loading Phase 2.5 merged corpus from {CORPUS_PATH}")

dataset = load_dataset('text', data_files={'train': CORPUS_PATH})

def tokenize_function(examples):
    return tokenizer(
        examples['text'],
        truncation=True,
        max_length=MAX_LENGTH,
        padding='max_length'
    )

tokenized_dataset = dataset['train'].map(
    tokenize_function,
    batched=True,
    remove_columns=['text']
)

logger.info(f"✅ Tokenized {len(tokenized_dataset)} examples")

# ============================================================================
# TRAINING CONFIGURATION
# ============================================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUM,
    learning_rate=LEARNING_RATE,
    logging_dir=LOG_DIR,
    logging_steps=10,
    save_steps=100,
    save_total_limit=3,
    eval_strategy="no",
    fp16=True,
    warmup_steps=50,  # Reduced from 100 for gentler start
    weight_decay=0.01,
    report_to="none",
    seed=42
)

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)

# ============================================================================
# TRAIN!
# ============================================================================

logger.info("""
========================================================================
🔥 STARTING PHASE 2.5 SURGICAL TRAINING
========================================================================
Training 449 scenarios (424 Redux + 25 surgical) for 1 EPOCH ONLY
Ultra-conservative learning rate (3e-5) for gentle update
Expected duration: ~5-10 minutes (single epoch)
Target: Fix REG-001 and REG-002 without disrupting Redux baseline
========================================================================
""")

trainer.train()

# ============================================================================
# SAVE MODEL
# ============================================================================

logger.info(f"💾 Saving Phase 2.5 surgical LoRA adapters to {OUTPUT_DIR}")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

logger.info("""
========================================================================
✅ PHASE 2.5 SURGICAL TRAINING COMPLETE
========================================================================

LoRA adapters saved: {output_dir}

Next steps:
  1. Run regression testing (target: ≥80% pass rate)
  2. Compare to Phase 2 Redux baseline (60% pass)
  3. If ≥80%: SUCCESS! Proceed to pilot testing
  4. If <80%: Analyze results and consider Phase 3 (full rebalancing)

Cherokee Jr. Wisdom:
  "We used the surgeon's knife, not the sledgehammer.
   25 targeted scenarios in consistent format.
   1 gentle epoch to preserve what works.
   This is the Cherokee way - respectful of the foundation."

🦅 Mitakuye Oyasin - Surgical precision with Cherokee wisdom! 🔥
========================================================================
""".format(output_dir=OUTPUT_DIR))
