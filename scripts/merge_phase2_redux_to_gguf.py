#!/usr/bin/env python3
"""
Merge Phase 2 Redux LoRA adapters into base model and convert to GGUF for Ollama
Cherokee Constitutional AI - Production Deployment
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os
from datetime import datetime

# Paths
BASE_MODEL_PATH = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"
LORA_PATH = "/ganuda/cherokee_resonance_training/phase2_redux_lora/cherokee_resonance_lora_adapters"
MERGED_OUTPUT_PATH = "/ganuda/cherokee_merged_model"
LOG_FILE = "/ganuda/phase2_redux_merge.log"

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} {message}\n")

log("="*80)
log("🦅 CHEROKEE CONSTITUTIONAL AI - PHASE 2 REDUX MERGE TO GGUF")
log("="*80)
log("")
log("Cherokee Council Decision: Full model merge for production deployment")
log("Target: 60% validated performance in Ollama-compatible format")
log("")

# Step 1: Load base model
log("📚 Loading base model...")
log(f"   Path: {BASE_MODEL_PATH}")

try:
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_PATH,
        torch_dtype=torch.float16,
        device_map="cpu"  # Keep on CPU for merge
    )
    log("✅ Base model loaded successfully")
except Exception as e:
    log(f"❌ Error loading base model: {e}")
    exit(1)

# Step 2: Load tokenizer
log("")
log("📚 Loading tokenizer...")

try:
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH)
    log("✅ Tokenizer loaded successfully")
except Exception as e:
    log(f"❌ Error loading tokenizer: {e}")
    exit(1)

# Step 3: Load LoRA adapters
log("")
log("📚 Loading Phase 2 Redux LoRA adapters...")
log(f"   Path: {LORA_PATH}")

try:
    model = PeftModel.from_pretrained(base_model, LORA_PATH)
    log("✅ LoRA adapters loaded successfully")
except Exception as e:
    log(f"❌ Error loading LoRA adapters: {e}")
    exit(1)

# Step 4: Merge LoRA into base model
log("")
log("🔧 Merging LoRA adapters into base model...")
log("   This permanently integrates Cherokee wisdom into the model weights")

try:
    merged_model = model.merge_and_unload()
    log("✅ LoRA adapters merged successfully")

    # Calculate model size
    total_params = sum(p.numel() for p in merged_model.parameters())
    log(f"   Total parameters: {total_params:,} ({total_params/1e9:.2f}B)")
except Exception as e:
    log(f"❌ Error merging adapters: {e}")
    exit(1)

# Step 5: Save merged model
log("")
log("💾 Saving merged model...")
log(f"   Output path: {MERGED_OUTPUT_PATH}")

try:
    os.makedirs(MERGED_OUTPUT_PATH, exist_ok=True)
    merged_model.save_pretrained(MERGED_OUTPUT_PATH, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_OUTPUT_PATH)
    log("✅ Merged model saved successfully")
except Exception as e:
    log(f"❌ Error saving merged model: {e}")
    exit(1)

log("")
log("="*80)
log("✅ PHASE 2 REDUX MERGE COMPLETE")
log("="*80)
log(f"Merged model location: {MERGED_OUTPUT_PATH}")
log("")
log("Next steps:")
log("1. Convert merged model to GGUF format using llama.cpp")
log("2. Import GGUF model into Ollama")
log("3. Test Cherokee Constitutional AI responses")
log("4. Deploy for pilot testing with Darrell & Dr. Joe")
log("")
log("🦅 Mitakuye Oyasin - All Our Relations! 🔥")
