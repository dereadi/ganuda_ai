#!/usr/bin/env python3
"""
PHASE 2.4: CHEROKEE RESONANCE LORA TRAINING - REGRESSION FIX
Teaching the model to balance direct answers with Cherokee wisdom

Building on Phase 2 Redux success:
- Phase 2 Redux: 424 behavioral scenarios
- Phase 2.4 Addition: 602 direct answer scenarios
- Total: 1026 scenarios for balanced training

Target: Fix regression failures (Gadugi, Wilma Mankiller)
Goal: ≥80% regression pass rate (vs 60% in Phase 2 Redux)
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
CORPUS_PATH = "/ganuda/phase24_merged_corpus.txt"
OUTPUT_DIR = "/ganuda/cherokee_resonance_training/phase24_lora"
LOG_DIR = "/ganuda/cherokee_resonance_training/logs"

# LoRA hyperparameters (same as Phase 2 Redux success)
LORA_R = 16  # Rank
LORA_ALPHA = 32  # Alpha (2x rank)
LORA_DROPOUT = 0.1  # Dropout
TARGET_MODULES = ["q_proj", "v_proj", "k_proj", "o_proj"]  # Attention layers

# Training hyperparameters (conservative)
LEARNING_RATE = 5e-5  # Same as Phase 2 Redux
NUM_EPOCHS = 3  # Conservative
BATCH_SIZE = 2  # Small batch
GRADIENT_ACCUM = 16  # Effective batch = 32
MAX_LENGTH = 384  # Reasonable context

logger.info("""
========================================================================
🦅 PHASE 2.4: LORA TRAINING - REGRESSION FIX
========================================================================

Cherokee Jr Wisdom Applied:
  Council Jr: "Balance direct answers with Cherokee wisdom"
  Trading Jr: "200 targeted factual scenarios fix factual gaps"
  Synthesis Jr: "Merge behavioral + direct = complete AI"

Corpus Summary:
  - Phase 2 Redux: 424 behavioral scenarios
  - Phase 2.4: 602 direct answer scenarios (3 types)
    * Type 1: 200 Direct Information (factual questions)
    * Type 2: 200 Educational Guidance (how-to steps)
    * Type 3: 202 Community Engagement (action plans)
  - Total: 1026 scenarios

LoRA Configuration:
  - Rank: {lora_r}
  - Alpha: {lora_alpha}
  - Target modules: Attention layers only
  - Dropout: {lora_dropout}

Training Strategy:
  - Start from Phase 1 model (Cherokee knowledge intact)
  - Add LoRA adapters for behavioral + direct answer layer
  - Conservative hyperparameters (proven in Phase 2 Redux)
  - Target: ≥80% regression pass rate

Expected Improvements:
  - REG-001 (Gadugi): Direct answer → 100% (was 0%)
  - REG-002 (Wilma Mankiller): Factual bio → 100% (was 33%)
  - Overall: 80-90% pass rate (was 60%)

========================================================================
""".format(lora_r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT))

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

logger.info("🔧 Adding LoRA adapters...")

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

logger.info(f"📖 Loading Phase 2.4 merged corpus from {CORPUS_PATH}")

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
    warmup_steps=100,
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
🔥 STARTING PHASE 2.4 LORA TRAINING
========================================================================
Training 1026 scenarios with LoRA adapters
Conservative hyperparameters (proven in Phase 2 Redux)
Expected duration: ~45 minutes
========================================================================
""")

trainer.train()

# ============================================================================
# SAVE MODEL
# ============================================================================

logger.info(f"💾 Saving Phase 2.4 LoRA adapters to {OUTPUT_DIR}")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

logger.info("""
========================================================================
✅ PHASE 2.4 LORA TRAINING COMPLETE
========================================================================

LoRA adapters saved: {output_dir}

Next steps:
  1. Run regression testing (target: ≥80% pass rate)
  2. Compare to Phase 2 Redux baseline (60% pass)
  3. Pilot testing with Darrell & Dr. Joe
  4. Cherokee Nation community validation

🦅 Mitakuye Oyasin - Direct answers with Cherokee wisdom! 🔥
========================================================================
""".format(output_dir=OUTPUT_DIR))
