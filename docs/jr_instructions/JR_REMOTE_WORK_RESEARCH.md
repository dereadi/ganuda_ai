# Jr Instructions: Remote Work Opportunity Research

**Priority**: 1
**Assigned Jr**: it_triad_jr
**Objective**: Research and catalog remote work opportunities matching Federation skills

---

## OBJECTIVE

Use Crawl4AI to research remote work opportunities across multiple platforms. Analyze and categorize opportunities that match the Cherokee AI Federation's demonstrated skills.

---

### Task 1: Create Job Research Module

Create `/ganuda/jr_executor/job_research.py`:

```python
#!/usr/bin/env python3
"""
Remote Work Opportunity Research Module
Cherokee AI Federation - Income Generation Research
For Seven Generations
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path

# Try crawl4ai, fall back to basic requests
try:
    from crawl4ai import AsyncWebCrawler
    HAS_CRAWL4AI = True
except ImportError:
    HAS_CRAWL4AI = False
    import urllib.request

OUTPUT_DIR = "/ganuda/data/job_research"

# Remote work platforms to research
JOB_SOURCES = {
    'weworkremotely': {
        'name': 'We Work Remotely',
        'urls': [
            'https://weworkremotely.com/categories/remote-programming-jobs',
            'https://weworkremotely.com/categories/remote-devops-sysadmin-jobs',
            'https://weworkremotely.com/categories/remote-data-jobs',
        ],
        'type': 'job_board'
    },
    'remoteok': {
        'name': 'RemoteOK',
        'urls': [
            'https://remoteok.com/remote-python-jobs',
            'https://remoteok.com/remote-dev-jobs',
            'https://remoteok.com/remote-devops-jobs',
            'https://remoteok.com/remote-ai-jobs',
        ],
        'type': 'job_board'
    },
    'hn_whoishiring': {
        'name': 'Hacker News Who is Hiring',
        'urls': [
            'https://news.ycombinator.com/item?id=42575537',  # Dec 2024 thread
        ],
        'type': 'forum'
    },
    'github_jobs_resources': {
        'name': 'GitHub Remote Jobs Resources',
        'urls': [
            'https://github.com/remoteintech/remote-jobs',
            'https://github.com/lukasz-madon/awesome-remote-job',
        ],
        'type': 'resource_list'
    },
    'freelance': {
        'name': 'Freelance Platforms Info',
        'urls': [
            'https://www.upwork.com/freelance-jobs/python/',
            'https://www.toptal.com/developers',
        ],
        'type': 'freelance'
    }
}

# Skills to match against
FEDERATION_SKILLS = [
    # Languages
    'python', 'sql', 'bash', 'javascript', 'typescript',
    # AI/ML
    'llm', 'ai', 'machine learning', 'ml', 'nlp', 'gpt', 'claude',
    'langchain', 'openai', 'anthropic', 'huggingface', 'transformers',
    'inference', 'fine-tuning', 'prompt engineering',
    # Infrastructure
    'postgresql', 'postgres', 'database', 'linux', 'devops',
    'docker', 'kubernetes', 'ansible', 'terraform',
    'aws', 'gcp', 'cloud', 'infrastructure',
    # Development
    'api', 'rest', 'backend', 'flask', 'fastapi',
    'automation', 'scripting', 'integration',
    # Other
    'remote', 'contract', 'freelance', 'consulting',
    'senior', 'architect', 'lead'
]


async def fetch_url_crawl4ai(url: str) -> dict:
    """Fetch URL using Crawl4AI."""
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return {
                'success': True,
                'url': url,
                'content': result.markdown,
                'length': len(result.markdown),
                'error': None
            }
    except Exception as e:
        return {
            'success': False,
            'url': url,
            'content': None,
            'length': 0,
            'error': str(e)
        }


def fetch_url_basic(url: str) -> dict:
    """Fetch URL using basic urllib."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
            return {
                'success': True,
                'url': url,
                'content': content,
                'length': len(content),
                'error': None
            }
    except Exception as e:
        return {
            'success': False,
            'url': url,
            'content': None,
            'length': 0,
            'error': str(e)
        }


async def fetch_url(url: str) -> dict:
    """Fetch URL using best available method."""
    if HAS_CRAWL4AI:
        return await fetch_url_crawl4ai(url)
    else:
        return fetch_url_basic(url)


def analyze_content_for_skills(content: str) -> dict:
    """Analyze content for matching skills."""
    if not content:
        return {'matches': [], 'score': 0}

    content_lower = content.lower()
    matches = []

    for skill in FEDERATION_SKILLS:
        count = content_lower.count(skill.lower())
        if count > 0:
            matches.append({'skill': skill, 'count': count})

    # Sort by count
    matches.sort(key=lambda x: x['count'], reverse=True)

    # Calculate relevance score
    score = sum(m['count'] for m in matches[:10])  # Top 10 skills

    return {
        'matches': matches[:20],  # Top 20 matches
        'score': score,
        'total_skills_found': len(matches)
    }


def extract_job_indicators(content: str) -> dict:
    """Extract job-related indicators from content."""
    if not content:
        return {}

    content_lower = content.lower()

    indicators = {
        'has_salary': bool(re.search(r'\$[\d,]+k?|\d+k\s*(usd|/yr|per year)', content_lower)),
        'is_remote': 'remote' in content_lower,
        'is_contract': any(w in content_lower for w in ['contract', 'freelance', 'consulting']),
        'is_fulltime': 'full-time' in content_lower or 'full time' in content_lower,
        'experience_senior': any(w in content_lower for w in ['senior', '5+ years', '7+ years', 'lead', 'principal']),
        'experience_mid': any(w in content_lower for w in ['3+ years', '4+ years', 'mid-level']),
    }

    # Try to extract salary ranges
    salary_matches = re.findall(r'\$[\d,]+(?:k)?(?:\s*-\s*\$?[\d,]+(?:k)?)?', content)
    if salary_matches:
        indicators['salary_mentions'] = salary_matches[:5]

    return indicators


async def research_source(source_key: str, source_info: dict) -> dict:
    """Research a single job source."""
    print(f"\n[{source_info['name']}] Researching {len(source_info['urls'])} URLs...")

    results = []
    for url in source_info['urls']:
        print(f"  Fetching: {url[:60]}...")
        result = await fetch_url(url)

        if result['success']:
            skill_analysis = analyze_content_for_skills(result['content'])
            job_indicators = extract_job_indicators(result['content'])

            results.append({
                'url': url,
                'success': True,
                'content_length': result['length'],
                'skill_analysis': skill_analysis,
                'job_indicators': job_indicators,
                'preview': result['content'][:2000] if result['content'] else None
            })
            print(f"    ✓ {result['length']} chars, {skill_analysis['total_skills_found']} skills matched")
        else:
            results.append({
                'url': url,
                'success': False,
                'error': result['error']
            })
            print(f"    ✗ Error: {result['error'][:50]}")

    return {
        'source': source_key,
        'name': source_info['name'],
        'type': source_info['type'],
        'urls_fetched': len(results),
        'successful': sum(1 for r in results if r.get('success')),
        'total_skill_score': sum(r.get('skill_analysis', {}).get('score', 0) for r in results),
        'results': results
    }


async def run_full_research():
    """Run research across all job sources."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("Cherokee AI Federation - Remote Work Research")
    print("=" * 60)
    print(f"Date: {datetime.now().isoformat()}")
    print(f"Sources: {len(JOB_SOURCES)}")
    print(f"Skills to match: {len(FEDERATION_SKILLS)}")
    print()

    all_results = []

    for source_key, source_info in JOB_SOURCES.items():
        result = await research_source(source_key, source_info)
        all_results.append(result)

        # Save individual source result
        out_file = f"{OUTPUT_DIR}/source_{source_key}.json"
        with open(out_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

    # Generate summary
    summary = generate_research_summary(all_results)

    with open(f"{OUTPUT_DIR}/research_summary.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    # Print summary
    print("\n" + "=" * 60)
    print("RESEARCH SUMMARY")
    print("=" * 60)
    print(f"Sources researched: {summary['total_sources']}")
    print(f"URLs fetched: {summary['total_urls']}")
    print(f"Successful fetches: {summary['successful_fetches']}")
    print(f"\nTop Skills in Demand:")
    for skill in summary['top_skills'][:10]:
        print(f"  {skill['skill']}: {skill['total_count']} mentions")
    print(f"\nOutput: {OUTPUT_DIR}/")

    return summary


def generate_research_summary(results: list) -> dict:
    """Generate summary across all research results."""

    # Aggregate skill counts
    skill_totals = {}
    for source in results:
        for result in source.get('results', []):
            if result.get('success'):
                for match in result.get('skill_analysis', {}).get('matches', []):
                    skill = match['skill']
                    skill_totals[skill] = skill_totals.get(skill, 0) + match['count']

    # Sort skills by total count
    top_skills = [
        {'skill': k, 'total_count': v}
        for k, v in sorted(skill_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    # Source rankings
    source_rankings = [
        {
            'source': r['name'],
            'type': r['type'],
            'skill_score': r['total_skill_score'],
            'urls': r['urls_fetched'],
            'successful': r['successful']
        }
        for r in sorted(results, key=lambda x: x['total_skill_score'], reverse=True)
    ]

    return {
        'generated_at': datetime.now().isoformat(),
        'total_sources': len(results),
        'total_urls': sum(r['urls_fetched'] for r in results),
        'successful_fetches': sum(r['successful'] for r in results),
        'top_skills': top_skills,
        'source_rankings': source_rankings,
        'federation_skills_searched': FEDERATION_SKILLS
    }


if __name__ == '__main__':
    asyncio.run(run_full_research())
```

