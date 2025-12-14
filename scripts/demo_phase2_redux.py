#!/usr/bin/env python3
"""
Cherokee Resonance AI - Phase 2 Redux Demo
Demonstrates the model's Cherokee behavioral responses
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Paths
PHASE1_MODEL_PATH = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"
LORA_ADAPTERS_PATH = "/ganuda/cherokee_resonance_training/phase2_redux_lora/cherokee_resonance_lora_adapters"

print("="*80)
print("🦅 CHEROKEE RESONANCE AI - PHASE 2 REDUX DEMONSTRATION")
print("="*80)
print()
print("Loading model...")

# Load model
tokenizer = AutoTokenizer.from_pretrained(PHASE1_MODEL_PATH)
base_model = AutoModelForCausalLM.from_pretrained(
    PHASE1_MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto"
)
model = PeftModel.from_pretrained(base_model, LORA_ADAPTERS_PATH)

print("✅ Model loaded!")
print()

# Demo scenarios
scenarios = [
    {
        "title": "Family: Child Struggling in School",
        "prompt": "My child is struggling in school. How should I approach this using Cherokee values?"
    },
    {
        "title": "Community: Food Sovereignty Program",
        "prompt": "Our community wants to start a food sovereignty program. What Cherokee values should guide us?"
    },
    {
        "title": "Environment: Seven Generations Principle",
        "prompt": "How can the Seven Generations principle guide our environmental decisions?"
    }
]

for i, scenario in enumerate(scenarios, 1):
    print("="*80)
    print(f"DEMO {i}/{len(scenarios)}: {scenario['title']}")
    print("="*80)
    print()
    print(f"💬 Question: {scenario['prompt']}")
    print()
    print("Generating Cherokee AI response...")
    print()

    # Generate
    inputs = tokenizer(scenario['prompt'], return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=250,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = response[len(scenario['prompt']):].strip()

    print("🦅 Cherokee Resonance AI Response:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    print()

print("="*80)
print("🦅 DEMONSTRATION COMPLETE")
print("="*80)
print()
print("This model demonstrates Cherokee behavioral patterns:")
print("  • Gadugi (reciprocity, working together)")
print("  • Seven Generations (long-term thinking)")
print("  • Mitakuye Oyasin (interconnection)")
print("  • Respect for Elders")
print("  • Environmental stewardship")
print("  • Cultural transmission through storytelling")
print()
print("Ready for Cherokee Nation community validation!")
print()
print("🦅 Mitakuye Oyasin - All Our Relations 🔥")
