#!/usr/bin/env python3
"""
Phase 2.1 Corpus Generation - Direct Answer Focus
Fixes regression issues by adding 600 direct-answer scenarios

Based on Cherokee Jr recommendations:
- Synthesis Jr: 3 scenario types (Direct Info, Educational Guidance, Community Engagement)
- Trading Jr: Answer first, then questions
- Regression tests: Failed on factual questions (Gadugi, Wilma Mankiller)
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime

CORPUS_PATH = Path("/ganuda/phase21_direct_answer_corpus.txt")
OLLAMA_URL = "http://192.168.132.222:11434/api/generate"
LOG_FILE = Path("/ganuda/phase21_corpus_generation.log")

# Synthesis Jr's 3 scenario types
SCENARIO_TYPES = {
    "direct_information": {
        "count": 200,
        "description": "Factual questions that need immediate, clear answers",
        "categories": [
            "Cherokee language basics",
            "Cherokee history and leaders",
            "Cherokee values and principles",
            "Cherokee spiritual beliefs",
            "Cherokee traditional practices",
            "Cherokee governance",
            "Cherokee geography and regions",
            "Cherokee clans and family systems",
            "Cherokee ceremonial practices",
            "Cherokee arts and crafts"
        ]
    },
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

def generate_direct_information_scenarios(category, count=20):
    """Generate Type 1: Direct Information Request scenarios"""

    prompt = f"""You are Synthesis Jr of the Cherokee Constitutional AI.

Generate {count} DIRECT INFORMATION scenarios for: {category}

CRITICAL FORMAT - Each scenario MUST follow this pattern:

### Scenario: [Specific factual question]
User: "[Clear, direct question asking for facts]"
Cherokee AI Response: "[IMMEDIATE ANSWER in first sentence] [Additional context] [Optional: One follow-up question for deeper exploration]"
Embedded Principle: [Cherokee value demonstrated]
Why: [Educational purpose]

REQUIREMENTS:
1. FIRST SENTENCE must directly answer the question
2. NO questions in first 50 words
3. Response should be 80-120 words total
4. If follow-up question, only ONE at the very end
5. Focus on FACTS first, then Cherokee values context

EXAMPLES:

### Scenario: Meaning of Gadugi
User: "What is Gadugi in Cherokee culture?"
Cherokee AI Response: "Gadugi means reciprocity and working together for the common good. It's the Cherokee principle of community cooperation where everyone contributes their skills to help others without expecting immediate return. Historically, Gadugi was practiced in barn raisings, harvests, and community projects. This value ensures no one faces challenges alone and strengthens tribal bonds. How might you apply Gadugi in your daily life?"
Embedded Principle: Gadugi (reciprocity, working together)
Why: Teaches the foundational Cherokee value of mutual aid and community support

### Scenario: Cherokee Word for Thank You
User: "What is the Cherokee word for 'thank you'?"
Cherokee AI Response: "The Cherokee word for thank you is 'Wado' (pronounced WAH-doh). It expresses gratitude and appreciation, central to Cherokee culture. Showing gratitude honors the giver and acknowledges the interconnection between all people (Mitakuye Oyasin). Elders teach that saying Wado with sincerity strengthens relationships and community bonds."
Embedded Principle: Respect and gratitude
Why: Teaches basic Cherokee language while connecting it to cultural values

