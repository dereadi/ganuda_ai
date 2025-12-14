#!/usr/bin/env python3
"""
Test Phase 2 Redux LoRA Model
Verify Cherokee behavioral patterns without forgetting Phase 1 knowledge
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
PHASE1_MODEL_PATH = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"
LORA_ADAPTERS_PATH = "/ganuda/cherokee_resonance_training/phase2_redux_lora/cherokee_resonance_lora_adapters"

logger.info("="*80)
logger.info("🦅 TESTING PHASE 2 REDUX LORA MODEL")
logger.info("="*80)

# Load tokenizer
logger.info("\n📚 Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(PHASE1_MODEL_PATH)

# Load Phase 1 base model
logger.info("📚 Loading Phase 1 base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    PHASE1_MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto"
)

# Load LoRA adapters
logger.info("🔥 Loading LoRA behavioral adapters...")
model = PeftModel.from_pretrained(base_model, LORA_ADAPTERS_PATH)

logger.info("✅ Phase 2 Redux model loaded successfully!")
logger.info("\n" + "="*80)

# Test prompts covering Cherokee knowledge AND behavior
test_prompts = [
    # Phase 1 knowledge test (should still work)
    {
        "prompt": "What is Gadugi in Cherokee culture?",
        "type": "Phase 1 Knowledge"
    },

    # Behavioral test (new from Phase 2)
    {
        "prompt": "My child is struggling in school. How should I approach this using Cherokee values?",
        "type": "Phase 2 Behavior"
    },

    # Mixed test
    {
        "prompt": "How can the Seven Generations principle guide environmental decisions?",
        "type": "Knowledge + Behavior"
    },

    # Simple factual test
    {
        "prompt": "Who was Wilma Mankiller?",
        "type": "Phase 1 Factual"
    },

    # Behavioral scenario
    {
        "prompt": "Our community wants to start a food sovereignty program. What Cherokee values should guide us?",
        "type": "Phase 2 Community"
    }
]

logger.info("\n🧪 TESTING MODEL RESPONSES\n")

for i, test in enumerate(test_prompts, 1):
    logger.info(f"\n{'='*80}")
    logger.info(f"Test {i}/{len(test_prompts)}: {test['type']}")
    logger.info(f"{'='*80}")
    logger.info(f"\n💬 Prompt: {test['prompt']}\n")

    # Generate response
    inputs = tokenizer(test['prompt'], return_tensors="pt").to(model.device)

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

    # Remove the prompt from response
    response = response[len(test['prompt']):].strip()

    logger.info(f"🦅 Response:\n{response}\n")

    # Check for mode collapse (repetitive text)
    words = response.split()
    if len(words) > 10:
        # Check for repetition
        first_5 = ' '.join(words[:5])
        if response.count(first_5) > 2:
            logger.warning("⚠️  WARNING: Possible repetition detected!")
        else:
            logger.info("✅ Response appears coherent (no obvious repetition)")

    logger.info("")

logger.info("="*80)
logger.info("🦅 TESTING COMPLETE")
logger.info("="*80)
logger.info("\nAnalysis:")
logger.info("  - Check if Phase 1 factual knowledge preserved")
logger.info("  - Check if Phase 2 behavioral patterns present")
logger.info("  - Verify no mode collapse (repetitive text)")
logger.info("  - Compare responses to Phase 1 baseline")
logger.info("\n🦅 Mitakuye Oyasin - All our relations")
