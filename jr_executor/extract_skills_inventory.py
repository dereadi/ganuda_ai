#!/usr/bin/env python3
"""
Skills Inventory Extractor
Analyzes thermal memory to extract demonstrated skills and capabilities.
Cherokee AI Federation - For Seven Generations
"""

import psycopg2
import json
import re
from datetime import datetime
from collections import defaultdict

import sys
sys.path.insert(0, '/ganuda')
from lib.secrets_loader import get_db_config
DB_CONFIG = get_db_config()

OUTPUT_DIR = "/ganuda/data/job_research"

# Skill categories and keywords
SKILL_CATEGORIES = {
    'languages': {
        'python': ['python', 'python3', 'py'],
        'sql': ['sql', 'postgresql', 'postgres', 'psql'],
        'bash': ['bash', 'shell', 'sh'],
        'javascript': ['javascript', 'js', 'node'],
    },
    'ai_ml': {
        'llm_orchestration': ['llm', 'council', 'specialist', 'multi-agent', 'gateway'],
        'inference': ['inference', 'vllm', 'nemotron', 'model'],
        'prompt_engineering': ['prompt', 'system prompt', 'instruction'],
        'embeddings': ['embedding', 'vector', 'similarity'],
    },
    'infrastructure': {
        'database': ['postgresql', 'database', 'thermal memory', 'schema'],
        'distributed_systems': ['federation', 'cluster', 'node', 'redfin', 'bluefin'],
        'devops': ['ansible', 'systemd', 'cron', 'daemon', 'deployment'],
        'monitoring': ['health', 'metrics', 'monitoring', 'grafana'],
    },
    'development': {
        'api_development': ['api', 'gateway', 'endpoint', 'rest', 'flask'],
        'automation': ['automation', 'script', 'cron', 'daemon'],
        'web_scraping': ['crawl4ai', 'scraping', 'fetch', 'web research'],
        'integration': ['integration', 'interface', 'connector'],
    },
    'architecture': {
        'system_design': ['architecture', 'design', 'schema', 'framework'],
        'multi_agent': ['council', 'specialist', 'cascaded', 'parallel voting'],
        'memory_systems': ['thermal memory', 'pheromone', 'decay', 'msp'],
    }
}

# Project artifacts to look for
PROJECT_PATTERNS = [
    (r'gateway\.py', 'LLM Gateway', 'Built production API gateway with auth, rate limiting, Council voting'),
    (r'thermal.memory', 'Thermal Memory System', 'Designed pheromone-based knowledge decay system (MSP-aligned)'),
    (r'council.*vote', '7-Specialist Council', 'Multi-agent voting system with cascaded/parallel modes'),
    (r'jr.*(instruction|executor|queue)', 'Jr Task System', 'Autonomous agent task queue and execution framework'),
    (r'crawl4ai', 'Web Research Pipeline', 'Automated web scraping and analysis system'),
    (r'xonsh.*xontrib', 'Custom Shell Integration', 'Python shell with custom database/infrastructure commands'),
    (r'telegram.*bot', 'Telegram Bot Integration', 'AI-powered chat bot with Council access'),
    (r'spatial.*zone', 'Spatial Awareness CMDB', 'Zone-based device and context management'),
    (r'presidential.*study', 'Behavioral Analysis Pipeline', 'Automated research and pattern analysis system'),
]


def get_thermal_memories():
    """Fetch relevant thermal memories for skill extraction."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get recent and high-temperature memories
    cur.execute("""
        SELECT id, original_content, current_stage, temperature_score, created_at
        FROM thermal_memory_archive
        WHERE temperature_score >= 80
           OR created_at > NOW() - INTERVAL '30 days'
        ORDER BY temperature_score DESC, created_at DESC
        LIMIT 500
    """)

    memories = cur.fetchall()
    cur.close()
    conn.close()

    return memories


def extract_skills_from_content(content: str) -> dict:
    """Extract skill mentions from content."""
    if not content:
        return {}

    content_lower = content.lower()
    found_skills = defaultdict(list)

    for category, skills in SKILL_CATEGORIES.items():
        for skill_name, keywords in skills.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    found_skills[category].append(skill_name)
                    break  # Only count skill once per content

    return dict(found_skills)


def extract_projects(content: str) -> list:
    """Extract project artifacts from content."""
    if not content:
        return []

    content_lower = content.lower()
    projects = []

    for pattern, name, description in PROJECT_PATTERNS:
        if re.search(pattern, content_lower):
            projects.append({
                'name': name,
                'description': description
            })

    return projects


def generate_skills_inventory():
    """Generate comprehensive skills inventory from thermal memory."""
    print("=" * 60)
    print("Cherokee AI Federation - Skills Inventory Extraction")
    print("=" * 60)
    print(f"Date: {datetime.now().isoformat()}")
    print()

    memories = get_thermal_memories()
    print(f"Analyzing {len(memories)} thermal memories...")

    # Aggregate skills
    skill_counts = defaultdict(lambda: defaultdict(int))
    all_projects = {}
    memory_samples = []

    for mem_id, content, stage, temp, created in memories:
        skills = extract_skills_from_content(content)
        projects = extract_projects(content)

        # Count skills
        for category, skill_list in skills.items():
            for skill in skill_list:
                skill_counts[category][skill] += 1

        # Track projects (dedupe by name)
        for project in projects:
            if project['name'] not in all_projects:
                all_projects[project['name']] = project

        # Keep sample memories
        if len(memory_samples) < 20 and temp >= 90:
            memory_samples.append({
                'id': mem_id,
                'preview': content[:300] if content else '',
                'stage': stage,
                'temperature': float(temp) if temp else 0,
                'skills_found': skills,
                'projects_found': [p['name'] for p in projects]
            })

    # Build inventory
    inventory = {
        'generated_at': datetime.now().isoformat(),
        'memories_analyzed': len(memories),
        'skill_summary': {},
        'projects': list(all_projects.values()),
        'sample_memories': memory_samples
    }

    # Format skill summary
    for category, skills in skill_counts.items():
        inventory['skill_summary'][category] = [
            {'skill': skill, 'mentions': count}
            for skill, count in sorted(skills.items(), key=lambda x: x[1], reverse=True)
        ]

    # Save inventory
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(f"{OUTPUT_DIR}/skills_inventory.json", 'w') as f:
        json.dump(inventory, f, indent=2, default=str)

    # Print summary
    print("\n" + "=" * 60)
    print("SKILLS INVENTORY SUMMARY")
    print("=" * 60)

    for category, skills in inventory['skill_summary'].items():
        print(f"\n{category.upper().replace('_', ' ')}:")
        for s in skills[:5]:
            print(f"  • {s['skill']}: {s['mentions']} mentions")

    print(f"\nPROJECTS DEMONSTRATED ({len(inventory['projects'])}):")
    for p in inventory['projects']:
        print(f"  • {p['name']}")
        print(f"    {p['description']}")

    print(f"\nOutput: {OUTPUT_DIR}/skills_inventory.json")

    return inventory


if __name__ == '__main__':
    generate_skills_inventory()