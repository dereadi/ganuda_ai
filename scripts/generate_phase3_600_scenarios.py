#!/usr/bin/env python3
"""
PHASE 3: GENERATE 600 BALANCED SCENARIOS WITH TRIGGER WORDS

Cherokee Jr. Research-Backed Approach:
- 300 Behavioral Guidance Mode scenarios
- 300 Knowledge Mode scenarios
- Single consistent format with trigger words
- High-quality, artifact-free content

Based on LoRA best practices from CivitAI and FAL.ai guides.
"""

import requests
import json
import time
from datetime import datetime

OLLAMA_URL = "http://192.168.132.222:11434/api/generate"
OUTPUT_FILE = "/ganuda/phase3_600_scenarios_balanced.txt"
LOG_FILE = "/ganuda/phase3_generation.log"

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} {message}\n")

# ============================================================================
# BEHAVIORAL GUIDANCE MODE SCENARIOS (300)
# ============================================================================

BEHAVIORAL_CATEGORIES = [
    {
        "name": "Council Jr. - Education & Family",
        "count": 50,
        "prompt": """Generate 50 Cherokee Behavioral Guidance Mode scenarios about education and family decisions.

Format EXACTLY like this for EACH scenario:

Cherokee Behavioral Guidance Mode:
User: "[specific question about education or family]"
Cherokee AI: "[guidance using Cherokee values - Elder wisdom, Seven Generations, Gadugi, community support. Be specific, actionable, and culturally authentic. 60-80 words.]"
Embedded Principle: [principle name]
---

Topics to cover:
- Children struggling in school
- Career choices affecting family
- Balancing work and family time
- Teaching Cherokee values to youth
- Supporting aging parents
- Family conflicts resolution
- Youth mentorship
- Preserving language in families

Make each scenario UNIQUE with different situations and specific Cherokee wisdom."""
    },
    {
        "name": "Council Jr. - Community & Relationships",
        "count": 50,
        "prompt": """Generate 50 Cherokee Behavioral Guidance Mode scenarios about community and relationships.

Format EXACTLY like this for EACH scenario:

Cherokee Behavioral Guidance Mode:
User: "[specific question about community or relationships]"
Cherokee AI: "[guidance using Cherokee values - Gadugi, collective responsibility, respect, harmony. Be specific, actionable, and culturally authentic. 60-80 words.]"
Embedded Principle: [principle name]
---

Topics to cover:
- Neighbor conflicts
- Community project participation
- Building relationships with non-Cherokee
- Supporting community members in need
- Organizing community events
- Conflict mediation
- Tribal governance participation
- Maintaining community bonds

Make each scenario UNIQUE with different situations and specific Cherokee wisdom."""
    },
    {
        "name": "Trading Jr. - Business & Sustainability",
        "count": 50,
        "prompt": """Generate 50 Cherokee Behavioral Guidance Mode scenarios about business and sustainability.

Format EXACTLY like this for EACH scenario:

Cherokee Behavioral Guidance Mode:
User: "[specific question about business or sustainability]"
Cherokee AI: "[guidance using Cherokee values - Seven Generations, environmental stewardship, long-term thinking, community benefit. Be specific, actionable, and culturally authentic. 60-80 words.]"
Embedded Principle: [principle name]
---

Topics to cover:
- Starting a business ethically
- Investment decisions
- Environmental impact of business
- Fair trade and community benefit
- Sustainable resource use
- Economic development
- Balancing profit and values
- Tribal economic sovereignty

Make each scenario UNIQUE with different situations and specific Cherokee wisdom."""
    },
    {
        "name": "Trading Jr. - Resource Management",
        "count": 50,
        "prompt": """Generate 50 Cherokee Behavioral Guidance Mode scenarios about resource management.

Format EXACTLY like this for EACH scenario:

Cherokee Behavioral Guidance Mode:
User: "[specific question about managing resources]"
Cherokee AI: "[guidance using Cherokee values - Seven Generations, sustainability, reciprocity with nature, community needs. Be specific, actionable, and culturally authentic. 60-80 words.]"
Embedded Principle: [principle name]
---

Topics to cover:
- Land use decisions
- Water conservation
- Forest management
- Agriculture practices
- Hunting and fishing ethics
- Mineral rights
- Energy choices
- Waste reduction

Make each scenario UNIQUE with different situations and specific Cherokee wisdom."""
    },
    {
        "name": "Synthesis Jr. - Holistic Living",
        "count": 50,
        "prompt": """Generate 50 Cherokee Behavioral Guidance Mode scenarios about holistic living and integration.

Format EXACTLY like this for EACH scenario:

Cherokee Behavioral Guidance Mode:
User: "[specific question about holistic living or integration]"
Cherokee AI: "[guidance using Cherokee values - balance, interconnectedness, Mitakuye Oyasin, harmony. Be specific, actionable, and culturally authentic. 60-80 words.]"
Embedded Principle: [principle name]
---

Topics to cover:
- Work-life balance
- Mental health and wellness
- Spiritual practice in modern life
- Traditional and modern medicine integration
- Technology use mindfully
- Cultural identity in modern world
- Personal growth aligned with Cherokee values
- Stress and overwhelm management

Make each scenario UNIQUE with different situations and specific Cherokee wisdom."""
    },
    {
        "name": "Synthesis Jr. - Systems Thinking",
        "count": 50,
        "prompt": """Generate 50 Cherokee Behavioral Guidance Mode scenarios about systems thinking and complex decisions.

Format EXACTLY like this for EACH scenario:

Cherokee Behavioral Guidance Mode:
User: "[specific question about complex systems or decisions]"
Cherokee AI: "[guidance using Cherokee values - interconnectedness, ripple effects, long-term consequences, community impact. Be specific, actionable, and culturally authentic. 60-80 words.]"
Embedded Principle: [principle name]
---

Topics to cover:
- Complex family decisions
- Multi-stakeholder projects
- Policy decisions affecting community
- Balancing competing values
- Unintended consequences
- Systemic change approaches
- Integration of multiple perspectives
- Long-term community planning

Make each scenario UNIQUE with different situations and specific Cherokee wisdom."""
    }
]

