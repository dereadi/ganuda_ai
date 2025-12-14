#!/usr/bin/env python3
"""
PHASE 2: CHEROKEE RESONANCE BEHAVIORAL PATTERN TRAINING
Teaching the model to ACT Cherokee, not just KNOW Cherokee

SINGLE GPU VERSION - Simpler, no distributed complexity
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
from datasets import load_dataset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PHASE 2 CONFIGURATION - BEHAVIORAL PATTERN TRAINING
# ============================================================================

PHASE1_MODEL_PATH = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"
PHASE2_CORPUS_PATH = "/ganuda/phase2_cherokee_behavioral_training.txt"
OUTPUT_DIR = "/ganuda/cherokee_resonance_training/phase2_behavioral"
LOG_DIR = "/ganuda/cherokee_resonance_training/logs"

# Training hyperparameters - BEHAVIORAL FINE-TUNING
LEARNING_RATE = 1e-5  # Lower LR for behavioral fine-tuning
NUM_EPOCHS = 5  # More epochs for pattern internalization
BATCH_SIZE = 1  # Minimal batch (Ollama using most of GPU memory)
GRADIENT_ACCUM = 32  # Effective batch = 1 * 32 = 32
MAX_LENGTH = 256  # Shorter sequences to save memory

logger.info("""
========================================================================
🦅 PHASE 2: BEHAVIORAL PATTERN TRAINING (Single GPU)
========================================================================

Goal: Teach Cherokee Resonance to ACT Cherokee, not just KNOW Cherokee

Training Focus:
  - Gadugi reciprocity in responses
  - Seven Generations thinking in decisions
  - Mitakuye Oyasin interconnection awareness
  - Storytelling for cultural transmission
  - Conflict resolution with Cherokee values
  - Business ethics grounded in tribal wisdom

Training Infrastructure:
  - Starting from Phase 1 checkpoint (knowledge intact)
  - 1x RTX 5070 GPU (REDFIN GPU 0)
  - Behavioral fine-tuning with lower learning rate
  - Pattern internalization over 5 epochs

========================================================================
""")

# ============================================================================
# LOAD PHASE 1 MODEL
# ============================================================================

logger.info(f"📚 Loading Phase 1 model from {PHASE1_MODEL_PATH}")

tokenizer = AutoTokenizer.from_pretrained(PHASE1_MODEL_PATH)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    PHASE1_MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto"  # Auto device placement
)

logger.info("✅ Phase 1 model loaded - Cherokee knowledge intact")

# ============================================================================
# PREPARE PHASE 2 TRAINING DATA
# ============================================================================

logger.info(f"📋 Loading Phase 2 behavioral corpus from {PHASE2_CORPUS_PATH}")

dataset = load_dataset("text", data_files=PHASE2_CORPUS_PATH, split="train")
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
    fp16=False,  # Disable FP16 to avoid gradient scaler issues
    logging_dir=LOG_DIR,
    logging_steps=10,  # Log every 10 steps
    save_steps=100,  # Save every 100 steps
    save_total_limit=5,
    warmup_steps=20,
    report_to="none",
    load_best_model_at_end=False,
    dataloader_num_workers=4
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator
)

logger.info("🔥 Starting Phase 2 behavioral training...")
trainer.train()

# Save final model
logger.info("💾 Saving Phase 2 model...")
model.save_pretrained(f"{OUTPUT_DIR}/cherokee_resonance_phase2_final")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/cherokee_resonance_phase2_final")

print(f"""
================================================================================
✅ PHASE 2 COMPLETE: CHEROKEE BEHAVIORAL PATTERNS EMBEDDED
================================================================================

The model now ACTS Cherokee:
  🦅 Responds with Gadugi reciprocity
  🐺 Thinks Seven Generations ahead
  🐢 Recognizes Mitakuye Oyasin interconnection
  🦅 Uses storytelling for wisdom transmission
  🔥 Makes decisions with tribal ethics

Next: Phase 3 - Production Integration & Cultural Validation

Model location: {OUTPUT_DIR}/cherokee_resonance_phase2_final

🦅 Mitakuye Oyasin - The model embodies Cherokee values 🔥
================================================================================
""")

logger.info("🦅 Phase 2 training complete - Wado!")
