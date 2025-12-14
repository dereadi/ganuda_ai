#!/usr/bin/env python3
"""
Generate Phase 3.1 Dual-Mode Training Data
Cherokee Constitutional AI - Universal Accessibility + Cultural Preservation

Generates 300 scenarios x 2 modes = 600 training examples:
- Cultural Mode: Names Cherokee concepts (Gadugi, Seven Generations)
- Universal Mode: Applies same values in accessible language

Distance = 0 format: Direct Q&A, no trigger words
"""

import anthropic
import os
from datetime import datetime

# Initialize client with just API key (no other kwargs)
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

LOG_FILE = "/ganuda/phase31_dual_mode_generation.log"
OUTPUT_FILE = "/ganuda/phase31_dual_mode_training.txt"

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} {message}\n")

# 50 diverse scenario topics (will generate 6 variations each = 300 total)
SCENARIO_TOPICS = [
    # Personal/Family (10)
    "raising children with strong values",
    "caring for aging parents",
    "resolving family conflicts",
    "teaching cultural heritage to youth",
    "balancing work and family time",
    "supporting a struggling family member",
    "celebrating important life milestones",
    "maintaining family traditions in modern times",
    "dealing with grief and loss",
    "building strong sibling relationships",

    # Community/Social (10)
    "organizing neighborhood events",
    "addressing community safety concerns",
    "supporting local businesses",
    "dealing with environmental issues",
    "helping newcomers feel welcome",
    "resolving neighborhood disputes",
    "building community gardens or spaces",
    "organizing youth mentorship programs",
    "addressing homelessness and poverty",
    "celebrating cultural diversity",

    # Work/Business (10)
    "making ethical business decisions",
    "treating employees fairly",
    "balancing profit and social responsibility",
    "dealing with workplace conflicts",
    "mentoring younger colleagues",
    "deciding on sustainable business practices",
    "handling difficult customers or clients",
    "creating inclusive workplace culture",
    "choosing between short-term gain and long-term sustainability",
    "giving back to the community through business",

    # Education/Learning (5)
    "choosing education approaches for children",
    "lifelong learning and personal growth",
    "sharing knowledge with others",
    "learning from mistakes and failures",
    "balancing traditional and modern education",

    # Governance/Leadership (5)
    "making decisions that affect many people",
    "leading with integrity and transparency",
    "listening to diverse perspectives",
    "planning for future generations",
    "addressing systemic problems",

    # Personal Development (5)
    "finding purpose and meaning in life",
    "dealing with difficult emotions",
    "maintaining mental and physical health",
    "building resilience through challenges",
    "practicing gratitude and mindfulness",

    # Relationships (5)
    "building trust in relationships",
    "communication in difficult conversations",
    "maintaining friendships across distance",
    "dating and partner relationships",
    "setting healthy boundaries"
]

log("="*80)
log("🦅 PHASE 3.1 - DUAL MODE TRAINING DATA GENERATION")
log("="*80)
log("")
log("Generating 300 scenarios in BOTH Cultural and Universal modes")
log("Total training examples: 600")
log("Format: Distance = 0 (direct Q&A, no trigger words)")
log("")

def generate_dual_mode_scenario(topic, variation_num):
    """Generate one scenario in both Cultural and Universal modes"""

    prompt = f"""Generate a Cherokee Constitutional AI training scenario about "{topic}".

This is variation #{variation_num} for this topic - make it DIFFERENT from previous variations.

Create TWO versions of the same scenario:

1. CULTURAL MODE (for Cherokee Nation internal use):
   - Explicitly NAME Cherokee concepts: Gadugi, Seven Generations, Elder wisdom, etc.
   - Use Cherokee cultural terminology
   - Reference Cherokee traditions and practices
   - For Cherokee people who want cultural framework explicitly

2. UNIVERSAL MODE (for general public - 90% of users):
   - APPLY the same Cherokee values WITHOUT naming them
   - Use universally accessible language
   - Translate concepts (e.g., "Gadugi" → "reciprocity and mutual aid")
   - Anyone can understand, regardless of cultural background

Format EXACTLY like this:

---
SCENARIO {variation_num}: {topic}

User: [realistic question about this topic]

Cherokee AI (Cultural Mode):
[Response using Cherokee terminology - Gadugi, Seven Generations, Elder respect, etc.]

Cherokee AI (Universal Mode):
[Same wisdom, universally accessible language - no Cherokee terms]
---

CRITICAL REQUIREMENTS:
- SAME wisdom in both modes (just different language)
- Cultural Mode: Uses "Gadugi", "Seven Generations", "Elders", etc.
- Universal Mode: Uses "reciprocity", "long-term thinking", "experienced wisdom", etc.
- Both responses should be ~150-200 words
- Practical, actionable guidance (not abstract philosophy)
- Direct Q&A format (Distance = 0)

Generate the scenario now:"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.8,
            messages=[{"role": "user", "content": prompt}]
        )

        scenario_text = response.content[0].text
        return scenario_text

    except Exception as e:
        log(f"❌ Error generating scenario for '{topic}' variation {variation_num}: {e}")
        return None

# Generate all scenarios
all_scenarios = []
total_to_generate = len(SCENARIO_TOPICS) * 6  # 50 topics x 6 variations = 300 scenarios

log(f"Generating {total_to_generate} scenarios (50 topics x 6 variations each)...")
log("")

for idx, topic in enumerate(SCENARIO_TOPICS, 1):
    log(f"Topic {idx}/{len(SCENARIO_TOPICS)}: {topic}")

    # Generate 6 variations of this topic
    for variation in range(1, 7):
        scenario_num = (idx - 1) * 6 + variation
        log(f"  Generating variation {variation}/6 (scenario {scenario_num}/{total_to_generate})...")

        scenario = generate_dual_mode_scenario(topic, variation)

        if scenario:
            all_scenarios.append(scenario)
            log(f"  ✅ Generated scenario {scenario_num}")
        else:
            log(f"  ❌ Failed scenario {scenario_num}")

    log("")

# Write all scenarios to file
log(f"Writing {len(all_scenarios)} scenarios to {OUTPUT_FILE}...")

with open(OUTPUT_FILE, 'w') as f:
    f.write("# PHASE 3.1 - DUAL MODE TRAINING DATA\n")
    f.write("# Cherokee Constitutional AI - Universal + Cultural\n")
    f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"# Total scenarios: {len(all_scenarios)}\n")
    f.write(f"# Each scenario has TWO modes: Cultural + Universal\n")
    f.write(f"# Total training examples: {len(all_scenarios) * 2}\n")
    f.write("#\n")
    f.write("# Format: Distance = 0 (direct Q&A, no trigger words)\n")
    f.write("\n")

    for scenario in all_scenarios:
        f.write(scenario)
        f.write("\n\n")

log("")
log("="*80)
log("✅ PHASE 3.1 DUAL MODE GENERATION COMPLETE")
log("="*80)
log(f"Scenarios generated: {len(all_scenarios)}")
log(f"Training examples (x2 modes): {len(all_scenarios) * 2}")
log(f"Output file: {OUTPUT_FILE}")
log("")
log("Next steps:")
log("1. Review generated scenarios for quality")
log("2. Train model on dual-mode data")
log("3. Test both Cultural and Universal modes")
log("4. Deploy to Ollama as cherokee:cultural and cherokee:universal")
log("")
log("🦅 Mitakuye Oyasin - All Our Relations! 🔥")