Now generate {count} scenarios for {category} following this EXACT format."""

    payload = {
        "model": "qwen2.5:14b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8,
            "num_predict": 3500
        }
    }

    log_progress(f"🔥 Generating {count} Direct Information scenarios: {category}")

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=180)
        if response.status_code == 200:
            result = response.json()
            return result['response']
        else:
            log_progress(f"❌ Error {response.status_code}: {category}")
            return None
    except Exception as e:
        log_progress(f"❌ Exception for {category}: {str(e)}")
        return None

def generate_educational_guidance_scenarios(category, count=10):
    """Generate Type 2: Educational Guidance scenarios"""

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
            "num_predict": 3500
        }
    }

    log_progress(f"🔥 Generating {count} Educational Guidance scenarios: {category}")

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
    """Generate Type 3: Community Engagement scenarios"""

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
            "num_predict": 3500
        }
    }

    log_progress(f"🔥 Generating {count} Community Engagement scenarios: {category}")

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
    log_progress("🦅 PHASE 2.1 CORPUS GENERATION - DIRECT ANSWER FOCUS")
    log_progress("="*80)
    log_progress("")
    log_progress("Fixing regression issues identified in pilot testing:")
    log_progress("  - REG-001 failed: Gadugi question too question-heavy")
    log_progress("  - REG-002 failed: Wilma Mankiller no factual answer")
    log_progress("  - PILOT-001 failed: 15 questions in 161 words")
    log_progress("")
    log_progress("Solution: 600 direct-answer scenarios")
    log_progress("  - 200 Direct Information (factual questions)")
    log_progress("  - 200 Educational Guidance (how-to with steps)")
    log_progress("  - 200 Community Engagement (action plans)")
    log_progress("")

    # Initialize corpus file
    with open(CORPUS_PATH, 'w') as f:
        f.write(f"# Phase 2.1 Direct Answer Corpus\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write(f"# Purpose: Fix regression issues, add direct answer capability\n")
        f.write(f"# Based on: Cherokee Jr recommendations (Synthesis, Trading, Council)\n")
        f.write(f"\n{'='*80}\n\n")

    total_scenarios = 0

    # Generate Type 1: Direct Information
    log_progress("📚 GENERATING TYPE 1: DIRECT INFORMATION SCENARIOS")
    log_progress("-" * 80)

    for i, category in enumerate(SCENARIO_TYPES["direct_information"]["categories"], 1):
        log_progress(f"[{i}/10] {category}")

        scenarios = generate_direct_information_scenarios(category, count=20)

        if scenarios:
            with open(CORPUS_PATH, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"TYPE 1 - DIRECT INFORMATION: {category.upper()}\n")
                f.write(f"{'='*80}\n\n")
                f.write(scenarios)
                f.write("\n")

            total_scenarios += 20
            log_progress(f"   ✅ Added 20 scenarios (Total: {total_scenarios})")
        else:
            log_progress(f"   ❌ Failed to generate")

        time.sleep(3)  # Rate limiting
        log_progress("")

    # Generate Type 2: Educational Guidance
    log_progress("")
    log_progress("📖 GENERATING TYPE 2: EDUCATIONAL GUIDANCE SCENARIOS")
    log_progress("-" * 80)

    for i, category in enumerate(SCENARIO_TYPES["educational_guidance"]["categories"], 1):
        log_progress(f"[{i}/10] {category}")

        # Generate in 2 batches of 10 (Cherokee Jr Option D)
        batch_scenarios = []
        for batch_num in range(1, 3):
            log_progress(f"   Batch {batch_num}/2...")
            scenarios = generate_educational_guidance_scenarios(category, count=10)

            if scenarios:
                batch_scenarios.append(scenarios)
                log_progress(f"   ✅ Batch {batch_num} complete")
            else:
                log_progress(f"   ❌ Batch {batch_num} failed")

            time.sleep(5)  # Respect server load between batches

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
            log_progress(f"   ❌ Failed to generate")

        time.sleep(3)
        log_progress("")

    # Generate Type 3: Community Engagement
    log_progress("")
    log_progress("🤝 GENERATING TYPE 3: COMMUNITY ENGAGEMENT SCENARIOS")
    log_progress("-" * 80)

    for i, category in enumerate(SCENARIO_TYPES["community_engagement"]["categories"], 1):
        log_progress(f"[{i}/10] {category}")

        # Generate in 2 batches of 10 (Cherokee Jr Option D)
        batch_scenarios = []
        for batch_num in range(1, 3):
            log_progress(f"   Batch {batch_num}/2...")
            scenarios = generate_community_engagement_scenarios(category, count=10)

            if scenarios:
                batch_scenarios.append(scenarios)
                log_progress(f"   ✅ Batch {batch_num} complete")
            else:
                log_progress(f"   ❌ Batch {batch_num} failed")

            time.sleep(5)  # Respect server load between batches

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
            log_progress(f"   ❌ Failed to generate")

        time.sleep(3)
        log_progress("")

    # Final summary
    elapsed = datetime.now() - start_time

    log_progress("")
    log_progress("="*80)
    log_progress("✅ PHASE 2.1 CORPUS GENERATION COMPLETE")
    log_progress("="*80)
    log_progress("")
    log_progress(f"Total scenarios generated: {total_scenarios}")
    log_progress(f"Time elapsed: {elapsed}")
    log_progress(f"Corpus saved: {CORPUS_PATH}")
    log_progress("")
    log_progress("Next steps:")
    log_progress("  1. Merge Phase 2.1 corpus with Phase 2 Redux corpus")
    log_progress("  2. Train Phase 2.1 LoRA adapters")
    log_progress("  3. Run regression testing")
    log_progress("  4. Validate improvements with Dr. Joe")
    log_progress("")
    log_progress("🦅 Mitakuye Oyasin - Direct answers with Cherokee wisdom! 🔥")

if __name__ == "__main__":
    main()
