#!/usr/bin/env python3
"""
RL2F Phase 2: QLoRA Fine-Tuning on Didactic Dialogues

Fine-tunes Qwen2.5-72B-Instruct-AWQ using QLoRA (4-bit quantized LoRA).
Trains on teacher-student dialogues from Phase 1.

Usage:
    python3 qlora_finetune.py --prepare     # Export dialogues to training format
    python3 qlora_finetune.py --train       # Run QLoRA training
    python3 qlora_finetune.py --evaluate    # Run regression benchmark after training
    python3 qlora_finetune.py --dry-run     # Show training config without running

Prerequisites:
    pip install peft bitsandbytes transformers datasets accelerate

For Seven Generations
"""

import argparse
import json
import os
import sys
import time
import psycopg2
import psycopg2.extras
from datetime import datetime

DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", "")
}
OUTPUT_DIR = "/ganuda/models/qlora"
DATA_DIR = "/ganuda/data/rl2f"
MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct-AWQ"

# QLoRA config
QLORA_CONFIG = {
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "learning_rate": 2e-4,
    "num_epochs": 3,
    "batch_size": 1,
    "gradient_accumulation_steps": 16,
    "max_seq_length": 2048,
    "warmup_ratio": 0.03,
    "weight_decay": 0.01,
    "fp16": True,
    "gradient_checkpointing": True,
    "save_steps": 100,
    "logging_steps": 10,
}


def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)


def prepare_training_data(min_quality=0.5):
    """Export didactic dialogues to training format."""
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, original_question, dialogue, quality_score,
                   student_final_correct, teacher_answer_leakage,
                   ground_truth_recommendation
            FROM didactic_dialogues
            WHERE quality_score >= %s
              AND teacher_answer_leakage = false
              AND NOT included_in_training
            ORDER BY quality_score DESC
        """, (min_quality,))
        dialogues = cur.fetchall()

    print(f"[RL2F] Found {len(dialogues)} eligible dialogues (quality >= {min_quality})")

    if not dialogues:
        print("[RL2F] No dialogues available. Run didactic_dialogue_generator.py first.")
        conn.close()
        return 0

    # Convert to ChatML training format
    training_data = []
    for d in dialogues:
        turns = d["dialogue"]
        if isinstance(turns, str):
            turns = json.loads(turns)

        # Build conversation in ChatML format
        messages = []
        messages.append({
            "role": "system",
            "content": "You are a council specialist analyzing questions for the Cherokee AI Federation. Think step by step, consider security, efficiency, cultural values, and architecture."
        })

        for turn in turns:
            role = "assistant" if turn["role"] == "student" else "user"
            messages.append({"role": role, "content": turn["content"]})

        training_data.append({
            "id": d["id"],
            "messages": messages,
            "quality_score": float(d["quality_score"]),
            "ground_truth": d["ground_truth_recommendation"]
        })

    # Split train/eval (90/10)
    split_idx = int(len(training_data) * 0.9)
    train_data = training_data[:split_idx]
    eval_data = training_data[split_idx:]

    # Write JSONL files
    train_path = os.path.join(DATA_DIR, "train.jsonl")
    eval_path = os.path.join(DATA_DIR, "eval.jsonl")

    for path, data in [(train_path, train_data), (eval_path, eval_data)]:
        with open(path, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

    print(f"[RL2F] Training set: {len(train_data)} dialogues -> {train_path}")
    print(f"[RL2F] Eval set: {len(eval_data)} dialogues -> {eval_path}")

    # Mark as included in training
    dialogue_ids = [d["id"] for d in dialogues]
    batch_name = f"qlora-{datetime.now().strftime('%Y%m%d')}"
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE didactic_dialogues
            SET included_in_training = true, training_batch = %s
            WHERE id = ANY(%s)
        """, (batch_name, dialogue_ids))
    conn.commit()
    conn.close()

    return len(training_data)


