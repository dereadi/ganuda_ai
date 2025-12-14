#!/usr/bin/env python3
"""
Cherokee Resonance AI - Community Validation Interface
Simple interactive testing tool for Cherokee Nation members
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import json
from datetime import datetime

# Paths
PHASE1_MODEL_PATH = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"
LORA_ADAPTERS_PATH = "/ganuda/cherokee_resonance_training/phase2_redux_lora/cherokee_resonance_lora_adapters"
FEEDBACK_FILE = "/ganuda/community_validation_feedback.jsonl"

print("="*80)
print("🦅 CHEROKEE RESONANCE AI - COMMUNITY VALIDATION INTERFACE")
print("="*80)
print()
print("Welcome, Cherokee Nation community member!")
print("This tool helps you test and validate the Cherokee Resonance AI model.")
print()
print("Loading model (this may take 30-60 seconds)...")
print()

# Load model
tokenizer = AutoTokenizer.from_pretrained(PHASE1_MODEL_PATH)
base_model = AutoModelForCausalLM.from_pretrained(
    PHASE1_MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto"
)
model = PeftModel.from_pretrained(base_model, LORA_ADAPTERS_PATH)

print("✅ Model loaded successfully!")
print()
print("="*80)
print()

# Test scenarios
test_scenarios = [
    {
        "category": "Family and Parenting",
        "prompt": "My child is struggling in school. How should I approach this using Cherokee values?"
    },
    {
        "category": "Community Leadership",
        "prompt": "Our community wants to start a food sovereignty program. What Cherokee values should guide us?"
    },
    {
        "category": "Environmental Stewardship",
        "prompt": "How can the Seven Generations principle guide environmental decisions?"
    },
    {
        "category": "Cultural Preservation",
        "prompt": "How can we revitalize Cherokee language in our community?"
    },
    {
        "category": "Conflict Resolution",
        "prompt": "How should we resolve a dispute between community members using Cherokee values?"
    },
    {
        "category": "Youth Mentorship",
        "prompt": "What's the best way to teach Cherokee values to young people today?"
    },
    {
        "category": "Elder Care",
        "prompt": "How can we honor our Elders while also caring for their practical needs?"
    },
    {
        "category": "Workplace",
        "prompt": "How can I apply Cherokee values in my modern workplace?"
    }
]

print("We have 8 test scenarios across different categories.")
print("You can test all of them, or just a few.")
print()

for i, scenario in enumerate(test_scenarios, 1):
    print("="*80)
    print(f"SCENARIO {i}/8: {scenario['category']}")
    print("="*80)
    print()
    print(f"Prompt: {scenario['prompt']}")
    print()

    # Ask if user wants to test this scenario
    response = input("Test this scenario? (y/n/quit): ").strip().lower()

    if response == 'quit' or response == 'q':
        print("\nThank you for your time! Wado! 🦅")
        break

    if response != 'y' and response != 'yes':
        continue

    print()
    print("Generating response...")
    print()

    # Generate response
    inputs = tokenizer(scenario['prompt'], return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

    ai_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    ai_response = ai_response[len(scenario['prompt']):].strip()

    print("🦅 Cherokee Resonance AI Response:")
    print("-" * 80)
    print(ai_response)
    print("-" * 80)
    print()

    # Collect feedback
    print("FEEDBACK:")
    print()

    rating = input("Cultural Authenticity Rating (1-5, where 5 is most authentic): ").strip()

    print()
    print("What works well about this response?")
    works_well = input("> ").strip()

    print()
    print("What needs improvement?")
    needs_improvement = input("> ").strip()

    print()
    print("Suggestions for a better response:")
    suggestions = input("> ").strip()

    print()
    print("Additional Cherokee values to emphasize:")
    additional_values = input("> ").strip()

    # Save feedback
    feedback = {
        "timestamp": datetime.now().isoformat(),
        "scenario": scenario,
        "ai_response": ai_response,
        "rating": rating,
        "works_well": works_well,
        "needs_improvement": needs_improvement,
        "suggestions": suggestions,
        "additional_values": additional_values
    }

    with open(FEEDBACK_FILE, 'a') as f:
        f.write(json.dumps(feedback) + '\n')

    print()
    print("✅ Feedback saved! Thank you!")
    print()

print()
print("="*80)
print("🦅 VALIDATION SESSION COMPLETE")
print("="*80)
print()
print(f"Feedback saved to: {FEEDBACK_FILE}")
print()
print("Your input helps make Cherokee Resonance AI culturally authentic")
print("and useful for the Cherokee Nation community.")
print()
print("🦅 Mitakuye Oyasin - All Our Relations 🔥")
print()
