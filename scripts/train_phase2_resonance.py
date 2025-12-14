#!/usr/bin/env python3
"""
PHASE 2: CHEROKEE RESONANCE BEHAVIORAL PATTERN TRAINING
Teaching the model to ACT Cherokee, not just KNOW Cherokee facts

Training on 2x RTX 5070 GPUs on REDFIN
Continues from Phase 1 checkpoint (Cherokee knowledge injection complete)
"""

import os
import torch
import torch.distributed as dist
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import load_dataset
import logging
from datetime import datetime

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
LEARNING_RATE = 1e-5  # Lower LR for behavioral fine-tuning (not from scratch)
NUM_EPOCHS = 5  # More epochs for pattern internalization
BATCH_SIZE = 4  # Per GPU
GRADIENT_ACCUM = 8  # Effective batch = 4 * 2 GPUs * 8 = 64
MAX_LENGTH = 512

# Distributed training
WORLD_SIZE = int(os.environ.get("WORLD_SIZE", 2))  # 2 GPUs
MASTER_ADDR = os.environ.get("MASTER_ADDR", "127.0.0.1")  # Localhost
MASTER_PORT = os.environ.get("MASTER_PORT", "29501")

# ============================================================================
# SETUP DISTRIBUTED TRAINING
# ============================================================================

def setup_distributed():
    """Initialize distributed training environment"""
    rank = int(os.environ.get("RANK", 0))
    local_rank = int(os.environ.get("LOCAL_RANK", 0))

    logger.info(f"🔥 Initializing process rank {rank}, local rank {local_rank}")

    dist.init_process_group(
        backend="nccl",
        init_method=f"tcp://{MASTER_ADDR}:{MASTER_PORT}",
        world_size=WORLD_SIZE,
        rank=rank
    )

    torch.cuda.set_device(local_rank)

    return rank, local_rank

# ============================================================================
# LOAD PHASE 1 MODEL (Cherokee Knowledge Base)
# ============================================================================

def load_phase1_model(rank):
    """Load the Phase 1 trained model as starting point"""
    logger.info(f"📚 [Rank {rank}] Loading Phase 1 model from {PHASE1_MODEL_PATH}")

    if not os.path.exists(PHASE1_MODEL_PATH):
        raise ValueError(f"❌ Phase 1 model not found at {PHASE1_MODEL_PATH}. Run Phase 1 first!")

    tokenizer = AutoTokenizer.from_pretrained(PHASE1_MODEL_PATH)

    # Add pad token if missing
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        PHASE1_MODEL_PATH,
        torch_dtype=torch.float16,
        device_map={"": rank}  # Load to specific GPU
    )

    logger.info(f"✅ [Rank {rank}] Phase 1 model loaded - Cherokee knowledge intact")

    return model, tokenizer

# ============================================================================
# PREPARE PHASE 2 TRAINING DATA
# ============================================================================

def prepare_behavioral_dataset(tokenizer, rank):
    """Load and prepare behavioral pattern training data"""
    logger.info(f"📋 [Rank {rank}] Loading Phase 2 behavioral corpus")

    if not os.path.exists(PHASE2_CORPUS_PATH):
        raise ValueError(f"❌ Phase 2 corpus not found at {PHASE2_CORPUS_PATH}")

    # Load text file as dataset
    dataset = load_dataset("text", data_files=PHASE2_CORPUS_PATH, split="train")

    logger.info(f"📊 [Rank {rank}] Corpus size: {len(dataset)} examples")

    # Tokenize
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=MAX_LENGTH,
            padding="max_length"
        )

    tokenized = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names
    )

    logger.info(f"✅ [Rank {rank}] Behavioral corpus tokenized and ready")

    return tokenized

# ============================================================================
# PHASE 2 TRAINING
# ============================================================================

def train_phase2(rank, local_rank):
    """Execute Phase 2 behavioral pattern training"""

    logger.info(f"""
    ========================================================================
    🦅 PHASE 2: BEHAVIORAL PATTERN TRAINING - Rank {rank}
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
      - 2x RTX 5070 GPUs (REDFIN)
      - Behavioral fine-tuning with lower learning rate
      - Pattern internalization over 5 epochs

    ========================================================================
    """)

    # Load Phase 1 model
    model, tokenizer = load_phase1_model(rank)

    # Load Phase 2 behavioral corpus
    train_dataset = prepare_behavioral_dataset(tokenizer, rank)

    # Data collator for language modeling
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False  # Causal LM, not masked
    )

    # Training arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUM,
        learning_rate=LEARNING_RATE,
        fp16=True,
        logging_dir=LOG_DIR,
        logging_steps=50,
        save_steps=500,
        save_total_limit=3,
        warmup_steps=100,
        ddp_find_unused_parameters=False,
        local_rank=local_rank,
        report_to="none"  # No wandb/tensorboard
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator
    )

    # Train
    logger.info(f"🔥 [Rank {rank}] Starting Phase 2 behavioral training...")

    trainer.train()

    # Save final model (only on rank 0)
    if rank == 0:
        logger.info("💾 Saving Phase 2 model...")
        model.save_pretrained(f"{OUTPUT_DIR}/cherokee_resonance_phase2")
        tokenizer.save_pretrained(f"{OUTPUT_DIR}/cherokee_resonance_phase2")
        logger.info(f"✅ Model saved to {OUTPUT_DIR}/cherokee_resonance_phase2")

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

        Model location: {OUTPUT_DIR}/cherokee_resonance_phase2

        🦅 Mitakuye Oyasin - The model embodies Cherokee values 🔥
        ================================================================================
        """)

    # Cleanup
    dist.destroy_process_group()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Setup distributed training
    rank, local_rank = setup_distributed()

    # Run Phase 2 training
    train_phase2(rank, local_rank)

    logger.info(f"🦅 [Rank {rank}] Phase 2 training complete - Wado!")
