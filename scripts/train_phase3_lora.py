#!/usr/bin/env python3
"""
PHASE 3: CHEROKEE CONSTITUTIONAL AI ULTIMATE TRAINING
Research-Backed LoRA Approach (CivitAI + FAL.ai insights)

Key Principles:
- Clean base model (Llama 3.1 8B Instruct)
- Single consistent format with trigger words
- 589 balanced scenarios (49.1% behavioral + 50.9% knowledge)
- 1000-step training target
- Checkpoint sampling every 200 steps
"""

import os
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import json
from datetime import datetime

# Paths
BASE_MODEL = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"  # Same as Phase 2 Redux
TRAINING_DATA = "/ganuda/phase3_final_corpus.txt"
OUTPUT_DIR = "/ganuda/cherokee_resonance_training/phase3_lora"
LOG_FILE = "/ganuda/phase3_lora_training.log"

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} {message}\n")

def parse_scenarios(file_path):
    """
    Cherokee Council JRs approved parser - Line-by-line state machine

    Handles mixed format corpus:
    - Format 1: **N** markers with mode headers per-scenario
    - Format 2: N. markers with mode headers per-category
    """
    log(f"📚 Parsing training data from {file_path}")

    scenarios = []

    # State machine for scenario accumulation
    current_mode = None  # 'behavioral' or 'knowledge'
    current_user = None
    current_ai = None
    current_principle = None

    behavioral_count = 0
    knowledge_count = 0

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Detect mode switches (category level headers)
            if "Cherokee Behavioral Guidance Mode:" in line:
                current_mode = "behavioral"
                continue
            elif "Cherokee Knowledge Mode:" in line:
                current_mode = "knowledge"
                continue

            # Detect scenario separators (flush current scenario if complete)
            is_separator = (
                line.startswith('---') or
                line.startswith('**') or
                (line and line[0].isdigit() and '.' in line[:3])  # Handles "1." through "999."
            )

            if is_separator:
                # Flush accumulated scenario
                if current_user and current_ai and current_mode:
                    scenarios.append({
                        'mode': current_mode,
                        'user': current_user,
                        'assistant': current_ai,
                        'principle': current_principle
                    })
                    if current_mode == "behavioral":
                        behavioral_count += 1
                    else:
                        knowledge_count += 1
                # Reset for next scenario
                current_user = None
                current_ai = None
                current_principle = None
                continue

            # Parse User question
            if line.startswith('User:') or line.startswith('User :'):
                current_user = line.split(':', 1)[1].strip().strip('"')
                continue

            # Parse Cherokee AI response
            if line.startswith('Cherokee AI:') or line.startswith('Cherokee AI Response:'):
                current_ai = line.split(':', 1)[1].strip().strip('"')
                continue

            # Parse principle
            if line.startswith('Embedded Principle:'):
                current_principle = line.split(':', 1)[1].strip()
                continue

    # Flush final scenario
    if current_user and current_ai and current_mode:
        scenarios.append({
            'mode': current_mode,
            'user': current_user,
            'assistant': current_ai,
            'principle': current_principle
        })
        if current_mode == "behavioral":
            behavioral_count += 1
        else:
            knowledge_count += 1

    log(f"✅ Parsed {len(scenarios)} scenarios")
    log(f"   - Behavioral: {behavioral_count}")
    log(f"   - Knowledge: {knowledge_count}")
    if len(scenarios) > 0:
        log(f"   - Balance: {behavioral_count/len(scenarios)*100:.1f}% behavioral")

    # Validation
    if len(scenarios) < 500:
        log(f"⚠️  WARNING: Expected ~589 scenarios, got {len(scenarios)}")
    elif len(scenarios) > 600:
        log(f"⚠️  WARNING: More scenarios than expected ({len(scenarios)} > 600)")

    return scenarios

def scenarios_to_dataset(scenarios, tokenizer):
    """Convert scenarios to tokenized dataset"""
    log("🔧 Converting scenarios to training dataset")

    texts = []
    for scenario in scenarios:
        # Format with Llama 3.1 Instruct template
        text = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>