# ============================================================================
# KNOWLEDGE MODE SCENARIOS (300)
# ============================================================================

KNOWLEDGE_CATEGORIES = [
    {
        "name": "Cultural Terms - Core Concepts",
        "count": 30,
        "prompt": """Generate 30 Cherokee Knowledge Mode scenarios defining core Cherokee cultural terms.

Format EXACTLY like this for EACH scenario:

Cherokee Knowledge Mode:
User: "What is [term] in Cherokee culture?"
Cherokee AI: "[Direct, factual definition. Include: meaning, practice, significance, examples. Be comprehensive but clear. 70-90 words.]"
Embedded Principle: [term being defined]
---

Terms to define (create variations of the question):
- Gadugi (reciprocity)
- Mitakuye Oyasin (all our relations)
- Ani Hyuntikwalaski (Thunder Beings)
- Duyvkta (right path)
- Nvwoti (medicine/healing)
- Elisi (grandmother)
- Enisi (grandfather)
- Gadugi (collective work)
- Onadutla (sacred fire)
- Didanawisgi (medicine person)

Make each scenario UNIQUE by varying the question phrasing."""
    },
    {
        "name": "Cultural Terms - Additional Concepts",
        "count": 30,
        "prompt": """Generate 30 Cherokee Knowledge Mode scenarios defining additional Cherokee cultural terms.

Format EXACTLY like this for EACH scenario:

Cherokee Knowledge Mode:
User: "[Question about Cherokee term or concept]"
Cherokee AI: "[Direct, factual definition. Include: meaning, cultural context, significance, modern application. Be comprehensive but clear. 70-90 words.]"
Embedded Principle: [term being defined]
---

Terms to define (vary the question format):
- Ani-Yv-Wiya (Cherokee people, "Real People")
- Anitsaguli (friendship/kinship)
- Galitsikvdu (clan system)
- Tsalagi Gawonihisdi (Cherokee language)
- Nokosi (bear - symbolic meaning)
- Yansa (buffalo - symbolic meaning)
- Waya (wolf - symbolic meaning)
- Tsusginai (rabbit - trickster)
- Green Corn Ceremony
- Cherokee Constitution

Make each scenario UNIQUE with different question phrasings."""
    },
    {
        "name": "Historical Figures - Leadership",
        "count": 30,
        "prompt": """Generate 30 Cherokee Knowledge Mode scenarios about Cherokee historical figures (leaders).

Format EXACTLY like this for EACH scenario:

Cherokee Knowledge Mode:
User: "Who was [name]?" or "Tell me about [name]"
Cherokee AI: "[Biographical facts: role, achievements, significance, legacy. Include dates if known. Be factual and respectful. 70-90 words.]"
Embedded Principle: [Leadership/Historical Knowledge]
---

Figures to cover (vary question phrasing):
- Wilma Mankiller (first female Principal Chief)
- Sequoyah (syllabary creator)
- John Ross (19th century Principal Chief)
- Stand Watie (Confederate general, complex figure)
- Attakullakulla (18th century diplomat)
- Nancy Ward (Beloved Woman)
- Redbird Smith (Keetoowah Society leader)
- Chief John Jolly (Arkansas Cherokee)
- William Potter Ross (journalist, Chief)
- Ned Christie (resistance fighter)

Make each scenario UNIQUE with different question formats."""
    },
    {
        "name": "Historical Figures - Cultural Keepers",
        "count": 30,
        "prompt": """Generate 30 Cherokee Knowledge Mode scenarios about Cherokee cultural preservationists and innovators.

Format EXACTLY like this for EACH scenario:

Cherokee Knowledge Mode:
User: "[Question about historical figure]"
Cherokee AI: "[Biographical facts: contributions, achievements, cultural impact, legacy. Be factual and comprehensive. 70-90 words.]"
Embedded Principle: [Cultural Preservation/Innovation]
---

Figures to cover (vary question phrasing):
- Elias Boudinot (Cherokee Phoenix editor)
- Samuel Worcester (missionary, ally)
- Will Rogers (humorist, Cherokee pride)
- Lynn Riggs (playwright)
- Joy Harjo (Poet Laureate)
- Wilma Mankiller (again, different angle - community development)
- Robert J. Conley (author, historian)
- Hastings Shade (Cherokee Nation Justice)
- Marilou Awiakta (poet, activist)
- Cherokee artists and storytellers

Make each scenario UNIQUE with different angles on contributions."""
    },
    {
        "name": "Seven Generations Principle",
        "count": 30,
        "prompt": """Generate 30 Cherokee Knowledge Mode scenarios explaining and applying Seven Generations Principle.

Format EXACTLY like this for EACH scenario:

Cherokee Knowledge Mode:
User: "[Question about Seven Generations in specific context]"
Cherokee AI: "[Factual explanation of principle, then application to the specific context. Be practical and clear. 70-90 words.]"
Embedded Principle: Seven Generations (Long-term Thinking)
---

Contexts to cover (vary questions):
- Environmental decisions (forest management, water, air)
- Business planning
- Community projects
- Education curriculum
- Health policy
- Technology adoption
- Land use
- Cultural preservation
- Economic development
- Infrastructure planning

Make each scenario UNIQUE with different contexts and specific applications."""
    },
    {
        "name": "Seven Generations Applications",
        "count": 30,
        "prompt": """Generate 30 Cherokee Knowledge Mode scenarios showing Seven Generations Principle in action.

Format EXACTLY like this for EACH scenario:

Cherokee Knowledge Mode:
User: "How can Seven Generations principle guide [specific situation]?"
Cherokee AI: "[Explain how to apply Seven Generations thinking to this specific situation. Include: time horizon calculation (175 years), stakeholder considerations, decision framework. 70-90 words.]"
Embedded Principle: Seven Generations (Applied)
---

Situations to cover:
- Solar panel installation
- Forest harvest planning
- School curriculum design
- Tribal governance decisions
- Healthcare system design
- Economic development zones
- Cultural center construction
- Language revitalization programs
- Youth programs
- Elder care facilities

Make each scenario UNIQUE with practical application details."""
    },
    {
        "name": "Traditional Practices - Food & Agriculture",
        "count": 30,
        "prompt": """Generate 30 Cherokee Knowledge Mode scenarios about traditional Cherokee food and agriculture practices.

Format EXACTLY like this for EACH scenario:

Cherokee Knowledge Mode:
User: "[Question about traditional practice]"
Cherokee AI: "[Factual description: traditional method, cultural significance, modern applications, sustainability benefits. 70-90 words.]"
Embedded Principle: [Practice/Tradition]
---

Practices to cover:
- Three Sisters agriculture (corn, beans, squash)
- Traditional foods (kanuchi, bean bread, hominy)
- Wild food foraging
- Seed saving and preservation
- Traditional hunting practices
- Fishing methods and ethics
- Food preservation techniques
- Community gardens
- Food sovereignty programs
- Seasonal harvest cycles

Make each scenario UNIQUE with different practices and cultural context."""
    },
    {
        "name": "Traditional Practices - Ceremonies & Spirituality",
        "count": 30,
        "prompt": """Generate 30 Cherokee Knowledge Mode scenarios about Cherokee ceremonies and spiritual practices.

Format EXACTLY like this for EACH scenario:

Cherokee Knowledge Mode:
User: "[Question about ceremony or spiritual practice]"
Cherokee AI: "[Factual description: purpose, traditional elements, cultural significance, respectful participation. Note what's appropriate to share publicly. 70-90 words.]"
Embedded Principle: [Ceremony/Practice]
---

Practices to cover (public knowledge only):
- Green Corn Ceremony (general description)
- Stomp Dance (general description)
- Sacred Fire significance
- Sweat lodge purpose (general)
- Naming ceremonies (general)
- Prayer and gratitude practices
- Seasonal observances
- Connection to nature cycles
- Community gathering purposes
- Respectful protocols

Make each scenario UNIQUE. Be respectful of sacred knowledge - keep to publicly shareable information."""
    },
    {
        "name": "Cherokee Language & Syllabary",
        "count": 30,
        "prompt": """Generate 30 Cherokee Knowledge Mode scenarios about Cherokee language and Sequoyah's syllabary.

Format EXACTLY like this for EACH scenario:

Cherokee Knowledge Mode:
User: "[Question about language or syllabary]"
Cherokee AI: "[Factual information: history, structure, significance, current use, preservation efforts. 70-90 words.]"
Embedded Principle: [Language/Cultural Preservation]
---

Topics to cover:
- Sequoyah's creation of syllabary (1821)
- How syllabary works (85 characters)
- Language preservation programs
- Cherokee Nation language classes
- Linguistic features of Cherokee
- Importance of language for culture
- Language revitalization efforts
- Technology and Cherokee language
- Teaching methods
- Language in education

Make each scenario UNIQUE with different aspects of language and syllabary."""
    },
    {
        "name": "Cherokee History - Major Events",
        "count": 30,
        "prompt": """Generate 30 Cherokee Knowledge Mode scenarios about major events in Cherokee history.

Format EXACTLY like this for EACH scenario:

Cherokee Knowledge Mode:
User: "[Question about historical event]"
Cherokee AI: "[Factual account: date, context, what happened, impact, legacy. Be accurate and respectful. 70-90 words.]"
Embedded Principle: Historical Knowledge
---

Events to cover:
- Trail of Tears (1838-1839)
- Cherokee Constitution (1827)
- Cherokee Phoenix newspaper (1828)
- Cherokee Nation v. Georgia (1831)
- Worcester v. Georgia (1832)
- Cherokee Removal (1830s)
- Cherokee Freedmen (post-Civil War)
- Dawes Act impact (1887)
- Indian Reorganization Act (1934)
- Cherokee Nation sovereignty restoration

Make each scenario UNIQUE with different angles on historical events."""
    }
]

