#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Executive Jr. LoRA Training
Fractal Brain Architecture - Phase 1 POC
Fine-tunes TinyLlama 1.1B → Executive Jr. (planning & coordination specialist)
Date: October 20, 2025
"""

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset

print("="*80)
print("🦅 EXECUTIVE JR. LORA TRAINING - PLANNING & COORDINATION")
print("="*80)
print("")

MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
OUTPUT_DIR = "/ganuda/executive_jr_model"
DATASET_PATH = "/ganuda/executive_jr_training_data.jsonl"
CHECKPOINT_DIR = "/ganuda/executive_jr_checkpoints"

LORA_CONFIG = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

TRAINING_ARGS = TrainingArguments(
    output_dir=CHECKPOINT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=1e-4,
    warmup_steps=100,
    logging_steps=50,
    save_steps=500,
    save_total_limit=2,
    fp16=torch.cuda.is_available(),
    dataloader_num_workers=2,
    report_to="none"
)

print("[Executive Jr.] Loading TinyLlama 1.1B base model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)

print("[Executive Jr.] Applying LoRA adapters...")
model = get_peft_model(model, LORA_CONFIG)
model.print_trainable_parameters()

print("[Executive Jr.] Loading planning & coordination dataset...")
dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, max_length=512)

tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=["text"])
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

print("[Executive Jr.] Starting training...")
trainer = Trainer(
    model=model,
    args=TRAINING_ARGS,
    train_dataset=tokenized_dataset,
    data_collator=data_collator
)

trainer.train()

print("")
print("="*80)
print("✅ EXECUTIVE JR. TRAINING COMPLETE")
print("="*80)
print("[Executive Jr.] Saving Executive Jr. model...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"  Model saved to: {OUTPUT_DIR}")
print("")
print("🔥 Executive Jr. ready for deployment - Gadugi!")