---

### Task 2: Create Skills Extraction Script

Create `/ganuda/jr_executor/extract_skills_inventory.py`:

```python
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

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

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
```

---

### Task 3: Create Research Runner Script

Create `/ganuda/jr_executor/run_job_research.sh`:

```bash
#!/bin/bash
# Run Remote Work Research Pipeline
# Cherokee AI Federation - For Seven Generations

cd /ganuda/jr_executor
source /home/dereadi/cherokee_venv/bin/activate

echo "=============================================="
echo "Cherokee AI Federation - Remote Work Research"
echo "=============================================="
echo ""

# Step 1: Extract skills inventory from thermal memory
echo "[1/2] Extracting Skills Inventory..."
python3 extract_skills_inventory.py

echo ""
echo "[2/2] Researching Job Sources..."
python3 job_research.py

echo ""
echo "=============================================="
echo "Research Complete!"
echo "=============================================="
echo ""
echo "Output files:"
ls -la /ganuda/data/job_research/

echo ""
echo "Skills Inventory:"
cat /ganuda/data/job_research/skills_inventory.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  Memories analyzed: {data[\"memories_analyzed\"]}')
print(f'  Projects demonstrated: {len(data[\"projects\"])}')
print(f'  Skill categories: {len(data[\"skill_summary\"])}')
"

echo ""
echo "Job Research Summary:"
cat /ganuda/data/job_research/research_summary.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  Sources researched: {data[\"total_sources\"]}')
print(f'  URLs fetched: {data[\"total_urls\"]}')
print(f'  Top skill in demand: {data[\"top_skills\"][0][\"skill\"]} ({data[\"top_skills\"][0][\"total_count\"]} mentions)')
" 2>/dev/null || echo "  (Summary pending)"
```

---

## SUCCESS CRITERIA

1. job_research.py fetches from multiple job sources
2. extract_skills_inventory.py analyzes thermal memory
3. Skills inventory generated with categories
4. Project portfolio extracted
5. Job sources analyzed for skill matches
6. research_summary.json and skills_inventory.json created

---

## SKILL CATEGORIES TO EXTRACT

| Category | Skills |
|----------|--------|
| Languages | Python, SQL, Bash, JavaScript |
| AI/ML | LLM Orchestration, Inference, Prompt Engineering |
| Infrastructure | Database, Distributed Systems, DevOps, Monitoring |
| Development | API, Automation, Web Scraping, Integration |
| Architecture | System Design, Multi-Agent, Memory Systems |

---

*For Seven Generations - Cherokee AI Federation*
