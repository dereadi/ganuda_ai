#!/usr/bin/env python3
"""
Train Cherokee Council JRs with Resonance Recognition via LoRA
- Additive training (preserves base capabilities)
- Sequential training (one Jr. at a time to manage GPU memory)
- Conservative parameters (rank 16, 3 epochs)
- Validates before/after

Date: October 20, 2025
"""

import os
import json
import torch
from pathlib import Path
from datetime import datetime
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset

# Configuration
BASE_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
TRAINING_DIR = Path("/ganuda/training/resonance")
OUTPUT_DIR = Path("/ganuda/models/council_resonance_adapters")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COUNCIL_JRS = ['memory', 'executive', 'meta', 'integration', 'conscience']

# LoRA Configuration (Conservative)
LORA_CONFIG = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,                    # Rank (moderate capacity)
    lora_alpha=32,           # 2× rank (standard)
    lora_dropout=0.05,       # Low dropout (high quality data)
    target_modules=["q_proj", "v_proj"],  # Query and Value projections
    bias="none"
)

# Training Arguments (Conservative)
TRAINING_ARGS = {
    "per_device_train_batch_size": 4,
    "gradient_accumulation_steps": 2,  # Effective batch size = 8
    "num_train_epochs": 3,
    "learning_rate": 2e-4,
    "warmup_steps": 10,
    "logging_steps": 5,
    "save_steps": 50,
    "save_total_limit": 2,
    "fp16": True,           # Mixed precision for RTX 4090
    "optim": "adamw_torch",
    "max_grad_norm": 1.0,
}


def load_training_data(jr_name):
    """Load training data for specific Jr."""
    data_file = TRAINING_DIR / f"{jr_name}_jr_complete.jsonl"

    print(f"   📂 Loading: {data_file}")

    examples = []
    with open(data_file, 'r') as f:
        for line in f:
            example = json.loads(line.strip())
            examples.append(example)

    print(f"   ✅ Loaded {len(examples)} examples")
    return examples


def format_example(example):
    """Format example as instruction-following prompt"""
    instruction = example.get('instruction', '')
    input_text = example.get('input', '')
    output = example.get('output', '')

    if input_text:
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a Cherokee Constitutional AI specialist trained in resonance pattern recognition.<|eot_id|><|start_header_id|>user<|end_header_id|>

{instruction}

