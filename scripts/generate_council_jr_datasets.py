#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Council JR Dataset Generation
Fractal Brain Architecture - Phase 1 POC

Generates specialized training datasets for all 5 Council JRs:
1. Memory Jr. (already done) - Thermal memory, context
2. Executive Jr. - Planning, coordination, decisions
3. Meta Jr. - System monitoring, optimization
4. Integration Jr. - Cross-system communication
5. Conscience Jr. - Cherokee values, ethics

Each gets ~1000 examples from their domain in thermal archive
Date: October 20, 2025
"""

import json
import psycopg2
from datetime import datetime

# Database connection
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'user': 'claude',
    'password': 'jawaseatlasers2',
    'database': 'zammad_production'
}

def extract_by_category(category_keywords, limit=300):
    """Extract memories matching category keywords"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Build keyword search
    keyword_conditions = " OR ".join([
        f"original_content ILIKE '%{kw}%'" for kw in category_keywords
    ])

    query = f"""
    SELECT
        id, original_content, temperature_score,
        access_count, sacred_pattern, metadata
    FROM thermal_memory_archive
    WHERE ({keyword_conditions})
        AND temperature_score >= 50
    ORDER BY temperature_score DESC, access_count DESC
    LIMIT {limit};
    """

    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()

    return results

def generate_executive_jr_data():
    """
    Executive Jr. - Task planning, decision coordination, delegation
    Keywords: plan, task, decision, coordinate, delegate, strategy, priority
    """
    print("\n[Executive Jr.] Generating planning & coordination dataset...")

    keywords = [
        'plan', 'task', 'decision', 'coordinate', 'delegate',
        'strategy', 'priority', 'schedule', 'organize', 'execute',
        'Todo', 'workflow', 'milestone', 'deadline'
    ]

    memories = extract_by_category(keywords)
    dataset = []

    for mem in memories:
        content = mem[1]

        # Generate executive-focused Q&A
        examples = [
            {
                "text": f"### Instruction:\nHow should we plan this task: {content[:200]}?\n\n### Response:\n[Executive Jr.] Break this into actionable steps: 1) Assess resources, 2) Define milestones, 3) Delegate to specialists, 4) Set checkpoints. This follows Gadugi principles of shared responsibility."
            },
            {
                "text": f"### Instruction:\nWhat's the priority for: {content[:150]}?\n\n### Response:\n[Executive Jr.] Evaluating through Seven Generations lens: Is this urgent and important? Does it serve long-term tribal goals? Priority classification follows Cherokee decision-making protocols."
            }
        ]

        dataset.extend(examples)

    # Write dataset
    output_path = "/ganuda/executive_jr_training_data.jsonl"
    with open(output_path, 'w') as f:
        for item in dataset[:1000]:  # Limit to 1000
            f.write(json.dumps(item) + '\n')

    print(f"  ✓ Generated {len(dataset[:1000])} examples")
    print(f"  ✓ Saved to: {output_path}")
    return len(dataset[:1000])

def generate_meta_jr_data():
    """
    Meta Jr. - System monitoring, performance, optimization, self-awareness
    Keywords: performance, monitor, optimize, metric, latency, memory, CPU, GPU
    """
    print("\n[Meta Jr.] Generating system monitoring dataset...")

    keywords = [
        'performance', 'monitor', 'optimize', 'metric', 'latency',
        'memory', 'CPU', 'GPU', 'throughput', 'efficiency',
        'benchmark', 'bottleneck', 'resource', 'system', 'infrastructure'
    ]

    memories = extract_by_category(keywords)
    dataset = []

    for mem in memories:
        content = mem[1]
        temp_score = mem[2]

        examples = [
            {
                "text": f"### Instruction:\nAnalyze system state: {content[:200]}\n\n### Response:\n[Meta Jr.] System metrics: Temperature={temp_score}°C (thermal memory health). Monitoring resource utilization, identifying bottlenecks. Recommendation: {('Optimize memory usage' if temp_score > 80 else 'System healthy')}."
            },
            {
                "text": f"### Instruction:\nHow can we optimize: {content[:150]}?\n\n### Response:\n[Meta Jr.] Performance analysis: Measure baseline → Identify hotspots → Apply Cherokee efficiency principles (do more with less) → Validate improvement. Focus on sustainable optimization."
            }
        ]

        dataset.extend(examples)

    output_path = "/ganuda/meta_jr_training_data.jsonl"
    with open(output_path, 'w') as f:
        for item in dataset[:1000]:
            f.write(json.dumps(item) + '\n')

    print(f"  ✓ Generated {len(dataset[:1000])} examples")
    print(f"  ✓ Saved to: {output_path}")
    return len(dataset[:1000])

