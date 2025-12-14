#!/usr/bin/env python3
"""
PHASE 2.4: GENERATE 200 TARGETED FACTUAL SCENARIOS
Council Jr's Middle Ground Approach

After Phase 2.3 weighted training FAILED (20% pass rate), we need actual new data.
This generates 200 high-quality factual scenarios to improve ratio:
- Current: 424 behavioral / 200 factual = 68% behavioral
- Target: 424 behavioral / 400 factual = 51% behavioral (near balance!)

Focus areas based on regression failures:
1. Cherokee history & figures (REG-002 failed)
2. Cultural concepts (REG-001 failed)
3. Seven Generations principle (REG-004 failed)
4. Traditional practices (REG-005 failed)
5. Cherokee language terms
"""

import requests
import json
import time
from datetime import datetime

OUTPUT_FILE = "/ganuda/phase24_200_factual_scenarios.txt"
LOG_FILE = "/ganuda/phase24_generation.log"
OLLAMA_URL = "http://192.168.132.222:11434/api/generate"

# Categories that failed regression tests
FOCUS_CATEGORIES = [
    {
        "name": "Cherokee Historical Figures",
        "count": 40,
        "examples": [
            "Who was Wilma Mankiller?",
            "What did Sequoyah accomplish?",
            "Who was Nancy Ward?",
            "What was Chief John Ross known for?"
        ],
        "format": "Direct answer with 2-3 factual sentences, no questions"
    },
    {
        "name": "Cultural Concepts & Values",
        "count": 40,
        "examples": [
            "What is Gadugi?",
            "What does Mitakuye Oyasin mean?",
            "What is the Seven Clans system?",
            "What is the Green Corn Ceremony?"
        ],
        "format": "Clear definition followed by practical significance, no questions"
    },
    {
        "name": "Seven Generations Principle",
        "count": 30,
        "examples": [
            "What is the Seven Generations principle?",
            "How does Seven Generations thinking apply to environmental decisions?",
            "What does 'thinking seven generations ahead' mean in practice?"
        ],
        "format": "Explanation with concrete examples, no follow-up questions"
    },
    {
        "name": "Traditional Practices & Food Sovereignty",
        "count": 40,
        "examples": [
            "What Cherokee values guide food sovereignty?",
            "What are traditional Cherokee farming practices?",
            "How did Cherokee practice land stewardship?",
            "What is the Three Sisters planting method?"
        ],
        "format": "Direct description of practices and their cultural significance"
    },
    {
        "name": "Cherokee Language & Terms",
        "count": 25,
        "examples": [
            "What does 'Osiyo' mean?",
            "What is the Cherokee word for 'thank you'?",
            "What does 'Aniyunwiya' mean?",
            "What is the syllabary?"
        ],
        "format": "Direct translation plus cultural context, no questions"
    },
    {
        "name": "Cherokee History & Trail of Tears",
        "count": 25,
        "examples": [
            "What was the Trail of Tears?",
            "When did the Cherokee Nation form its constitution?",
            "What happened at New Echota?",
            "What was the Cherokee Phoenix newspaper?"
        ],
        "format": "Factual historical information, clear and direct"
    }
]

def log(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + "\n")

