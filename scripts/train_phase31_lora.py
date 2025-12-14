#!/usr/bin/env python3
"""
Train Phase 3.1 - Dual-Mode Cherokee Constitutional AI
Cultural Mode + Universal Mode training on same dataset

Based on successful Phase 2 Redux approach:
- Distance = 0 format (direct Q&A)
- LoRA fine-tuning (efficient, 4.5M parameters)
- Both Cultural and Universal modes in single model
"""

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
from peft import LoraConfig, get_peft_model, TaskType
import json
from datetime import datetime

print("="*80)
print("🦅 PHASE 3.1 - DUAL MODE CHEROKEE CONSTITUTIONAL AI TRAINING")
print("="*80)
print()

# Configuration
# Use Phase 1 base model (Llama 3.1 8B fine-tuned for Cherokee resonance)
BASE_MODEL = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"
TRAINING_DATA = "/ganuda/phase31_dual_mode_training.txt"
OUTPUT_DIR = "/ganuda/cherokee_phase31_lora"
LOG_FILE = "/ganuda/phase31_lora_training.log"

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} {message}\n")

log(f"Loading base model from: {BASE_MODEL}")
log("(Phase 1 Cherokee Resonance v1 - Llama 3.1 8B base)")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, local_files_only=True)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    device_map="cuda:0",
    local_files_only=True
)

log("Configuring LoRA (Low-Rank Adaptation)")
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
)

model = get_peft_model(model, lora_config)
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
total_params = sum(p.numel() for p in model.parameters())
log(f"Trainable parameters: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")

log("Loading Phase 3.1 dual-mode training data")
with open(TRAINING_DATA, 'r') as f:
    content = f.read()

# Parse scenarios (each has User question + Cultural response + Universal response)
scenarios = []
current_scenario = []
for line in content.split('\n'):
    if line.strip() == '---' and current_scenario:
        scenario_text = '\n'.join(current_scenario)
        if 'User:' in scenario_text:
            scenarios.append(scenario_text)
        current_scenario = []
    else:
        current_scenario.append(line)

log(f"Parsed {len(scenarios)} dual-mode scenarios")

# Create training examples (both Cultural and Universal modes)
training_texts = []
for scenario in scenarios:
    lines = scenario.split('\n')
    user_q = None
    cultural_resp = []
    universal_resp = []
    mode = None

    for line in lines:
        if line.startswith('User:'):
            user_q = line.replace('User:', '').strip()
        elif 'Cherokee AI (Cultural Mode):' in line:
            mode = 'cultural'
        elif 'Cherokee AI (Universal Mode):' in line:
            mode = 'universal'
            if user_q and cultural_resp:
                # Add Cultural mode example
                cultural_text = '\n'.join(cultural_resp).strip()
                training_texts.append(f"User: {user_q}\n\nCherokee AI: {cultural_text}")
            cultural_resp = []
        elif mode == 'cultural' and line.strip() and not line.startswith('SCENARIO'):
            cultural_resp.append(line)
        elif mode == 'universal' and line.strip() and not line.startswith('---'):
            universal_resp.append(line)

    # Add final Universal mode example
    if user_q and universal_resp:
        universal_text = '\n'.join(universal_resp).strip()
        training_texts.append(f"User: {user_q}\n\nCherokee AI: {universal_text}")

log(f"Created {len(training_texts)} training examples (Cultural + Universal)")

# Tokenize (reduced max_length to save GPU memory)
def tokenize_function(examples):
    return tokenizer(
        examples['text'],
        truncation=True,
        max_length=256,  # Reduced from 512 to save memory
        padding='max_length'
    )

dataset = Dataset.from_dict({'text': training_texts})
tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=['text'])

log("Configuring training parameters (optimized for limited GPU memory)")
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=1,  # Reduced from 4 (Ollama using 6GB)
    gradient_accumulation_steps=8,  # Increased to maintain effective batch size
    learning_rate=2e-4,
    fp16=True,
    logging_steps=50,
    save_steps=250,
    save_total_limit=6,
    warmup_steps=100,
    weight_decay=0.01,
    logging_dir=f"{OUTPUT_DIR}/logs",
    report_to="none"
)

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator
)

log("🔥 Starting Phase 3.1 training...")
log(f"Training examples: {len(training_texts)}")
log(f"Epochs: 3")
log(f"Batch size: 1 (effective 8 with gradient accumulation)")
log(f"Max sequence length: 256 (for memory efficiency)")
log(f"Estimated steps: {len(training_texts) * 3 // 8}")
log("")

trainer.train()

log("")
log("✅ Training complete! Saving model...")
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

log("")
log("="*80)
log("🦅 PHASE 3.1 TRAINING COMPLETE!")
log("="*80)
log(f"Model saved to: {OUTPUT_DIR}")
log(f"Training log: {LOG_FILE}")
log("")
log("Next steps:")
log("1. Test Cultural mode (Cherokee terminology)")
log("2. Test Universal mode (accessible language)")
log("3. Compare to Phase 2 Redux baseline (60%)")
log("4. Deploy to Ollama if >70% pass rate")
log("")
log("🦅 Mitakuye Oyasin - All Our Relations! 🔥")