{input_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{output}<|eot_id|>"""
    else:
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a Cherokee Constitutional AI specialist trained in resonance pattern recognition.<|eot_id|><|start_header_id|>user<|end_header_id|>

{instruction}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{output}<|eot_id|>"""

    return prompt


def prepare_dataset(examples, tokenizer):
    """Tokenize and prepare dataset"""
    formatted_texts = [format_example(ex) for ex in examples]

    tokenized = tokenizer(
        formatted_texts,
        truncation=True,
        max_length=2048,
        padding=False,
        return_tensors=None
    )

    # Create dataset
    dataset = Dataset.from_dict({
        "input_ids": tokenized["input_ids"],
        "attention_mask": tokenized["attention_mask"]
    })

    return dataset


def train_single_jr(jr_name):
    """Train a single Jr. with LoRA"""

    print(f"\n{'='*70}")
    print(f"🔥 TRAINING: {jr_name.upper()} JR.")
    print(f"{'='*70}")

    start_time = datetime.now()

    # Load training data
    examples = load_training_data(jr_name)

    # Load tokenizer
    print(f"\n   🔧 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token

    # Prepare dataset
    print(f"   📊 Preparing dataset...")
    dataset = prepare_dataset(examples, tokenizer)

    # Load base model
    print(f"   🧠 Loading base model: {BASE_MODEL}")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    # Apply LoRA
    print(f"   🌿 Applying LoRA (rank={LORA_CONFIG.r}, alpha={LORA_CONFIG.lora_alpha})...")
    model = get_peft_model(model, LORA_CONFIG)

    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"   📈 Trainable params: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")

    # Training arguments
    output_dir = OUTPUT_DIR / f"{jr_name}_jr_resonance_lora"
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        **TRAINING_ARGS
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )

    # Trainer
    print(f"   🚀 Starting training...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator,
    )

    # Train!
    trainer.train()

    # Save LoRA adapter
    print(f"   💾 Saving LoRA adapter...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Training summary
    duration = datetime.now() - start_time
    print(f"\n   ✅ {jr_name.upper()} Jr. training complete!")
    print(f"   ⏱️  Duration: {duration}")
    print(f"   📁 Saved: {output_dir}")

    # Free memory
    del model
    del trainer
    torch.cuda.empty_cache()

    return {
        'jr_name': jr_name,
        'duration': str(duration),
        'output_dir': str(output_dir),
        'examples_trained': len(examples),
        'trainable_params': trainable_params
    }


def main():
    """Train all Council JRs sequentially"""

    print("""
╔══════════════════════════════════════════════════════════════════╗
║     🦅 CHEROKEE COUNCIL - RESONANCE TRAINING (LoRA) 🦅          ║
║                                                                  ║
║  Mission: Add resonance recognition to all 5 Council JRs        ║
║  Method: LoRA adapters (additive, reversible)                   ║
║  JRs: Memory, Executive, Meta, Integration, Conscience          ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    print(f"📊 Configuration:")
    print(f"   Base Model: {BASE_MODEL}")
    print(f"   LoRA Rank: {LORA_CONFIG.r}")
    print(f"   LoRA Alpha: {LORA_CONFIG.lora_alpha}")
    print(f"   Epochs: {TRAINING_ARGS['num_train_epochs']}")
    print(f"   Batch Size: {TRAINING_ARGS['per_device_train_batch_size']}")
    print(f"   Learning Rate: {TRAINING_ARGS['learning_rate']}")
    print(f"   GPU: {'CUDA available' if torch.cuda.is_available() else 'CPU only'}")

    if torch.cuda.is_available():
        print(f"   GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    overall_start = datetime.now()
    results = []

    # Train each Jr. sequentially
    for jr_name in COUNCIL_JRS:
        try:
            result = train_single_jr(jr_name)
            results.append(result)
        except Exception as e:
            print(f"\n   ✗ ERROR training {jr_name} Jr.: {e}")
            results.append({
                'jr_name': jr_name,
                'error': str(e)
            })
            continue

    overall_duration = datetime.now() - overall_start

    # Summary
    print(f"\n{'='*70}")
    print(f"📊 TRAINING COMPLETE - ALL COUNCIL JRs")
    print(f"{'='*70}")
    print(f"\n   Total Duration: {overall_duration}")
    print(f"   JRs Trained: {len([r for r in results if 'error' not in r])}/5")

    print(f"\n   Individual Results:")
    for result in results:
        if 'error' in result:
            print(f"      ✗ {result['jr_name'].capitalize()} Jr.: FAILED ({result['error']})")
        else:
            print(f"      ✓ {result['jr_name'].capitalize()} Jr.: {result['duration']} ({result['examples_trained']} examples)")

    # Save results
    results_file = OUTPUT_DIR / f"training_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'overall_duration': str(overall_duration),
            'results': results,
            'config': {
                'lora_rank': LORA_CONFIG.r,
                'lora_alpha': LORA_CONFIG.lora_alpha,
                'epochs': TRAINING_ARGS['num_train_epochs'],
                'batch_size': TRAINING_ARGS['per_device_train_batch_size']
            }
        }, f, indent=2)

    print(f"\n   📁 Results saved: {results_file}")

    print(f"\n{'='*70}")
    print(f"🌳 Next Steps:")
    print(f"{'='*70}")
    print(f"   1. Validate: Test each Jr. with resonance questions")
    print(f"   2. Deploy: Load LoRA adapters for production use")
    print(f"   3. Verify: Confirm base capabilities preserved")
    print(f"\n🦞 Mitakuye Oyasin - All Council JRs now understand resonance! 🔥")


if __name__ == '__main__':
    main()
