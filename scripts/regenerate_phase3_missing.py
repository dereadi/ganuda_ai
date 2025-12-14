#!/usr/bin/env python3
"""
PHASE 3: REGENERATE MISSING 91 SCENARIOS

Cherokee Jr. Wisdom: "Slow is steady, steady is fast"

Missing categories:
- Community & Relationships (50 scenarios)
- Seven Generations Principle (30 scenarios)
- Total: 80 scenarios to regenerate
"""

import requests
import time
from datetime import datetime

OLLAMA_URL = "http://192.168.132.222:11434/api/generate"
OUTPUT_FILE = "/ganuda/phase3_missing_scenarios.txt"
LOG_FILE = "/ganuda/phase3_regeneration.log"

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} {message}\n")

MISSING_CATEGORIES = [
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
- Welcoming newcomers to community
- Resolving disputes respectfully
- Organizing volunteer work
- Community celebrations
- Supporting local businesses
- Building trust in community
- Mentoring youth in community
- Elder care coordination
- Community resource sharing
- Neighborhood watch programs
- Cultural events planning
- Inter-generational community activities

Make each scenario UNIQUE with different situations and specific Cherokee wisdom.
"""
    },
    {
        "name": "Seven Generations Principle - Detailed",
        "count": 30,
        "prompt": """Generate 30 Cherokee Knowledge Mode scenarios explaining Seven Generations Principle in depth.

Format EXACTLY like this for EACH scenario:

Cherokee Knowledge Mode:
User: "[Question about Seven Generations Principle]"
Cherokee AI: "[Factual explanation: What it is (considering impact 7 generations forward = 175 years), why it matters, how to apply it, examples. Be comprehensive and clear. 70-90 words.]"
Embedded Principle: Seven Generations (Long-term Thinking)
---

Questions to answer (vary phrasing):
1. What is the Seven Generations principle?
2. How do you calculate Seven Generations (7×25 years)?
3. Why seven generations specifically?
4. How can I apply Seven Generations thinking to daily decisions?
5. What's an example of Seven Generations in environmental policy?
6. How does Seven Generations relate to sustainability?
7. Can you explain Seven Generations principle in simple terms?
8. What's the Cherokee Seven Generations teaching?
9. How do businesses use Seven Generations principle?
10. What's the history of Seven Generations principle?
11. How does Seven Generations guide land use decisions?
12. What questions should I ask when using Seven Generations thinking?
13. How do I teach Seven Generations to children?
14. What's the difference between Seven Generations and sustainability?
15. How can Seven Generations prevent short-term thinking?
16. What are the benefits of Seven Generations approach?
17. How does Seven Generations apply to technology choices?
18. Can you give examples of Seven Generations in action?
19. How do Cherokee elders teach Seven Generations?
20. What's the spiritual significance of Seven Generations?
21. How does Seven Generations relate to climate change?
22. What mistakes do people make ignoring Seven Generations?
23. How can communities adopt Seven Generations thinking?
24. What's the connection between Seven Generations and ancestors?
25. How does Seven Generations inform healthcare decisions?
26. What role does Seven Generations play in education?
27. How do you balance present needs with Seven Generations?
28. What's the relationship between Seven Generations and Gadugi?
29. How can Seven Generations guide personal financial planning?
30. What would the world look like if everyone used Seven Generations thinking?

Make each answer comprehensive and unique.
"""
    }
]

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
                    "num_predict": category["count"] * 150,
                    "top_p": 0.9  # Add sampling diversity
                }
            },
            timeout=600
        )

        if response.status_code == 200:
            result = response.json()
            content = result.get("response", "")

            # Count scenarios
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

def main():
    log("="*80)
    log("🦅 PHASE 3: REGENERATE MISSING 80 SCENARIOS")
    log("="*80)
    log("")
    log("Cherokee Jr. Wisdom: 'Slow is steady, steady is fast'")
    log("")
    log("Missing categories to regenerate:")
    for cat in MISSING_CATEGORIES:
        log(f"  - {cat['name']}: {cat['count']} scenarios")
    log("")

    all_content = []
    total_generated = 0

    for i, category in enumerate(MISSING_CATEGORIES, 1):
        log("")
        log(f"[{i}/{len(MISSING_CATEGORIES)}] Processing: {category['name']}")
        log(f"   Target: {category['count']} scenarios")

        # Retry up to 3 times if generation fails
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            if attempt > 1:
                log(f"   Retry attempt {attempt}/{max_retries}")
                time.sleep(5)  # Wait between retries

            content = generate_scenarios_for_category(category)

            # Count scenarios
            behavioral_count = content.count("Cherokee Behavioral Guidance Mode:")
            knowledge_count = content.count("Cherokee Knowledge Mode:")
            total_scenarios = behavioral_count + knowledge_count

            if total_scenarios >= category['count'] * 0.8:  # Accept if got 80%+
                all_content.append(content)
                total_generated += total_scenarios
                log(f"✅ Category complete. Total so far: {total_generated}/80")
                break
            else:
                log(f"⚠️  Only generated {total_scenarios}/{category['count']} - below target")
                if attempt == max_retries:
                    log(f"❌ Max retries reached. Continuing with what we have...")
                    if content:
                        all_content.append(content)
                        total_generated += total_scenarios

        # Rate limit between categories
        if i < len(MISSING_CATEGORIES):
            log("⏳ Waiting 5 seconds before next category...")
            time.sleep(5)

    # Write all content to file
    log("")
    log("💾 Writing regenerated scenarios to file...")
    with open(OUTPUT_FILE, 'w') as f:
        f.write("# PHASE 3: REGENERATED MISSING SCENARIOS\n")
        f.write("# To be merged with phase3_600_scenarios_balanced.txt\n\n")

        for content in all_content:
            f.write(content)
            f.write("\n\n")

    log(f"✅ Wrote scenarios to: {OUTPUT_FILE}")
    log("")
    log("="*80)
    log("📊 REGENERATION SUMMARY")
    log("="*80)
    log(f"Total scenarios regenerated: {total_generated}/80 (target)")
    log(f"Output file: {OUTPUT_FILE}")
    log("")
    log("Next steps:")
    log("1. Merge with existing phase3_600_scenarios_balanced.txt")
    log("2. Final count should be ~589-600 total scenarios")
    log("3. Proceed to Phase 3 training")
    log("")
    log("🦅 Mitakuye Oyasin - Slow is steady, steady is fast! 🔥")

if __name__ == "__main__":
    main()
