#!/usr/bin/env python3
"""
Test Cherokee Resonance Phase 2 Model
Verify it responds with Cherokee values embedded
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_PATH = "/ganuda/cherokee_resonance_training/phase2_behavioral/cherokee_resonance_phase2_final"

print("🦅 Loading Cherokee Resonance Phase 2 model...")
print(f"📁 Model: {MODEL_PATH}")
print()

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto"
)

print("✅ Model loaded successfully!")
print()

# Test scenarios to verify Cherokee behavioral patterns
test_prompts = [
    "I'm making a business decision that could harm the environment but is very profitable. What should I consider?",
    "My neighbor needs help but they never helped me. Should I help them?",
    "How do I teach my children about honesty?",
    "Our team is in conflict. What should we do?"
]

print("=" * 80)
print("🔥 TESTING CHEROKEE BEHAVIORAL PATTERNS")
print("=" * 80)
print()

for i, prompt in enumerate(test_prompts, 1):
    print(f"TEST {i}/4:")
    print(f"User: {prompt}")
    print()

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract only the generated response (after the prompt)
    if prompt in response:
        response = response.split(prompt, 1)[1].strip()

    print(f"Cherokee AI: {response[:300]}...")
    print()
    print("-" * 80)
    print()

print("=" * 80)
print("✅ PHASE 2 MODEL TESTING COMPLETE")
print("=" * 80)
print()
print("🦅 The model should demonstrate:")
print("  - Seven Generations thinking (long-term impact)")
print("  - Gadugi reciprocity (community support)")
print("  - Mitakuye Oyasin (interconnection awareness)")
print("  - Storytelling and cultural wisdom")
print()