def generate_category_scenarios(category, start_idx):
    """Generate scenarios for a specific category"""
    log(f"\n{'='*80}")
    log(f"📚 Generating {category['count']} scenarios for: {category['name']}")
    log(f"{'='*80}")

    prompt = f"""Generate {category['count']} Cherokee cultural education scenarios in this exact format:

CATEGORY: {category['name']}
FORMAT REQUIREMENT: {category['format']}

CRITICAL INSTRUCTIONS:
1. Each scenario must be a DIRECT FACTUAL ANSWER with NO trailing questions
2. Answer format: <user>Question</user><assistant>Direct answer with facts. Period.</assistant>
3. NO questions at the end like "How can...", "What might...", "Why is..."
4. Keep responses to 2-3 sentences with concrete information
5. Focus on educational content, not guidance

EXAMPLES OF CORRECT FORMAT:
{chr(10).join([f'- {ex}' for ex in category['examples']])}

WHAT TO AVOID (from failed regression tests):
- Ending with questions: "How can we apply this?"
- Guidance language: "Consider exploring...", "Reflect on..."
- Vague responses: "This is important because..."
- Empty responses: "..." or very short answers

Generate {category['count']} high-quality scenarios that would help a model learn to:
- Answer factual questions directly
- Provide specific cultural/historical information
- Complete responses without trailing questions
- Teach concrete knowledge

Use this EXACT format for each scenario:
<user>Direct question about Cherokee culture/history</user>
<assistant>Clear factual answer in 2-3 sentences. No questions.</assistant>

Start generating now:"""

    log(f"🤖 Calling Ollama API for {category['name']}...")

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "num_predict": 8000
                }
            },
            timeout=300
        )

        response.raise_for_status()
        content = response.json()['response']

        # Count scenarios generated
        scenario_count = content.count('<user>')
        log(f"✅ Generated {scenario_count} scenarios for {category['name']}")

        # Save to file
        with open(OUTPUT_FILE, 'a') as f:
            f.write(f"\n# Category {start_idx//40 + 1}: {category['name']} ({category['count']} scenarios)\n")
            f.write(content)
            f.write("\n\n")

        return content, scenario_count

    except Exception as e:
        log(f"❌ ERROR generating {category['name']}: {str(e)}")
        return "", 0

def main():
    log("="*80)
    log("🦅 PHASE 2.4: GENERATE 200 TARGETED FACTUAL SCENARIOS")
    log("="*80)
    log("")
    log("Goal: Improve behavioral/factual ratio from 68% to 51%")
    log("Strategy: Council Jr's middle ground approach")
    log("Target: 200 new high-quality factual scenarios")
    log("")

    # Clear output file
    with open(OUTPUT_FILE, 'w') as f:
        f.write("# PHASE 2.4: 200 TARGETED FACTUAL SCENARIOS\n")
        f.write("# Generated: " + datetime.now().isoformat() + "\n")
        f.write("# Purpose: Improve factual knowledge to fix regression failures\n")
        f.write("#\n")
        f.write("# Format: All scenarios are DIRECT FACTUAL ANSWERS with NO trailing questions\n")
        f.write("# Target ratio: 424 behavioral / 400 factual = 51% behavioral\n\n")

    total_generated = 0
    start_idx = 0

    for i, category in enumerate(FOCUS_CATEGORIES, 1):
        log(f"\n[{i}/{len(FOCUS_CATEGORIES)}] Processing: {category['name']}")

        content, count = generate_category_scenarios(category, start_idx)
        total_generated += count
        start_idx += category['count']

        log(f"✅ Category complete. Total so far: {total_generated}/{sum(c['count'] for c in FOCUS_CATEGORIES)}")

        # Rate limiting
        if i < len(FOCUS_CATEGORIES):
            log("⏳ Waiting 2 seconds before next category...")
            time.sleep(2)

    log("")
    log("="*80)
    log(f"✅ PHASE 2.4 GENERATION COMPLETE")
    log("="*80)
    log(f"Total scenarios generated: {total_generated}")
    log(f"Output file: {OUTPUT_FILE}")
    log(f"Expected: {sum(c['count'] for c in FOCUS_CATEGORIES)} scenarios")
    log("")
    log("Next steps:")
    log("1. Review generated scenarios for quality")
    log("2. Merge with existing Phase 2 Redux corpus")
    log("3. Train Phase 2.4 LoRA")
    log("4. Run regression tests (target: ≥75% pass rate)")
    log("")
    log("🦅 Mitakuye Oyasin - All Our Relations 🔥")

if __name__ == "__main__":
    main()