def train(dry_run=False):
    """Run QLoRA fine-tuning."""
    train_path = os.path.join(DATA_DIR, "train.jsonl")
    eval_path = os.path.join(DATA_DIR, "eval.jsonl")

    if not os.path.exists(train_path):
        print("[RL2F] No training data. Run --prepare first.")
        return

    # Count training examples
    with open(train_path) as f:
        train_count = sum(1 for _ in f)
    print(f"[RL2F] Training examples: {train_count}")

    if train_count < 50:
        print(f"[RL2F] WARNING: Only {train_count} examples. Recommend >= 500 for stable training.")

    config = QLORA_CONFIG.copy()
    config["model_name"] = MODEL_NAME
    config["train_path"] = train_path
    config["eval_path"] = eval_path
    config["output_dir"] = os.path.join(OUTPUT_DIR, f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    print(f"\n[RL2F] QLoRA Configuration:")
    for k, v in config.items():
        print(f"  {k}: {v}")

    if dry_run:
        print("\n[RL2F] DRY RUN — training not started")
        return

    # Safety check: run canary probe first
    canary_path = "/ganuda/scripts/safety/canary_probe.py"
    if os.path.exists(canary_path):
        print("\n[RL2F] Running pre-training safety canary...")
        import subprocess
        result = subprocess.run(
            [sys.executable, canary_path, "--quick"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print("[RL2F] SAFETY CANARY FAILED — aborting training")
            print(result.stdout)
            return
        print("[RL2F] Safety canary passed")

    # Regression benchmark baseline
    benchmark_path = "/ganuda/scripts/rl2f/regression_benchmark.py"
    if os.path.exists(benchmark_path):
        print("\n[RL2F] Running pre-training regression baseline...")
        import subprocess
        subprocess.run(
            [sys.executable, benchmark_path, "--mode", "baseline"],
            timeout=600
        )

    os.makedirs(config["output_dir"], exist_ok=True)

    print(f"\n[RL2F] Starting QLoRA training...")
    print(f"  Output: {config['output_dir']}")
    print(f"  Estimated time: {train_count * 3 * 2 // 60} minutes (rough)")

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from datasets import load_dataset
        import torch

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model with 4-bit quantization
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )

        # Prepare for kbit training
        model = prepare_model_for_kbit_training(model)

        # LoRA config
        lora_config = LoraConfig(
            r=config["lora_r"],
            lora_alpha=config["lora_alpha"],
            lora_dropout=config["lora_dropout"],
            target_modules=config["target_modules"],
            bias="none",
            task_type="CAUSAL_LM"
        )

        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

        # Load dataset
        dataset = load_dataset("json", data_files={
            "train": train_path,
            "eval": eval_path
        })

        # Tokenize
        def tokenize(example):
            text = tokenizer.apply_chat_template(
                example["messages"],
                tokenize=False,
                add_generation_prompt=False
            )
            return tokenizer(
                text,
                truncation=True,
                max_length=config["max_seq_length"],
                padding="max_length"
            )

        tokenized = dataset.map(tokenize, batched=False, remove_columns=dataset["train"].column_names)

        # Training args
        training_args = TrainingArguments(
            output_dir=config["output_dir"],
            num_train_epochs=config["num_epochs"],
            per_device_train_batch_size=config["batch_size"],
            gradient_accumulation_steps=config["gradient_accumulation_steps"],
            learning_rate=config["learning_rate"],
            warmup_ratio=config["warmup_ratio"],
            weight_decay=config["weight_decay"],
            fp16=config["fp16"],
            gradient_checkpointing=config["gradient_checkpointing"],
            save_steps=config["save_steps"],
            logging_steps=config["logging_steps"],
            evaluation_strategy="steps",
            eval_steps=config["save_steps"],
            save_total_limit=3,
            report_to="none",
        )

        from transformers import Trainer

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized["train"],
            eval_dataset=tokenized["eval"],
        )

        trainer.train()

        # Save adapter
        adapter_path = os.path.join(config["output_dir"], "adapter")
        model.save_pretrained(adapter_path)
        tokenizer.save_pretrained(adapter_path)
        print(f"\n[RL2F] Adapter saved: {adapter_path}")

        # Post-training regression check
        if os.path.exists(benchmark_path):
            print("\n[RL2F] Running post-training regression benchmark...")
            subprocess.run(
                [sys.executable, benchmark_path, "--mode", "compare"],
                timeout=600
            )

        # Post-training safety canary
        if os.path.exists(canary_path):
            print("\n[RL2F] Running post-training safety canary...")
            result = subprocess.run(
                [sys.executable, canary_path],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                print("[RL2F] POST-TRAINING SAFETY CANARY FAILED")
                print("[RL2F] ADAPTER MAY HAVE DEGRADED SAFETY — DO NOT DEPLOY")
                print(result.stdout)

    except ImportError as e:
        print(f"[RL2F] Missing dependency: {e}")
        print("[RL2F] Install: pip install peft bitsandbytes transformers datasets accelerate")
    except Exception as e:
        print(f"[RL2F] Training error: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="RL2F Phase 2: QLoRA Fine-Tuning")
    parser.add_argument("--prepare", action="store_true", help="Export dialogues to training format")
    parser.add_argument("--train", action="store_true", help="Run QLoRA training")
    parser.add_argument("--evaluate", action="store_true", help="Run post-training evaluation")
    parser.add_argument("--dry-run", action="store_true", help="Show config without training")
    parser.add_argument("--min-quality", type=float, default=0.5, help="Min dialogue quality score")
    args = parser.parse_args()

    if args.prepare:
        count = prepare_training_data(min_quality=args.min_quality)
        print(f"[RL2F] Prepared {count} training examples")
    elif args.train or args.dry_run:
        train(dry_run=args.dry_run)
    elif args.evaluate:
        print("[RL2F] Running regression benchmark...")
        import subprocess
        subprocess.run([sys.executable, "/ganuda/scripts/rl2f/regression_benchmark.py", "--mode", "compare"])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()