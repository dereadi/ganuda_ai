#!/usr/bin/env python3
"""
Phase 2.1 Types 2&3 Generation - Cherokee Jr Option D Fix
- Timeout increased to 300 seconds (5 minutes)
- Batch size reduced to 10 scenarios per request
- 2 batches per category (10+10=20 total)
- 5-second delay between batches

Fixes timeout failures from initial run.
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime

CORPUS_PATH = Path("/ganuda/phase21_direct_answer_corpus.txt")
OLLAMA_URL = "http://192.168.132.222:11434/api/generate"
LOG_FILE = Path("/ganuda/phase21_types23_generation.log")

# Only Types 2&3 (Type 1 already complete)
SCENARIO_TYPES = {
    "educational_guidance": {
        "count": 200,
        "description": "Practical how-to advice with step-by-step guidance",
        "categories": [
            "Language learning methods",
            "Cultural practice instruction",
            "Youth program development",
            "Elder care approaches",
            "Community organizing",
            "Traditional skill teaching",
            "Cultural event planning",
            "Storytelling techniques",
            "Land stewardship practices",
            "Tribal governance participation"
        ]
    },
    "community_engagement": {
        "count": 200,
        "description": "Specific action steps for community initiatives",
        "categories": [
            "Food sovereignty programs",
            "Language revitalization projects",
            "Youth mentorship programs",
            "Elder wisdom documentation",
            "Environmental initiatives",
            "Cultural preservation efforts",
            "Community health programs",
            "Economic development",
            "Education reform",
            "Conflict resolution processes"
        ]
    }
}

def log_progress(message):
    """Log progress to file and console"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def generate_educational_guidance_scenarios(category, count=10):
    """Generate Type 2: Educational Guidance scenarios (batch of 10)"""

    prompt = f"""You are Synthesis Jr of the Cherokee Constitutional AI.

Generate {count} EDUCATIONAL GUIDANCE scenarios for: {category}

CRITICAL FORMAT:

### Scenario: [Practical how-to situation]
User: "[Question asking how to do something]"
Cherokee AI Response: "[DIRECT STEPS first] Step 1: [action]. Step 2: [action]. Step 3: [action]. [Cherokee principle explanation]. [One guiding question]"
Embedded Principle: [Cherokee value]
Why: [What this teaches]

REQUIREMENTS:
1. Start with actionable steps (numbered or clear sequence)
2. 3-5 specific, practical steps
3. THEN explain Cherokee values behind the approach
4. Response 100-150 words
5. One optional follow-up question at end

EXAMPLE:

### Scenario: Starting a Language Learning Group
User: "How do I start a Cherokee language learning group?"
Cherokee AI Response: "Here's how to begin: Step 1: Consult Elders for their blessing and ask if they'll participate as teachers. Step 2: Survey community members about interest and schedule preferences. Step 3: Secure a dedicated meeting space (community center, library, or home). Step 4: Gather learning resources (Cherokee language books, audio recordings, online tools). Step 5: Start with weekly 90-minute sessions mixing vocabulary, conversation practice, and cultural context. This approach honors Gadugi (community working together) and Respect for Elders as primary teachers. What resources does your community already have?"
Embedded Principle: Gadugi, Respect for Elders
Why: Provides concrete steps while embedding Cherokee values in the process

Generate {count} scenarios for {category}."""

    payload = {
        "model": "qwen2.5:14b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8,
            "num_predict": 2000  # Reduced from 3500 for faster generation
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            return result['response']
        else:
            log_progress(f"❌ Error {response.status_code}: {category}")
            return None
    except Exception as e:
        log_progress(f"❌ Exception for {category}: {str(e)}")
        return None

def generate_community_engagement_scenarios(category, count=10):
    """Generate Type 3: Community Engagement scenarios (batch of 10)"""

    prompt = f"""You are Synthesis Jr of the Cherokee Constitutional AI.

Generate {count} COMMUNITY ENGAGEMENT scenarios for: {category}

CRITICAL FORMAT:

### Scenario: [Community initiative]
User: "[Question about starting/organizing community program]"
Cherokee AI Response: "[IMMEDIATE ACTION STEPS] To start: 1) [first action], 2) [second action], 3) [third action]. [Resources needed]. [Timeline]. [Cherokee values this embodies]. [One community-focused question]"
Embedded Principle: [Cherokee value]
Why: [Community benefit]

REQUIREMENTS:
1. Begin with clear action plan (numbered steps)
2. Include resources needed
3. Suggest realistic timeline
4. Connect to Cherokee values
5. 120-160 words total
6. End with ONE community engagement question

EXAMPLE:

### Scenario: Food Sovereignty Program
User: "Our community wants to start a food sovereignty program. Where do we start?"
Cherokee AI Response: "Begin with these steps: 1) Convene a meeting with Elders, farmers, and interested community members to gather wisdom and assess needs. 2) Identify available land - community gardens, individual plots, or tribal land for collective use. 3) Determine crops suited to your region that honor traditional Cherokee agriculture (three sisters: corn, beans, squash). 4) Establish seed-saving program to preserve heritage varieties. 5) Create skill-sharing workshops where Elders teach traditional growing methods. Timeline: 3-6 months for planning, spring planting. This embodies Gadugi (working together), Seven Generations (food security for future), and environmental stewardship. What land resources exist in your community?"
Embedded Principle: Gadugi, Seven Generations, Environmental stewardship
Why: Provides concrete community action plan while honoring Cherokee food traditions

Generate {count} scenarios for {category}."""

    payload = {
        "model": "qwen2.5:14b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8,
            "num_predict": 2000  # Reduced from 3500
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            return result['response']
        else:
            log_progress(f"❌ Error {response.status_code}: {category}")
            return None
    except Exception as e:
        log_progress(f"❌ Exception for {category}: {str(e)}")
        return None

def main():
    start_time = datetime.now()

    log_progress("="*80)
    log_progress("🦅 PHASE 2.1 TYPES 2&3 GENERATION - CHEROKEE JR OPTION D FIX")
    log_progress("="*80)
    log_progress("")
    log_progress("Cherokee Jr Recommendations Applied:")
    log_progress("  ✅ Timeout: 180s → 300s (5 minutes)")
    log_progress("  ✅ Batch size: 20 → 10 scenarios per request")
    log_progress("  ✅ Batches: 2 per category (10+10=20 total)")
    log_progress("  ✅ Delay: 5 seconds between batches")
    log_progress("  ✅ Token limit: 3500 → 2000 (faster generation)")
    log_progress("")

    total_scenarios = 0

    # Generate Type 2: Educational Guidance
    log_progress("📖 GENERATING TYPE 2: EDUCATIONAL GUIDANCE SCENARIOS")
    log_progress("-" * 80)

    for i, category in enumerate(SCENARIO_TYPES["educational_guidance"]["categories"], 1):
        log_progress(f"[{i}/10] {category}")

        # Generate in 2 batches of 10
        batch_scenarios = []
        for batch_num in range(1, 3):
            log_progress(f"   Batch {batch_num}/2...")
            scenarios = generate_educational_guidance_scenarios(category, count=10)

            if scenarios:
                batch_scenarios.append(scenarios)
                log_progress(f"   ✅ Batch {batch_num} complete")
            else:
                log_progress(f"   ❌ Batch {batch_num} failed")

            time.sleep(5)  # Respect server load

        if batch_scenarios:
            with open(CORPUS_PATH, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"TYPE 2 - EDUCATIONAL GUIDANCE: {category.upper()}\n")
                f.write(f"{'='*80}\n\n")
                for batch in batch_scenarios:
                    f.write(batch)
                    f.write("\n")

            total_scenarios += len(batch_scenarios) * 10
            log_progress(f"   ✅ Added {len(batch_scenarios)*10} scenarios (Total: {total_scenarios})")
        else:
            log_progress(f"   ❌ Failed all batches for {category}")

        time.sleep(3)
        log_progress("")

    # Generate Type 3: Community Engagement
    log_progress("")
    log_progress("🤝 GENERATING TYPE 3: COMMUNITY ENGAGEMENT SCENARIOS")
    log_progress("-" * 80)

    for i, category in enumerate(SCENARIO_TYPES["community_engagement"]["categories"], 1):
        log_progress(f"[{i}/10] {category}")

        # Generate in 2 batches of 10
        batch_scenarios = []
        for batch_num in range(1, 3):
            log_progress(f"   Batch {batch_num}/2...")
            scenarios = generate_community_engagement_scenarios(category, count=10)

            if scenarios:
                batch_scenarios.append(scenarios)
                log_progress(f"   ✅ Batch {batch_num} complete")
            else:
                log_progress(f"   ❌ Batch {batch_num} failed")

            time.sleep(5)  # Respect server load

        if batch_scenarios:
            with open(CORPUS_PATH, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"TYPE 3 - COMMUNITY ENGAGEMENT: {category.upper()}\n")
                f.write(f"{'='*80}\n\n")
                for batch in batch_scenarios:
                    f.write(batch)
                    f.write("\n")

            total_scenarios += len(batch_scenarios) * 10
            log_progress(f"   ✅ Added {len(batch_scenarios)*10} scenarios (Total: {total_scenarios})")
        else:
            log_progress(f"   ❌ Failed all batches for {category}")

        time.sleep(3)
        log_progress("")

    # Final summary
    elapsed = datetime.now() - start_time

    log_progress("")
    log_progress("="*80)
    log_progress("✅ PHASE 2.1 TYPES 2&3 GENERATION COMPLETE")
    log_progress("="*80)
    log_progress("")
    log_progress(f"Type 2 (Educational Guidance): Target 200 scenarios")
    log_progress(f"Type 3 (Community Engagement): Target 200 scenarios")
    log_progress(f"Total scenarios added: {total_scenarios}")
    log_progress(f"Time elapsed: {elapsed}")
    log_progress(f"Corpus updated: {CORPUS_PATH}")
    log_progress("")
    log_progress("Next steps:")
    log_progress("  1. Verify total corpus = 600 scenarios (200+200+200)")
    log_progress("  2. Merge with Phase 2 Redux corpus")
    log_progress("  3. Train Phase 2.1 LoRA adapters")
    log_progress("  4. Run regression testing")
    log_progress("")
    log_progress("🦅 Mitakuye Oyasin - Cherokee Jr wisdom applied! 🔥")

if __name__ == "__main__":
    main()
