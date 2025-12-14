#!/usr/bin/env python3
"""
PHASE 2.3: WEIGHTED LORA TRAINING - SYNTHESIS JR'S BAYESIAN PRIOR FIX
Fix the Bayesian prior by weighting factual scenarios 4x during training

Hypothesis: The model learned "80% of questions want guidance" because 80% of
training data was behavioral. By weighting factual scenarios 4x, we create an
effective 50/50 balance WITHOUT generating new data.

Math:
- 824 behavioral scenarios × 1.0 weight = 824 effective
- 200 factual scenarios × 4.0 weight = 800 effective
- Result: ~50/50 effective distribution!
"""

import os
import torch
import numpy as np
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

# Paths
PHASE1_MODEL_PATH = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"
PHASE2_REDUX_PATH = "/ganuda/phase2_redux_reformatted.txt"
PHASE21_PATH = "/ganuda/phase21_reformatted.txt"
OUTPUT_DIR = "/ganuda/cherokee_resonance_training/phase23_weighted_lora"
LOG_DIR = "/ganuda/cherokee_resonance_training/logs"

# LoRA hyperparameters (same as before)
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.1
TARGET_MODULES = ["q_proj", "v_proj", "k_proj", "o_proj"]

# Training hyperparameters
LEARNING_RATE = 5e-5
NUM_EPOCHS = 3
BATCH_SIZE = 2
GRADIENT_ACCUM = 16
MAX_LENGTH = 384

# WEIGHTED SAMPLING PARAMETERS
BEHAVIORAL_WEIGHT = 1.0  # Phase 2 Redux scenarios
FACTUAL_WEIGHT = 4.0     # Phase 2.1 factual scenarios (4x oversampling!)

logger.info("""
========================================================================
🦅 PHASE 2.3: WEIGHTED LORA TRAINING - BAYESIAN PRIOR FIX
========================================================================

Synthesis Jr's Hypothesis:
  "The model learned a Bayesian prior: 80% behavioral → 80% guidance responses"

Solution:
  Weight factual scenarios 4x to create effective 50/50 balance

Math:
  - 424 behavioral × 1.0 = 424 effective
  - 200 factual × 4.0 = 800 effective
  - Effective ratio: 424/1224 = 35% behavioral, 800/1224 = 65% factual

Expected Result:
  Model learns new Bayesian prior: "Most questions want direct answers"
  Target: ≥75% regression pass rate (vs 40% in Phase 2.1/2.2)

========================================================================
""")

# Load Phase 1 model
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

# Load datasets separately to apply different weights
logger.info("📖 Loading Phase 2 Redux (behavioral) corpus...")
behavioral_dataset = load_dataset('text', data_files={'train': PHASE2_REDUX_PATH})

logger.info("📖 Loading Phase 2.1 (factual) corpus...")
factual_dataset = load_dataset('text', data_files={'train': PHASE21_PATH})

def tokenize_function(examples):
    return tokenizer(
        examples['text'],
        truncation=True,
        max_length=MAX_LENGTH,
        padding='max_length'
    )

# Tokenize both datasets
behavioral_tokenized = behavioral_dataset['train'].map(
    tokenize_function,
    batched=True,
    remove_columns=['text']
)

factual_tokenized = factual_dataset['train'].map(
    tokenize_function,
    batched=True,
    remove_columns=['text']
)

logger.info(f"✅ Behavioral examples: {len(behavioral_tokenized)}")
logger.info(f"✅ Factual examples: {len(factual_tokenized)}")

# Create weighted sampling
# Repeat factual examples 4x to create 4x weighting
logger.info("⚖️  Applying weighted sampling (factual 4x oversampling)...")

# Simple approach: Concatenate datasets with factual repeated 4x
from datasets import concatenate_datasets

weighted_dataset = concatenate_datasets([
    behavioral_tokenized,
    factual_tokenized,
    factual_tokenized,  # 2x
    factual_tokenized,  # 3x
    factual_tokenized,  # 4x
])

logger.info(f"✅ Weighted dataset size: {len(weighted_dataset)} examples")
logger.info(f"   Effective ratio: 424 behavioral / 800 factual (35% behavioral)")

# Shuffle for good measure
weighted_dataset = weighted_dataset.shuffle(seed=42)

# Training configuration
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
    train_dataset=weighted_dataset,
    data_collator=data_collator,
)

# Train!
logger.info("""
========================================================================
🔥 STARTING PHASE 2.3 WEIGHTED LORA TRAINING
========================================================================
Training with 4x factual oversampling to fix Bayesian prior
Expected duration: ~17 minutes
========================================================================
""")

trainer.train()

# Save model
logger.info(f"💾 Saving Phase 2.3 weighted LoRA adapters to {OUTPUT_DIR}")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

logger.info("""
========================================================================
✅ PHASE 2.3 WEIGHTED TRAINING COMPLETE
========================================================================

LoRA adapters saved: {output_dir}

Hypothesis Test:
  Did weighting factual scenarios 4x fix the Bayesian prior?

Next step:
  Run regression testing to see if pass rate improved:
  - Phase 2 Redux: 60% (baseline)
  - Phase 2.1/2.2: 40% (failed)
  - Phase 2.3 target: ≥75% (weighted prior)

🦅 Synthesis Jr's elegant solution tested! 🔥
========================================================================
""".format(output_dir=OUTPUT_DIR))
