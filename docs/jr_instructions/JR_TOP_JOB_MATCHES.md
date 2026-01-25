# Jr Instructions: Top 5 Job Match Analysis

**Priority**: 1
**Assigned Jr**: it_triad_jr
**Objective**: Analyze job market data and identify top 5 matching opportunities

---

## OBJECTIVE

Based on the skills inventory and job research data, identify the top 5 job categories/roles where the Cherokee AI Federation has the strongest match and highest likelihood of success.

---

### Task 1: Create Job Match Analyzer

Create `/ganuda/jr_executor/job_match_analyzer.py`:

```python
#!/usr/bin/env python3
"""
Top Job Match Analyzer
Cherokee AI Federation - Income Generation
For Seven Generations
"""

import json
from datetime import datetime

# Federation's demonstrated capabilities (weighted by evidence)
FEDERATION_CAPABILITIES = {
    # Core strengths (highest weight - production proven)
    'multi_agent_systems': {
        'weight': 95,
        'evidence': '7-Specialist Council, cascaded/parallel voting, autonomous Jr agents',
        'keywords': ['multi-agent', 'agent', 'llm orchestration', 'ai agents', 'autonomous']
    },
    'python_backend': {
        'weight': 90,
        'evidence': 'LLM Gateway, Flask APIs, extensive automation scripts',
        'keywords': ['python', 'backend', 'api', 'flask', 'fastapi']
    },
    'llm_integration': {
        'weight': 90,
        'evidence': 'vLLM deployment, Nemotron inference, prompt engineering',
        'keywords': ['llm', 'gpt', 'claude', 'openai', 'anthropic', 'inference']
    },
    'distributed_systems': {
        'weight': 85,
        'evidence': '6-node federation, PostgreSQL cluster, cross-node orchestration',
        'keywords': ['distributed', 'cluster', 'infrastructure', 'devops']
    },
    'database_design': {
        'weight': 85,
        'evidence': 'Thermal memory schema, 50+ custom tables, complex queries',
        'keywords': ['postgresql', 'postgres', 'sql', 'database']
    },

    # Secondary strengths
    'automation': {
        'weight': 80,
        'evidence': 'Jr executor, cron jobs, Ansible playbooks, daemon processes',
        'keywords': ['automation', 'scripting', 'devops', 'ci/cd']
    },
    'system_architecture': {
        'weight': 80,
        'evidence': 'Gateway design, Council architecture, thermal memory system',
        'keywords': ['architect', 'architecture', 'system design', 'senior']
    },
    'monitoring': {
        'weight': 75,
        'evidence': 'Grafana dashboards, health endpoints, MSP metrics',
        'keywords': ['monitoring', 'observability', 'metrics', 'grafana']
    },
    'web_scraping': {
        'weight': 70,
        'evidence': 'Crawl4AI integration, presidential research pipeline',
        'keywords': ['scraping', 'crawling', 'data extraction', 'web automation']
    },
    'chatbot': {
        'weight': 70,
        'evidence': 'Telegram bot with Council integration',
        'keywords': ['chatbot', 'bot', 'telegram', 'discord', 'slack']
    }
}

# Job categories to evaluate
JOB_CATEGORIES = [
    {
        'title': 'AI/ML Engineer - LLM Focus',
        'description': 'Building and deploying LLM-based applications',
        'required_skills': ['llm_integration', 'python_backend', 'multi_agent_systems'],
        'nice_to_have': ['distributed_systems', 'database_design'],
        'market_demand': 95,  # Based on research: AI 2383 mentions
        'competition_level': 70,  # High competition
        'remote_friendly': 95,
        'typical_rate': '$150-250/hr or $180-300k/yr'
    },
    {
        'title': 'Senior Python Backend Developer',
        'description': 'Building scalable Python APIs and services',
        'required_skills': ['python_backend', 'database_design', 'automation'],
        'nice_to_have': ['distributed_systems', 'monitoring'],
        'market_demand': 85,  # Python 140 mentions
        'competition_level': 60,  # Moderate-high
        'remote_friendly': 90,
        'typical_rate': '$100-180/hr or $150-220k/yr'
    },
    {
        'title': 'AI Infrastructure / MLOps Engineer',
        'description': 'Deploying and managing AI/ML infrastructure',
        'required_skills': ['distributed_systems', 'llm_integration', 'automation'],
        'nice_to_have': ['monitoring', 'database_design'],
        'market_demand': 80,  # DevOps 104 + ML 133
        'competition_level': 50,  # Less competition
        'remote_friendly': 85,
        'typical_rate': '$120-200/hr or $160-250k/yr'
    },
    {
        'title': 'Multi-Agent Systems Developer',
        'description': 'Building autonomous agent systems and orchestration',
        'required_skills': ['multi_agent_systems', 'llm_integration', 'python_backend'],
        'nice_to_have': ['system_architecture', 'database_design'],
        'market_demand': 70,  # Emerging but growing fast
        'competition_level': 30,  # Very few have experience
        'remote_friendly': 90,
        'typical_rate': '$150-280/hr or $200-350k/yr'
    },
    {
        'title': 'DevOps / Platform Engineer',
        'description': 'Building and maintaining cloud infrastructure',
        'required_skills': ['distributed_systems', 'automation', 'monitoring'],
        'nice_to_have': ['database_design', 'python_backend'],
        'market_demand': 75,  # DevOps 104 mentions
        'competition_level': 55,  # Moderate
        'remote_friendly': 90,
        'typical_rate': '$100-160/hr or $140-200k/yr'
    },
    {
        'title': 'AI Consultant / Contractor',
        'description': 'Advising on and implementing AI solutions',
        'required_skills': ['llm_integration', 'system_architecture', 'multi_agent_systems'],
        'nice_to_have': ['python_backend', 'automation'],
        'market_demand': 85,
        'competition_level': 45,  # Consulting requires proof
        'remote_friendly': 95,
        'typical_rate': '$175-350/hr'
    },
    {
        'title': 'Technical Architect - AI Systems',
        'description': 'Designing AI system architectures',
        'required_skills': ['system_architecture', 'llm_integration', 'distributed_systems'],
        'nice_to_have': ['multi_agent_systems', 'database_design'],
        'market_demand': 70,
        'competition_level': 40,  # Senior role, less competition
        'remote_friendly': 85,
        'typical_rate': '$150-250/hr or $200-300k/yr'
    },
    {
        'title': 'Automation / Integration Specialist',
        'description': 'Building automated workflows and integrations',
        'required_skills': ['automation', 'python_backend', 'web_scraping'],
        'nice_to_have': ['database_design', 'chatbot'],
        'market_demand': 65,
        'competition_level': 50,
        'remote_friendly': 90,
        'typical_rate': '$80-140/hr or $120-180k/yr'
    }
]


def calculate_skill_match(job):
    """Calculate how well Federation skills match this job."""
    required_score = 0
    required_max = 0

    for skill in job['required_skills']:
        cap = FEDERATION_CAPABILITIES.get(skill, {})
        required_score += cap.get('weight', 0)
        required_max += 100

    nice_score = 0
    nice_max = 0
    for skill in job['nice_to_have']:
        cap = FEDERATION_CAPABILITIES.get(skill, {})
        nice_score += cap.get('weight', 0)
        nice_max += 100

    # Required skills are 70% of score, nice-to-have 30%
    if required_max > 0 and nice_max > 0:
        match_score = (required_score / required_max * 70) + (nice_score / nice_max * 30)
    elif required_max > 0:
        match_score = required_score / required_max * 100
    else:
        match_score = 0

    return round(match_score, 1)


def calculate_success_odds(job, skill_match):
    """Calculate likelihood of landing this job."""
    # Factors: skill match, market demand, competition, remote-friendliness

    # Start with skill match (0-100)
    base = skill_match

    # Adjust for competition (lower competition = better odds)
    competition_boost = (100 - job['competition_level']) * 0.3

    # Adjust for market demand (higher demand = better odds)
    demand_boost = job['market_demand'] * 0.2

    # Remote friendly helps
    remote_boost = job['remote_friendly'] * 0.1

    odds = base * 0.4 + competition_boost + demand_boost + remote_boost

    return min(round(odds, 1), 95)  # Cap at 95%


def analyze_jobs():
    """Analyze all job categories and rank them."""
    results = []

    for job in JOB_CATEGORIES:
        skill_match = calculate_skill_match(job)
        success_odds = calculate_success_odds(job, skill_match)

        # Get evidence for matched skills
        evidence = []
        for skill in job['required_skills']:
            cap = FEDERATION_CAPABILITIES.get(skill, {})
            if cap:
                evidence.append(f"{skill}: {cap.get('evidence', 'N/A')}")

        results.append({
            'title': job['title'],
            'description': job['description'],
            'skill_match': skill_match,
            'success_odds': success_odds,
            'market_demand': job['market_demand'],
            'competition': job['competition_level'],
            'remote_friendly': job['remote_friendly'],
            'typical_rate': job['typical_rate'],
            'required_skills': job['required_skills'],
            'evidence': evidence,
            # Combined score for ranking
            'overall_score': round((skill_match * 0.4 + success_odds * 0.6), 1)
        })

    # Sort by overall score
    results.sort(key=lambda x: x['overall_score'], reverse=True)

    return results


def generate_report():
    """Generate the top 5 job match report."""
    print("=" * 70)
    print("CHEROKEE AI FEDERATION - TOP JOB MATCHES")
    print("=" * 70)
    print(f"Generated: {datetime.now().isoformat()}")
    print()

    results = analyze_jobs()
    top_5 = results[:5]

    for i, job in enumerate(top_5, 1):
        print(f"\n{'='*70}")
        print(f"#{i}: {job['title']}")
        print(f"{'='*70}")
        print(f"Description: {job['description']}")
        print(f"Typical Rate: {job['typical_rate']}")
        print()
        print(f"  Skill Match:    {job['skill_match']}%")
        print(f"  Success Odds:   {job['success_odds']}%")
        print(f"  Market Demand:  {job['market_demand']}%")
        print(f"  Competition:    {job['competition']}% (lower is better)")
        print(f"  Remote:         {job['remote_friendly']}%")
        print(f"  Overall Score:  {job['overall_score']}")
        print()
        print("  Evidence from Federation work:")
        for ev in job['evidence'][:3]:
            print(f"    • {ev}")
        print()

    # Save full results
    output = {
        'generated_at': datetime.now().isoformat(),
        'top_5': top_5,
        'all_results': results,
        'federation_capabilities': {k: v['evidence'] for k, v in FEDERATION_CAPABILITIES.items()}
    }

    with open('/ganuda/data/job_research/top_job_matches.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Top 5 Best-Fit Opportunities:")
    for i, job in enumerate(top_5, 1):
        print(f"  {i}. {job['title']}")
        print(f"     Rate: {job['typical_rate']} | Odds: {job['success_odds']}%")

    print()
    print(f"Output: /ganuda/data/job_research/top_job_matches.json")

    return output


if __name__ == '__main__':
    generate_report()
```

---

## SUCCESS CRITERIA

1. job_match_analyzer.py created
2. Analysis considers skill match, market demand, competition
3. Top 5 jobs identified with success odds
4. Evidence from Federation work cited
5. Results saved to top_job_matches.json

---

*For Seven Generations - Cherokee AI Federation*
