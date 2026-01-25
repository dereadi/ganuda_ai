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