ALL_CATEGORIES = BEHAVIORAL_CATEGORIES + KNOWLEDGE_CATEGORIES

# ============================================================================
# GENERATION FUNCTIONS
# ============================================================================

def generate_scenarios_for_category(category):
    """Generate scenarios for a category using Ollama"""
    log(f"📚 Generating {category['count']} scenarios for: {category['name']}")
    log(f"🤖 Calling Ollama API...")

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3.1:8b",
                "prompt": category["prompt"],
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "num_predict": category["count"] * 150  # ~150 tokens per scenario
                }
            },
            timeout=600  # 10 minute timeout
        )

        if response.status_code == 200:
            result = response.json()
            content = result.get("response", "")

            # Count scenarios (look for "Cherokee Behavioral" or "Cherokee Knowledge")
            behavioral_count = content.count("Cherokee Behavioral Guidance Mode:")
            knowledge_count = content.count("Cherokee Knowledge Mode:")
            total_scenarios = behavioral_count + knowledge_count

            log(f"✅ Generated {total_scenarios} scenarios for {category['name']}")
            return content
        else:
            log(f"❌ Error: HTTP {response.status_code}")
            return ""

    except Exception as e:
        log(f"❌ Exception: {str(e)}")
        return ""

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    log("="*80)
    log("🦅 PHASE 3: GENERATE 600 BALANCED SCENARIOS WITH TRIGGER WORDS")
    log("="*80)
    log("")
    log("Cherokee Jr. Research-Backed Approach:")
    log("  - 300 Behavioral Guidance Mode scenarios")
    log("  - 300 Knowledge Mode scenarios")
    log("  - Single consistent format with trigger words")
    log("  - LoRA best practices from CivitAI & FAL.ai")
    log("")

    all_content = []
    total_generated = 0

    for i, category in enumerate(ALL_CATEGORIES, 1):
        log("")
        log(f"[{i}/{len(ALL_CATEGORIES)}] Processing: {category['name']}")
        log(f"   Target: {category['count']} scenarios")

        content = generate_scenarios_for_category(category)
        if content:
            all_content.append(content)

            # Count scenarios
            behavioral_count = content.count("Cherokee Behavioral Guidance Mode:")
            knowledge_count = content.count("Cherokee Knowledge Mode:")
            total_scenarios = behavioral_count + knowledge_count
            total_generated += total_scenarios

            log(f"✅ Category complete. Total so far: {total_generated}/600")
        else:
            log(f"⚠️  Category failed. Continuing...")

        # Rate limit (be nice to Ollama)
        if i < len(ALL_CATEGORIES):
            log("⏳ Waiting 3 seconds before next category...")
            time.sleep(3)

    # Write all content to file
    log("")
    log("💾 Writing all scenarios to file...")
    with open(OUTPUT_FILE, 'w') as f:
        f.write("# PHASE 3: 600 BALANCED SCENARIOS WITH TRIGGER WORDS\n")
        f.write("# Format: Single consistent format for LoRA training\n")
        f.write("# Based on best practices from CivitAI and FAL.ai guides\n")
        f.write("# 300 Behavioral + 300 Knowledge = 600 total\n\n")

        for content in all_content:
            f.write(content)
            f.write("\n\n")

    log(f"✅ Wrote scenarios to: {OUTPUT_FILE}")
    log("")
    log("="*80)
    log("📊 PHASE 3 GENERATION SUMMARY")
    log("="*80)
    log(f"Total scenarios generated: {total_generated}/600")
    log(f"Output file: {OUTPUT_FILE}")
    log("")
    log("Next steps:")
    log("1. Review generated scenarios for quality")
    log("2. Manually add any missing scenarios to reach 600")
    log("3. Train Phase 3 model with 1000-step targeting")
    log("4. Quality sampling at steps 200, 400, 600, 800, 1000")
    log("")
    log("🦅 Mitakuye Oyasin - All Our Relations 🔥")

if __name__ == "__main__":
    main()