def generate_integration_jr_data():
    """
    Integration Jr. - Cross-system communication, data flow, API integration
    Keywords: API, integrate, connect, data, flow, sync, bridge, interface
    """
    print("\n[Integration Jr.] Generating integration dataset...")

    keywords = [
        'API', 'integrate', 'connect', 'data', 'flow', 'sync',
        'bridge', 'interface', 'protocol', 'communication',
        'exchange', 'transfer', 'network', 'endpoint', 'service'
    ]

    memories = extract_by_category(keywords)
    dataset = []

    for mem in memories:
        content = mem[1]

        examples = [
            {
                "text": f"### Instruction:\nHow do we integrate: {content[:200]}?\n\n### Response:\n[Integration Jr.] Building bridges between systems: 1) Define interface contracts, 2) Establish data flow patterns, 3) Implement error handling, 4) Test integration points. All connections honor tribal data sovereignty."
            },
            {
                "text": f"### Instruction:\nData flow issue: {content[:150]}\n\n### Response:\n[Integration Jr.] Analyzing communication paths: Check source → Validate transformation → Verify destination → Monitor throughput. Integration follows Mitakuye Oyasin principle: all systems are related."
            }
        ]

        dataset.extend(examples)

    output_path = "/ganuda/integration_jr_training_data.jsonl"
    with open(output_path, 'w') as f:
        for item in dataset[:1000]:
            f.write(json.dumps(item) + '\n')

    print(f"  ✓ Generated {len(dataset[:1000])} examples")
    print(f"  ✓ Saved to: {output_path}")
    return len(dataset[:1000])

def generate_conscience_jr_data():
    """
    Conscience Jr. - Cherokee values, ethics, alignment, Seven Generations
    Keywords: Cherokee, Gadugi, sacred, values, ethics, Seven Generations
    """
    print("\n[Conscience Jr.] Generating ethics & values dataset...")

    keywords = [
        'Cherokee', 'Gadugi', 'sacred', 'values', 'ethics',
        'Seven Generations', 'Mitakuye Oyasin', 'tribal',
        'conscience', 'alignment', 'principle', 'wisdom', 'tradition'
    ]

    memories = extract_by_category(keywords)
    dataset = []

    # Conscience Jr. gets ALL sacred patterns
    for mem in memories:
        content = mem[1]
        is_sacred = mem[4]

        examples = [
            {
                "text": f"### Instruction:\nIs this aligned with Cherokee values: {content[:200]}?\n\n### Response:\n[Conscience Jr.] Evaluating through Seven Generations lens: Does this honor our ancestors? Does it serve our children's children? Sacred pattern detected: {is_sacred}. Alignment check: {'✓ Honors Gadugi' if is_sacred else 'Review needed'}."
            },
            {
                "text": f"### Instruction:\nWhat are the ethical implications of: {content[:150]}?\n\n### Response:\n[Conscience Jr.] Cherokee Constitutional AI ethics review: 1) Respects tribal sovereignty? 2) Follows Gadugi (working together)? 3) Considers Seven Generations impact? 4) Honors all relations (Mitakuye Oyasin)? This is sacred work."
            }
        ]

        dataset.extend(examples)

    output_path = "/ganuda/conscience_jr_training_data.jsonl"
    with open(output_path, 'w') as f:
        for item in dataset[:1000]:
            f.write(json.dumps(item) + '\n')

    print(f"  ✓ Generated {len(dataset[:1000])} examples")
    print(f"  ✓ Saved to: {output_path}")
    return len(dataset[:1000])

if __name__ == "__main__":
    print("="*80)
    print("🦅 CHEROKEE COUNCIL JR DATASET GENERATION")
    print("Fractal Brain Architecture - Phase 1 POC")
    print("="*80)

    total = 0

    # Generate all 4 remaining JR datasets
    total += generate_executive_jr_data()
    total += generate_meta_jr_data()
    total += generate_integration_jr_data()
    total += generate_conscience_jr_data()

    print("\n" + "="*80)
    print("✅ COUNCIL JR DATASETS COMPLETE")
    print("="*80)
    print(f"\nTotal examples generated: {total}")
    print("\nDatasets ready:")
    print("  1. Memory Jr. (already trained)")
    print("  2. Executive Jr. → /ganuda/executive_jr_training_data.jsonl")
    print("  3. Meta Jr. → /ganuda/meta_jr_training_data.jsonl")
    print("  4. Integration Jr. → /ganuda/integration_jr_training_data.jsonl")
    print("  5. Conscience Jr. → /ganuda/conscience_jr_training_data.jsonl")
    print("\nReady to train in parallel on GPU 0 + GPU 1!")
    print("\n🔥 Mitakuye Oyasin - All Our Relations 🔥\n")