{scenario['user']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{scenario['assistant']}<|eot_id|>"""
        texts.append(text)

    # Tokenize
    encodings = tokenizer(texts, truncation=True, padding=False, max_length=512)

    dataset = Dataset.from_dict({
        'input_ids': encodings['input_ids'],
        'attention_mask': encodings['attention_mask']
    })

    log(f"✅ Created dataset with {len(dataset)} examples")
    return dataset

def main():
    log("="*80)
    log("🦅 PHASE 3: CHEROKEE CONSTITUTIONAL AI ULTIMATE TRAINING")
    log("="*80)
    log("")
    log("Research-Backed Approach:")
    log("  - CivitAI: Avoid false positives, single format, quality sampling")
    log("  - FAL.ai: 1000-step sweet spot, checkpoint testing")
    log("  - Cherokee Jr. Wisdom: Slow is steady, steady is fast")
    log("")

    # Parse training data
    scenarios = parse_scenarios(TRAINING_DATA)

    # Load tokenizer
    log(f"🔧 Loading tokenizer: {BASE_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token

    # Create dataset
    dataset = scenarios_to_dataset(scenarios, tokenizer)

    # Load base model
    log(f"🔧 Loading base model: {BASE_MODEL}")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    # Prepare for LoRA
    model = prepare_model_for_kbit_training(model)

    # LoRA configuration (same as Phase 2 Redux for consistency)
    log("🔧 Configuring LoRA (rank=16, alpha=32)")
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, lora_config)

    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    log(f"📊 Trainable parameters: {trainable_params:,} ({trainable_params/total_params*100:.2f}%)")

    # Calculate training steps
    batch_size = 2
    gradient_accum = 16
    effective_batch_size = batch_size * gradient_accum

    # Target 1000 steps
    total_samples = len(dataset)
    steps_per_epoch = total_samples // effective_batch_size
    target_epochs = max(1, 1000 // steps_per_epoch)

    log(f"📊 Training configuration:")
    log(f"   - Total samples: {total_samples}")
    log(f"   - Batch size: {batch_size}")
    log(f"   - Gradient accumulation: {gradient_accum}")
    log(f"   - Effective batch size: {effective_batch_size}")
    log(f"   - Steps per epoch: {steps_per_epoch}")
    log(f"   - Target epochs: {target_epochs}")
    log(f"   - Total steps: ~{steps_per_epoch * target_epochs}")
    log("")

    # Training arguments with checkpointing
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=target_epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accum,
        learning_rate=5e-5,  # Same as Phase 2 Redux
        lr_scheduler_type="cosine",
        warmup_steps=50,
        logging_steps=10,
        save_strategy="steps",
        save_steps=200,  # Checkpoint every 200 steps
        save_total_limit=10,  # Keep all checkpoints (5 x 200 = 1000 steps)
        fp16=True,
        optim="adamw_torch",
        report_to="none",
        dataloader_num_workers=4,
        remove_unused_columns=False
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator
    )

    log("🚀 Starting Phase 3 training...")
    log("📊 Checkpoints will be saved every 200 steps")
    log("")

    # Train
    trainer.train()

    # Save final model
    log("")
    log("💾 Saving final model...")
    trainer.save_model()

    log("")
    log("="*80)
    log("✅ PHASE 3 TRAINING COMPLETE")
    log("="*80)
    log(f"Model saved to: {OUTPUT_DIR}")
    log("")
    log("Next steps:")
    log("1. Test checkpoints at steps 200, 400, 600, 800, 1000")
    log("2. Run regression tests on each checkpoint")
    log("3. Select best performing checkpoint")
    log("4. Target: 80%+ pass rate (4/5 or 5/5 tests)")
    log("")
    log("🦅 Mitakuye Oyasin - All Our Relations! 🔥")

if __name__ == "__main__":
    main()
